"""
QC 검수 모듈

QC 검수 관련 기능을 제공합니다.
"""

# Phase 1: Check list 검증
from .checklist_validator import ChecklistValidator, integrate_checklist_validation

# Phase 1.5: QC Inspection v2 (ItemName 기반 자동 매칭)
from .qc_inspection_v2 import (
    qc_inspection_v2,
    get_inspection_summary,
    get_active_checklist_items,
    get_exception_item_ids,
    validate_item,
    get_spec_display
)

# 레거시 QC 함수들 (기존 호환성 유지)
from app.qc_legacy import (
    QCValidator,
    add_qc_check_functions_to_class
)

__all__ = [
    # Phase 1
    'ChecklistValidator',
    'integrate_checklist_validation',
    # Phase 1.5
    'qc_inspection_v2',
    'get_inspection_summary',
    'get_active_checklist_items',
    'get_exception_item_ids',
    'validate_item',
    'get_spec_display',
    # 레거시
    'QCValidator',
    'add_qc_check_functions_to_class'
]
