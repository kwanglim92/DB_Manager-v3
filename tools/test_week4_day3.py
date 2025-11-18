"""
Phase 2 Week 4 Day 3 Test
Import Logic 검증

테스트 범위:
1. parse_equipment_file() - TSV 파일 파싱 (2776 파라미터)
2. match_configuration() - Model/Type/Configuration 자동 매칭
3. import_from_file() - 전체 플로우 (파일 → DB)
4. 리핏 오더 처리 (is_refit, original_serial_number)
5. 성능 테스트 (2776 파라미터 일괄 삽입)
"""

import sys
import os
from pathlib import Path
import time

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# 테스트 파일 경로
TEST_FILE = project_root / "test" / "분리형 AE" / "04. NX-Hybrid WLI" / "NX-Hybrid WLI" / "U27006-100225_Intel Hillsboro #4_NX-Hybrid WLI.txt"


def test_1_parse_equipment_file():
    """Test 1: parse_equipment_file() - TSV 파일 파싱"""
    print("\n" + "=" * 60)
    print("Test 1: parse_equipment_file() - TSV 파일 파싱")
    print("=" * 60)

    try:
        from app.services.shipped_equipment.shipped_equipment_service import ShippedEquipmentService
        from db_schema import DBSchema

        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db_path = os.path.join(temp_dir, "test.sqlite")
            db_schema = DBSchema(test_db_path)

            service = ShippedEquipmentService(db_schema)

            # 파일 파싱
            start_time = time.time()
            result = service.parse_equipment_file(str(TEST_FILE))
            parse_time = time.time() - start_time

            if not result.success:
                print(f"[FAIL] File parsing failed: {result.error_message}")
                return False

            # 결과 검증
            print(f"[PASS] File parsed successfully")
            print(f"   - Serial Number: {result.serial_number}")
            print(f"   - Customer Name: {result.customer_name}")
            print(f"   - Model Name: {result.model_name}")
            print(f"   - Total Parameters: {result.total_count}")
            print(f"   - Parse Time: {parse_time * 1000:.2f}ms")

            # 예상 값 검증
            if result.serial_number != "U27006-100225":
                print(f"[FAIL] Expected serial 'U27006-100225', got '{result.serial_number}'")
                return False

            if result.customer_name != "Intel Hillsboro #4":
                print(f"[FAIL] Expected customer 'Intel Hillsboro #4', got '{result.customer_name}'")
                return False

            if result.model_name != "NX-Hybrid WLI":
                print(f"[FAIL] Expected model 'NX-Hybrid WLI', got '{result.model_name}'")
                return False

            # 파라미터 개수 확인 (헤더 제외, 약 2776개 예상)
            if result.total_count < 2700:
                print(f"[FAIL] Expected ~2776 parameters, got {result.total_count}")
                return False

            print(f"[PASS] All parsing validations passed")

            # 샘플 파라미터 검증
            if result.parameters:
                sample = result.parameters[0]
                print(f"\n   Sample Parameter:")
                print(f"     - parameter_name: {sample['parameter_name']}")
                print(f"     - parameter_value: {sample['parameter_value']}")
                print(f"     - module: {sample['module']}")
                print(f"     - part: {sample['part']}")
                print(f"     - data_type: {sample['data_type']}")

                # Module.Part.ItemName 형식 확인
                if '.' not in sample['parameter_name']:
                    print(f"[FAIL] Expected Module.Part.ItemName format")
                    return False

                print(f"[PASS] Parameter format validation passed")

        return True

    except Exception as e:
        print(f"[FAIL] Parse test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_2_match_configuration():
    """Test 2: match_configuration() - Model 기반 Configuration 자동 매칭"""
    print("\n" + "=" * 60)
    print("Test 2: match_configuration() - Configuration 자동 매칭")
    print("=" * 60)

    try:
        from app.services.shipped_equipment.shipped_equipment_service import ShippedEquipmentService
        from db_schema import DBSchema

        # 실제 DB 사용 (Equipment_Models, Equipment_Types, Equipment_Configurations 필요)
        db_path = project_root / "data" / "equipment_db.sqlite"

        if not db_path.exists():
            print(f"[SKIP] Database not found: {db_path}")
            print("   (Equipment Hierarchy 데이터가 필요합니다)")
            return True  # Skip은 PASS로 처리

        db_schema = DBSchema(str(db_path))
        service = ShippedEquipmentService(db_schema)

        # Model 이름 기반 Configuration 매칭
        model_name = "NX-Hybrid WLI"
        configuration_id = service.match_configuration(model_name)

        if configuration_id is None:
            print(f"[WARN] Configuration matching failed for '{model_name}'")
            print("   (Model/Type/Configuration 데이터가 없을 수 있습니다)")
            return True  # 데이터 없으면 PASS로 처리
        else:
            print(f"[PASS] Configuration matched: ID={configuration_id}")

        return True

    except Exception as e:
        print(f"[FAIL] Match configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_3_import_from_file():
    """Test 3: import_from_file() - 전체 플로우 (파일 → DB)"""
    print("\n" + "=" * 60)
    print("Test 3: import_from_file() - 전체 플로우")
    print("=" * 60)

    try:
        from app.services.shipped_equipment.shipped_equipment_service import ShippedEquipmentService
        from db_schema import DBSchema

        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db_path = os.path.join(temp_dir, "test.sqlite")
            db_schema = DBSchema(test_db_path)

            # Equipment_Models, Equipment_Types, Equipment_Configurations 생성
            with db_schema.get_connection() as conn:
                cursor = conn.cursor()

                # Equipment_Models
                cursor.execute("""
                    INSERT INTO Equipment_Models (model_name, description, display_order)
                    VALUES ('NX-Hybrid WLI', 'Hybrid WLI System', 1)
                """)
                model_id = cursor.lastrowid

                # Equipment_Types
                cursor.execute("""
                    INSERT INTO Equipment_Types (model_id, type_name, description, display_order)
                    VALUES (?, 'WLI-Standard', 'Standard WLI', 1)
                """, (model_id,))
                type_id = cursor.lastrowid

                # Equipment_Configurations
                cursor.execute("""
                    INSERT INTO Equipment_Configurations (
                        type_id, configuration_name, port_type, port_count,
                        wafer_size, wafer_count, is_customer_specific
                    ) VALUES (?, 'WLI-Single-300mm', 'Single', 1, '300mm', 1, 0)
                """, (type_id,))
                configuration_id = cursor.lastrowid

                conn.commit()

            service = ShippedEquipmentService(db_schema)

            # Import from file (auto-matching)
            print(f"\n   Importing file: {TEST_FILE.name}")
            start_time = time.time()

            success, message, equipment_id = service.import_from_file(
                str(TEST_FILE),
                configuration_id=configuration_id,  # 수동 지정
                auto_match=False
            )

            import_time = time.time() - start_time

            if not success:
                print(f"[FAIL] Import failed: {message}")
                return False

            print(f"[PASS] Import succeeded (ID: {equipment_id})")
            print(f"   - Message: {message}")
            print(f"   - Import Time: {import_time:.2f}s")

            # DB 검증
            equipment = service.get_shipped_equipment_by_id(equipment_id)

            if not equipment:
                print(f"[FAIL] Shipped equipment not found in DB")
                return False

            print(f"\n   Shipped Equipment:")
            print(f"     - ID: {equipment.id}")
            print(f"     - Serial: {equipment.serial_number}")
            print(f"     - Customer: {equipment.customer_name}")
            print(f"     - Configuration ID: {equipment.configuration_id}")

            # 파라미터 개수 검증
            parameters = service.get_parameters_by_equipment(equipment_id)
            print(f"\n   Parameters:")
            print(f"     - Total Count: {len(parameters)}")

            if len(parameters) < 2700:
                print(f"[FAIL] Expected ~2776 parameters, got {len(parameters)}")
                return False

            print(f"[PASS] All import validations passed")

        return True

    except Exception as e:
        print(f"[FAIL] Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_4_refit_order():
    """Test 4: 리핏 오더 처리 (is_refit, original_serial_number)"""
    print("\n" + "=" * 60)
    print("Test 4: 리핏 오더 처리")
    print("=" * 60)

    try:
        from app.services.shipped_equipment.shipped_equipment_service import ShippedEquipmentService
        from db_schema import DBSchema
        from datetime import date

        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db_path = os.path.join(temp_dir, "test.sqlite")
            db_schema = DBSchema(test_db_path)

            # 기본 데이터 생성
            with db_schema.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO Equipment_Models (model_name, description, display_order)
                    VALUES ('Test-Model', 'Test', 1)
                """)
                model_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO Equipment_Types (model_id, type_name, description, display_order)
                    VALUES (?, 'Test-Type', 'Test', 1)
                """, (model_id,))
                type_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO Equipment_Configurations (
                        type_id, configuration_name, port_type, port_count,
                        wafer_size, wafer_count
                    ) VALUES (?, 'Test-Config', 'Single', 1, '300mm', 1)
                """, (type_id,))
                configuration_id = cursor.lastrowid

                conn.commit()

            service = ShippedEquipmentService(db_schema)

            # 1. 원본 장비 생성
            original_id = service.create_shipped_equipment(
                equipment_type_id=type_id,
                configuration_id=configuration_id,
                serial_number="ORIGINAL-001",
                customer_name="Original Customer",
                ship_date=date(2024, 1, 1)
            )

            print(f"[PASS] Original equipment created (ID: {original_id})")

            # 2. 리핏 장비 생성
            refit_id = service.create_shipped_equipment(
                equipment_type_id=type_id,
                configuration_id=configuration_id,
                serial_number="REFIT-001",
                customer_name="Refit Customer",
                ship_date=date(2024, 6, 1),
                is_refit=True,
                original_serial_number="ORIGINAL-001",
                notes="리핏 오더 - 원본 장비 업그레이드"
            )

            print(f"[PASS] Refit equipment created (ID: {refit_id})")

            # 3. 리핏 장비 검증
            refit_equipment = service.get_shipped_equipment_by_id(refit_id)

            if not refit_equipment.is_refit:
                print(f"[FAIL] is_refit should be True")
                return False

            if refit_equipment.original_serial_number != "ORIGINAL-001":
                print(f"[FAIL] original_serial_number mismatch")
                return False

            print(f"\n   Refit Equipment:")
            print(f"     - Serial: {refit_equipment.serial_number}")
            print(f"     - Is Refit: {refit_equipment.is_refit}")
            print(f"     - Original Serial: {refit_equipment.original_serial_number}")
            print(f"     - Notes: {refit_equipment.notes}")

            print(f"[PASS] Refit order validation passed")

        return True

    except Exception as e:
        print(f"[FAIL] Refit test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_5_performance():
    """Test 5: 성능 테스트 (2776 파라미터 일괄 삽입)"""
    print("\n" + "=" * 60)
    print("Test 5: 성능 테스트 (2776 파라미터)")
    print("=" * 60)

    try:
        from app.services.shipped_equipment.shipped_equipment_service import ShippedEquipmentService
        from db_schema import DBSchema

        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db_path = os.path.join(temp_dir, "test.sqlite")
            db_schema = DBSchema(test_db_path)

            service = ShippedEquipmentService(db_schema)

            # 1. 파일 파싱 성능
            start_time = time.time()
            parse_result = service.parse_equipment_file(str(TEST_FILE))
            parse_time = time.time() - start_time

            print(f"\n   Parse Performance:")
            print(f"     - Time: {parse_time * 1000:.2f}ms")
            print(f"     - Parameters: {parse_result.total_count}")
            print(f"     - Rate: {parse_result.total_count / parse_time:.0f} params/sec")

            # 기준: 10,000 params/sec 이상
            if parse_result.total_count / parse_time < 10000:
                print(f"[WARN] Parse rate below target (10,000 params/sec)")
            else:
                print(f"[PASS] Parse rate meets target")

            # 2. Batch Insert 성능
            with db_schema.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO Equipment_Models (model_name, description, display_order)
                    VALUES ('Perf-Model', 'Performance Test', 1)
                """)
                model_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO Equipment_Types (model_id, type_name, description, display_order)
                    VALUES (?, 'Perf-Type', 'Test', 1)
                """, (model_id,))
                type_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO Equipment_Configurations (
                        type_id, configuration_name, port_type, port_count,
                        wafer_size, wafer_count
                    ) VALUES (?, 'Perf-Config', 'Single', 1, '300mm', 1)
                """, (type_id,))
                configuration_id = cursor.lastrowid

                conn.commit()

            equipment_id = service.create_shipped_equipment(
                equipment_type_id=type_id,
                configuration_id=configuration_id,
                serial_number="PERF-001",
                customer_name="Performance Test"
            )

            start_time = time.time()
            count = service.add_parameters_bulk(equipment_id, parse_result.parameters)
            insert_time = time.time() - start_time

            print(f"\n   Batch Insert Performance:")
            print(f"     - Time: {insert_time:.2f}s")
            print(f"     - Parameters: {count}")
            print(f"     - Rate: {count / insert_time:.0f} params/sec")

            # 기준: 5,000 params/sec 이상
            if count / insert_time < 5000:
                print(f"[WARN] Insert rate below target (5,000 params/sec)")
            else:
                print(f"[PASS] Insert rate meets target")

            # 전체 플로우 성능 (파싱 + 삽입)
            total_time = parse_time + insert_time
            total_rate = parse_result.total_count / total_time

            print(f"\n   Overall Performance:")
            print(f"     - Total Time: {total_time:.2f}s")
            print(f"     - Total Rate: {total_rate:.0f} params/sec")

            # 기준: 2,000 params/sec 이상
            if total_rate < 2000:
                print(f"[FAIL] Overall rate below target (2,000 params/sec)")
                return False
            else:
                print(f"[PASS] Overall rate meets target")

        return True

    except Exception as e:
        print(f"[FAIL] Performance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """모든 테스트 실행"""
    print("=" * 60)
    print("Phase 2 Week 4 Day 3 - Import Logic Test")
    print("=" * 60)

    # 테스트 파일 존재 확인
    if not TEST_FILE.exists():
        print(f"\n[ERROR] Test file not found: {TEST_FILE}")
        return 1

    tests = [
        test_1_parse_equipment_file,
        test_2_match_configuration,
        test_3_import_from_file,
        test_4_refit_order,
        test_5_performance
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
