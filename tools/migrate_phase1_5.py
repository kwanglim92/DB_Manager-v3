"""
Phase 1.5 Database Migration Script

목적: Equipment Hierarchy System 구축
- Equipment_Models 테이블 생성
- Equipment_Types 수정 (model_id FK 추가)
- Equipment_Configurations 테이블 생성
- Default_DB_Values 수정 (configuration_id 추가, min_spec/max_spec 제거)
- QC_Checklist_Items 수정 (severity_level 제거, spec 필드 추가)
- Equipment_Checklist_Exceptions 테이블 생성 (Configuration 기반)
- Equipment_Checklist_Mapping 테이블 제거

작성일: 2025-11-13
"""

import sys
import os

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import sqlite3
import json
from datetime import datetime
from contextlib import contextmanager


class Phase15Migration:
    """Phase 1.5 마이그레이션 클래스"""

    def __init__(self, db_path=None):
        if db_path is None:
            # 기본 데이터베이스 경로
            data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
            self.db_path = os.path.join(data_dir, 'local_db.sqlite')
        else:
            self.db_path = db_path

        # 백업 경로
        backup_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_path = os.path.join(backup_dir, f'pre_phase1_5_backup_{timestamp}.sqlite')

        # ID 매핑 (구 → 신)
        self.type_id_mapping = {}

    @contextmanager
    def get_connection(self):
        """데이터베이스 연결 컨텍스트 매니저"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def backup_database(self):
        """데이터베이스 백업"""
        import shutil

        if os.path.exists(self.db_path):
            shutil.copy2(self.db_path, self.backup_path)
            print(f"[OK] 백업 생성: {self.backup_path}")
            return True
        else:
            print("[WARN]  데이터베이스 파일이 없습니다.")
            return False

    def step1_create_equipment_models(self, conn):
        """
        Step 1: Equipment_Models 테이블 생성 및 초기 데이터 삽입

        test 폴더 구조를 기반으로 모델명 추출:
        - Wafer
        - NX-Mask
        - NX-Wafer Plus
        - NX-Hybrid WLI
        - NX-TSH300 Overlay
        - NX-TSH400TF
        - NX-eAFM
        - NX-eView
        """
        print("\n=== Step 1: Equipment_Models 테이블 생성 ===")

        cursor = conn.cursor()

        # 1. 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Equipment_Models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL UNIQUE,
                model_code TEXT,
                description TEXT,
                display_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 2. test 폴더에서 확인된 모델명 (display_order 순서대로)
        models = [
            ("Wafer", "WFR", "Wafer 검사 장비"),
            ("NX-Mask", "NX-M", "마스크 검사 장비"),
            ("NX-Wafer Plus", "NX-WP", "Wafer Plus 검사 장비"),
            ("NX-Hybrid WLI", "NX-H-WLI", "Hybrid WLI 검사 장비"),
            ("NX-TSH300 Overlay", "NX-TSH300", "TSH300 Overlay 장비"),
            ("NX-TSH400TF", "NX-TSH400TF", "TSH400TF 장비"),
            ("NX-eAFM", "NX-eAFM", "eAFM 장비"),
            ("NX-eView", "NX-eView", "eView 장비"),
        ]

        # 3. 모델 삽입
        for idx, (model_name, model_code, description) in enumerate(models):
            try:
                cursor.execute('''
                    INSERT INTO Equipment_Models (model_name, model_code, description, display_order)
                    VALUES (?, ?, ?, ?)
                ''', (model_name, model_code, description, idx))
                print(f"  [OK] {model_name} (Order: {idx})")
            except sqlite3.IntegrityError:
                print(f"  [WARN]  {model_name} 이미 존재 (스킵)")

        conn.commit()

        # 4. 결과 확인
        cursor.execute("SELECT COUNT(*) FROM Equipment_Models")
        count = cursor.fetchone()[0]
        print(f"\n[OK] Step 1 완료: {count}개 모델 생성")

    def step2_modify_equipment_types(self, conn):
        """
        Step 2: Equipment_Types 테이블 수정
        - model_id FK 추가
        - type_name 의미 변경: 장비 모델명 → AE 형태 ("분리형"/"일체형")
        """
        print("\n=== Step 2: Equipment_Types 수정 ===")

        cursor = conn.cursor()

        # 1. 백업 테이블 생성
        cursor.execute("DROP TABLE IF EXISTS Equipment_Types_Backup")
        cursor.execute('''
            CREATE TABLE Equipment_Types_Backup AS
            SELECT * FROM Equipment_Types
        ''')

        backup_count = cursor.execute("SELECT COUNT(*) FROM Equipment_Types_Backup").fetchone()[0]
        print(f"  백업 완료: {backup_count}개 레코드")

        # 2. Equipment_Types 재생성
        cursor.execute("DROP TABLE Equipment_Types")
        cursor.execute('''
            CREATE TABLE Equipment_Types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id INTEGER NOT NULL,
                type_name TEXT NOT NULL,
                description TEXT,
                is_default BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (model_id) REFERENCES Equipment_Models(id) ON DELETE CASCADE,
                UNIQUE (model_id, type_name)
            )
        ''')

        # 3. 데이터 마이그레이션
        cursor.execute("SELECT id, type_name, description FROM Equipment_Types_Backup")
        backup_types = cursor.fetchall()

        for old_type in backup_types:
            old_id = old_type['id']
            old_type_name = old_type['type_name']
            old_desc = old_type['description']

            # 모델명 추출 (휴리스틱: type_name을 그대로 모델명으로 간주)
            model_name = old_type_name

            # Equipment_Models에서 model_id 찾기
            cursor.execute("SELECT id FROM Equipment_Models WHERE model_name = ?", (model_name,))
            model_row = cursor.fetchone()

            if model_row:
                model_id = model_row['id']

                # AE 형태 결정 (기본값: "분리형", 향후 사용자가 수정 가능)
                # TODO: 실제로는 test 폴더 구조 스캔 필요
                ae_type = "분리형"  # 기본값

                # 새 Equipment_Types에 삽입
                cursor.execute('''
                    INSERT INTO Equipment_Types (model_id, type_name, description, is_default)
                    VALUES (?, ?, ?, 1)
                ''', (model_id, ae_type, old_desc))

                new_id = cursor.lastrowid
                self.type_id_mapping[old_id] = new_id

                print(f"  [OK] {old_type_name} → Model: {model_name}, Type: {ae_type} (ID: {old_id} → {new_id})")
            else:
                print(f"  [WARN]  모델을 찾을 수 없음: {model_name} (ID: {old_id})")

        conn.commit()
        print(f"\n[OK] Step 2 완료: {len(self.type_id_mapping)}개 Equipment_Types 마이그레이션")

    def step3_create_equipment_configurations(self, conn):
        """
        Step 3: Equipment_Configurations 테이블 생성

        초기 데이터는 수동 생성으로 남겨둠 (자동 생성 없음)
        """
        print("\n=== Step 3: Equipment_Configurations 테이블 생성 ===")

        cursor = conn.cursor()

        # 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Equipment_Configurations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_type_id INTEGER NOT NULL,
                config_name TEXT NOT NULL,

                port_type TEXT CHECK(port_type IN ('Single Port', 'Double Port', 'Multi Port', NULL)),
                wafer_sizes TEXT CHECK(wafer_sizes IN ('150mm', '150/200mm', '200mm', '200/300mm', '300mm', NULL)),

                custom_options TEXT,
                is_customer_specific BOOLEAN DEFAULT 0,
                customer_name TEXT,
                is_default BOOLEAN DEFAULT 0,

                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (equipment_type_id) REFERENCES Equipment_Types(id) ON DELETE CASCADE,
                UNIQUE (equipment_type_id, config_name)
            )
        ''')

        conn.commit()
        print("[OK] Step 3 완료: Equipment_Configurations 테이블 생성 (초기 데이터 없음)")

    def step4_modify_default_db_values(self, conn):
        """
        Step 4: Default_DB_Values 수정
        - configuration_id FK 추가
        - min_spec, max_spec 제거
        - equipment_type_id 업데이트 (ID 매핑 적용)
        """
        print("\n=== Step 4: Default_DB_Values 수정 ===")

        cursor = conn.cursor()

        # 1. 백업
        cursor.execute("DROP TABLE IF EXISTS Default_DB_Values_Backup")
        cursor.execute('''
            CREATE TABLE Default_DB_Values_Backup AS
            SELECT * FROM Default_DB_Values
        ''')

        backup_count = cursor.execute("SELECT COUNT(*) FROM Default_DB_Values_Backup").fetchone()[0]
        print(f"  백업 완료: {backup_count}개 레코드")

        # 2. Default_DB_Values 재생성
        cursor.execute("DROP TABLE Default_DB_Values")
        cursor.execute('''
            CREATE TABLE Default_DB_Values (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_type_id INTEGER NOT NULL,
                configuration_id INTEGER,

                parameter_name TEXT NOT NULL,
                default_value TEXT,
                module TEXT,
                part TEXT,
                data_type TEXT,
                is_performance BOOLEAN DEFAULT 0,
                description TEXT,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (equipment_type_id) REFERENCES Equipment_Types(id) ON DELETE CASCADE,
                FOREIGN KEY (configuration_id) REFERENCES Equipment_Configurations(id) ON DELETE SET NULL,
                UNIQUE (equipment_type_id, configuration_id, parameter_name)
            )
        ''')

        # 3. 데이터 마이그레이션 (min_spec, max_spec 제외)
        cursor.execute("SELECT * FROM Default_DB_Values_Backup")
        backup_values = cursor.fetchall()

        migrated = 0
        skipped = 0

        for old_value in backup_values:
            old_type_id = old_value['equipment_type_id']

            # ID 매핑 적용
            new_type_id = self.type_id_mapping.get(old_type_id)

            if new_type_id:
                try:
                    module = old_value['module'] if 'module' in old_value.keys() and old_value['module'] else None
                except:
                    module = None
                try:
                    part = old_value['part'] if 'part' in old_value.keys() and old_value['part'] else None
                except:
                    part = None
                try:
                    data_type = old_value['data_type'] if 'data_type' in old_value.keys() and old_value['data_type'] else None
                except:
                    data_type = None
                try:
                    is_performance = old_value['is_performance'] if 'is_performance' in old_value.keys() else 0
                except:
                    is_performance = 0
                try:
                    description = old_value['description'] if 'description' in old_value.keys() and old_value['description'] else None
                except:
                    description = None

                cursor.execute('''
                    INSERT INTO Default_DB_Values
                    (equipment_type_id, configuration_id, parameter_name, default_value,
                     module, part, data_type, is_performance, description)
                    VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    new_type_id,
                    old_value['parameter_name'],
                    old_value['default_value'],
                    module,
                    part,
                    data_type,
                    is_performance,
                    description
                ))
                migrated += 1
            else:
                print(f"  [WARN]  매핑되지 않은 equipment_type_id: {old_type_id} (스킵)")
                skipped += 1

        conn.commit()
        print(f"[OK] Step 4 완료: {migrated}개 마이그레이션, {skipped}개 스킵 (min_spec/max_spec 제거)")

    def step5_modify_qc_checklist_items(self, conn):
        """
        Step 5: QC_Checklist_Items 수정
        - severity_level 제거
        - spec_min, spec_max, expected_value 추가
        - validation_rule에서 spec 추출
        """
        print("\n=== Step 5: QC_Checklist_Items 수정 ===")

        cursor = conn.cursor()

        # 1. 백업
        cursor.execute("DROP TABLE IF EXISTS QC_Checklist_Items_Backup")
        cursor.execute('''
            CREATE TABLE QC_Checklist_Items_Backup AS
            SELECT * FROM QC_Checklist_Items
        ''')

        backup_count = cursor.execute("SELECT COUNT(*) FROM QC_Checklist_Items_Backup").fetchone()[0]
        print(f"  백업 완료: {backup_count}개 레코드")

        # 2. QC_Checklist_Items 재생성
        cursor.execute("DROP TABLE QC_Checklist_Items")
        cursor.execute('''
            CREATE TABLE QC_Checklist_Items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL UNIQUE,

                spec_min TEXT,
                spec_max TEXT,
                expected_value TEXT,

                category TEXT,
                description TEXT,
                is_active BOOLEAN DEFAULT 1,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 3. 데이터 마이그레이션 (severity_level 제외, validation_rule에서 spec 추출)
        cursor.execute("SELECT * FROM QC_Checklist_Items_Backup")
        backup_items = cursor.fetchall()

        for old_item in backup_items:
            item_name = old_item['item_name']
            try:
                validation_rule_str = old_item['validation_rule']
            except (KeyError, IndexError):
                validation_rule_str = None
            try:
                category = old_item['category'] if old_item['category'] else ''
            except (KeyError, IndexError):
                category = ''
            try:
                description = old_item['description'] if old_item['description'] else ''
            except (KeyError, IndexError):
                description = ''

            spec_min = None
            spec_max = None
            expected_value = None

            # validation_rule (JSON)에서 spec 추출
            if validation_rule_str:
                try:
                    validation_rule = json.loads(validation_rule_str)

                    if validation_rule.get('type') == 'range':
                        spec_min = str(validation_rule.get('min', ''))
                        spec_max = str(validation_rule.get('max', ''))
                    elif validation_rule.get('type') == 'enum':
                        # Enum을 JSON 배열로 저장
                        expected_value = json.dumps(validation_rule.get('values', []))
                    elif validation_rule.get('type') == 'pattern':
                        expected_value = validation_rule.get('pattern', '')
                except json.JSONDecodeError:
                    print(f"  [WARN]  JSON 파싱 실패: {item_name}")

            # 삽입
            cursor.execute('''
                INSERT INTO QC_Checklist_Items
                (item_name, spec_min, spec_max, expected_value, category, description, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            ''', (item_name, spec_min, spec_max, expected_value, category, description))

            print(f"  [OK] {item_name} (Spec: {spec_min or expected_value or 'N/A'})")

        conn.commit()
        print(f"[OK] Step 5 완료: {len(backup_items)}개 QC_Checklist_Items 마이그레이션 (Severity 제거, Spec 추가)")

    def step6_create_equipment_checklist_exceptions(self, conn):
        """
        Step 6: Equipment_Checklist_Exceptions 테이블 생성 (Configuration 기반)

        기존 Equipment_Checklist_Exceptions는 equipment_type_id 기반이었으나
        Phase 1.5에서는 configuration_id 기반으로 변경
        """
        print("\n=== Step 6: Equipment_Checklist_Exceptions 재생성 ===")

        cursor = conn.cursor()

        # 1. 기존 테이블 백업 (있다면)
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='Equipment_Checklist_Exceptions'
        """)

        if cursor.fetchone():
            cursor.execute("DROP TABLE IF EXISTS Equipment_Checklist_Exceptions_Backup")
            cursor.execute('''
                CREATE TABLE Equipment_Checklist_Exceptions_Backup AS
                SELECT * FROM Equipment_Checklist_Exceptions
            ''')
            print("  기존 Equipment_Checklist_Exceptions 백업 완료")

            # 기존 테이블 삭제
            cursor.execute("DROP TABLE Equipment_Checklist_Exceptions")

        # 2. 새 테이블 생성 (configuration_id 기반)
        cursor.execute('''
            CREATE TABLE Equipment_Checklist_Exceptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                configuration_id INTEGER NOT NULL,
                checklist_item_id INTEGER NOT NULL,

                reason TEXT NOT NULL,
                approved_by TEXT,
                approved_date TIMESTAMP,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (configuration_id) REFERENCES Equipment_Configurations(id) ON DELETE CASCADE,
                FOREIGN KEY (checklist_item_id) REFERENCES QC_Checklist_Items(id) ON DELETE CASCADE,
                UNIQUE (configuration_id, checklist_item_id)
            )
        ''')

        conn.commit()
        print("[OK] Step 6 완료: Equipment_Checklist_Exceptions 재생성 (Configuration 기반)")

    def step7_remove_equipment_checklist_mapping(self, conn):
        """
        Step 7: Equipment_Checklist_Mapping 제거

        ItemName 자동 매칭으로 대체되므로 불필요
        """
        print("\n=== Step 7: Equipment_Checklist_Mapping 제거 ===")

        cursor = conn.cursor()

        # 1. 테이블 존재 여부 확인
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='Equipment_Checklist_Mapping'
        """)

        if cursor.fetchone():
            # 2. 백업 (혹시 모를 롤백용)
            cursor.execute("DROP TABLE IF EXISTS Equipment_Checklist_Mapping_Archive")
            cursor.execute('''
                CREATE TABLE Equipment_Checklist_Mapping_Archive AS
                SELECT * FROM Equipment_Checklist_Mapping
            ''')

            archive_count = cursor.execute("SELECT COUNT(*) FROM Equipment_Checklist_Mapping_Archive").fetchone()[0]
            print(f"  Archive 생성: {archive_count}개 레코드")

            # 3. 테이블 삭제
            cursor.execute("DROP TABLE Equipment_Checklist_Mapping")
            conn.commit()
            print("[OK] Step 7 완료: Equipment_Checklist_Mapping 제거 (Archive로 백업)")
        else:
            print("  테이블이 존재하지 않음 (스킵)")
            print("[OK] Step 7 완료: 작업 없음")

    def verify_migration(self, conn):
        """마이그레이션 검증"""
        print("\n=== 마이그레이션 검증 ===")

        cursor = conn.cursor()

        # 1. 테이블 존재 확인
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]

        expected_tables = [
            'Equipment_Models',
            'Equipment_Types',
            'Equipment_Configurations',
            'Default_DB_Values',
            'QC_Checklist_Items',
            'Equipment_Checklist_Exceptions'
        ]

        print("\n테이블 존재 확인:")
        for table in expected_tables:
            if table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  [OK] {table}: {count}개 레코드")
            else:
                print(f"  [ERROR] {table}: 테이블 없음")

        # 2. Equipment_Checklist_Mapping 제거 확인
        if 'Equipment_Checklist_Mapping' in tables:
            print("  [WARN]  Equipment_Checklist_Mapping: 아직 존재 (제거 실패?)")
        else:
            print("  [OK] Equipment_Checklist_Mapping: 제거됨")

        # 3. FK 관계 확인
        print("\nFK 관계 확인:")
        cursor.execute("PRAGMA foreign_key_list(Equipment_Types)")
        fk_types = cursor.fetchall()
        if fk_types:
            print(f"  [OK] Equipment_Types → Equipment_Models FK: {len(fk_types)}개")

        cursor.execute("PRAGMA foreign_key_list(Default_DB_Values)")
        fk_defaults = cursor.fetchall()
        if fk_defaults:
            print(f"  [OK] Default_DB_Values FK: {len(fk_defaults)}개")

        # 4. 데이터 무결성 확인
        print("\n데이터 무결성 확인:")
        cursor.execute("""
            SELECT COUNT(*) FROM Equipment_Types et
            LEFT JOIN Equipment_Models em ON et.model_id = em.id
            WHERE em.id IS NULL
        """)
        orphan_types = cursor.fetchone()[0]
        if orphan_types == 0:
            print("  [OK] Equipment_Types 고아 레코드 없음")
        else:
            print(f"  [WARN]  Equipment_Types 고아 레코드: {orphan_types}개")

        cursor.execute("""
            SELECT COUNT(*) FROM Default_DB_Values dv
            LEFT JOIN Equipment_Types et ON dv.equipment_type_id = et.id
            WHERE et.id IS NULL
        """)
        orphan_defaults = cursor.fetchone()[0]
        if orphan_defaults == 0:
            print("  [OK] Default_DB_Values 고아 레코드 없음")
        else:
            print(f"  [WARN]  Default_DB_Values 고아 레코드: {orphan_defaults}개")

    def rollback(self):
        """마이그레이션 롤백 (백업에서 복원)"""
        print("\n=== 마이그레이션 롤백 ===")

        if not os.path.exists(self.backup_path):
            print("[ERROR] 백업 파일이 없습니다.")
            return False

        try:
            import shutil

            # 현재 DB 삭제
            if os.path.exists(self.db_path):
                os.remove(self.db_path)

            # 백업에서 복원
            shutil.copy2(self.backup_path, self.db_path)
            print(f"[OK] 백업에서 복원 완료: {self.backup_path}")
            return True
        except Exception as e:
            print(f"[ERROR] 롤백 실패: {e}")
            return False

    def run(self, dry_run=False):
        """전체 마이그레이션 실행"""
        print("=" * 80)
        print("Phase 1.5 Database Migration")
        print("=" * 80)
        print(f"데이터베이스: {self.db_path}")
        print(f"백업 경로: {self.backup_path}")
        print(f"Dry Run: {dry_run}")
        print("=" * 80)

        if dry_run:
            print("\n[DRY RUN] 실제 변경은 수행되지 않습니다.\n")

        # 1. 백업
        if not self.backup_database():
            print("[ERROR] 백업 실패. 마이그레이션 중단.")
            return False

        try:
            with self.get_connection() as conn:
                # 외래 키 활성화
                conn.execute("PRAGMA foreign_keys = ON")

                # 마이그레이션 단계 실행
                self.step1_create_equipment_models(conn)
                self.step2_modify_equipment_types(conn)
                self.step3_create_equipment_configurations(conn)
                self.step4_modify_default_db_values(conn)
                self.step5_modify_qc_checklist_items(conn)
                self.step6_create_equipment_checklist_exceptions(conn)
                self.step7_remove_equipment_checklist_mapping(conn)

                # 검증
                self.verify_migration(conn)

                if dry_run:
                    print("\n[WARN]  DRY RUN 모드: 변경사항 롤백")
                    conn.rollback()
                else:
                    print("\n[OK] 모든 마이그레이션 완료")
                    conn.commit()

            print("\n" + "=" * 80)
            print("마이그레이션 성공!")
            print("=" * 80)
            return True

        except Exception as e:
            print(f"\n[ERROR] 마이그레이션 오류: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description='Phase 1.5 Database Migration')
    parser.add_argument('--db', type=str, help='데이터베이스 경로 (기본: data/local_db.sqlite)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run 모드 (실제 변경 안함)')
    parser.add_argument('--rollback', action='store_true', help='마이그레이션 롤백')

    args = parser.parse_args()

    migration = Phase15Migration(db_path=args.db)

    if args.rollback:
        migration.rollback()
    else:
        migration.run(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
