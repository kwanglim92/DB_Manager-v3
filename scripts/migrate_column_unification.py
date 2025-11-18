"""
DB 컬럼 구조 통일화 마이그레이션 스크립트

옵션 1: 전체 테이블 컬럼명 통일
- Default_DB_Values: module_name → module, part_name → part
- Shipped_Equipment_Parameters: data_type → item_type
- QC_Checklist_Items: module, part, item_type 컬럼 추가

작성일: 2025-11-18
"""

import sqlite3
import os
import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from app.schema import DBSchema


def backup_database(db_path):
    """데이터베이스 백업"""
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"✅ 데이터베이스 백업 완료: {backup_path}")
    return backup_path


def migrate_default_db_values(conn):
    """
    Default_DB_Values 테이블 컬럼명 변경
    - module_name → module
    - part_name → part
    """
    cursor = conn.cursor()

    print("\n" + "="*60)
    print("Step 1: Default_DB_Values 테이블 마이그레이션")
    print("="*60)

    # 현재 컬럼 확인
    cursor.execute("PRAGMA table_info(Default_DB_Values)")
    columns = {col[1]: col for col in cursor.fetchall()}

    # module_name, part_name 컬럼 존재 확인
    if 'module_name' not in columns and 'part_name' not in columns:
        print("⚠️  module_name, part_name 컬럼이 없습니다. 이미 마이그레이션된 것으로 보입니다.")
        return

    print("\n1-1. 기존 테이블 백업 (Default_DB_Values_old)")
    cursor.execute("DROP TABLE IF EXISTS Default_DB_Values_old")
    cursor.execute("ALTER TABLE Default_DB_Values RENAME TO Default_DB_Values_old")

    print("1-2. 새 테이블 생성 (module, part 컬럼명 사용)")
    cursor.execute('''
    CREATE TABLE Default_DB_Values (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipment_type_id INTEGER NOT NULL,
        parameter_name TEXT NOT NULL,
        default_value TEXT NOT NULL,
        min_spec TEXT,
        max_spec TEXT,
        occurrence_count INTEGER DEFAULT 1,
        total_files INTEGER DEFAULT 1,
        confidence_score REAL DEFAULT 1.0,
        source_files TEXT,
        description TEXT,
        module TEXT,
        part TEXT,
        item_type TEXT,
        is_checklist INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (equipment_type_id) REFERENCES Equipment_Types(id),
        UNIQUE(equipment_type_id, parameter_name)
    )
    ''')

    print("1-3. 데이터 마이그레이션 (module_name → module, part_name → part)")
    cursor.execute('''
    INSERT INTO Default_DB_Values (
        id, equipment_type_id, parameter_name, default_value,
        min_spec, max_spec, occurrence_count, total_files,
        confidence_score, source_files, description,
        module, part, item_type, is_checklist,
        created_at, updated_at
    )
    SELECT
        id, equipment_type_id, parameter_name, default_value,
        min_spec, max_spec, occurrence_count, total_files,
        confidence_score, source_files, description,
        module_name, part_name, item_type, is_checklist,
        created_at, updated_at
    FROM Default_DB_Values_old
    ''')

    migrated_count = cursor.rowcount
    print(f"✅ {migrated_count}개 레코드 마이그레이션 완료")

    conn.commit()


def migrate_shipped_equipment_parameters(conn):
    """
    Shipped_Equipment_Parameters 테이블 컬럼명 변경
    - data_type → item_type
    """
    cursor = conn.cursor()

    print("\n" + "="*60)
    print("Step 2: Shipped_Equipment_Parameters 테이블 마이그레이션")
    print("="*60)

    # 테이블 존재 확인
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Shipped_Equipment_Parameters'")
    if not cursor.fetchone():
        print("⚠️  Shipped_Equipment_Parameters 테이블이 없습니다. 스킵합니다.")
        return

    # 현재 컬럼 확인
    cursor.execute("PRAGMA table_info(Shipped_Equipment_Parameters)")
    columns = {col[1]: col for col in cursor.fetchall()}

    if 'data_type' not in columns:
        print("⚠️  data_type 컬럼이 없습니다. 이미 마이그레이션된 것으로 보입니다.")
        return

    print("\n2-1. 기존 테이블 백업 (Shipped_Equipment_Parameters_old)")
    cursor.execute("DROP TABLE IF EXISTS Shipped_Equipment_Parameters_old")
    cursor.execute("ALTER TABLE Shipped_Equipment_Parameters RENAME TO Shipped_Equipment_Parameters_old")

    print("2-2. 새 테이블 생성 (item_type 컬럼명 사용)")
    cursor.execute('''
    CREATE TABLE Shipped_Equipment_Parameters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shipped_equipment_id INTEGER NOT NULL,
        parameter_name TEXT NOT NULL,
        parameter_value TEXT NOT NULL,
        module TEXT,
        part TEXT,
        item_type TEXT,
        FOREIGN KEY (shipped_equipment_id) REFERENCES Shipped_Equipment(id) ON DELETE CASCADE,
        UNIQUE (shipped_equipment_id, parameter_name)
    )
    ''')

    print("2-3. 데이터 마이그레이션 (data_type → item_type)")
    cursor.execute('''
    INSERT INTO Shipped_Equipment_Parameters (
        id, shipped_equipment_id, parameter_name, parameter_value,
        module, part, item_type
    )
    SELECT
        id, shipped_equipment_id, parameter_name, parameter_value,
        module, part, data_type
    FROM Shipped_Equipment_Parameters_old
    ''')

    migrated_count = cursor.rowcount
    print(f"✅ {migrated_count}개 레코드 마이그레이션 완료")

    # 인덱스 재생성
    print("2-4. 인덱스 재생성")
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_shipped_params_equipment
    ON Shipped_Equipment_Parameters(shipped_equipment_id)
    ''')
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_shipped_params_name
    ON Shipped_Equipment_Parameters(parameter_name)
    ''')

    conn.commit()


def migrate_qc_checklist_items(conn):
    """
    QC_Checklist_Items 테이블에 module, part, item_type 컬럼 추가
    """
    cursor = conn.cursor()

    print("\n" + "="*60)
    print("Step 3: QC_Checklist_Items 테이블 마이그레이션")
    print("="*60)

    # 현재 컬럼 확인
    cursor.execute("PRAGMA table_info(QC_Checklist_Items)")
    columns = {col[1]: col for col in cursor.fetchall()}

    if 'module' in columns and 'part' in columns and 'item_type' in columns:
        print("⚠️  module, part, item_type 컬럼이 이미 존재합니다. 스킵합니다.")
        return

    print("\n3-1. 기존 테이블 백업 (QC_Checklist_Items_old)")
    cursor.execute("DROP TABLE IF EXISTS QC_Checklist_Items_old")
    cursor.execute("ALTER TABLE QC_Checklist_Items RENAME TO QC_Checklist_Items_old")

    print("3-2. 새 테이블 생성 (module, part, item_type 컬럼 추가)")
    cursor.execute('''
    CREATE TABLE QC_Checklist_Items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT NOT NULL,
        parameter_pattern TEXT NOT NULL,
        is_common INTEGER DEFAULT 1,
        severity_level TEXT CHECK(severity_level IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')) DEFAULT 'MEDIUM',
        validation_rule TEXT,
        description TEXT,
        module TEXT,
        part TEXT,
        item_type TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(module, part, item_name)
    )
    ''')

    print("3-3. 기존 데이터 마이그레이션")
    cursor.execute('''
    INSERT INTO QC_Checklist_Items (
        id, item_name, parameter_pattern, is_common, severity_level,
        validation_rule, description, created_at, updated_at
    )
    SELECT
        id, item_name, parameter_pattern, is_common, severity_level,
        validation_rule, description, created_at, updated_at
    FROM QC_Checklist_Items_old
    ''')

    migrated_count = cursor.rowcount
    print(f"✅ {migrated_count}개 레코드 마이그레이션 완료 (module, part, item_type은 NULL)")

    conn.commit()


def populate_qc_checklist_module_part(conn):
    """
    QC_Checklist_Items의 module, part, item_type 값을 Default_DB_Values에서 추출하여 채우기
    """
    cursor = conn.cursor()

    print("\n" + "="*60)
    print("Step 4: QC_Checklist_Items에 Module/Part 정보 채우기")
    print("="*60)

    print("\n4-1. Default_DB_Values에서 Module/Part 정보 추출")
    cursor.execute('''
    SELECT DISTINCT parameter_name, module, part, item_type
    FROM Default_DB_Values
    WHERE module IS NOT NULL AND module != ''
       AND part IS NOT NULL AND part != ''
    ''')

    param_mapping = {}
    for row in cursor.fetchall():
        param_name, module, part, item_type = row
        if param_name not in param_mapping:
            param_mapping[param_name] = []
        param_mapping[param_name].append((module, part, item_type))

    print(f"   - {len(param_mapping)}개 고유 파라미터에 대한 Module/Part 정보 발견")

    print("\n4-2. QC_Checklist_Items 업데이트")
    cursor.execute("SELECT id, item_name, module, part FROM QC_Checklist_Items")
    checklist_items = cursor.fetchall()

    updated_count = 0
    skipped_count = 0

    for item_id, item_name, current_module, current_part in checklist_items:
        # 이미 module/part가 설정되어 있으면 스킵
        if current_module and current_part:
            skipped_count += 1
            continue

        # Default_DB_Values에서 매칭되는 정보 찾기
        if item_name in param_mapping:
            mappings = param_mapping[item_name]

            # 여러 매핑이 있을 경우 첫 번째 것 사용 (또는 사용자가 선택하도록 할 수도 있음)
            if len(mappings) == 1:
                module, part, item_type = mappings[0]
                cursor.execute('''
                UPDATE QC_Checklist_Items
                SET module = ?, part = ?, item_type = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                ''', (module, part, item_type, item_id))
                updated_count += 1
            else:
                # 여러 매핑이 있을 경우 - 첫 번째 사용
                module, part, item_type = mappings[0]
                cursor.execute('''
                UPDATE QC_Checklist_Items
                SET module = ?, part = ?, item_type = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                ''', (module, part, item_type, item_id))
                updated_count += 1
                print(f"   ⚠️  '{item_name}': {len(mappings)}개 매핑 발견, 첫 번째 사용 ({module}.{part})")

    print(f"\n✅ {updated_count}개 항목 업데이트 완료")
    print(f"   - {skipped_count}개 항목 스킵 (이미 module/part 설정됨)")
    print(f"   - {len(checklist_items) - updated_count - skipped_count}개 항목 매칭 실패 (수동 설정 필요)")

    conn.commit()


def cleanup_old_tables(conn, keep_backup=False):
    """마이그레이션 완료 후 백업 테이블 정리"""
    cursor = conn.cursor()

    print("\n" + "="*60)
    print("Step 5: 백업 테이블 정리")
    print("="*60)

    if keep_backup:
        print("⚠️  --keep-backup 옵션이 설정되어 백업 테이블을 유지합니다.")
        return

    backup_tables = [
        'Default_DB_Values_old',
        'Shipped_Equipment_Parameters_old',
        'QC_Checklist_Items_old'
    ]

    for table in backup_tables:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        if cursor.fetchone():
            cursor.execute(f"DROP TABLE {table}")
            print(f"✅ {table} 테이블 삭제 완료")

    conn.commit()


def verify_migration(conn):
    """마이그레이션 결과 검증"""
    cursor = conn.cursor()

    print("\n" + "="*60)
    print("Step 6: 마이그레이션 검증")
    print("="*60)

    # Default_DB_Values 검증
    print("\n6-1. Default_DB_Values 테이블")
    cursor.execute("PRAGMA table_info(Default_DB_Values)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'module' in columns and 'part' in columns and 'item_type' in columns:
        print("   ✅ module, part, item_type 컬럼 존재")

        cursor.execute("SELECT COUNT(*) FROM Default_DB_Values WHERE module IS NOT NULL")
        count = cursor.fetchone()[0]
        print(f"   - module 값이 있는 레코드: {count}개")
    else:
        print("   ❌ 필수 컬럼이 없습니다!")

    # Shipped_Equipment_Parameters 검증
    print("\n6-2. Shipped_Equipment_Parameters 테이블")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Shipped_Equipment_Parameters'")
    if cursor.fetchone():
        cursor.execute("PRAGMA table_info(Shipped_Equipment_Parameters)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'item_type' in columns:
            print("   ✅ item_type 컬럼 존재")

            cursor.execute("SELECT COUNT(*) FROM Shipped_Equipment_Parameters WHERE item_type IS NOT NULL")
            count = cursor.fetchone()[0]
            print(f"   - item_type 값이 있는 레코드: {count}개")
        else:
            print("   ❌ item_type 컬럼이 없습니다!")
    else:
        print("   ⚠️  테이블이 없습니다 (스킵됨)")

    # QC_Checklist_Items 검증
    print("\n6-3. QC_Checklist_Items 테이블")
    cursor.execute("PRAGMA table_info(QC_Checklist_Items)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'module' in columns and 'part' in columns and 'item_type' in columns:
        print("   ✅ module, part, item_type 컬럼 존재")

        cursor.execute("SELECT COUNT(*) FROM QC_Checklist_Items")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM QC_Checklist_Items WHERE module IS NOT NULL AND part IS NOT NULL")
        filled = cursor.fetchone()[0]
        print(f"   - 전체 레코드: {total}개")
        print(f"   - module/part 채워진 레코드: {filled}개 ({filled/total*100:.1f}%)" if total > 0 else "   - 레코드 없음")
    else:
        print("   ❌ 필수 컬럼이 없습니다!")

    # UNIQUE 제약 조건 확인
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='QC_Checklist_Items'")
    table_sql = cursor.fetchone()[0]
    if 'UNIQUE(module, part, item_name)' in table_sql:
        print("   ✅ UNIQUE(module, part, item_name) 제약 조건 적용됨")
    else:
        print("   ⚠️  UNIQUE 제약 조건이 예상과 다릅니다")


def main():
    """메인 마이그레이션 함수"""
    import argparse
    from datetime import datetime

    parser = argparse.ArgumentParser(description='DB 컬럼 구조 통일화 마이그레이션')
    parser.add_argument('--db-path', type=str, help='데이터베이스 파일 경로 (기본값: data/local_db.sqlite)')
    parser.add_argument('--keep-backup', action='store_true', help='백업 테이블 유지 (삭제하지 않음)')
    parser.add_argument('--skip-backup', action='store_true', help='DB 파일 백업 스킵')

    args = parser.parse_args()

    # 데이터베이스 경로 설정
    if args.db_path:
        db_path = args.db_path
    else:
        data_dir = project_root / 'data'
        db_path = str(data_dir / 'local_db.sqlite')

    if not os.path.exists(db_path):
        print(f"❌ 데이터베이스 파일을 찾을 수 없습니다: {db_path}")
        return 1

    print("="*60)
    print("DB 컬럼 구조 통일화 마이그레이션")
    print("="*60)
    print(f"\n데이터베이스 경로: {db_path}")
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 백업 생성
    if not args.skip_backup:
        backup_path = backup_database(db_path)
        print(f"백업 경로: {backup_path}")

    # 마이그레이션 실행
    try:
        conn = sqlite3.connect(db_path)

        # 1. Default_DB_Values 마이그레이션
        migrate_default_db_values(conn)

        # 2. Shipped_Equipment_Parameters 마이그레이션
        migrate_shipped_equipment_parameters(conn)

        # 3. QC_Checklist_Items 마이그레이션
        migrate_qc_checklist_items(conn)

        # 4. QC_Checklist_Items에 Module/Part 정보 채우기
        populate_qc_checklist_module_part(conn)

        # 5. 백업 테이블 정리
        cleanup_old_tables(conn, keep_backup=args.keep_backup)

        # 6. 검증
        verify_migration(conn)

        conn.close()

        print("\n" + "="*60)
        print("✅ 마이그레이션 완료!")
        print("="*60)

        return 0

    except Exception as e:
        print(f"\n❌ 마이그레이션 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
