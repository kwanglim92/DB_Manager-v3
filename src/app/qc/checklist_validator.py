"""
QC Check list 검증 모듈

QC 검수 시 Check list 기반으로 파라미터를 검증합니다.
"""

import pandas as pd
from typing import Dict, List, Tuple


class ChecklistValidator:
    """Check list 기반 파라미터 검증"""

    def __init__(self, checklist_service, equipment_type_id):
        """
        Args:
            checklist_service: ChecklistService 인스턴스
            equipment_type_id: 장비 유형 ID
        """
        self.checklist_service = checklist_service
        self.equipment_type_id = equipment_type_id

        # Check list 캐싱
        self.checklist_items = self._load_checklist()

    def _load_checklist(self):
        """장비별 Check list 로드"""
        try:
            return self.checklist_service.get_equipment_checklist(self.equipment_type_id)
        except Exception as e:
            print(f"Check list 로드 실패: {e}")
            return []

    def validate_parameters(self, df: pd.DataFrame) -> Dict:
        """
        데이터프레임의 파라미터들을 Check list 기반으로 검증

        Args:
            df: 검증할 데이터프레임 (ItemName 컬럼 필요)

        Returns:
            {
                'total_params': int,  # 전체 파라미터 수
                'checklist_params': int,  # Check list 파라미터 수
                'validated_params': int,  # 검증 통과 파라미터 수
                'failed_params': int,  # 검증 실패 파라미터 수
                'critical_failures': List[Dict],  # CRITICAL 레벨 실패 목록
                'high_failures': List[Dict],  # HIGH 레벨 실패 목록
                'medium_failures': List[Dict],  # MEDIUM 레벨 실패 목록
                'low_failures': List[Dict],  # LOW 레벨 실패 목록
                'details': List[Dict]  # 상세 검증 결과
            }
        """
        if df is None or df.empty:
            return self._empty_result()

        if 'ItemName' not in df.columns:
            print("경고: ItemName 컬럼이 없습니다.")
            return self._empty_result()

        results = {
            'total_params': len(df),
            'checklist_params': 0,
            'validated_params': 0,
            'failed_params': 0,
            'critical_failures': [],
            'high_failures': [],
            'medium_failures': [],
            'low_failures': [],
            'details': []
        }

        # 각 파라미터 검증
        for idx, row in df.iterrows():
            param_name = row.get('ItemName', '')
            param_value = row.get('Value1', '') if 'Value1' in df.columns else ''

            if not param_name:
                continue

            # Check list 검증
            validation_result = self.checklist_service.validate_parameter_against_checklist(
                self.equipment_type_id,
                str(param_name),
                str(param_value)
            )

            if validation_result['is_checklist']:
                results['checklist_params'] += 1

                detail = {
                    'param_name': param_name,
                    'param_value': param_value,
                    'item_name': validation_result.get('item_name', ''),
                    'severity': validation_result['severity_level'],
                    'validation_passed': validation_result['validation_passed'],
                    'message': validation_result.get('message', ''),
                    'row_index': idx
                }

                results['details'].append(detail)

                if validation_result['validation_passed']:
                    results['validated_params'] += 1
                else:
                    results['failed_params'] += 1

                    # 심각도별로 분류
                    severity = validation_result['severity_level']
                    if severity == 'CRITICAL':
                        results['critical_failures'].append(detail)
                    elif severity == 'HIGH':
                        results['high_failures'].append(detail)
                    elif severity == 'MEDIUM':
                        results['medium_failures'].append(detail)
                    else:
                        results['low_failures'].append(detail)

        return results

    def _empty_result(self):
        """빈 결과 반환"""
        return {
            'total_params': 0,
            'checklist_params': 0,
            'validated_params': 0,
            'failed_params': 0,
            'critical_failures': [],
            'high_failures': [],
            'medium_failures': [],
            'low_failures': [],
            'details': []
        }

    def generate_report_summary(self, validation_result: Dict) -> str:
        """
        검증 결과 요약 생성

        Args:
            validation_result: validate_parameters() 반환값

        Returns:
            요약 문자열
        """
        lines = []
        lines.append("=" * 60)
        lines.append("Check list 검증 결과")
        lines.append("=" * 60)
        lines.append(f"전체 파라미터: {validation_result['total_params']}개")
        lines.append(f"Check list 파라미터: {validation_result['checklist_params']}개")
        lines.append(f"검증 통과: {validation_result['validated_params']}개")
        lines.append(f"검증 실패: {validation_result['failed_params']}개")
        lines.append("")

        if validation_result['failed_params'] > 0:
            lines.append("심각도별 실패 항목:")
            lines.append(f"  CRITICAL: {len(validation_result['critical_failures'])}개")
            lines.append(f"  HIGH: {len(validation_result['high_failures'])}개")
            lines.append(f"  MEDIUM: {len(validation_result['medium_failures'])}개")
            lines.append(f"  LOW: {len(validation_result['low_failures'])}개")
            lines.append("")

            # CRITICAL 실패 항목 상세
            if validation_result['critical_failures']:
                lines.append("[CRITICAL] 치명적 문제:")
                for failure in validation_result['critical_failures']:
                    lines.append(f"  - {failure['param_name']}: {failure['message']}")
                lines.append("")

            # HIGH 실패 항목 상세
            if validation_result['high_failures']:
                lines.append("[HIGH] 중요 문제:")
                for failure in validation_result['high_failures'][:5]:  # 최대 5개만
                    lines.append(f"  - {failure['param_name']}: {failure['message']}")
                if len(validation_result['high_failures']) > 5:
                    lines.append(f"  ... 외 {len(validation_result['high_failures']) - 5}개")
                lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)

    def get_checklist_coverage(self) -> float:
        """Check list 커버리지 반환 (0.0 ~ 1.0)"""
        if not hasattr(self, '_last_validation_result'):
            return 0.0

        result = self._last_validation_result
        if result['total_params'] == 0:
            return 0.0

        return result['checklist_params'] / result['total_params']

    def get_pass_rate(self) -> float:
        """검증 통과율 반환 (0.0 ~ 1.0)"""
        if not hasattr(self, '_last_validation_result'):
            return 0.0

        result = self._last_validation_result
        if result['checklist_params'] == 0:
            return 1.0  # Check list 항목이 없으면 100%

        return result['validated_params'] / result['checklist_params']

    def is_qc_passed(self) -> Tuple[bool, str]:
        """
        QC 합격 여부 판단

        Returns:
            (합격 여부, 사유)
        """
        if not hasattr(self, '_last_validation_result'):
            return False, "검증 결과 없음"

        result = self._last_validation_result

        # CRITICAL 레벨 실패가 있으면 무조건 불합격
        if result['critical_failures']:
            return False, f"CRITICAL 레벨 {len(result['critical_failures'])}개 항목 실패"

        # HIGH 레벨 실패가 3개 이상이면 불합격
        if len(result['high_failures']) >= 3:
            return False, f"HIGH 레벨 {len(result['high_failures'])}개 항목 실패"

        # Check list 통과율이 95% 미만이면 경고
        pass_rate = self.get_pass_rate()
        if pass_rate < 0.95:
            return False, f"Check list 통과율 {pass_rate*100:.1f}% (기준: 95% 이상)"

        return True, "모든 Check list 검증 통과"


def integrate_checklist_validation(qc_func):
    """
    QC 함수에 Check list 검증을 통합하는 데코레이터

    사용 예:
    @integrate_checklist_validation
    def perform_qc_check(self, df, equipment_type_id):
        # 기존 QC 로직
        ...
    """
    def wrapper(self, *args, **kwargs):
        # 기존 QC 함수 실행
        result = qc_func(self, *args, **kwargs)

        # Check list 검증 추가
        try:
            if hasattr(self, 'service_factory') and self.service_factory:
                checklist_service = self.service_factory.get_checklist_service()

                if checklist_service and 'equipment_type_id' in kwargs:
                    equipment_type_id = kwargs['equipment_type_id']
                    df = args[0] if args else kwargs.get('df')

                    if df is not None:
                        validator = ChecklistValidator(checklist_service, equipment_type_id)
                        validation_result = validator.validate_parameters(df)

                        # 결과에 Check list 검증 정보 추가
                        if isinstance(result, dict):
                            result['checklist_validation'] = validation_result
                        else:
                            # 기존 결과를 딕셔너리로 감싸서 반환
                            result = {
                                'qc_result': result,
                                'checklist_validation': validation_result
                            }

        except Exception as e:
            print(f"Check list 검증 통합 중 오류: {e}")

        return result

    return wrapper
