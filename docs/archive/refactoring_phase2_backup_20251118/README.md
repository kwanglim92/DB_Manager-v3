# QC 시스템 리팩토링 Phase 2 - 레거시 파일 백업

**날짜**: 2025-11-18
**작업**: Phase 2-4 리팩토링 완료 후 레거시 파일 정리

---

## 백업된 파일

이 디렉토리에는 Phase 2 리팩토링으로 대체된 레거시 QC 파일들이 백업되어 있습니다.

### 제거 예정 파일 (현재 보관)

| 레거시 파일 | 대체 파일/서비스 | 상태 |
|------------|----------------|------|
| `qc_custom_config.py` | `qc/services/config_service.py` | ⚠️ 보관 (나중에 제거 가능) |
| `qc_reports.py` | `qc/services/report_service.py` | ⚠️ 보관 (나중에 제거 가능) |
| `qc_utils.py` | `qc/utils/data_processor.py`, `qc/utils/file_handler.py` | ⚠️ 보관 (나중에 제거 가능) |
| `qc_integration.py` | `qc/ui/qc_inspection_tab.py` (통합 예정) | ⚠️ 보관 (UI 통합 후 제거) |
| `qc_simplified.py` | `qc/ui/qc_inspection_tab.py` (통합 예정) | ⚠️ 보관 (UI 통합 후 제거) |
| `qc_simplified_custom.py` | `qc/ui/qc_inspection_tab.py` (통합 예정) | ⚠️ 보관 (UI 통합 후 제거) |
| `unified_qc_system.py` | 사용하지 않음 | ✅ 안전하게 제거 가능 |

### 유지 중인 파일 (레거시 호환성)

| 파일 | 사용처 | 이유 |
|-----|--------|------|
| `qc_legacy.py` | `app/qc/__init__.py` | 레거시 호환성 유지 |
| `simplified_qc_system.py` | `app/manager.py` | 아직 사용 중 (나중에 마이그레이션 필요) |

---

## 새로운 아키텍처

Phase 2 리팩토링 후 구조:

```
src/app/qc/
├── core/               # 핵심 비즈니스 로직
│   ├── inspection_engine.py
│   ├── spec_matcher.py
│   ├── checklist_provider.py
│   └── models.py
│
├── services/           # 서비스 레이어 (NEW)
│   ├── qc_service.py          # 통합 검수 서비스
│   ├── spec_service.py        # Spec 관리
│   ├── report_service.py      # 보고서 생성
│   └── config_service.py      # 설정 관리
│
├── ui/                 # UI 레이어 (NEW)
│   ├── qc_inspection_tab.py   # 통합 검수 탭
│   └── widgets/
│       ├── result_table.py
│       └── summary_panel.py
│
└── utils/              # 유틸리티 (NEW)
    ├── data_processor.py
    └── file_handler.py
```

---

## 마이그레이션 가이드

### 1. QCService 사용 (권장)

**기존 코드:**
```python
from app.qc_simplified import perform_qc_check
result = perform_qc_check(file_data)
```

**새 코드:**
```python
from app.qc.services import QCService, ReportService

qc_service = QCService(db_schema)
result = qc_service.run_inspection(file_data, configuration_id)

# 보고서 생성
report_service = ReportService()
report_service.export_to_excel(result, 'output.xlsx')
```

### 2. ConfigService 사용

**기존 코드:**
```python
from app.qc_custom_config import CustomQCConfig
config = CustomQCConfig()
```

**새 코드:**
```python
from app.qc.services import ConfigService

config_service = ConfigService()
equipment_types = config_service.get_equipment_types()
```

### 3. 데이터 처리 유틸리티

**기존 코드:**
```python
from app.qc_utils import QCDataProcessor
processor = QCDataProcessor()
```

**새 코드:**
```python
from app.qc.utils import DataProcessor, FileHandler

# 데이터 처리
df, error = DataProcessor.create_safe_dataframe(data, columns)

# 파일 처리
parameters, error = FileHandler.load_and_parse(file_path)
```

---

## 제거 계획

1. **즉시 제거 가능**: `unified_qc_system.py` (사용하지 않음)
2. **Phase 5 후 제거**: `qc_custom_config.py`, `qc_reports.py`, `qc_utils.py`
3. **UI 통합 후 제거**: `qc_integration.py`, `qc_simplified.py`, `qc_simplified_custom.py`
4. **최종 마이그레이션 후 제거**: `simplified_qc_system.py`

---

**백업 담당자**: Claude Code
**리팩토링 계획서**: `/docs/REFACTORING_PLAN.md`
