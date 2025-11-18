#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 1 End-to-End 통합 테스트

전체 워크플로우를 테스트합니다:
1. Check list 항목 추가
2. 장비별 Check list 매핑
3. QC 검수 실행 및 검증
4. Check list 수정
5. Audit Log 확인
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


class Phase1E2ETest:
    """Phase 1 End-to-End 테스트"""

    def __init__(self):
        self.db_schema = DBSchema()
        self.service_factory = ServiceFactory(self.db_schema)
        self.checklist_service = self.service_factory.get_checklist_service()
        self.test_results = []

    def log(self, message, level="INFO"):
        """테스트 로그"""
        prefix = {
            "INFO": ">>",
            "SUCCESS": "✅",
            "FAIL": "❌",
            "WARN": "⚠️"
        }.get(level, ">>")
        print(f"{prefix} {message}")

    def assert_true(self, condition, test_name, message=""):
        """검증 및 결과 기록"""
        if condition:
            self.log(f"{test_name}: PASS {message}", "SUCCESS")
            self.test_results.append((test_name, True, message))
            return True
        else:
            self.log(f"{test_name}: FAIL {message}", "FAIL")
            self.test_results.append((test_name, False, message))
            return False

    def test_scenario_1_add_checklist_item(self):
        """시나리오 1: 새로운 Check list 항목 추가"""
        self.log("\n[시나리오 1] 새로운 Check list 항목 추가")

        # 테스트용 항목 추가
        test_item_name = "TEST_파워 서플라이 전압"
        test_pattern = r".*(power|supply).*(voltage|volt).*"

        # 기존 항목 삭제 (있다면)
        try:
            items = self.db_schema.get_checklist_items(common_only=False)
            for item in items:
                if item[1] == test_item_name:
                    self.db_schema.delete_checklist_item(item[0])
        except:
            pass

        # 새 항목 추가
        item_id = self.checklist_service.add_checklist_item(
            item_name=test_item_name,
            parameter_pattern=test_pattern,
            is_common=True,
            severity_level='HIGH',
            validation_rule='{"type": "range", "min": 100, "max": 240}',
            description='전원 공급 전압 검증'
        )

        success = self.assert_true(
            item_id is not None,
            "Check list 항목 추가",
            f"ID: {item_id}"
        )

        if success:
            # 추가된 항목 확인
            items = self.db_schema.get_checklist_items(common_only=True)
            found = any(item[1] == test_item_name for item in items)
            self.assert_true(found, "항목 조회 확인", f"{test_item_name} 발견")

        return item_id

    def test_scenario_2_equipment_mapping(self, checklist_item_id):
        """시나리오 2: 장비별 Check list 매핑"""
        self.log("\n[시나리오 2] 장비별 Check list 매핑")

        # 첫 번째 장비 가져오기
        equipment_types = self.db_schema.get_equipment_types()
        if not equipment_types:
            self.log("장비 유형이 없습니다.", "WARN")
            return False

        equipment_type_id = equipment_types[0][0]
        equipment_name = equipment_types[0][1]

        # 장비별 매핑 추가
        try:
            mapping_id = self.db_schema.add_equipment_checklist_mapping(
                equipment_type_id=equipment_type_id,
                checklist_item_id=checklist_item_id,
                custom_validation_rule='{"type": "range", "min": 110, "max": 220}',
                priority=1,
                added_reason='E2E 테스트용 매핑'
            )

            self.assert_true(
                mapping_id is not None,
                "장비별 매핑 추가",
                f"장비: {equipment_name}, 매핑 ID: {mapping_id}"
            )

            return mapping_id
        except Exception as e:
            self.log(f"매핑 추가 실패: {str(e)}", "FAIL")
            return None

    def test_scenario_3_qc_validation(self):
        """시나리오 3: QC 검수 및 Check list 검증"""
        self.log("\n[시나리오 3] QC 검수 및 Check list 검증")

        # 장비 유형 가져오기
        equipment_types = self.db_schema.get_equipment_types()
        if not equipment_types:
            self.log("장비 유형이 없습니다.", "WARN")
            return False

        equipment_type_id = equipment_types[0][0]

        # QC 시스템 초기화
        qc_system = SimplifiedQCSystem(
            db_schema=self.db_schema,
            update_log_callback=lambda msg: None,  # 로그 출력 억제
            service_factory=self.service_factory
        )

        # QC 검수 실행
        result = qc_system.perform_qc_check(equipment_type_id, mode="comprehensive")

        # 검수 성공 확인
        self.assert_true(
            result['success'],
            "QC 검수 실행",
            f"모드: comprehensive"
        )

        # Check list 검증 결과 확인
        checklist_validation = result.get('checklist_validation')
        if checklist_validation:
            self.assert_true(
                checklist_validation['total_params'] > 0,
                "Check list 검증 실행",
                f"총 {checklist_validation['total_params']}개 파라미터 검증"
            )

            self.assert_true(
                checklist_validation['checklist_params'] > 0,
                "Check list 매칭 파라미터 발견",
                f"{checklist_validation['checklist_params']}개 항목"
            )

            # 심각도별 분류 확인
            has_severity_classification = (
                'critical_failures' in checklist_validation and
                'high_failures' in checklist_validation and
                'medium_failures' in checklist_validation and
                'low_failures' in checklist_validation
            )

            self.assert_true(
                has_severity_classification,
                "심각도별 분류",
                "CRITICAL/HIGH/MEDIUM/LOW"
            )

            # QC 합격 판정 확인
            self.assert_true(
                'qc_passed' in checklist_validation,
                "QC 합격 판정",
                f"결과: {'PASS' if checklist_validation.get('qc_passed') else 'FAIL'}"
            )
        else:
            self.log("Check list 검증 결과가 없습니다.", "WARN")

        return result

    def test_scenario_4_audit_log(self):
        """시나리오 4: Audit Log 확인"""
        self.log("\n[시나리오 4] Audit Log 확인")

        # Audit Log 조회
        try:
            audit_logs = self.db_schema.get_checklist_audit_logs(limit=10)

            self.assert_true(
                len(audit_logs) > 0,
                "Audit Log 조회",
                f"{len(audit_logs)}개 로그 발견"
            )

            # 최근 로그 샘플 출력
            if audit_logs:
                self.log("\n최근 Audit Log (최대 3개):")
                for log in audit_logs[:3]:
                    action = log[1]
                    target = f"{log[2]}/{log[3]}"
                    user = log[6]
                    timestamp = log[7]
                    self.log(f"  - [{action}] {target} by {user} at {timestamp}", "INFO")

            return True
        except Exception as e:
            self.log(f"Audit Log 조회 실패: {str(e)}", "FAIL")
            return False

    def test_scenario_5_checklist_update(self, item_id):
        """시나리오 5: Check list 항목 수정"""
        self.log("\n[시나리오 5] Check list 항목 수정")

        try:
            # 항목 수정
            success = self.db_schema.update_checklist_item(
                item_id=item_id,
                item_name="TEST_파워 서플라이 전압 (수정됨)",
                parameter_pattern=r".*(power|supply).*(voltage|volt).*",
                severity_level='CRITICAL',  # HIGH -> CRITICAL로 변경
                validation_rule='{"type": "range", "min": 110, "max": 230}',
                description='전원 공급 전압 검증 (수정됨)'
            )

            self.assert_true(
                success,
                "Check list 항목 수정",
                "심각도: HIGH -> CRITICAL"
            )

            return success
        except Exception as e:
            self.log(f"항목 수정 실패: {str(e)}", "FAIL")
            return False

    def test_scenario_6_cleanup(self, item_id, mapping_id):
        """시나리오 6: 테스트 데이터 정리"""
        self.log("\n[시나리오 6] 테스트 데이터 정리")

        cleanup_success = True

        # 매핑 삭제
        if mapping_id:
            try:
                self.db_schema.delete_equipment_checklist_mapping(mapping_id)
                self.log("장비별 매핑 삭제 완료", "SUCCESS")
            except Exception as e:
                self.log(f"매핑 삭제 실패: {str(e)}", "WARN")
                cleanup_success = False

        # Check list 항목 삭제
        if item_id:
            try:
                self.db_schema.delete_checklist_item(item_id)
                self.log("Check list 항목 삭제 완료", "SUCCESS")
            except Exception as e:
                self.log(f"항목 삭제 실패: {str(e)}", "WARN")
                cleanup_success = False

        self.assert_true(cleanup_success, "테스트 데이터 정리", "")
        return cleanup_success

    def print_summary(self):
        """테스트 결과 요약"""
        self.log("\n" + "=" * 70)
        self.log("End-to-End 테스트 결과 요약")
        self.log("=" * 70)

        total = len(self.test_results)
        passed = sum(1 for _, success, _ in self.test_results if success)
        failed = total - passed

        self.log(f"\n총 테스트: {total}개")
        self.log(f"통과: {passed}개", "SUCCESS")
        if failed > 0:
            self.log(f"실패: {failed}개", "FAIL")

        self.log("\n상세 결과:")
        for name, success, message in self.test_results:
            status = "PASS" if success else "FAIL"
            level = "SUCCESS" if success else "FAIL"
            self.log(f"  [{status}] {name} {message}", level)

        self.log("\n" + "=" * 70)

        if failed == 0:
            self.log("모든 테스트 통과!", "SUCCESS")
            return True
        else:
            self.log(f"{failed}개 테스트 실패", "FAIL")
            return False

    def run_all_tests(self):
        """모든 E2E 테스트 실행"""
        self.log("=" * 70)
        self.log("Phase 1 End-to-End 통합 테스트 시작")
        self.log("=" * 70)

        item_id = None
        mapping_id = None

        try:
            # 시나리오 1: Check list 항목 추가
            item_id = self.test_scenario_1_add_checklist_item()

            # 시나리오 2: 장비별 매핑
            if item_id:
                mapping_id = self.test_scenario_2_equipment_mapping(item_id)

            # 시나리오 3: QC 검수 및 검증
            self.test_scenario_3_qc_validation()

            # 시나리오 4: Audit Log 확인
            self.test_scenario_4_audit_log()

            # 시나리오 5: Check list 수정
            if item_id:
                self.test_scenario_5_checklist_update(item_id)

            # 시나리오 6: 정리
            self.test_scenario_6_cleanup(item_id, mapping_id)

        except Exception as e:
            self.log(f"\n테스트 실행 중 예외 발생: {str(e)}", "FAIL")
            import traceback
            traceback.print_exc()

        # 결과 요약
        return self.print_summary()


def main():
    """메인 실행 함수"""
    try:
        tester = Phase1E2ETest()
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n>> ERROR: 테스트 초기화 실패")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
