"""
Phase 2 Week 4 Day 1-2 Test
Database & Service 구축 검증

테스트 범위:
1. Shipped_Equipment 테이블 생성 검증
2. Shipped_Equipment_Parameters 테이블 생성 검증
3. ShippedEquipmentService import 검증
4. ServiceFactory 통합 검증
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


def test_1_database_tables():
    """Test 1: Shipped_Equipment, Shipped_Equipment_Parameters 테이블 생성 검증"""
    print("\n" + "=" * 60)
    print("Test 1: Database Tables")
    print("=" * 60)

    try:
        from db_schema import DBSchema

        # 임시 DB 생성
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db_path = os.path.join(temp_dir, "test.sqlite")
            db_schema = DBSchema(test_db_path)

            # 테이블 존재 확인
            with db_schema.get_connection() as conn:
                cursor = conn.cursor()

                # Shipped_Equipment 테이블
                cursor.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name='Shipped_Equipment'
                """)
                if cursor.fetchone():
                    print("[PASS] Shipped_Equipment table exists")
                else:
                    print("[FAIL] Shipped_Equipment table not found")
                    return False

                # Shipped_Equipment_Parameters 테이블
                cursor.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name='Shipped_Equipment_Parameters'
                """)
                if cursor.fetchone():
                    print("[PASS] Shipped_Equipment_Parameters table exists")
                else:
                    print("[FAIL] Shipped_Equipment_Parameters table not found")
                    return False

                # 인덱스 확인
                cursor.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='index' AND name='idx_shipped_params_equipment'
                """)
                if cursor.fetchone():
                    print("[PASS] Index idx_shipped_params_equipment exists")
                else:
                    print("[FAIL] Index not found")
                    return False

        return True

    except Exception as e:
        print(f"[FAIL] Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_2_shipped_equipment_service_import():
    """Test 2: ShippedEquipmentService import 검증"""
    print("\n" + "=" * 60)
    print("Test 2: ShippedEquipmentService Import")
    print("=" * 60)

    try:
        from app.services.shipped_equipment.shipped_equipment_service import ShippedEquipmentService
        from app.services.interfaces.shipped_equipment_service_interface import (
            IShippedEquipmentService,
            ShippedEquipment,
            ShippedEquipmentParameter,
            FileParseResult,
            ParameterHistory
        )

        print("[PASS] ShippedEquipmentService import success")
        print("[PASS] Interface classes import success")

        # 인터페이스 구현 확인
        if issubclass(ShippedEquipmentService, IShippedEquipmentService):
            print("[PASS] ShippedEquipmentService implements IShippedEquipmentService")
        else:
            print("[FAIL] Interface not implemented")
            return False

        return True

    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_3_service_factory_integration():
    """Test 3: ServiceFactory 통합 검증"""
    print("\n" + "=" * 60)
    print("Test 3: ServiceFactory Integration")
    print("=" * 60)

    try:
        from db_schema import DBSchema
        from app.services.service_factory import ServiceFactory

        # 임시 DB로 ServiceFactory 생성
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db_path = os.path.join(temp_dir, "test.sqlite")
            db_schema = DBSchema(test_db_path)

            factory = ServiceFactory(db_schema)

            # ShippedEquipmentService 조회
            shipped_equipment_service = factory.get_shipped_equipment_service()

            if shipped_equipment_service:
                print("[PASS] ShippedEquipmentService registered in ServiceFactory")
            else:
                print("[FAIL] ShippedEquipmentService not registered")
                return False

            # 메서드 존재 확인
            methods = [
                'get_all_shipped_equipment',
                'create_shipped_equipment',
                'import_from_file',
                'parse_equipment_file',
                'get_parameter_history',
                'match_configuration'
            ]

            for method in methods:
                if hasattr(shipped_equipment_service, method):
                    print(f"[PASS] Method '{method}' exists")
                else:
                    print(f"[FAIL] Method '{method}' not found")
                    return False

        return True

    except Exception as e:
        print(f"[FAIL] ServiceFactory test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_4_crud_operations():
    """Test 4: CRUD 연산 테스트 (간단)"""
    print("\n" + "=" * 60)
    print("Test 4: Basic CRUD Operations")
    print("=" * 60)

    try:
        from db_schema import DBSchema
        from app.services.shipped_equipment.shipped_equipment_service import ShippedEquipmentService
        from datetime import date

        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db_path = os.path.join(temp_dir, "test.sqlite")
            db_schema = DBSchema(test_db_path)

            # Equipment_Models, Equipment_Types, Equipment_Configurations 임시 데이터 생성
            with db_schema.get_connection() as conn:
                cursor = conn.cursor()

                # Models
                cursor.execute("""
                    INSERT INTO Equipment_Models (model_name, description, display_order)
                    VALUES ('Test-Model', 'Test', 1)
                """)
                model_id = cursor.lastrowid

                # Types
                cursor.execute("""
                    INSERT INTO Equipment_Types (model_id, type_name, description)
                    VALUES (?, 'Test-Type', 'Test')
                """, (model_id,))
                type_id = cursor.lastrowid

                # Configurations
                cursor.execute("""
                    INSERT INTO Equipment_Configurations (
                        type_id, configuration_name, port_count, wafer_count
                    ) VALUES (?, 'Test-Config', 1, 1)
                """, (type_id,))
                config_id = cursor.lastrowid

                conn.commit()

            service = ShippedEquipmentService(db_schema)

            # CREATE
            equipment_id = service.create_shipped_equipment(
                equipment_type_id=type_id,
                configuration_id=config_id,
                serial_number="TEST-001",
                customer_name="Test Customer",
                ship_date=date.today()
            )

            if equipment_id:
                print(f"[PASS] Created shipped equipment (ID: {equipment_id})")
            else:
                print("[FAIL] Create failed")
                return False

            # READ
            equipment = service.get_shipped_equipment_by_id(equipment_id)
            if equipment and equipment.serial_number == "TEST-001":
                print("[PASS] Read shipped equipment")
            else:
                print("[FAIL] Read failed")
                return False

            # UPDATE
            updated = service.update_shipped_equipment(
                equipment_id=equipment_id,
                notes="Test notes"
            )
            if updated:
                print("[PASS] Update shipped equipment")
            else:
                print("[FAIL] Update failed")
                return False

            # ADD PARAMETERS
            parameters = [
                {"parameter_name": "Param1", "parameter_value": "100"},
                {"parameter_name": "Param2", "parameter_value": "200"}
            ]
            count = service.add_parameters_bulk(equipment_id, parameters)
            if count == 2:
                print(f"[PASS] Added {count} parameters")
            else:
                print(f"[FAIL] Expected 2 parameters, got {count}")
                return False

            # DELETE
            deleted = service.delete_shipped_equipment(equipment_id)
            if deleted:
                print("[PASS] Delete shipped equipment")
            else:
                print("[FAIL] Delete failed")
                return False

        return True

    except Exception as e:
        print(f"[FAIL] CRUD test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """모든 테스트 실행"""
    print("=" * 60)
    print("Phase 2 Week 4 Day 1-2 - Database & Service Test")
    print("=" * 60)

    tests = [
        test_1_database_tables,
        test_2_shipped_equipment_service_import,
        test_3_service_factory_integration,
        test_4_crud_operations
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"\n[FAIL] Test exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test.__name__, False))

    # 결과 요약
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "[PASS] PASS" if result else "[FAIL] FAIL"
        print(f"{status} - {test_name}")

    print("\n" + "=" * 60)
    print(f"Total: {passed}/{total} ({passed/total*100:.1f}%)")
    print("=" * 60)

    if passed == total:
        print("\n[SUCCESS] All tests passed!")
        return 0
    else:
        print(f"\n[WARN] {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
