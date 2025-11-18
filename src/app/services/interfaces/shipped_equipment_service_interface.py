"""
Shipped Equipment Service 인터페이스 (Phase 2)

출고 장비 Raw Data 관리를 위한 추상 인터페이스를 정의합니다.
- Shipped_Equipment: 출고 장비 메타데이터
- Shipped_Equipment_Parameters: 출고 장비 파라미터 Raw Data (2000+)
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import date


@dataclass
class ShippedEquipment:
    """출고 장비 데이터 클래스"""
    id: int
    equipment_type_id: int
    configuration_id: int
    serial_number: str
    customer_name: str
    ship_date: Optional[date] = None
    is_refit: bool = False
    original_serial_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None

    # 관계 데이터 (조회 시)
    type_name: Optional[str] = None
    configuration_name: Optional[str] = None
    model_name: Optional[str] = None


@dataclass
class ShippedEquipmentParameter:
    """출고 장비 파라미터 데이터 클래스"""
    id: int
    shipped_equipment_id: int
    parameter_name: str
    parameter_value: str
    module: Optional[str] = None
    part: Optional[str] = None
    data_type: Optional[str] = None


@dataclass
class FileParseResult:
    """파일 파싱 결과 데이터 클래스"""
    serial_number: str
    customer_name: str
    model_name: str
    parameters: List[Dict[str, str]]  # [{parameter_name, parameter_value, module, part}, ...]
    total_count: int
    success: bool
    error_message: Optional[str] = None


@dataclass
class ParameterHistory:
    """파라미터 이력 데이터 클래스 (통계용)"""
    parameter_name: str
    value_count: int
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    avg_value: Optional[float] = None
    std_dev: Optional[float] = None
    values: Optional[List[Tuple[str, str, date]]] = None  # [(serial, value, ship_date), ...]


class IShippedEquipmentService(ABC):
    """출고 장비 관리 서비스 인터페이스"""

    # ==================== Shipped Equipment CRUD ====================

    @abstractmethod
    def get_all_shipped_equipment(
        self,
        configuration_id: Optional[int] = None,
        customer_name: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[ShippedEquipment]:
        """
        모든 출고 장비 조회 (필터링 지원)

        Args:
            configuration_id: Configuration ID 필터
            customer_name: 고객명 필터 (부분 일치)
            start_date: 출고일 시작 (이상)
            end_date: 출고일 종료 (이하)

        Returns:
            List[ShippedEquipment]: 출고 장비 목록
        """
        pass

    @abstractmethod
    def get_shipped_equipment_by_id(self, equipment_id: int) -> Optional[ShippedEquipment]:
        """특정 출고 장비 조회"""
        pass

    @abstractmethod
    def get_shipped_equipment_by_serial(self, serial_number: str) -> Optional[ShippedEquipment]:
        """시리얼 번호로 출고 장비 조회"""
        pass

    @abstractmethod
    def create_shipped_equipment(
        self,
        equipment_type_id: int,
        configuration_id: int,
        serial_number: str,
        customer_name: str,
        ship_date: Optional[date] = None,
        is_refit: bool = False,
        original_serial_number: Optional[str] = None,
        notes: Optional[str] = None
    ) -> int:
        """
        출고 장비 생성

        Args:
            equipment_type_id: Equipment Type ID
            configuration_id: Configuration ID
            serial_number: 시리얼 번호 (UNIQUE)
            customer_name: 고객명
            ship_date: 출고일
            is_refit: 리핏 여부
            original_serial_number: 원본 시리얼 (리핏인 경우)
            notes: 비고

        Returns:
            int: 생성된 장비 ID

        Raises:
            ValueError: 시리얼 번호 중복 또는 유효하지 않은 configuration_id
        """
        pass

    @abstractmethod
    def update_shipped_equipment(
        self,
        equipment_id: int,
        customer_name: Optional[str] = None,
        ship_date: Optional[date] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        출고 장비 정보 수정

        Args:
            equipment_id: 장비 ID
            customer_name: 고객명 (선택)
            ship_date: 출고일 (선택)
            notes: 비고 (선택)

        Returns:
            bool: 수정 성공 여부
        """
        pass

    @abstractmethod
    def delete_shipped_equipment(self, equipment_id: int) -> bool:
        """
        출고 장비 삭제 (CASCADE: 파라미터도 함께 삭제)

        Args:
            equipment_id: 장비 ID

        Returns:
            bool: 삭제 성공 여부
        """
        pass

    # ==================== Shipped Equipment Parameters ====================

    @abstractmethod
    def get_parameters_by_equipment(
        self, equipment_id: int
    ) -> List[ShippedEquipmentParameter]:
        """특정 출고 장비의 모든 파라미터 조회"""
        pass

    @abstractmethod
    def add_parameters_bulk(
        self,
        equipment_id: int,
        parameters: List[Dict[str, str]]
    ) -> int:
        """
        파라미터 일괄 추가 (2000+ 파라미터 지원)

        Args:
            equipment_id: 장비 ID
            parameters: 파라미터 목록
                [{parameter_name, parameter_value, module, part, data_type}, ...]

        Returns:
            int: 추가된 파라미터 개수

        Raises:
            ValueError: equipment_id 유효하지 않음
        """
        pass

    # ==================== File Import ====================

    @abstractmethod
    def parse_equipment_file(self, file_path: str) -> FileParseResult:
        """
        장비 데이터 파일 파싱 ({Serial}_{Customer}_{Model}.txt)

        Args:
            file_path: 파일 경로

        Returns:
            FileParseResult: 파싱 결과
                - serial_number: 시리얼 번호
                - customer_name: 고객명
                - model_name: 모델명
                - parameters: 파라미터 목록
                - total_count: 파라미터 개수
                - success: 성공 여부
                - error_message: 오류 메시지 (실패 시)
        """
        pass

    @abstractmethod
    def import_from_file(
        self,
        file_path: str,
        configuration_id: Optional[int] = None,
        auto_match: bool = True
    ) -> Tuple[bool, str, Optional[int]]:
        """
        파일에서 출고 장비 데이터 임포트

        Args:
            file_path: 파일 경로
            configuration_id: Configuration ID (수동 지정, 선택)
            auto_match: Model/Type/Configuration 자동 매칭 여부

        Returns:
            Tuple[bool, str, Optional[int]]:
                - success: 성공 여부
                - message: 결과 메시지
                - equipment_id: 생성된 장비 ID (성공 시)

        Flow:
            1. 파일 파싱 (parse_equipment_file)
            2. Configuration 자동/수동 매칭
            3. Shipped_Equipment 생성
            4. Parameters 일괄 삽입 (bulk insert)
        """
        pass

    # ==================== Parameter History & Statistics ====================

    @abstractmethod
    def get_parameter_history(
        self,
        parameter_name: str,
        configuration_id: Optional[int] = None,
        limit: int = 100
    ) -> ParameterHistory:
        """
        특정 파라미터의 출고 이력 및 통계 조회

        Args:
            parameter_name: 파라미터 이름
            configuration_id: Configuration ID 필터 (선택)
            limit: 최대 조회 개수

        Returns:
            ParameterHistory: 파라미터 이력 및 통계
                - value_count: 값 개수
                - min/max/avg/std_dev: 통계 (숫자형인 경우)
                - values: [(serial, value, ship_date), ...]
        """
        pass

    # ==================== Auto Matching ====================

    @abstractmethod
    def match_configuration(
        self,
        model_name: str,
        serial_number: Optional[str] = None
    ) -> Optional[int]:
        """
        Model 이름 및 시리얼 번호 기반 Configuration 자동 매칭

        Args:
            model_name: 모델명 (파일명에서 추출)
            serial_number: 시리얼 번호 (옵션, 추가 힌트)

        Returns:
            Optional[int]: 매칭된 Configuration ID (실패 시 None)

        Logic:
            1. model_name → Equipment_Models 조회
            2. 해당 Model의 기본 Type 조회
            3. 해당 Type의 기본 Configuration 조회 (is_customer_specific=0)
            4. 매칭 실패 시 None 반환
        """
        pass
