"""
QC Package - Quality Control System

리팩토링된 QC 시스템 (Phase 2)

아키텍처:
    qc/
    ├── core/           # 핵심 비즈니스 로직
    ├── services/       # 서비스 레이어
    ├── ui/             # UI 레이어
    └── utils/          # 유틸리티

사용 예제:
    # Services Layer 사용 (권장)
    from app.qc.services import QCService, ReportService

    qc_service = QCService(db_schema)
    result = qc_service.run_inspection(file_data, configuration_id)

    # Core Layer 직접 사용
    from app.qc.core import InspectionEngine

    engine = InspectionEngine()
    result = engine.inspect(file_data, configuration_id)
"""

# Core Layer
from .core import (
    ChecklistItem,
    InspectionResult,
    InspectionEngine,
    ChecklistProvider,
    SpecMatcher
)

# Services Layer (권장)
from .services import (
    QCService,
    SpecService,
    ReportService,
    ConfigService
)

# Utils
from .utils import (
    DataProcessor,
    FileHandler
)

# Phase 1: Check list 검증 (레거시 호환성)
from .checklist_validator import ChecklistValidator, integrate_checklist_validation

# Phase 1.5: QC Inspection v2 (레거시 호환성)
from .qc_inspection_v2 import (
    qc_inspection_v2,
    get_inspection_summary,
    get_active_checklist_items,
    get_exception_item_ids,
    validate_item,
    get_spec_display,
    get_engine
)

# 레거시 QC 함수들 (기존 호환성 유지)
from app.qc_legacy import (
    QCValidator,
    add_qc_check_functions_to_class
)

__all__ = [
    # Core Layer
    'ChecklistItem',
    'InspectionResult',
    'InspectionEngine',
    'ChecklistProvider',
    'SpecMatcher',

    # Services Layer (권장)
    'QCService',
    'SpecService',
    'ReportService',
    'ConfigService',

    # Utils
    'DataProcessor',
    'FileHandler',

    # Phase 1 (레거시)
    'ChecklistValidator',
    'integrate_checklist_validation',

    # Phase 1.5 (레거시)
    'qc_inspection_v2',
    'get_inspection_summary',
    'get_active_checklist_items',
    'get_exception_item_ids',
    'validate_item',
    'get_spec_display',
    'get_engine',

    # 레거시
    'QCValidator',
    'add_qc_check_functions_to_class'
]

__version__ = '2.0.0'
