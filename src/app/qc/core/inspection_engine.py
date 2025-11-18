"""
Inspection Engine - QC 검수 엔진 (Phase 2)
"""

import json
from typing import Dict, List, Any, Optional
from .models import ChecklistItem, InspectionResult
from .checklist_provider import ChecklistProvider
from .spec_matcher import SpecMatcher


class InspectionEngine:
    """
    QC 검수 엔진

    Phase 2 구현:
    - Module.Part.ItemName 복합 키 기반 자동 매칭
    - Equipment_Checklist_Exceptions 적용
    - Pass/Fail 판정 (심각도 없음, 모든 항목 동일 중요도)
    """

    def __init__(self, checklist_provider: Optional[ChecklistProvider] = None):
        """
        초기화

        Args:
            checklist_provider: Checklist 제공자 (None이면 자동 생성)
        """
        self.checklist_provider = checklist_provider or ChecklistProvider()
        self.spec_matcher = SpecMatcher()

    def inspect(
        self,
        file_data: Dict[str, Any],
        configuration_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        QC 검수 실행

        Args:
            file_data: 파일 데이터
                - 옵션 1: ItemName → Value 매핑 (레거시)
                - 옵션 2: (Module, Part, ItemName) → Value 매핑 (신규)
            configuration_id: Configuration ID (None이면 Type Common)

        Returns:
            Dict[str, Any]: 검수 결과
                {
                    'is_pass': bool,           # 전체 합격 여부
                    'total_count': int,        # 검증된 항목 수
                    'failed_count': int,       # 실패한 항목 수
                    'passed_count': int,       # 합격한 항목 수
                    'results': List[Dict],     # 각 항목 검증 결과
                    'matched_count': int,      # 매칭된 항목 수
                    'exception_count': int     # 예외 처리된 항목 수
                }
        """
        # 1. 예외를 제외한 활성 Checklist 항목 조회
        checklist_items = self.checklist_provider.get_items_excluding_exceptions(
            configuration_id
        )

        # 예외 항목 수
        all_items = self.checklist_provider.get_active_items()
        exception_count = len(all_items) - len(checklist_items)

        # 2. 파일 데이터와 매칭
        matched_items = self.spec_matcher.match(checklist_items, file_data)

        # 3. 각 항목 검증
        results = []
        for item, file_key, file_value in matched_items:
            is_valid = self.validate_item(item, file_value)

            result = InspectionResult(
                item_name=item.item_name,
                module=item.module,
                part=item.part,
                display_name=item.display_name,
                file_value=file_value,
                is_valid=is_valid,
                spec=self.get_spec_display(item),
                category=item.category or 'Uncategorized',
                description=item.description or ''
            )
            results.append(result.to_dict())

        # 4. Pass/Fail 판정 (모든 항목이 Pass일 때만 전체 Pass)
        failed_count = sum(1 for r in results if not r['is_valid'])
        passed_count = len(results) - failed_count
        is_pass = failed_count == 0

        return {
            'is_pass': is_pass,
            'total_count': len(results),
            'failed_count': failed_count,
            'passed_count': passed_count,
            'results': results,
            'matched_count': len(matched_items),
            'exception_count': exception_count
        }

    @staticmethod
    def validate_item(item: ChecklistItem, file_value: Any) -> bool:
        """
        단일 Check list 항목 검증

        Args:
            item: Check list 항목
            file_value: 파일의 실제 값

        Returns:
            bool: 검증 성공 여부
        """
        # Spec 범위 검증 (Min/Max)
        if item.spec_min and item.spec_max:
            try:
                val = float(file_value)
                return float(item.spec_min) <= val <= float(item.spec_max)
            except (ValueError, TypeError):
                return False

        # Expected Value 검증 (Pass/Fail, Enum 등)
        elif item.expected_value:
            # JSON 파싱 시도 (Enum: ["Pass", "Fail"] 등)
            try:
                allowed_values = json.loads(item.expected_value)
                if isinstance(allowed_values, list):
                    return str(file_value) in [str(v) for v in allowed_values]
            except (json.JSONDecodeError, TypeError):
                pass

            # 단순 문자열 비교 (대소문자 무시)
            return str(file_value).upper() == str(item.expected_value).upper()

        # Spec 없음 (항목 존재만 확인)
        else:
            return True

    @staticmethod
    def get_spec_display(item: ChecklistItem) -> str:
        """
        Spec 표시 문자열 생성

        Args:
            item: Check list 항목

        Returns:
            str: Spec 표시 문자열 ("0.5 ~ 2.0", "Pass", "N/A" 등)
        """
        if item.spec_min and item.spec_max:
            return f"{item.spec_min} ~ {item.spec_max}"
        elif item.expected_value:
            # JSON인 경우 파싱하여 보기 좋게 표시
            try:
                allowed_values = json.loads(item.expected_value)
                if isinstance(allowed_values, list):
                    return " / ".join(str(v) for v in allowed_values)
            except (json.JSONDecodeError, TypeError):
                pass
            return item.expected_value
        else:
            return "N/A"

    def get_inspection_summary(self, result: Dict[str, Any]) -> str:
        """
        검수 결과 요약 문자열 생성

        Args:
            result: inspect() 결과

        Returns:
            str: 요약 문자열
        """
        is_pass = result['is_pass']
        total = result['total_count']
        failed = result['failed_count']
        passed = result.get('passed_count', total - failed)

        status = "✅ PASS" if is_pass else "❌ FAIL"

        summary = f"QC Inspection Result: {status}\n"
        summary += f"{'=' * 40}\n"
        summary += f"Total Items: {total}\n"

        if total > 0:
            summary += f"Passed: {passed} ({passed/total*100:.1f}%)\n"
            summary += f"Failed: {failed} ({failed/total*100:.1f}%)\n"
        else:
            summary += "Passed: 0\nFailed: 0\n"

        if result.get('exception_count', 0) > 0:
            summary += f"\nExceptions Applied: {result['exception_count']}\n"

        return summary
