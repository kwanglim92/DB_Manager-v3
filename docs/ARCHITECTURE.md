# DB Manager v3 - Architecture Documentation

## 개요

DB Manager v3는 장비 생산 데이터 비교 및 QC 검수를 위한 Tkinter 기반 데스크톱 애플리케이션입니다.

**최종 업데이트:** 2025-11-19

---

## 시스템 아키텍처

### 전체 구조

```
DB_Manager-v3/
├── src/
│   ├── main.py                    # 애플리케이션 진입점
│   └── app/
│       ├── manager.py             # 메인 GUI 관리 (DBManager 클래스)
│       ├── schema.py              # 데이터베이스 스키마
│       ├── qc/                    # QC 시스템 (리팩토링됨)
│       │   ├── core/             # 핵심 비즈니스 로직
│       │   ├── services/         # 서비스 레이어
│       │   ├── ui/               # PyQt6 UI 컴포넌트 (미사용)
│       │   └── utils/            # 유틸리티
│       ├── ui/                    # Tkinter UI 컨트롤러
│       │   └── controllers/
│       │       └── tab_controllers/
│       │           └── qc_tab_controller.py  # QC 탭 컨트롤러
│       ├── dialogs/               # 다이얼로그
│       ├── services/              # 서비스 레이어
│       └── utils/                 # 유틸리티
├── config/                        # 설정 파일
├── data/                          # 데이터 파일
└── docs/                          # 문서

```

---

## 핵심 컴포넌트

### 1. QC System (품질 검수 시스템)

#### 아키텍처 (3-Layer)

```
┌─────────────────────────────────────────┐
│         UI Layer (Tkinter)              │
│   src/app/ui/controllers/               │
│   └── tab_controllers/                  │
│       └── qc_tab_controller.py         │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│         Services Layer                  │
│   src/app/qc/services/                  │
│   ├── qc_service.py                    │
│   ├── spec_service.py                  │
│   ├── report_service.py                │
│   └── config_service.py                │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│         Core Layer                      │
│   src/app/qc/core/                      │
│   ├── inspection_engine.py             │
│   ├── checklist_provider.py            │
│   ├── spec_matcher.py                  │
│   └── models.py                        │
└─────────────────────────────────────────┘
```

#### 핵심 클래스

**UI Layer:**
- `QCTabController`: QC 검수 탭 UI 관리
  - 파일 선택 및 검수 실행
  - 결과 표시 (Treeview)
  - 필터링 (Module/Part/Result)
  - 보고서 생성 및 Excel 내보내기

**Services Layer:**
- `QCService`: QC 검수 통합 서비스
- `ReportService`: 보고서 생성
- `SpecService`: Spec 관리
- `ConfigService`: 설정 관리

**Core Layer:**
- `InspectionEngine`: 검수 엔진
- `ChecklistProvider`: Checklist 제공
- `SpecMatcher`: Spec 매칭
- `ChecklistItem`, `InspectionResult`: 데이터 모델

#### 검수 플로우

```
1. 파일 선택
   ↓
2. FileHandler.load_files()  → 파일 로드 및 파싱
   ↓
3. QCService.run_inspection() → 검수 실행
   ↓
4. InspectionEngine.inspect()  → 실제 검수 로직
   ↓
5. 결과 표시 (Pass/Fail)
   ↓
6. 보고서 생성 (선택)
```

---

### 2. Default DB System (기본값 관리)

- DB 스키마 기반 파라미터 관리
- Equipment Type별 기본값 설정
- Min/Max Spec 관리

**위치:** `src/app/services/default_db_service.py`

---

### 3. Data Comparison System (데이터 비교)

- 여러 파일 간 파라미터 값 비교
- 차이점 분석
- Grid/Table 뷰

**위치:** `src/app/comparison.py`

---

## 데이터베이스

### SQLite Schema

**주요 테이블:**

1. `equipment_types` - 장비 유형
2. `configurations` - 장비 설정
3. `default_parameters` - 기본 파라미터
4. `check_list` - QC 체크리스트
5. `configuration_exceptions` - 예외 항목

**위치:** `data/default_db.sqlite`

---

## 설정 파일

### QC Custom Config

QC Spec Management용 사용자 정의 설정

**위치:** `config/qc_custom_config.json`

**구조:**
```json
{
  "equipment_types": {
    "Type1": {
      "specs": [
        {
          "item_name": "...",
          "min_spec": "...",
          "max_spec": "...",
          "module": "...",
          "part": "..."
        }
      ]
    }
  }
}
```

---

## 의존성

### 필수 라이브러리

- **tkinter**: GUI 프레임워크
- **pandas**: 데이터 처리
- **sqlite3**: 데이터베이스
- **openpyxl**: Excel 파일 처리
- **matplotlib**: 차트/그래프

### 선택적 라이브러리

- **PyQt6**: 일부 미사용 UI 컴포넌트 (향후 마이그레이션용)

---

## 코드 스타일 가이드

### 명명 규칙

- **클래스**: PascalCase (예: `QCService`)
- **함수/메서드**: snake_case (예: `run_inspection()`)
- **상수**: UPPER_SNAKE_CASE (예: `MAX_FILES`)
- **프라이빗 메서드**: `_method_name()`

### 파일 구조

```python
"""
모듈 설명
"""

# 표준 라이브러리
import os
import sys

# 서드파티 라이브러리
import pandas as pd

# 로컬 모듈
from app.qc.core import InspectionEngine


class MyClass:
    """클래스 설명"""

    def __init__(self):
        """초기화"""
        pass

    def public_method(self):
        """공개 메서드"""
        pass

    def _private_method(self):
        """비공개 메서드"""
        pass
```

---

## 테스트

### 테스트 구조

```
tests/
├── test_qc_inspection.py
├── test_default_db.py
└── test_data_comparison.py
```

### 실행 방법

```bash
# 전체 테스트
pytest tests/

# 특정 테스트
pytest tests/test_qc_inspection.py
```

---

## 배포

### 빌드 방법

```bash
# 의존성 설치
pip install -r requirements.txt

# 애플리케이션 실행
python src/main.py
```

### 실행 파일 생성

```bash
# PyInstaller 사용
pyinstaller --onefile --windowed src/main.py
```

---

## 향후 개선 사항

1. **Manager.py 리팩토링**
   - 현재 7000+ 줄 → 모듈화 필요
   - 탭별로 별도 컨트롤러로 분리

2. **PyQt6 마이그레이션**
   - Tkinter → PyQt6 전환 고려
   - 더 나은 UI/UX

3. **API 레이어 추가**
   - REST API 제공
   - 원격 접근 가능

4. **성능 최적화**
   - 대용량 파일 처리 개선
   - 비동기 처리

---

## 문제 해결

### 자주 발생하는 문제

**Q: QC 탭이 생성되지 않습니다**
- A: DBSchema 초기화 확인 (`data/default_db.sqlite` 존재 여부)

**Q: 파일 로드 실패**
- A: 파일 형식 확인 (지원: .txt, .csv, .xlsx)

**Q: 검수 결과가 표시되지 않습니다**
- A: Equipment Type 선택 및 Checklist 데이터 확인

---

## 기여 가이드

### 코드 기여 프로세스

1. 브랜치 생성: `feature/기능명` 또는 `fix/버그명`
2. 코드 작성 및 테스트
3. Pull Request 생성
4. 코드 리뷰 후 머지

### 커밋 메시지 규칙

```
타입: 제목

본문 (선택)

푸터 (선택)
```

**타입:**
- `feat`: 새 기능
- `fix`: 버그 수정
- `refactor`: 리팩토링
- `docs`: 문서 수정
- `test`: 테스트 추가/수정

---

## 라이센스

내부 사용 전용

---

## 연락처

기술 지원: [담당자 이메일]
프로젝트 관리자: [PM 이메일]
