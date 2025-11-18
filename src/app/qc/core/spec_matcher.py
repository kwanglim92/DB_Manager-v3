"""
Spec Matcher - Module.Part.ItemName 복합 키 기반 매칭
"""

from typing import Dict, List, Tuple, Any, Optional
from .models import ChecklistItem


class SpecMatcher:
    """Module.Part.ItemName 복합 키 기반 파라미터 매칭 클래스"""

    @staticmethod
    def parse_file_data(file_data: Dict[str, Any]) -> Dict[Tuple, Any]:
        """
        파일 데이터를 복합 키 형식으로 파싱

        Args:
            file_data: 파일 데이터
                - 옵션 1: ItemName → Value 매핑 (레거시)
                - 옵션 2: (Module, Part, ItemName) → Value 매핑 (신규)

        Returns:
            Dict[Tuple, Any]: (Module, Part, ItemName) → Value 매핑
        """
        parsed = {}

        for key, value in file_data.items():
            if isinstance(key, tuple) and len(key) == 3:
                # (Module, Part, ItemName) 복합 키 (신규)
                parsed[key] = value
            else:
                # ItemName 단순 키 (레거시)
                # None, None, ItemName 형태로 변환
                composite_key = (None, None, str(key))
                parsed[composite_key] = value

        return parsed

    @staticmethod
    def match_items(
        checklist_items: List[ChecklistItem],
        file_data_parsed: Dict[Tuple, Any]
    ) -> List[Tuple[ChecklistItem, Tuple, Any]]:
        """
        Checklist 항목과 파일 데이터 매칭

        매칭 우선순위:
        1. 정확한 복합 키 매칭 (Module.Part.ItemName)
        2. Type Common 매칭 (module, part가 NULL인 경우 ItemName만 매칭)

        Args:
            checklist_items: Checklist 항목 목록
            file_data_parsed: 파싱된 파일 데이터

        Returns:
            List[Tuple[ChecklistItem, Tuple, Any]]: (항목, 파일키, 값) 튜플 목록
        """
        matched = []

        for item in checklist_items:
            item_key = item.composite_key

            # 우선순위 1: 정확한 복합 키 매칭
            if item_key in file_data_parsed:
                matched.append((item, item_key, file_data_parsed[item_key]))
                continue

            # 우선순위 2: module, part가 NULL이면 ItemName만 매칭 (Type Common)
            if item.module is None and item.part is None:
                for file_key, file_value in file_data_parsed.items():
                    if file_key[2] == item.item_name:  # ItemName만 비교
                        matched.append((item, file_key, file_value))
                        break

        return matched

    @classmethod
    def match(
        cls,
        checklist_items: List[ChecklistItem],
        file_data: Dict[str, Any]
    ) -> List[Tuple[ChecklistItem, Tuple, Any]]:
        """
        Checklist 항목과 파일 데이터 매칭 (All-in-One)

        Args:
            checklist_items: Checklist 항목 목록
            file_data: 원본 파일 데이터

        Returns:
            List[Tuple[ChecklistItem, Tuple, Any]]: (항목, 파일키, 값) 튜플 목록
        """
        file_data_parsed = cls.parse_file_data(file_data)
        return cls.match_items(checklist_items, file_data_parsed)
