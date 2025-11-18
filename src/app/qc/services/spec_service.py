"""
Spec Service - QC Spec 관리 서비스

기존 qc_spec_service.py를 개선하여 Services Layer로 통합
"""

from typing import Dict, List, Optional
from datetime import datetime


class SpecService:
    """QC Spec 관리 서비스"""

    def __init__(self, db_schema=None):
        """
        초기화

        Args:
            db_schema: 데이터베이스 스키마
        """
        self.db_schema = db_schema
        self.spec_cache = {}

    def get_all_checklist_items(self, is_active: bool = True) -> List[Dict]:
        """
        모든 Checklist 항목 조회

        Args:
            is_active: 활성화된 항목만 조회

        Returns:
            List[Dict]: Checklist 항목 목록
        """
        if not self.db_schema:
            return []

        query = """
        SELECT id, item_name, module, part, spec_min, spec_max,
               expected_value, category, description, is_active
        FROM Equipment_Checklist
        WHERE is_active = ?
        ORDER BY category, module, part, item_name
        """

        results = self.db_schema.execute_query(query, (1 if is_active else 0,))

        items = []
        for row in results:
            items.append({
                'id': row[0],
                'item_name': row[1],
                'module': row[2],
                'part': row[3],
                'spec_min': row[4],
                'spec_max': row[5],
                'expected_value': row[6],
                'category': row[7],
                'description': row[8],
                'is_active': bool(row[9])
            })

        return items

    def get_checklist_item_by_id(self, item_id: int) -> Optional[Dict]:
        """
        ID로 Checklist 항목 조회

        Args:
            item_id: 항목 ID

        Returns:
            Dict: Checklist 항목 또는 None
        """
        if not self.db_schema:
            return None

        query = """
        SELECT id, item_name, module, part, spec_min, spec_max,
               expected_value, category, description, is_active
        FROM Equipment_Checklist
        WHERE id = ?
        """

        result = self.db_schema.execute_query(query, (item_id,))

        if result:
            row = result[0]
            return {
                'id': row[0],
                'item_name': row[1],
                'module': row[2],
                'part': row[3],
                'spec_min': row[4],
                'spec_max': row[5],
                'expected_value': row[6],
                'category': row[7],
                'description': row[8],
                'is_active': bool(row[9])
            }

        return None

    def add_checklist_item(
        self,
        item_name: str,
        module: Optional[str] = None,
        part: Optional[str] = None,
        spec_min: Optional[str] = None,
        spec_max: Optional[str] = None,
        expected_value: Optional[str] = None,
        category: Optional[str] = None,
        description: Optional[str] = None
    ) -> bool:
        """
        Checklist 항목 추가

        Args:
            item_name: 항목명
            module: 모듈명
            part: 파트명
            spec_min: 최소 Spec
            spec_max: 최대 Spec
            expected_value: 기대값
            category: 카테고리
            description: 설명

        Returns:
            bool: 성공 여부
        """
        if not self.db_schema:
            return False

        query = """
        INSERT INTO Equipment_Checklist
        (item_name, module, part, spec_min, spec_max, expected_value,
         category, description, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
        """

        try:
            self.db_schema.execute_update(
                query,
                (item_name, module, part, spec_min, spec_max,
                 expected_value, category, description)
            )
            self.spec_cache.clear()
            return True
        except Exception as e:
            print(f"Checklist 항목 추가 오류: {e}")
            return False

    def update_checklist_item(self, item_id: int, **kwargs) -> bool:
        """
        Checklist 항목 업데이트

        Args:
            item_id: 항목 ID
            **kwargs: 업데이트할 필드

        Returns:
            bool: 성공 여부
        """
        if not self.db_schema:
            return False

        allowed_fields = [
            'item_name', 'module', 'part', 'spec_min', 'spec_max',
            'expected_value', 'category', 'description', 'is_active'
        ]

        updates = []
        values = []
        for field, value in kwargs.items():
            if field in allowed_fields:
                updates.append(f"{field} = ?")
                values.append(value)

        if not updates:
            return False

        query = f"""
        UPDATE Equipment_Checklist
        SET {', '.join(updates)}
        WHERE id = ?
        """

        values.append(item_id)

        try:
            self.db_schema.execute_update(query, values)
            self.spec_cache.clear()
            return True
        except Exception as e:
            print(f"Checklist 항목 업데이트 오류: {e}")
            return False

    def delete_checklist_item(self, item_id: int) -> bool:
        """
        Checklist 항목 삭제 (비활성화)

        Args:
            item_id: 항목 ID

        Returns:
            bool: 성공 여부
        """
        if not self.db_schema:
            return False

        query = """
        UPDATE Equipment_Checklist
        SET is_active = 0
        WHERE id = ?
        """

        try:
            self.db_schema.execute_update(query, (item_id,))
            self.spec_cache.clear()
            return True
        except Exception as e:
            print(f"Checklist 항목 삭제 오류: {e}")
            return False

    def get_exceptions(
        self,
        configuration_id: Optional[int] = None
    ) -> List[Dict]:
        """
        예외 항목 조회

        Args:
            configuration_id: Configuration ID

        Returns:
            List[Dict]: 예외 항목 목록
        """
        if not self.db_schema:
            return []

        query = """
        SELECT e.id, e.configuration_id, e.checklist_item_id,
               c.item_name, c.module, c.part, e.reason
        FROM Equipment_Checklist_Exceptions e
        JOIN Equipment_Checklist c ON e.checklist_item_id = c.id
        WHERE 1=1
        """
        params = []

        if configuration_id:
            query += " AND e.configuration_id = ?"
            params.append(configuration_id)

        results = self.db_schema.execute_query(query, params)

        exceptions = []
        for row in results:
            exceptions.append({
                'id': row[0],
                'configuration_id': row[1],
                'checklist_item_id': row[2],
                'item_name': row[3],
                'module': row[4],
                'part': row[5],
                'reason': row[6]
            })

        return exceptions

    def add_exception(
        self,
        configuration_id: int,
        checklist_item_id: int,
        reason: str = ''
    ) -> bool:
        """
        예외 항목 추가

        Args:
            configuration_id: Configuration ID
            checklist_item_id: Checklist 항목 ID
            reason: 예외 사유

        Returns:
            bool: 성공 여부
        """
        if not self.db_schema:
            return False

        query = """
        INSERT OR REPLACE INTO Equipment_Checklist_Exceptions
        (configuration_id, checklist_item_id, reason)
        VALUES (?, ?, ?)
        """

        try:
            self.db_schema.execute_update(
                query,
                (configuration_id, checklist_item_id, reason)
            )
            return True
        except Exception as e:
            print(f"예외 항목 추가 오류: {e}")
            return False

    def remove_exception(self, exception_id: int) -> bool:
        """
        예외 항목 제거

        Args:
            exception_id: 예외 ID

        Returns:
            bool: 성공 여부
        """
        if not self.db_schema:
            return False

        query = """
        DELETE FROM Equipment_Checklist_Exceptions
        WHERE id = ?
        """

        try:
            self.db_schema.execute_update(query, (exception_id,))
            return True
        except Exception as e:
            print(f"예외 항목 제거 오류: {e}")
            return False

    def get_categories(self) -> List[str]:
        """
        모든 카테고리 목록 조회

        Returns:
            List[str]: 카테고리 목록
        """
        if not self.db_schema:
            return []

        query = """
        SELECT DISTINCT category
        FROM Equipment_Checklist
        WHERE category IS NOT NULL AND is_active = 1
        ORDER BY category
        """

        results = self.db_schema.execute_query(query)
        return [row[0] for row in results if row[0]]
