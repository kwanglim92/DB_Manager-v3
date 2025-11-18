"""
Checklist Provider - QC Checklist 항목 제공자
"""

from typing import List, Optional
from .models import ChecklistItem


class ChecklistProvider:
    """QC Checklist 항목 제공 클래스"""

    def __init__(self, db_schema=None):
        """
        초기화

        Args:
            db_schema: 데이터베이스 스키마 객체 (None이면 자동 생성)
        """
        if db_schema is None:
            from db_schema import DBSchema
            self.db_schema = DBSchema()
        else:
            self.db_schema = db_schema

    def get_active_items(self) -> List[ChecklistItem]:
        """
        활성화된 QC Checklist 항목 조회

        Returns:
            List[ChecklistItem]: 활성화된 Check list 항목 목록
        """
        with self.db_schema.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, item_name, module, part, spec_min, spec_max, expected_value,
                       category, description, is_active
                FROM QC_Checklist_Items
                WHERE is_active = 1
                ORDER BY module, part, item_name
            """)

            rows = cursor.fetchall()

            return [
                ChecklistItem(
                    id=row[0],
                    item_name=row[1],
                    module=row[2],
                    part=row[3],
                    spec_min=row[4],
                    spec_max=row[5],
                    expected_value=row[6],
                    category=row[7],
                    description=row[8],
                    is_active=bool(row[9])
                )
                for row in rows
            ]

    def get_exception_item_ids(self, configuration_id: Optional[int]) -> List[int]:
        """
        Configuration별 예외 항목 ID 목록 조회

        Args:
            configuration_id: Configuration ID (None이면 빈 목록 반환)

        Returns:
            List[int]: 예외 항목 ID 목록
        """
        if configuration_id is None:
            return []

        with self.db_schema.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT checklist_item_id
                FROM Equipment_Checklist_Exceptions
                WHERE configuration_id = ?
            """, (configuration_id,))

            rows = cursor.fetchall()
            return [row[0] for row in rows]

    def get_items_excluding_exceptions(
        self,
        configuration_id: Optional[int] = None
    ) -> List[ChecklistItem]:
        """
        예외 항목을 제외한 활성 Checklist 항목 조회

        Args:
            configuration_id: Configuration ID

        Returns:
            List[ChecklistItem]: 예외 제외한 항목 목록
        """
        all_items = self.get_active_items()
        exception_ids = self.get_exception_item_ids(configuration_id)

        return [item for item in all_items if item.id not in exception_ids]
