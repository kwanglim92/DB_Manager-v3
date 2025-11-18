#!/usr/bin/env python3
"""
데이터베이스 마이그레이션 스크립트
Default DB와 QC Spec 분리 및 Equipment Configuration 재설계
"""

import sqlite3
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def backup_database(db_path):
    """데이터베이스 백업"""
    backup_path = db_path.replace('.sqlite', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.sqlite')
    print(f"📦 데이터베이스 백업 중: {backup_path}")
    
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"✅ 백업 완료: {backup_path}")
    return backup_path

def create_new_tables(conn):
    """새로운 테이블 생성"""
    cursor = conn.cursor()
    
    # 1. QC_Spec_Master 테이블 생성
    print("📊 QC_Spec_Master 테이블 생성...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS QC_Spec_Master (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT NOT NULL UNIQUE,
        min_spec TEXT,
        max_spec TEXT,
        expected_value TEXT,
        check_type TEXT CHECK(check_type IN ('range', 'exact', 'boolean', 'exists')),
        category TEXT,
        severity TEXT CHECK(severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
        is_active BOOLEAN DEFAULT 1,
        is_common BOOLEAN DEFAULT 1,
        description TEXT,
        validation_rule TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 2. QC_Equipment_Exceptions 테이블 생성
    print("📊 QC_Equipment_Exceptions 테이블 생성...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS QC_Equipment_Exceptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        configuration_id INTEGER,
        model_id INTEGER,
        spec_master_id INTEGER NOT NULL,
        reason TEXT NOT NULL,
        approved_by TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (spec_master_id) REFERENCES QC_Spec_Master(id),
        UNIQUE(configuration_id, model_id, spec_master_id)
    )
    ''')
    
    # 3. QC_Spec_Overrides 테이블 생성
    print("📊 QC_Spec_Overrides 테이블 생성...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS QC_Spec_Overrides (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        spec_master_id INTEGER NOT NULL,
        configuration_id INTEGER,
        min_spec_override TEXT,
        max_spec_override TEXT,
        expected_value_override TEXT,
        reason TEXT,
        approved_by TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (spec_master_id) REFERENCES QC_Spec_Master(id),
        UNIQUE(spec_master_id, configuration_id)
    )
    ''')
    
    conn.commit()
    print("✅ 새로운 테이블 생성 완료")

def migrate_specs_to_master(conn):
    """기존 Default_DB_Values의 스펙을 QC_Spec_Master로 이동"""
    cursor = conn.cursor()
    
    print("🔄 기존 스펙 데이터 마이그레이션 시작...")
    
    # 1. 기존 스펙 데이터 조회
    cursor.execute('''
    SELECT DISTINCT parameter_name, min_spec, max_spec
    FROM Default_DB_Values
    WHERE min_spec IS NOT NULL OR max_spec IS NOT NULL
    ''')
    
    specs = cursor.fetchall()
    print(f"📊 마이그레이션할 스펙: {len(specs)}개")
    
    # 2. QC_Spec_Master에 삽입
    migrated = 0
    for param_name, min_spec, max_spec in specs:
        # 카테고리 추론
        category = 'General'
        if 'Temp' in param_name or 'Temperature' in param_name:
            category = 'Temperature'
        elif 'Pressure' in param_name:
            category = 'Pressure'
        elif 'Motion' in param_name:
            category = 'Motion'
        elif 'Safety' in param_name:
            category = 'Safety'
        elif 'Sensor' in param_name:
            category = 'Sensor'
            
        # severity 추론
        severity = 'MEDIUM'
        if 'Safety' in param_name or 'Limit' in param_name or 'Emergency' in param_name:
            severity = 'CRITICAL'
        elif 'Process' in param_name or 'Critical' in param_name:
            severity = 'HIGH'
        elif 'Warning' in param_name:
            severity = 'LOW'
            
        # check_type 결정
        check_type = 'range' if min_spec and max_spec else 'exists'
        
        try:
            cursor.execute('''
            INSERT INTO QC_Spec_Master 
            (item_name, min_spec, max_spec, check_type, category, severity, is_active, is_common)
            VALUES (?, ?, ?, ?, ?, ?, 1, 1)
            ''', (param_name, min_spec, max_spec, check_type, category, severity))
            migrated += 1
        except sqlite3.IntegrityError:
            # 이미 존재하는 경우 업데이트
            cursor.execute('''
            UPDATE QC_Spec_Master 
            SET min_spec=?, max_spec=?, check_type=?, category=?, severity=?
            WHERE item_name=?
            ''', (min_spec, max_spec, check_type, category, severity, param_name))
            
    conn.commit()
    print(f"✅ {migrated}개 스펙 마이그레이션 완료")
    
    # 3. 기존 Check list 데이터도 통합 (있다면)
    try:
        cursor.execute('''
        SELECT item_name, spec_min, spec_max, expected_value, category
        FROM QC_Checklist_Items
        WHERE is_active = 1
        ''')
        
        checklist_items = cursor.fetchall()
        if checklist_items:
            print(f"📊 Check list 항목 통합: {len(checklist_items)}개")
            
            for item_name, spec_min, spec_max, expected_value, category in checklist_items:
                cursor.execute('''
                INSERT OR REPLACE INTO QC_Spec_Master
                (item_name, min_spec, max_spec, expected_value, check_type, category, severity)
                VALUES (?, ?, ?, ?, ?, ?, 'HIGH')
                ''', (item_name, spec_min, spec_max, expected_value, 
                     'range' if spec_min else 'exact', category or 'General'))
            
            conn.commit()
            print("✅ Check list 항목 통합 완료")
    except sqlite3.OperationalError:
        print("ℹ️ QC_Checklist_Items 테이블이 없습니다. 건너뜁니다.")

def update_equipment_configurations(conn):
    """Equipment_Configurations 테이블 업데이트"""
    cursor = conn.cursor()
    
    print("🔄 Equipment_Configurations 테이블 업데이트...")
    
    # 각 컬럼을 개별적으로 추가 시도
    columns_to_add = [
        ('ae_type', 'TEXT'),
        ('cabinet_type', 'TEXT'),
        ('efem_type', 'TEXT'),
        ('config_code', 'TEXT')
    ]
    
    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f'ALTER TABLE Equipment_Configurations ADD COLUMN {col_name} {col_type}')
            print(f"✅ {col_name} 컬럼 추가 완료")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print(f"ℹ️ {col_name} 컬럼이 이미 존재합니다.")
            else:
                print(f"⚠️ {col_name} 컬럼 추가 실패: {e}")
    
    # 기존 데이터 업데이트
    cursor.execute('SELECT id, configuration_name FROM Equipment_Configurations')
    configs = cursor.fetchall()
    
    for config_id, config_name in configs:
        # config_name에서 정보 추출
        ae_type = '일체형'  # 기본값
        cabinet_type = 'T1'
        efem_type = 'Single'
        
        if config_name:
            config_lower = config_name.lower()
            if '분리' in config_name or 'separated' in config_lower:
                ae_type = '분리형'
            if 'double' in config_lower:
                efem_type = 'Double'
            elif 'none' in config_lower or '없음' in config_name:
                efem_type = 'None'
            if 'pb' in config_lower:
                cabinet_type = 'PB'
                
        # config_code 생성
        ae_code = 'I' if ae_type == '일체형' else 'S'
        cabinet_code = cabinet_type or 'NC'
        efem_code = efem_type[0] if efem_type != 'None' else 'N'
        
        # 모델 ID 조회
        cursor.execute('''
        SELECT equipment_type_id FROM Equipment_Configurations
        WHERE id = ?
        ''', (config_id,))
        
        result = cursor.fetchone()
        model_id = result[0] if result else 1
        
        config_code = f"M{model_id}_{ae_code}_{cabinet_code}_{efem_code}"
        
        # 업데이트
        cursor.execute('''
        UPDATE Equipment_Configurations
        SET ae_type=?, cabinet_type=?, efem_type=?, config_code=?
        WHERE id=?
        ''', (ae_type, cabinet_type, efem_type, config_code, config_id))
    
    conn.commit()
    print(f"✅ {len(configs)}개 Configuration 업데이트 완료")

def create_default_db_values_new(conn):
    """Default_DB_Values 테이블 재생성 (min/max_spec 제거)"""
    cursor = conn.cursor()
    
    print("🔄 Default_DB_Values 테이블 재구성...")
    
    # 1. 임시 테이블 생성
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Default_DB_Values_New (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        configuration_id INTEGER,
        equipment_type_id INTEGER,
        parameter_name TEXT NOT NULL,
        default_value TEXT,
        module TEXT,
        sub_module TEXT,
        data_type TEXT,
        unit TEXT,
        description TEXT,
        is_performance BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(configuration_id, equipment_type_id, parameter_name)
    )
    ''')
    
    # 2. 데이터 복사 (min_spec, max_spec 제외)
    cursor.execute('''
    INSERT INTO Default_DB_Values_New 
    (configuration_id, equipment_type_id, parameter_name, default_value, 
     module, sub_module, data_type, unit, description, is_performance)
    SELECT 
        configuration_id,
        equipment_type_id,
        parameter_name,
        default_value,
        module,
        part,
        item_type,
        NULL as unit,
        description,
        is_performance
    FROM Default_DB_Values
    ''')
    
    # 3. 기존 테이블 백업
    cursor.execute('ALTER TABLE Default_DB_Values RENAME TO Default_DB_Values_Old')
    
    # 4. 새 테이블로 교체
    cursor.execute('ALTER TABLE Default_DB_Values_New RENAME TO Default_DB_Values')
    
    conn.commit()
    print("✅ Default_DB_Values 테이블 재구성 완료")

def add_sample_qc_specs(conn):
    """샘플 QC 스펙 추가"""
    cursor = conn.cursor()
    
    print("📝 샘플 QC 스펙 추가...")
    
    sample_specs = [
        ('Temperature.Chamber.SetPoint', '20', '30', 'range', 'Temperature', 'CRITICAL'),
        ('Temperature.Chamber.Limit', '0', '100', 'range', 'Temperature', 'CRITICAL'),
        ('Pressure.Main.Vacuum', '1e-6', '1e-4', 'range', 'Pressure', 'HIGH'),
        ('Safety.EmergencyStop.Status', None, None, 'exact', 'Safety', 'CRITICAL', 'PASS'),
        ('Motion.Speed.Max', '0', '1000', 'range', 'Motion', 'MEDIUM'),
        ('Sensor.Calibration.Status', None, None, 'boolean', 'Sensor', 'HIGH', '1'),
    ]
    
    for spec in sample_specs:
        if len(spec) == 6:
            item_name, min_spec, max_spec, check_type, category, severity = spec
            expected_value = None
        else:
            item_name, min_spec, max_spec, check_type, category, severity, expected_value = spec
            
        try:
            cursor.execute('''
            INSERT INTO QC_Spec_Master
            (item_name, min_spec, max_spec, expected_value, check_type, category, severity)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (item_name, min_spec, max_spec, expected_value, check_type, category, severity))
        except sqlite3.IntegrityError:
            pass  # 이미 존재
    
    conn.commit()
    print("✅ 샘플 QC 스펙 추가 완료")

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("🚀 DB 마이그레이션 시작: Default DB와 QC Spec 분리")
    print("=" * 60)
    
    # 데이터베이스 경로
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                          'data', 'db_manager.sqlite')
    
    if not os.path.exists(db_path):
        print(f"❌ 데이터베이스 파일을 찾을 수 없습니다: {db_path}")
        return
    
    # 1. 백업
    backup_path = backup_database(db_path)
    
    try:
        # 2. 연결
        conn = sqlite3.connect(db_path)
        
        # 3. 새 테이블 생성
        create_new_tables(conn)
        
        # 4. 스펙 마이그레이션
        migrate_specs_to_master(conn)
        
        # 5. Equipment_Configurations 업데이트
        update_equipment_configurations(conn)
        
        # 6. Default_DB_Values 재구성
        create_default_db_values_new(conn)
        
        # 7. 샘플 데이터 추가
        add_sample_qc_specs(conn)
        
        # 8. 완료
        conn.close()
        
        print("=" * 60)
        print("✅ 마이그레이션 완료!")
        print(f"📦 백업 파일: {backup_path}")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 마이그레이션 실패: {e}")
        print(f"백업 파일에서 복원하세요: {backup_path}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()