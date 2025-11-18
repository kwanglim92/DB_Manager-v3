#!/usr/bin/env python3
"""
Phase 2 마이그레이션: QC_Checklist_Items 테이블에 module, part 컬럼 추가

목적:
- Module.Part.ItemName 복합 키 매칭을 위한 테이블 구조 변경
- 기존 데이터는 module, part를 NULL로 유지 (Type Common 항목)

Author: Phase 2
Date: 2025-11-18
"""

import sys
import os

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from db_schema import DBSchema


def migrate_add_module_part_columns():
    """QC_Checklist_Items 테이블에 module, part 컬럼 추가"""

    db_schema = DBSchema()

    print("=" * 60)
    print("Phase 2 마이그레이션: QC_Checklist_Items에 module, part 추가")
    print("=" * 60)

    with db_schema.get_connection() as conn:
        cursor = conn.cursor()

        # 1. 현재 테이블 구조 확인
        print("\n1. 현재 QC_Checklist_Items 테이블 구조 확인...")
        cursor.execute("PRAGMA table_info(QC_Checklist_Items)")
        columns = cursor.fetchall()

        existing_columns = [col[1] for col in columns]
        print(f"   기존 컬럼: {', '.join(existing_columns)}")

        # 2. module, part 컬럼이 이미 있는지 확인
        has_module = 'module' in existing_columns
        has_part = 'part' in existing_columns

        if has_module and has_part:
            print("   ✓ module, part 컬럼이 이미 존재합니다. 마이그레이션 스킵.")
            return True

        # 3. 백업 테이블 생성
        print("\n2. 백업 테이블 생성...")
        cursor.execute("DROP TABLE IF EXISTS QC_Checklist_Items_Backup")
        cursor.execute("""
            CREATE TABLE QC_Checklist_Items_Backup AS
            SELECT * FROM QC_Checklist_Items
        """)
        backup_count = cursor.execute("SELECT COUNT(*) FROM QC_Checklist_Items_Backup").fetchone()[0]
        print(f"   ✓ {backup_count}개 항목 백업 완료")

        # 4. 기존 데이터 조회
        print("\n3. 기존 데이터 조회...")
        cursor.execute("SELECT COUNT(*) FROM QC_Checklist_Items")
        total_count = cursor.fetchone()[0]
        print(f"   총 {total_count}개 항목")

        # 5. 새 테이블 구조 생성 (module, part 컬럼 추가)
        print("\n4. 새 테이블 구조 생성...")
        cursor.execute("DROP TABLE IF EXISTS QC_Checklist_Items_New")

        cursor.execute("""
            CREATE TABLE QC_Checklist_Items_New (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                module TEXT,
                part TEXT,
                spec_min TEXT,
                spec_max TEXT,
                expected_value TEXT,
                category TEXT,
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (module, part, item_name)
            )
        """)
        print("   ✓ 새 테이블 구조 생성 완료")

        # 6. 기존 데이터 마이그레이션
        print("\n5. 기존 데이터 마이그레이션...")

        # 기존 테이블에서 컬럼 확인
        if 'spec_min' in existing_columns:
            # Phase 1.5 Week 3 이후 구조 (spec_min, spec_max, expected_value 있음)
            cursor.execute("""
                INSERT INTO QC_Checklist_Items_New
                (id, item_name, module, part, spec_min, spec_max, expected_value,
                 category, description, is_active, created_at, updated_at)
                SELECT
                    id, item_name, NULL, NULL, spec_min, spec_max, expected_value,
                    category, description, is_active, created_at, updated_at
                FROM QC_Checklist_Items
            """)
        else:
            # 구버전 구조 (parameter_pattern, severity_level 등)
            cursor.execute("""
                INSERT INTO QC_Checklist_Items_New
                (id, item_name, module, part, description, is_active, created_at, updated_at)
                SELECT
                    id, item_name, NULL, NULL, description, 1, created_at, updated_at
                FROM QC_Checklist_Items
            """)

        migrated_count = cursor.execute("SELECT COUNT(*) FROM QC_Checklist_Items_New").fetchone()[0]
        print(f"   ✓ {migrated_count}개 항목 마이그레이션 완료")

        # 7. 테이블 교체
        print("\n6. 테이블 교체...")
        cursor.execute("DROP TABLE QC_Checklist_Items")
        cursor.execute("ALTER TABLE QC_Checklist_Items_New RENAME TO QC_Checklist_Items")
        print("   ✓ 테이블 교체 완료")

        # 8. 인덱스 생성
        print("\n7. 인덱스 생성...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_qc_checklist_module_part
            ON QC_Checklist_Items(module, part)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_qc_checklist_item_name
            ON QC_Checklist_Items(item_name)
        """)
        print("   ✓ 인덱스 생성 완료")

        # 9. 변경사항 커밋
        conn.commit()
        print("\n8. 변경사항 커밋 완료")

        # 10. 검증
        print("\n9. 마이그레이션 검증...")
        cursor.execute("PRAGMA table_info(QC_Checklist_Items)")
        new_columns = [col[1] for col in cursor.fetchall()]
        print(f"   새 컬럼: {', '.join(new_columns)}")

        cursor.execute("SELECT COUNT(*) FROM QC_Checklist_Items")
        final_count = cursor.fetchone()[0]
        print(f"   최종 항목 수: {final_count}")

        if final_count == total_count:
            print("   ✓ 데이터 무결성 확인 완료")
        else:
            print(f"   ⚠️ 경고: 데이터 수 불일치 (이전: {total_count}, 이후: {final_count})")
            return False

        # 11. 샘플 데이터 확인
        print("\n10. 샘플 데이터 확인...")
        cursor.execute("SELECT id, item_name, module, part, is_active FROM QC_Checklist_Items LIMIT 3")
        samples = cursor.fetchall()
        for sample in samples:
            print(f"   - ID {sample[0]}: {sample[1]} (module={sample[2]}, part={sample[3]}, active={sample[4]})")

    print("\n" + "=" * 60)
    print("✓ 마이그레이션 성공!")
    print("=" * 60)
    print("\n다음 단계:")
    print("1. QC Inspection 로직을 Module.Part.ItemName 복합 키 매칭으로 변경")
    print("2. UI에 Module/Part 필터링 기능 추가")
    print("3. Checklist Manager에 Module/Part 컬럼 표시")

    return True


def rollback_migration():
    """마이그레이션 롤백 (백업 테이블에서 복원)"""

    db_schema = DBSchema()

    print("\n마이그레이션 롤백 중...")

    with db_schema.get_connection() as conn:
        cursor = conn.cursor()

        # 백업 테이블 존재 확인
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='QC_Checklist_Items_Backup'
        """)

        if not cursor.fetchone():
            print("⚠️ 백업 테이블이 없습니다. 롤백할 수 없습니다.")
            return False

        # 현재 테이블 삭제 및 백업 복원
        cursor.execute("DROP TABLE IF EXISTS QC_Checklist_Items")
        cursor.execute("ALTER TABLE QC_Checklist_Items_Backup RENAME TO QC_Checklist_Items")

        conn.commit()

        print("✓ 롤백 완료")
        return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Phase 2 마이그레이션: module, part 컬럼 추가")
    parser.add_argument("--rollback", action="store_true", help="마이그레이션 롤백")

    args = parser.parse_args()

    try:
        if args.rollback:
            success = rollback_migration()
        else:
            success = migrate_add_module_part_columns()

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
