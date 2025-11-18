"""
QC Service - QC 검수 통합 서비스

Phase 2 리팩토링:
- Core Layer (InspectionEngine) 사용
- 검수 실행 및 결과 관리 통합
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

from ..core import InspectionEngine, ChecklistProvider, SpecMatcher


class QCService:
    """
    QC 검수 통합 서비스

    Core Layer와 UI Layer 사이의 서비스 레이어
    비즈니스 로직과 데이터 처리를 담당
    """

    def __init__(self, db_schema=None):
        """
        초기화

        Args:
            db_schema: 데이터베이스 스키마 (선택)
        """
        self.db_schema = db_schema
        self.engine = InspectionEngine()
        self.checklist_provider = ChecklistProvider()

    def run_inspection(
        self,
        file_data: Dict[str, Any],
        configuration_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        QC 검수 실행

        Args:
            file_data: 파일 데이터 (ItemName → Value 또는 복합 키 매핑)
            configuration_id: Configuration ID (None이면 Type Common)

        Returns:
            Dict: 검수 결과
                {
                    'is_pass': bool,
                    'total_count': int,
                    'failed_count': int,
                    'passed_count': int,
                    'results': List[Dict],
                    'matched_count': int,
                    'exception_count': int,
                    'timestamp': str
                }
        """
        result = self.engine.inspect(file_data, configuration_id)
        result['timestamp'] = datetime.now().isoformat()
        return result

    def get_inspection_summary(self, result: Dict[str, Any]) -> str:
        """
        검수 결과 요약 문자열 생성

        Args:
            result: run_inspection() 결과

        Returns:
            str: 요약 문자열
        """
        return self.engine.get_inspection_summary(result)

    def get_active_checklist_items(self) -> List[Dict]:
        """
        활성화된 Checklist 항목 조회

        Returns:
            List[Dict]: Checklist 항목 목록
        """
        items = self.checklist_provider.get_active_items()
        return [self._checklist_item_to_dict(item) for item in items]

    def get_exception_items(self, configuration_id: Optional[int]) -> List[Dict]:
        """
        Configuration별 예외 항목 조회

        Args:
            configuration_id: Configuration ID

        Returns:
            List[Dict]: 예외 항목 목록
        """
        if not configuration_id:
            return []

        exception_ids = self.checklist_provider.get_exception_item_ids(configuration_id)
        all_items = self.checklist_provider.get_active_items()

        exception_items = [item for item in all_items if item.id in exception_ids]
        return [self._checklist_item_to_dict(item) for item in exception_items]

    def validate_single_item(self, item_dict: Dict, file_value: Any) -> bool:
        """
        단일 항목 검증 (UI에서 사용)

        Args:
            item_dict: Checklist 항목 딕셔너리
            file_value: 파일 값

        Returns:
            bool: 검증 결과
        """
        from ..core.models import ChecklistItem

        # Dict to ChecklistItem 변환
        item = ChecklistItem(
            id=item_dict.get('id', 0),
            item_name=item_dict['item_name'],
            module=item_dict.get('module'),
            part=item_dict.get('part'),
            spec_min=item_dict.get('spec_min'),
            spec_max=item_dict.get('spec_max'),
            expected_value=item_dict.get('expected_value'),
            category=item_dict.get('category'),
            description=item_dict.get('description'),
            is_active=item_dict.get('is_active', True)
        )

        return self.engine.validate_item(item, file_value)

    def _checklist_item_to_dict(self, item) -> Dict:
        """ChecklistItem을 딕셔너리로 변환"""
        return {
            'id': item.id,
            'item_name': item.item_name,
            'module': item.module,
            'part': item.part,
            'display_name': item.display_name,
            'spec_min': item.spec_min,
            'spec_max': item.spec_max,
            'expected_value': item.expected_value,
            'category': item.category,
            'description': item.description,
            'is_active': item.is_active,
            'spec_display': self.engine.get_spec_display(item)
        }

    def get_statistics(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        검수 결과 통계 생성

        Args:
            result: run_inspection() 결과

        Returns:
            Dict: 통계 정보
        """
        total = result.get('total_count', 0)
        passed = result.get('passed_count', 0)
        failed = result.get('failed_count', 0)

        # 카테고리별 통계
        category_stats = {}
        for r in result.get('results', []):
            category = r.get('category', 'Uncategorized')
            if category not in category_stats:
                category_stats[category] = {'passed': 0, 'failed': 0, 'total': 0}

            category_stats[category]['total'] += 1
            if r.get('is_valid'):
                category_stats[category]['passed'] += 1
            else:
                category_stats[category]['failed'] += 1

        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': (passed / total * 100) if total > 0 else 0,
            'matched_count': result.get('matched_count', 0),
            'exception_count': result.get('exception_count', 0),
            'by_category': category_stats,
            'is_pass': result.get('is_pass', False)
        }
