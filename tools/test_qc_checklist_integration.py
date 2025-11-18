#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QC Check list 통합 테스트

QC 검수 워크플로우에 Check list 검증이 정상적으로 통합되었는지 테스트합니다.
"""

import sys
import os
import io

# Windows 콘솔 인코딩 문제 해결
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 프로젝트 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from app.schema import DBSchema
from app.services import ServiceFactory
from app.simplified_qc_system import SimplifiedQCSystem
import pandas as pd


def test_qc_checklist_integration():
    """QC Check list 통합 테스트"""
    print("=" * 70)
    print("QC Check list 통합 테스트 시작")
    print("=" * 70)

    # 1. DB 및 서비스 초기화
    print("\n[1단계] DB 및 서비스 초기화")
    db_schema = DBSchema()
    service_factory = ServiceFactory(db_schema)
    checklist_service = service_factory.get_checklist_service()

    # 장비 유형 조회
    equipment_types = db_schema.get_equipment_types()
    if not equipment_types:
        print(">> FAIL: 장비 유형이 없습니다.")
        return False

    equipment_type_id = equipment_types[0][0]  # 첫 번째 장비 사용
    equipment_type_name = equipment_types[0][1]
    print(f">> OK: 장비 유형 ID {equipment_type_id} ({equipment_type_name}) 사용")

    # 2. Check list 항목 확인
    print("\n[2단계] Check list 항목 확인")
    checklist_items = checklist_service.get_common_checklist_items()
    print(f">> OK: 공통 Check list {len(checklist_items)}개 항목 존재")

    if len(checklist_items) == 0:
        print(">> WARN: Check list 항목이 없습니다. data/initial_checklist_data.py를 먼저 실행하세요.")
        return False

    # 샘플 출력 (tuple: id, item_name, parameter_pattern, is_common, severity_level, validation_rule, description)
    print("\n샘플 Check list 항목:")
    for item in checklist_items[:3]:
        print(f"  - {item[1]} ({item[4]})")

    # 3. QC 시스템 초기화
    print("\n[3단계] QC 시스템 초기화 (Check list 지원)")
    qc_system = SimplifiedQCSystem(
        db_schema=db_schema,
        update_log_callback=lambda msg: print(f"   [QC] {msg}"),
        service_factory=service_factory  # Check list 검증 지원
    )
    print(">> OK: SimplifiedQCSystem 초기화 완료")

    # 4. QC 검수 실행 (comprehensive 모드)
    print("\n[4단계] QC 검수 실행 (comprehensive 모드)")
    result = qc_system.perform_qc_check(equipment_type_id, mode="comprehensive")

    if not result['success']:
        print(f">> FAIL: QC 검수 실패 - {result.get('message', 'Unknown error')}")
        return False

    print(f">> OK: QC 검수 성공")

    # 5. 결과 검증
    print("\n[5단계] 결과 검증")
    summary = result['summary']
    checklist_validation = result.get('checklist_validation')

    print(f"\n>> 기본 QC 결과:")
    print(f"   - 전체 상태: {summary['overall_status']}")
    print(f"   - 총 이슈: {summary['total_issues']}개")
    print(f"   - 높음: {summary['high_severity']}, 중간: {summary['medium_severity']}, 낮음: {summary['low_severity']}")

    if checklist_validation:
        print(f"\n>> Check list 검증 결과:")
        print(f"   - 전체 파라미터: {checklist_validation['total_params']}개")
        print(f"   - Check list 파라미터: {checklist_validation['checklist_params']}개")
        print(f"   - 검증 통과: {checklist_validation['validated_params']}개")
        print(f"   - 검증 실패: {checklist_validation['failed_params']}개")
        print(f"   - QC 합격: {'YES' if checklist_validation['qc_passed'] else 'NO'}")
        if not checklist_validation['qc_passed']:
            print(f"   - 사유: {checklist_validation['qc_reason']}")

        # 심각도별 실패 항목
        if checklist_validation['failed_params'] > 0:
            print(f"\n   심각도별 실패:")
            print(f"   - CRITICAL: {len(checklist_validation['critical_failures'])}개")
            print(f"   - HIGH: {len(checklist_validation['high_failures'])}개")
            print(f"   - MEDIUM: {len(checklist_validation['medium_failures'])}개")
            print(f"   - LOW: {len(checklist_validation['low_failures'])}개")

        print("\n>> OK: Check list 검증이 정상적으로 통합되었습니다!")
    else:
        print("\n>> WARN: Check list 검증 결과가 없습니다.")
        print("   (ServiceFactory가 전달되지 않았거나 Check list가 비활성화됨)")

    # 6. 권장사항 확인
    print("\n[6단계] 권장사항 확인")
    recommendations = result.get('recommendations', [])
    if recommendations:
        print(f">> 권장사항 {len(recommendations)}개:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    else:
        print(">> 권장사항 없음")

    # 7. 최종 판정
    print("\n" + "=" * 70)
    print("최종 결과")
    print("=" * 70)

    if result['success']:
        print(">> SUCCESS: QC Check list 통합 테스트 성공!")
        print(f"   - 기본 QC: {summary['overall_status']}")
        if checklist_validation:
            print(f"   - Check list: {'PASS' if checklist_validation['qc_passed'] else 'FAIL'}")
        return True
    else:
        print(">> FAIL: QC Check list 통합 테스트 실패")
        return False


def main():
    """메인 실행 함수"""
    try:
        success = test_qc_checklist_integration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n>> ERROR: 테스트 중 예외 발생")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
