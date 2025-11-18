"""
QC Inspection v2 - Module.Part.ItemName 복합 키 기반 자동 매칭 검수 시스템

Phase 2 구현:
- Module.Part.ItemName 복합 키 기반 자동 매칭
- Equipment_Checklist_Exceptions 적용
- Pass/Fail 판정 (심각도 없음, 모든 항목 동일 중요도)

⚠️ 레거시 호환성 모듈:
이 모듈은 하위 호환성을 위해 유지됩니다.
새로운 코드는 qc.core.InspectionEngine을 직접 사용하세요.

Author: Phase 2
Date: 2025-11-18
Updated: 2025-11-18 (리팩토링 - Core Layer 사용)
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# ✅ 새로운 Core Layer 사용
from .core import (
    ChecklistItem,
    InspectionResult,
    InspectionEngine,
    ChecklistProvider,
    SpecMatcher
)


# 레거시 함수 - Core Layer로 위임

def get_active_checklist_items() -> List[ChecklistItem]:
    """
    활성화된 QC Checklist 항목 조회 (레거시 함수)

    ⚠️ Deprecated: 대신 ChecklistProvider.get_active_items() 사용

    Returns:
        List[ChecklistItem]: 활성화된 Check list 항목 목록
    """
    provider = ChecklistProvider()
    return provider.get_active_items()


def get_exception_item_ids(configuration_id: Optional[int]) -> List[int]:
    """
    Configuration별 예외 항목 ID 목록 조회 (레거시 함수)

    ⚠️ Deprecated: 대신 ChecklistProvider.get_exception_item_ids() 사용

    Args:
        configuration_id: Configuration ID (None이면 빈 목록 반환)

    Returns:
        List[int]: 예외 항목 ID 목록
    """
    provider = ChecklistProvider()
    return provider.get_exception_item_ids(configuration_id)


def validate_item(item: ChecklistItem, file_value: Any) -> bool:
    """
    단일 Check list 항목 검증 (레거시 함수)

    ⚠️ Deprecated: 대신 InspectionEngine.validate_item() 사용

    Args:
        item: Check list 항목
        file_value: 파일의 실제 값

    Returns:
        bool: 검증 성공 여부
    """
    return InspectionEngine.validate_item(item, file_value)


def get_spec_display(item: ChecklistItem) -> str:
    """
    Spec 표시 문자열 생성 (레거시 함수)

    ⚠️ Deprecated: 대신 InspectionEngine.get_spec_display() 사용

    Args:
        item: Check list 항목

    Returns:
        str: Spec 표시 문자열 ("0.5 ~ 2.0", "Pass", "N/A" 등)
    """
    return InspectionEngine.get_spec_display(item)


def qc_inspection_v2(file_data: Dict[str, Any], configuration_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Module.Part.ItemName 복합 키 기반 자동 매칭 QC 검수 (Phase 2)

    ⚠️ Deprecated: 대신 InspectionEngine.inspect() 사용

    특징:
    - Module.Part.ItemName 복합 키 기반 자동 매칭
    - 레거시 호환성: ItemName만으로도 매칭 가능 (module, part가 NULL인 Type Common 항목)
    - Equipment_Checklist_Exceptions 적용
    - Pass/Fail 판정 (심각도 없음, 모든 항목 동일 중요도)

    Args:
        file_data: 파일 데이터
            - 옵션 1: ItemName → Value 매핑 (레거시)
            - 옵션 2: (Module, Part, ItemName) → Value 매핑 (신규)
        configuration_id: Configuration ID (None이면 Type Common)

    Returns:
        Dict[str, Any]: 검수 결과
            {
                'is_pass': bool,           # 전체 합격 여부 (모든 항목 Pass)
                'total_count': int,        # 검증된 항목 수
                'failed_count': int,       # 실패한 항목 수
                'passed_count': int,       # 합격한 항목 수
                'results': List[Dict]      # 각 항목 검증 결과
                'matched_count': int,      # 매칭된 항목 수
                'exception_count': int     # 예외 처리된 항목 수
            }
    """
    # ✅ Core Layer로 위임
    engine = InspectionEngine()
    return engine.inspect(file_data, configuration_id)


def get_inspection_summary(result: Dict[str, Any]) -> str:
    """
    검수 결과 요약 문자열 생성 (레거시 함수)

    ⚠️ Deprecated: 대신 InspectionEngine.get_inspection_summary() 사용

    Args:
        result: qc_inspection_v2() 결과

    Returns:
        str: 요약 문자열
    """
    # ✅ Core Layer로 위임
    engine = InspectionEngine()
    return engine.get_inspection_summary(result)


# 레거시 호환성을 위한 Alias (향후 제거 예정)
def perform_qc_inspection_v2(file_data: Dict[str, Any], configuration_id: Optional[int] = None) -> Dict[str, Any]:
    """
    qc_inspection_v2() 별칭 (레거시 호환성)

    ⚠️ Deprecated: qc_inspection_v2() 또는 InspectionEngine.inspect() 사용
    """
    return qc_inspection_v2(file_data, configuration_id)


# 모듈 레벨 엔진 인스턴스 (레거시 호환성)
_engine = None


def get_engine() -> InspectionEngine:
    """
    공유 InspectionEngine 인스턴스 반환

    Returns:
        InspectionEngine: 검수 엔진 인스턴스
    """
    global _engine
    if _engine is None:
        _engine = InspectionEngine()
    return _engine
