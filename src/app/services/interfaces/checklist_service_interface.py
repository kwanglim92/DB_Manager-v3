"""
Check list 관리 서비스 인터페이스
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple

class IChecklistService(ABC):
    """Check list 관리 서비스 인터페이스"""

    @abstractmethod
    def add_checklist_item(self, item_name: str, parameter_pattern: str,
                          is_common: bool = True, severity_level: str = 'MEDIUM',
                          validation_rule: Optional[str] = None,
                          description: str = "") -> Optional[int]:
        """
        새 Check list 항목 추가

        Args:
            item_name: 항목 이름
            parameter_pattern: 파라미터 패턴 (정규식)
            is_common: 공통 항목 여부
            severity_level: 심각도 (CRITICAL/HIGH/MEDIUM/LOW)
            validation_rule: 검증 규칙 (JSON)
            description: 설명

        Returns:
            생성된 항목 ID 또는 None
        """
        pass

    @abstractmethod
    def get_common_checklist_items(self) -> List[Tuple]:
        """
        공통 Check list 항목 조회

        Returns:
            (id, item_name, parameter_pattern, is_common, severity_level,
             validation_rule, description) 튜플 리스트
        """
        pass

    @abstractmethod
    def get_equipment_checklist(self, equipment_type_id: int) -> List[Dict]:
        """
        장비별 적용되는 Check list 조회 (공통 + 장비 특화)

        Args:
            equipment_type_id: 장비 유형 ID

        Returns:
            Check list 항목 딕셔너리 리스트
        """
        pass

    @abstractmethod
    def add_equipment_specific_checklist(self, equipment_type_id: int,
                                        checklist_item_id: int,
                                        is_required: bool = True,
                                        custom_validation_rule: Optional[str] = None,
                                        priority: int = 100,
                                        added_reason: str = "",
                                        added_by: str = "") -> Optional[int]:
        """
        장비별 Check list 항목 추가

        Args:
            equipment_type_id: 장비 유형 ID
            checklist_item_id: Check list 항목 ID
            is_required: 필수 여부
            custom_validation_rule: 커스텀 검증 규칙
            priority: 우선순위
            added_reason: 추가 이유
            added_by: 추가한 사용자

        Returns:
            생성된 매핑 ID 또는 None
        """
        pass

    @abstractmethod
    def add_checklist_exception(self, equipment_type_id: int,
                               checklist_item_id: int,
                               reason: str,
                               approved_by: str = "") -> Optional[int]:
        """
        장비별 Check list 예외 추가 (특정 공통 항목 제외)

        Args:
            equipment_type_id: 장비 유형 ID
            checklist_item_id: Check list 항목 ID
            reason: 예외 사유
            approved_by: 승인자

        Returns:
            생성된 예외 ID 또는 None
        """
        pass

    @abstractmethod
    def get_audit_log(self, limit: int = 100) -> List[Tuple]:
        """
        Check list 변경 이력 조회

        Args:
            limit: 최대 조회 건수

        Returns:
            (id, action, target_table, target_id, old_value, new_value,
             reason, user, timestamp) 튜플 리스트
        """
        pass

    @abstractmethod
    def validate_parameter_against_checklist(self, equipment_type_id: int,
                                            parameter_name: str,
                                            parameter_value: str) -> Dict:
        """
        파라미터가 Check list에 포함되는지 검증

        Args:
            equipment_type_id: 장비 유형 ID
            parameter_name: 파라미터 이름
            parameter_value: 파라미터 값

        Returns:
            {
                'is_checklist': bool,
                'severity_level': str,
                'validation_passed': bool,
                'message': str
            }
        """
        pass
