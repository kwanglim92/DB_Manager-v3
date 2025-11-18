"""
QC Inspection v2 테스트

Phase 1.5 Week 3 Day 1-2: qc_inspection_v2() 기능 테스트
- ItemName 기반 자동 매칭
- Exception 적용
- Pass/Fail 판정

Author: Phase 1.5 Week 3
Date: 2025-11-13
"""

import sys
import os

# src 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from db_schema import DBSchema
from app.qc import (
    qc_inspection_v2,
    get_inspection_summary,
    get_active_checklist_items
)


def setup_test_data():
    """
    테스트 데이터 생성
    """
    db_schema = DBSchema()

    with db_schema.get_connection() as conn:
        cursor = conn.cursor()

        # 기존 테스트 데이터 삭제
        cursor.execute("DELETE FROM QC_Checklist_Items")

        # 테스트 Check list 항목 추가
        test_items = [
            # Spec 범위 검증
            ('Module.Dsp.XDetector.Gain', '0.5', '2.0', None, 'Performance', 'X Detector Gain 범위'),
            ('Module.Temperature.Chamber', '20.0', '25.0', None, 'Safety', 'Chamber 온도 범위'),

            # Expected Value 검증 (Enum)
            ('Module.Status.SelfTest', None, None, '["Pass", "Fail"]', 'Safety', 'Self Test 결과'),
            ('Module.Heater.Enable', None, None, '["ON", "OFF"]', 'Configuration', 'Heater 활성화 상태'),

            # Expected Value 검증 (단순 문자열)
            ('Module.Communication.Status', None, None, 'OK', 'Communication', '통신 상태'),

            # Spec 없음 (존재만 확인)
            ('Module.Version', None, None, None, 'Information', '버전 정보'),
        ]

        cursor.executemany("""
            INSERT INTO QC_Checklist_Items (item_name, spec_min, spec_max, expected_value, category, description, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, test_items)

        conn.commit()

    print("[OK] 테스트 데이터 생성 완료 (6개 항목)")


def test_basic_inspection():
    """
    테스트 1: 기본 검수 (모든 항목 Pass)
    """
    print("\n=== 테스트 1: 기본 검수 (모든 항목 Pass) ===")

    # 파일 데이터 (모든 항목 Pass)
    file_data = {
        'Module.Dsp.XDetector.Gain': 1.5,  # Pass (0.5~2.0 범위 내)
        'Module.Temperature.Chamber': 22.5,  # Pass (20.0~25.0 범위 내)
        'Module.Status.SelfTest': 'Pass',  # Pass (Enum)
        'Module.Heater.Enable': 'ON',  # Pass (Enum)
        'Module.Communication.Status': 'OK',  # Pass (문자열 비교)
        'Module.Version': '1.2.3',  # Pass (존재만 확인)
    }

    result = qc_inspection_v2(file_data, configuration_id=None)

    print(get_inspection_summary(result))

    # 검증
    assert result['is_pass'] == True, "전체 검수가 Pass여야 합니다"
    assert result['total_count'] == 6, "6개 항목이 검증되어야 합니다"
    assert result['failed_count'] == 0, "실패 항목이 없어야 합니다"

    print("[OK] 테스트 1 통과")


def test_failed_inspection():
    """
    테스트 2: 실패 케이스 (일부 항목 Fail)
    """
    print("\n=== 테스트 2: 실패 케이스 (일부 항목 Fail) ===")

    # 파일 데이터 (일부 항목 Fail)
    file_data = {
        'Module.Dsp.XDetector.Gain': 3.0,  # Fail (2.0 초과)
        'Module.Temperature.Chamber': 22.5,  # Pass
        'Module.Status.SelfTest': 'Unknown',  # Fail (Enum에 없는 값)
        'Module.Heater.Enable': 'ON',  # Pass
        'Module.Communication.Status': 'ERROR',  # Fail (문자열 불일치)
        'Module.Version': '1.2.3',  # Pass
    }

    result = qc_inspection_v2(file_data, configuration_id=None)

    print(get_inspection_summary(result))

    # 검증
    assert result['is_pass'] == False, "전체 검수가 Fail이어야 합니다"
    assert result['total_count'] == 6, "6개 항목이 검증되어야 합니다"
    assert result['failed_count'] == 3, "3개 항목이 실패해야 합니다"

    # 실패 항목 확인
    failed_items = [r for r in result['results'] if not r['is_valid']]
    failed_item_names = [r['item_name'] for r in failed_items]

    assert 'Module.Dsp.XDetector.Gain' in failed_item_names
    assert 'Module.Status.SelfTest' in failed_item_names
    assert 'Module.Communication.Status' in failed_item_names

    print("[OK] 테스트 2 통과")


def test_partial_matching():
    """
    테스트 3: 부분 매칭 (파일에 일부 항목만 존재)
    """
    print("\n=== 테스트 3: 부분 매칭 (파일에 일부 항목만 존재) ===")

    # 파일 데이터 (3개 항목만 존재)
    file_data = {
        'Module.Dsp.XDetector.Gain': 1.5,  # Pass
        'Module.Temperature.Chamber': 22.5,  # Pass
        'Module.Version': '1.2.3',  # Pass
    }

    result = qc_inspection_v2(file_data, configuration_id=None)

    print(get_inspection_summary(result))

    # 검증
    assert result['is_pass'] == True, "전체 검수가 Pass여야 합니다"
    assert result['total_count'] == 3, "3개 항목만 검증되어야 합니다"
    assert result['failed_count'] == 0, "실패 항목이 없어야 합니다"

    print("[OK] 테스트 3 통과")


def test_exception_handling():
    """
    테스트 4: Configuration 예외 처리
    """
    print("\n=== 테스트 4: Configuration 예외 처리 ===")

    # Configuration 및 예외 생성
    db_schema = DBSchema()

    with db_schema.get_connection() as conn:
        cursor = conn.cursor()

        # 테스트용 Configuration 생성
        cursor.execute("""
            INSERT INTO Equipment_Configurations (equipment_type_id, config_name, port_type, wafer_sizes, notes)
            VALUES (1, 'Test Configuration', 'Single', '300mm', 'Test configuration for exception testing')
        """)
        config_id = cursor.lastrowid

        # 'Module.Dsp.XDetector.Gain' 항목을 예외로 추가
        cursor.execute("""
            SELECT id FROM QC_Checklist_Items WHERE item_name = 'Module.Dsp.XDetector.Gain'
        """)
        item_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO Equipment_Checklist_Exceptions (configuration_id, checklist_item_id, reason)
            VALUES (?, ?, 'Test exception')
        """, (config_id, item_id))

        conn.commit()

    # 파일 데이터 (모든 항목 포함)
    file_data = {
        'Module.Dsp.XDetector.Gain': 1.5,  # 예외 처리됨 (검증 제외)
        'Module.Temperature.Chamber': 22.5,  # Pass
        'Module.Status.SelfTest': 'Pass',  # Pass
        'Module.Heater.Enable': 'ON',  # Pass
        'Module.Communication.Status': 'OK',  # Pass
        'Module.Version': '1.2.3',  # Pass
    }

    result = qc_inspection_v2(file_data, configuration_id=config_id)

    print(get_inspection_summary(result))

    # 검증
    assert result['is_pass'] == True, "전체 검수가 Pass여야 합니다"
    assert result['total_count'] == 5, "5개 항목만 검증되어야 합니다 (1개 예외)"
    assert result['failed_count'] == 0, "실패 항목이 없어야 합니다"
    assert result['exception_count'] == 1, "1개 예외가 적용되어야 합니다"

    # 예외 항목이 검증 결과에 없는지 확인
    verified_items = [r['item_name'] for r in result['results']]
    assert 'Module.Dsp.XDetector.Gain' not in verified_items, "예외 항목은 검증되지 않아야 합니다"

    print("[OK] 테스트 4 통과")

    # 테스트 데이터 정리
    with db_schema.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Equipment_Checklist_Exceptions WHERE configuration_id = ?", (config_id,))
        cursor.execute("DELETE FROM Equipment_Configurations WHERE id = ?", (config_id,))
        conn.commit()


def test_active_items_only():
    """
    테스트 5: 활성화된 항목만 검증
    """
    print("\n=== 테스트 5: 활성화된 항목만 검증 ===")

    # 'Module.Version' 항목을 비활성화
    db_schema = DBSchema()

    with db_schema.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE QC_Checklist_Items
            SET is_active = 0
            WHERE item_name = 'Module.Version'
        """)
        conn.commit()

    # 파일 데이터 (6개 항목 포함)
    file_data = {
        'Module.Dsp.XDetector.Gain': 1.5,
        'Module.Temperature.Chamber': 22.5,
        'Module.Status.SelfTest': 'Pass',
        'Module.Heater.Enable': 'ON',
        'Module.Communication.Status': 'OK',
        'Module.Version': '1.2.3',  # 비활성화됨 (검증 제외)
    }

    result = qc_inspection_v2(file_data, configuration_id=None)

    print(get_inspection_summary(result))

    # 검증
    assert result['total_count'] == 5, "5개 항목만 검증되어야 합니다 (1개 비활성화)"

    # 비활성화 항목이 검증 결과에 없는지 확인
    verified_items = [r['item_name'] for r in result['results']]
    assert 'Module.Version' not in verified_items, "비활성화 항목은 검증되지 않아야 합니다"

    print("[OK] 테스트 5 통과")

    # 테스트 데이터 복원
    with db_schema.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE QC_Checklist_Items
            SET is_active = 1
            WHERE item_name = 'Module.Version'
        """)
        conn.commit()


def cleanup_test_data():
    """
    테스트 데이터 정리
    """
    db_schema = DBSchema()

    with db_schema.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM QC_Checklist_Items")
        conn.commit()

    print("\n[OK] 테스트 데이터 정리 완료")


def main():
    """
    테스트 실행
    """
    print("QC Inspection v2 테스트 시작\n")
    print("=" * 60)

    try:
        # 테스트 데이터 생성
        setup_test_data()

        # 테스트 실행
        test_basic_inspection()
        test_failed_inspection()
        test_partial_matching()
        test_exception_handling()
        test_active_items_only()

        # 테스트 데이터 정리
        cleanup_test_data()

        print("\n" + "=" * 60)
        print("[SUCCESS] 모든 테스트 통과 (5/5)")
        print("=" * 60)

        return 0

    except AssertionError as e:
        print(f"\n[FAIL] 테스트 실패: {e}")
        cleanup_test_data()
        return 1

    except Exception as e:
        print(f"\n[ERROR] 테스트 오류: {e}")
        import traceback
        traceback.print_exc()
        cleanup_test_data()
        return 1


if __name__ == "__main__":
    sys.exit(main())
