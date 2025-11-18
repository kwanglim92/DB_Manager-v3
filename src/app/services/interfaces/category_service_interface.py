"""
Category Service 인터페이스 (Phase 1.5)

Equipment Models 및 Equipment Types 관리를 위한 추상 인터페이스를 정의합니다.
- Equipment_Models: 장비 모델명 (최상위 계층)
- Equipment_Types: AE 형태 (model_id FK)
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class EquipmentModel:
    """장비 모델 데이터 클래스"""
    id: int
    model_name: str
    model_code: Optional[str] = None
    description: Optional[str] = None
    display_order: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class EquipmentTypeV2:
    """
    장비 유형 데이터 클래스 (Phase 1.5 수정 버전)

    주요 변경사항:
    - model_id FK 추가
    - type_name 의미 변경: 장비 모델명 → AE 형태 ("분리형"/"일체형")
    """
    id: int
    model_id: int
    type_name: str  # "분리형" 또는 "일체형"
    description: Optional[str] = None
    is_default: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    # 관계 데이터 (조회 시)
    model_name: Optional[str] = None


class ICategoryService(ABC):
    """Category 관리 서비스 인터페이스 (Equipment Models + Types)"""

    # ==================== Equipment Models ====================

    @abstractmethod
    def get_all_models(self) -> List[EquipmentModel]:
        """모든 장비 모델 조회 (display_order 순)"""
        pass

    @abstractmethod
    def get_model_by_id(self, model_id: int) -> Optional[EquipmentModel]:
        """특정 장비 모델 조회"""
        pass

    @abstractmethod
    def get_model_by_name(self, model_name: str) -> Optional[EquipmentModel]:
        """모델명으로 조회"""
        pass

    @abstractmethod
    def create_model(
        self,
        model_name: str,
        model_code: Optional[str] = None,
        description: Optional[str] = None,
        display_order: Optional[int] = None
    ) -> int:
        """
        새 장비 모델 생성

        Args:
            model_name: 모델명 (예: "NX-Hybrid WLI")
            model_code: 모델 코드 (예: "NX-H-WLI")
            description: 설명
            display_order: 정렬 순서 (None이면 자동 할당)

        Returns:
            생성된 모델 ID
        """
        pass

    @abstractmethod
    def update_model(
        self,
        model_id: int,
        model_name: Optional[str] = None,
        model_code: Optional[str] = None,
        description: Optional[str] = None,
        display_order: Optional[int] = None
    ) -> bool:
        """장비 모델 정보 수정"""
        pass

    @abstractmethod
    def delete_model(self, model_id: int) -> bool:
        """
        장비 모델 삭제 (CASCADE: 관련 Equipment_Types도 삭제)

        주의: 모델 삭제 시 연결된 모든 Types와 그 하위 데이터도 삭제됨
        """
        pass

    @abstractmethod
    def reorder_models(self, model_id_order: List[int]) -> bool:
        """
        모델 정렬 순서 변경

        Args:
            model_id_order: 모델 ID 리스트 (원하는 순서대로)
        """
        pass

    # ==================== Equipment Types ====================

    @abstractmethod
    def get_types_by_model(self, model_id: int) -> List[EquipmentTypeV2]:
        """특정 모델의 모든 Types 조회"""
        pass

    @abstractmethod
    def get_all_types(self) -> List[EquipmentTypeV2]:
        """모든 Equipment Types 조회 (모델 정보 포함)"""
        pass

    @abstractmethod
    def get_type_by_id(self, type_id: int) -> Optional[EquipmentTypeV2]:
        """특정 Equipment Type 조회"""
        pass

    @abstractmethod
    def create_type(
        self,
        model_id: int,
        type_name: str,
        description: Optional[str] = None,
        is_default: bool = False
    ) -> int:
        """
        새 Equipment Type 생성

        Args:
            model_id: 장비 모델 ID
            type_name: AE 형태 ("분리형" 또는 "일체형")
            description: 설명
            is_default: 기본 타입 여부

        Returns:
            생성된 Type ID
        """
        pass

    @abstractmethod
    def update_type(
        self,
        type_id: int,
        type_name: Optional[str] = None,
        description: Optional[str] = None,
        is_default: Optional[bool] = None
    ) -> bool:
        """Equipment Type 정보 수정"""
        pass

    @abstractmethod
    def delete_type(self, type_id: int) -> bool:
        """
        Equipment Type 삭제 (CASCADE: 관련 Configurations 삭제)

        주의: Type 삭제 시 연결된 모든 Configurations와 그 하위 데이터도 삭제됨
        """
        pass

    # ==================== Hierarchy Operations ====================

    @abstractmethod
    def get_hierarchy_tree(self) -> List[Dict[str, Any]]:
        """
        전체 Equipment Hierarchy Tree 조회

        Returns:
            [
                {
                    'model': EquipmentModel,
                    'types': [
                        {
                            'type': EquipmentTypeV2,
                            'configuration_count': int
                        },
                        ...
                    ]
                },
                ...
            ]
        """
        pass

    @abstractmethod
    def validate_model_type_combination(self, model_id: int, type_name: str) -> bool:
        """
        Model + Type 조합 유효성 검사

        Unique 제약: (model_id, type_name)
        """
        pass

    @abstractmethod
    def search_models(self, query: str) -> List[EquipmentModel]:
        """모델명, 코드로 검색"""
        pass

    @abstractmethod
    def search_types(self, query: str) -> List[EquipmentTypeV2]:
        """Type 검색 (모델 정보 포함)"""
        pass
