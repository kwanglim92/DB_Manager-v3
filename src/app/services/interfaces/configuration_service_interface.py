"""
Configuration Service 인터페이스 (Phase 1.5)

Equipment Configurations 관리를 위한 추상 인터페이스를 정의합니다.
- Equipment_Configurations: 장비 구성 (type_id FK, Port/Wafer/Custom)
- Default DB Values: 구성별 파라미터 기준값
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class EquipmentConfiguration:
    """장비 구성 데이터 클래스"""
    id: int
    type_id: int
    configuration_name: str
    port_count: int  # CHECK (port_count > 0)
    wafer_count: int  # CHECK (wafer_count > 0)
    custom_options: Optional[Dict[str, Any]] = None
    is_customer_specific: bool = False
    customer_name: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    # 관계 데이터 (조회 시)
    type_name: Optional[str] = None
    model_name: Optional[str] = None


@dataclass
class DefaultDBValue:
    """Default DB 파라미터 데이터 클래스 (Phase 1.5)"""
    id: int
    configuration_id: int
    parameter_name: str
    default_value: str
    is_type_common: bool = False
    notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    # 관계 데이터 (조회 시)
    configuration_name: Optional[str] = None
    type_name: Optional[str] = None
    model_name: Optional[str] = None


class IConfigurationService(ABC):
    """Configuration 관리 서비스 인터페이스"""

    # ==================== Equipment Configurations ====================

    @abstractmethod
    def get_all_configurations(self) -> List[EquipmentConfiguration]:
        """모든 장비 구성 조회 (관계 데이터 포함)"""
        pass

    @abstractmethod
    def get_configurations_by_type(self, type_id: int) -> List[EquipmentConfiguration]:
        """특정 Equipment Type의 모든 Configurations 조회"""
        pass

    @abstractmethod
    def get_configuration_by_id(self, config_id: int) -> Optional[EquipmentConfiguration]:
        """특정 Configuration 조회"""
        pass

    @abstractmethod
    def get_configuration_by_name(
        self,
        type_id: int,
        configuration_name: str
    ) -> Optional[EquipmentConfiguration]:
        """Type + Configuration 이름으로 조회"""
        pass

    @abstractmethod
    def create_configuration(
        self,
        type_id: int,
        configuration_name: str,
        port_count: int,
        wafer_count: int,
        custom_options: Optional[Dict[str, Any]] = None,
        is_customer_specific: bool = False,
        customer_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> int:
        """
        새 장비 구성 생성

        Args:
            type_id: Equipment Type ID
            configuration_name: 구성 이름 (예: "2P4W", "4P8W", "Custom A")
            port_count: Port 수 (> 0)
            wafer_count: Wafer 수 (> 0)
            custom_options: 커스텀 옵션 (JSON)
            is_customer_specific: 고객 특화 여부
            customer_name: 고객명 (특화 시)
            description: 설명

        Returns:
            생성된 Configuration ID

        Raises:
            ValueError: port_count 또는 wafer_count가 0 이하
            ValueError: Unique 제약 위반 (type_id, configuration_name)
        """
        pass

    @abstractmethod
    def update_configuration(
        self,
        config_id: int,
        configuration_name: Optional[str] = None,
        port_count: Optional[int] = None,
        wafer_count: Optional[int] = None,
        custom_options: Optional[Dict[str, Any]] = None,
        is_customer_specific: Optional[bool] = None,
        customer_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> bool:
        """
        장비 구성 정보 수정

        Raises:
            ValueError: port_count 또는 wafer_count가 0 이하
        """
        pass

    @abstractmethod
    def delete_configuration(self, config_id: int) -> bool:
        """
        장비 구성 삭제 (CASCADE: 관련 Default_DB_Values 삭제)

        주의: Configuration 삭제 시 연결된 모든 Default DB Values도 삭제됨
        """
        pass

    # ==================== Custom Options Management ====================

    @abstractmethod
    def update_custom_options(
        self,
        config_id: int,
        custom_options: Dict[str, Any]
    ) -> bool:
        """
        커스텀 옵션 JSON 업데이트

        Args:
            config_id: Configuration ID
            custom_options: 커스텀 옵션 딕셔너리
                예: {
                    "has_loadport": true,
                    "chamber_type": "single",
                    "special_features": ["auto_calibration", "remote_monitoring"]
                }
        """
        pass

    @abstractmethod
    def get_custom_options(self, config_id: int) -> Optional[Dict[str, Any]]:
        """커스텀 옵션 조회"""
        pass

    # ==================== Customer-Specific Configurations ====================

    @abstractmethod
    def get_customer_configurations(self, customer_name: str) -> List[EquipmentConfiguration]:
        """특정 고객의 모든 특화 구성 조회"""
        pass

    @abstractmethod
    def get_all_customers(self) -> List[str]:
        """고객 특화 구성이 있는 모든 고객 목록"""
        pass

    # ==================== Default DB Values ====================

    @abstractmethod
    def get_default_values_by_configuration(
        self,
        config_id: int,
        include_type_common: bool = True
    ) -> List[DefaultDBValue]:
        """
        특정 Configuration의 모든 Default DB Values 조회

        Args:
            config_id: Configuration ID
            include_type_common: Type 공통 파라미터 포함 여부 (기본: True)

        Returns:
            Configuration-specific + (선택적) Type-common 파라미터 목록
        """
        pass

    @abstractmethod
    def get_default_value_by_name(
        self,
        config_id: int,
        parameter_name: str
    ) -> Optional[DefaultDBValue]:
        """특정 파라미터의 Default DB Value 조회"""
        pass

    @abstractmethod
    def create_default_value(
        self,
        configuration_id: int,
        parameter_name: str,
        default_value: str,
        is_type_common: bool = False,
        notes: Optional[str] = None
    ) -> int:
        """
        새 Default DB Value 생성

        Args:
            configuration_id: Configuration ID
            parameter_name: 파라미터 이름
            default_value: 기준값
            is_type_common: Type 공통 파라미터 여부
            notes: 비고

        Returns:
            생성된 Default DB Value ID

        Raises:
            ValueError: Unique 제약 위반 (configuration_id, parameter_name)
        """
        pass

    @abstractmethod
    def update_default_value(
        self,
        value_id: int,
        default_value: Optional[str] = None,
        is_type_common: Optional[bool] = None,
        notes: Optional[str] = None
    ) -> bool:
        """Default DB Value 정보 수정"""
        pass

    @abstractmethod
    def delete_default_value(self, value_id: int) -> bool:
        """Default DB Value 삭제"""
        pass

    @abstractmethod
    def bulk_create_default_values(
        self,
        configuration_id: int,
        values: List[Dict[str, Any]]
    ) -> int:
        """
        Default DB Values 대량 생성

        Args:
            configuration_id: Configuration ID
            values: 파라미터 목록
                예: [
                    {"parameter_name": "Temp_Setpoint", "default_value": "25.0", "is_type_common": False},
                    {"parameter_name": "Pressure_Max", "default_value": "100", "is_type_common": True}
                ]

        Returns:
            생성된 레코드 수
        """
        pass

    # ==================== Hierarchy Operations ====================

    @abstractmethod
    def get_configuration_hierarchy(self, type_id: int) -> Dict[str, Any]:
        """
        특정 Type의 Configuration 계층 구조 조회

        Returns:
            {
                'type': EquipmentTypeV2,
                'configurations': [
                    {
                        'configuration': EquipmentConfiguration,
                        'default_value_count': int,
                        'type_common_count': int,
                        'config_specific_count': int
                    },
                    ...
                ]
            }
        """
        pass

    @abstractmethod
    def get_full_hierarchy(self) -> List[Dict[str, Any]]:
        """
        전체 Equipment Hierarchy 조회 (Model → Type → Configuration)

        Returns:
            [
                {
                    'model': EquipmentModel,
                    'types': [
                        {
                            'type': EquipmentTypeV2,
                            'configurations': [
                                {
                                    'configuration': EquipmentConfiguration,
                                    'default_value_count': int
                                },
                                ...
                            ]
                        },
                        ...
                    ]
                },
                ...
            ]
        """
        pass

    # ==================== Validation ====================

    @abstractmethod
    def validate_port_wafer_counts(self, port_count: int, wafer_count: int) -> bool:
        """
        Port/Wafer 수 유효성 검사 (> 0)

        Raises:
            ValueError: 값이 0 이하인 경우
        """
        pass

    @abstractmethod
    def validate_configuration_name(self, type_id: int, configuration_name: str) -> bool:
        """
        Configuration 이름 유효성 검사 (Unique 제약)

        Returns:
            True: 사용 가능, False: 이미 존재
        """
        pass

    @abstractmethod
    def validate_parameter_name(self, config_id: int, parameter_name: str) -> bool:
        """
        파라미터 이름 유효성 검사 (Unique 제약)

        Returns:
            True: 사용 가능, False: 이미 존재
        """
        pass

    # ==================== Search ====================

    @abstractmethod
    def search_configurations(self, query: str) -> List[EquipmentConfiguration]:
        """Configuration 검색 (이름, 고객명, 설명)"""
        pass

    @abstractmethod
    def search_default_values(self, query: str) -> List[DefaultDBValue]:
        """Default DB Value 검색 (파라미터 이름, 값, 비고)"""
        pass
