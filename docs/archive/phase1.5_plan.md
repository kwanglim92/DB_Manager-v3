# Phase 1.5-2 Implementation Plan: Equipment Hierarchy & Raw Data Management

## 문서 정보
- **작성일**: 2025-11-13
- **Phase**: 1.5 (Equipment Hierarchy) + 2 (Raw Data Management)
- **목표**: 모델 기반 장비 관리 시스템 구축 및 출고 장비 데이터 관리
- **예상 기간**: 4-6주

---

## 📋 목차
1. [프로젝트 개요](#프로젝트-개요)
2. [Phase 1.5: Equipment Hierarchy System](#phase-15-equipment-hierarchy-system)
3. [Phase 2: Raw Data Management](#phase-2-raw-data-management)
4. [Check list System Redesign](#check-list-system-redesign)
5. [Database Schema](#database-schema)
6. [Migration Strategy](#migration-strategy)
7. [Implementation Roadmap](#implementation-roadmap)
8. [Risk Management](#risk-management)

---

## 프로젝트 개요

### 배경
현재 시스템의 제한사항:
- **단순 장비 유형 관리**: Equipment_Types만으로 복잡한 장비 변형 관리 불가
- **Configuration 누락**: Port 구성, Wafer 크기, 고객 커스터마이징 미지원
- **Check list 비효율**: Configuration마다 매핑 필요 → 관리 부담
- **출고 데이터 미관리**: 출고된 장비 추적 불가, Raw Data 활용 불가

### 목표
1. **계층적 장비 관리**: Model → Type → Configuration 3단계 구조
2. **유연한 Configuration**: Port/Wafer 조합 + 커스텀 옵션 + 고객별 변형
3. **효율적인 Check list**: ItemName 기반 자동 매칭, 예외 관리만
4. **출고 데이터 관리**: 시리얼 번호 기반 추적, 리핏 오더 지원

### 핵심 설계 원칙
- **Model First**: 장비 모델명을 최상위 계층으로 (기존 AE 형태 → 하위 계층)
- **Manual Configuration**: Configuration 자동 생성 없음, 수동 생성으로 품질 관리
- **Dropdown Constraints**: Port/Wafer 드롭다운으로 휴먼 에러 방지
- **ItemName Auto-Matching**: Check list 단일 마스터, 파일 ItemName과 자동 매칭
- **Exception-Based**: 모든 것을 매핑하지 않고 예외만 관리
- **Cal vs Spec Separation**: Default DB = Cal 값, QC Check list = Spec

---

## Phase 1.5: Equipment Hierarchy System

### 개요
**목표**: 모델명 기반 3단계 장비 계층 구조 구축
**기간**: 2-3주
**핵심 테이블**: Equipment_Models, Equipment_Types (수정), Equipment_Configurations

### 1.1 Equipment_Models (신규)

**목적**: 장비 모델명을 최상위 계층으로 관리

**테이블 구조**:
```sql
CREATE TABLE Equipment_Models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL UNIQUE,         -- "NX-Hybrid WLI", "NX-Mask", "NX-eView"
    model_code TEXT,                         -- "NX-H-WLI", "NX-M", "NX-EV" (선택)
    description TEXT,
    display_order INTEGER DEFAULT 0,         -- UI 정렬 순서
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**초기 데이터** (test 폴더 분석 기반):
- NX-Hybrid WLI
- NX-Mask
- NX-eView
- Wafer (모델명인지 확인 필요)

**관리 기능**:
- 모델명 추가/수정/삭제
- Display order 조정 (드래그 앤 드롭)
- 모델별 Type 개수 표시

### 1.2 Equipment_Types (수정)

**목적**: 각 모델의 AE 형태 관리 (일체형/분리형)

**변경 사항**:
- `model_id` FK 추가 (Equipment_Models 참조)
- `type_name` 의미 변경: 장비 모델명 → AE 형태
- Unique 제약 변경: `type_name` → `(model_id, type_name)`

**테이블 구조**:
```sql
CREATE TABLE Equipment_Types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER NOT NULL,               -- FK to Equipment_Models
    type_name TEXT NOT NULL,                 -- "분리형", "일체형"
    description TEXT,
    is_default BOOLEAN DEFAULT 0,            -- 모델의 기본 Type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (model_id) REFERENCES Equipment_Models(id) ON DELETE CASCADE,
    UNIQUE (model_id, type_name)
);
```

**마이그레이션**:
1. Equipment_Models에 기존 모델명 추출 및 삽입
2. Equipment_Types에 model_id FK 컬럼 추가
3. 기존 type_name을 분석하여 model_id 매핑
4. type_name을 AE 형태로 변경 ("분리형" 또는 "일체형")

**예시**:
```
기존: type_name = "NX-Hybrid WLI"
변경: model_id = 1 (NX-Hybrid WLI), type_name = "분리형"
```

### 1.3 Equipment_Configurations (신규)

**목적**: Port 구성, Wafer 크기, 고객 커스터마이징 관리

**테이블 구조**:
```sql
CREATE TABLE Equipment_Configurations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_type_id INTEGER NOT NULL,
    config_name TEXT NOT NULL,               -- "Single Port 150mm", "Double Port 200/300mm"

    -- Dropdown 제약으로 휴먼 에러 방지
    port_type TEXT CHECK(port_type IN ('Single Port', 'Double Port', 'Multi Port', NULL)),
    wafer_sizes TEXT CHECK(wafer_sizes IN ('150mm', '150/200mm', '200mm', '200/300mm', '300mm', NULL)),

    custom_options TEXT,                     -- JSON: {"feature_x": true, "chamber_count": 4}
    is_customer_specific BOOLEAN DEFAULT 0,  -- 고객 특화 여부
    customer_name TEXT,                      -- 고객 특화 시 고객명
    is_default BOOLEAN DEFAULT 0,            -- Type의 기본 Configuration

    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (equipment_type_id) REFERENCES Equipment_Types(id) ON DELETE CASCADE,
    UNIQUE (equipment_type_id, config_name)
);
```

**드롭다운 값**:
- **Port Type**: Single Port, Double Port, Multi Port
- **Wafer Sizes**: 150mm, 150/200mm, 200mm, 200/300mm, 300mm

**Custom Options JSON 예시**:
```json
{
    "interferometer_version": "2.0",
    "chamber_count": 2,
    "has_auto_loader": true,
    "special_coating": "anti-reflective"
}
```

**관리 기능**:
- Configuration 수동 생성 (자동 생성 없음)
- Port/Wafer 드롭다운 선택
- Custom options JSON 편집기
- 고객 특화 Configuration 플래그

### 1.4 Default_DB_Values (수정)

**목적**: Configuration별 기준 파라미터 값 (Spec 제거)

**변경 사항**:
- `configuration_id` FK 추가 (NULL 허용 = Type 공통)
- `min_spec`, `max_spec` 필드 **제거** (QC Check list로 이동)
- Unique 제약 확장: `(equipment_type_id, configuration_id, parameter_name)`

**테이블 구조**:
```sql
CREATE TABLE Default_DB_Values (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_type_id INTEGER NOT NULL,
    configuration_id INTEGER,                -- NULL = Type 공통, NOT NULL = Configuration 특화

    parameter_name TEXT NOT NULL,
    default_value TEXT,                      -- Cal 값만, Spec 없음!
    module TEXT,
    part TEXT,
    data_type TEXT,
    is_performance BOOLEAN DEFAULT 0,
    description TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (equipment_type_id) REFERENCES Equipment_Types(id) ON DELETE CASCADE,
    FOREIGN KEY (configuration_id) REFERENCES Equipment_Configurations(id) ON DELETE SET NULL,
    UNIQUE (equipment_type_id, configuration_id, parameter_name)
);
```

**우선순위 로직** (향후 구현):
```python
def get_default_value(equipment_type_id, configuration_id, parameter_name):
    # 1. Configuration 특화 값 우선
    value = query(configuration_id=configuration_id, parameter_name=parameter_name)
    if value:
        return value

    # 2. Type 공통 값
    value = query(equipment_type_id=equipment_type_id, configuration_id=NULL, parameter_name=parameter_name)
    return value
```

### 1.5 UI 설계

#### 1.5.1 Equipment Hierarchy Tree View
```
📁 NX-Hybrid WLI (Model)
  ├─ 🔧 분리형 (Type)
  │   ├─ ⚙️ Single Port 150mm (Configuration)
  │   ├─ ⚙️ Single Port 200mm
  │   ├─ ⚙️ Double Port 150/200mm
  │   └─ ⚙️ [Intel Hillsboro 특화] Double Port 300mm (Customer-specific)
  └─ 🔧 일체형
      ├─ ⚙️ Single Port 150mm
      └─ ⚙️ [Samsung SEC 특화] Single Port 200mm

📁 NX-Mask
  └─ 🔧 분리형
      └─ ⚙️ Single Port 300mm

📁 NX-eView
  └─ 🔧 일체형
      └─ ⚙️ Multi Port 200/300mm
```

#### 1.5.2 Configuration 생성 Dialog
```
┌─────────────────────────────────────────┐
│ Add Equipment Configuration             │
├─────────────────────────────────────────┤
│ Equipment Type: [분리형 (NX-Hybrid WLI)]│
│                                         │
│ Configuration Name: [________________]  │
│                                         │
│ Port Type:    [Single Port ▼]          │
│ Wafer Sizes:  [150mm ▼]                │
│                                         │
│ ☐ Customer-Specific Configuration      │
│ Customer Name: [__________________]     │
│                                         │
│ Custom Options (JSON):                  │
│ ┌─────────────────────────────────────┐ │
│ │ {                                   │ │
│ │   "interferometer_version": "2.0"   │ │
│ │ }                                   │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ Notes: [__________________________]     │
│                                         │
│          [Cancel]  [Create]             │
└─────────────────────────────────────────┘
```

#### 1.5.3 Default DB Management (수정)
```
현재 선택: NX-Hybrid WLI > 분리형 > Double Port 150/200mm

┌──────────────────────────────────────────────────────┐
│ Parameter Name        │ Default Value │ Module │ Part│
├──────────────────────────────────────────────────────┤
│ Temp.Chamber.SetPoint │ 25.0         │ Temp   │ -   │ (Configuration 특화)
│ Pressure.Vacuum.Max   │ 1.0e-5       │ Press  │ -   │ (Type 공통)
│ ...                   │              │        │     │
└──────────────────────────────────────────────────────┘

우클릭 메뉴:
  - Add Parameter (Configuration-specific)
  - Add Parameter (Type-common)
  - Edit Parameter
  - Delete Parameter
  - Convert to Configuration-specific
  - Convert to Type-common
```

---

## Phase 2: Raw Data Management

### 개요
**목표**: 출고된 장비의 Raw Data 추적 및 관리
**기간**: 2-3주
**핵심 테이블**: Shipped_Equipment, Shipped_Equipment_Parameters

### 2.1 Shipped_Equipment (신규)

**목적**: 출고 장비 메타데이터 관리

**테이블 구조**:
```sql
CREATE TABLE Shipped_Equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_type_id INTEGER NOT NULL,
    configuration_id INTEGER NOT NULL,

    serial_number TEXT NOT NULL UNIQUE,      -- "U27005-100225", "D27004-211124"
    customer_name TEXT NOT NULL,             -- "Intel Hillsboro", "Samsung SEC P1F"
    ship_date DATE,
    version TEXT,                            -- 소프트웨어/펌웨어 버전

    -- 리핏 오더 추적
    is_refit BOOLEAN DEFAULT 0,
    original_serial_number TEXT,             -- 리핏 시 원래 시리얼 번호

    notes TEXT,
    file_path TEXT,                          -- 원본 파일 경로

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (equipment_type_id) REFERENCES Equipment_Types(id) ON DELETE RESTRICT,
    FOREIGN KEY (configuration_id) REFERENCES Equipment_Configurations(id) ON DELETE RESTRICT
);
```

**파일명 파싱 예시**:
```
파일명: "U27005-100225_Intel Hillsboro #3_NX-Hybrid WLI.txt"
파싱 결과:
  - serial_number: "U27005-100225"
  - customer_name: "Intel Hillsboro #3"
  - model_name: "NX-Hybrid WLI" (Equipment_Models와 매칭)
```

**리핏 오더 관리**:
```python
# 리핏 오더 생성 예시
{
    "serial_number": "U27005-100225-R1",  # 리핏 시리얼
    "is_refit": True,
    "original_serial_number": "U27005-100225",
    "customer_name": "Intel Hillsboro (Refit)",
    "ship_date": "2024-03-15"
}
```

### 2.2 Shipped_Equipment_Parameters (신규)

**목적**: 출고 장비의 모든 파라미터 Raw Data 저장

**테이블 구조**:
```sql
CREATE TABLE Shipped_Equipment_Parameters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shipped_equipment_id INTEGER NOT NULL,

    parameter_name TEXT NOT NULL,            -- ItemName
    parameter_value TEXT NOT NULL,
    module TEXT,
    part TEXT,
    data_type TEXT,

    FOREIGN KEY (shipped_equipment_id) REFERENCES Shipped_Equipment(id) ON DELETE CASCADE,
    UNIQUE (shipped_equipment_id, parameter_name)
);
```

**인덱스**:
```sql
CREATE INDEX idx_shipped_params_equipment ON Shipped_Equipment_Parameters(shipped_equipment_id);
CREATE INDEX idx_shipped_params_name ON Shipped_Equipment_Parameters(parameter_name);
```

**데이터 활용 예시**:
```python
# 특정 파라미터의 출고 장비별 값 조회
def get_parameter_history(parameter_name, configuration_id=None):
    """
    특정 파라미터의 출고 이력 조회
    향후 통계 분석, Default DB 자동 업데이트에 활용
    """
    query = """
        SELECT
            se.serial_number,
            se.customer_name,
            se.ship_date,
            sep.parameter_value
        FROM Shipped_Equipment se
        JOIN Shipped_Equipment_Parameters sep ON se.id = sep.shipped_equipment_id
        WHERE sep.parameter_name = ?
    """
    if configuration_id:
        query += " AND se.configuration_id = ?"

    return execute_query(query)
```

### 2.3 UI 설계

#### 2.3.1 Shipped Equipment List
```
┌────────────────────────────────────────────────────────────────────────────┐
│ Shipped Equipment Management                                              │
├────────────────────────────────────────────────────────────────────────────┤
│ Filter: Configuration: [All ▼]  Customer: [All ▼]  Date: [2024 ▼]        │
├────────────────────────────────────────────────────────────────────────────┤
│ Serial Number    │ Customer          │ Configuration        │ Ship Date  │
├────────────────────────────────────────────────────────────────────────────┤
│ U27005-100225    │ Intel Hillsboro#3 │ 분리형 Single 150mm  │ 2024-01-15 │
│ U27006-100225    │ Intel Hillsboro#4 │ 분리형 Single 150mm  │ 2024-01-16 │
│ D27004-211124    │ Samsung SEC P1F   │ 분리형 Single 200mm  │ 2024-02-20 │
│ U27005-100225-R1 │ Intel (Refit) 🔄  │ 분리형 Single 150mm  │ 2024-03-15 │
└────────────────────────────────────────────────────────────────────────────┘

[Import from File]  [View Parameters]  [Export Statistics]
```

#### 2.3.2 Import Shipped Equipment Dialog
```
┌─────────────────────────────────────────────────┐
│ Import Shipped Equipment                        │
├─────────────────────────────────────────────────┤
│ File: [U27005-100225_Intel_NX-Hybrid.txt] [Browse]│
│                                                 │
│ Auto-Parsed Information:                        │
│   Serial Number: U27005-100225                  │
│   Customer Name: Intel Hillsboro #3             │
│   Model Name:    NX-Hybrid WLI                  │
│                                                 │
│ Select Configuration:                           │
│   Model: [NX-Hybrid WLI ▼]                     │
│   Type:  [분리형 ▼]                             │
│   Config: [Single Port 150mm ▼]                │
│                                                 │
│ Ship Date: [2024-01-15]  📅                    │
│                                                 │
│ ☐ This is a Refit Order                        │
│ Original Serial: [________________]             │
│                                                 │
│ Notes: [___________________________]            │
│                                                 │
│ 📊 Preview: 2,053 parameters will be imported  │
│                                                 │
│          [Cancel]  [Import]                     │
└─────────────────────────────────────────────────┘
```

---

## Check list System Redesign

### 개요
**목표**: Configuration별 매핑 제거, ItemName 기반 자동 매칭
**핵심 변경**:
- QC_Checklist_Items 단일 마스터 (Spec 포함)
- Equipment_Checklist_Exceptions (예외만 관리)
- Equipment_Checklist_Mapping **제거**
- 심각도 제거, Pass/Fail만

### 3.1 QC_Checklist_Items (수정)

**목적**: ItemName 마스터 + Spec 관리 (심각도 제거)

**변경 사항**:
- `severity_level` 필드 **제거**
- `spec_min`, `spec_max`, `expected_value` 필드 **추가**
- `is_common` 필드 **제거** (모든 항목이 공통)

**테이블 구조**:
```sql
CREATE TABLE QC_Checklist_Items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT NOT NULL UNIQUE,          -- "Module.Dsp.XDetector.Gain"

    -- Spec 관리 (Default DB에는 없음!)
    spec_min TEXT,                           -- "0.5"
    spec_max TEXT,                           -- "2.0"
    expected_value TEXT,                     -- "PASS" (Pass/Fail 항목용)

    category TEXT,                           -- "Safety", "Temperature", "Pressure"
    description TEXT,
    is_active BOOLEAN DEFAULT 1,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**데이터 예시**:
```sql
-- Spec 범위 항목
INSERT INTO QC_Checklist_Items (item_name, spec_min, spec_max, category)
VALUES ('Module.Dsp.XDetector.Gain', '0.5', '2.0', 'Performance');

-- Pass/Fail 항목
INSERT INTO QC_Checklist_Items (item_name, expected_value, category)
VALUES ('Safety.EmergencyStop.Status', 'PASS', 'Safety');

-- Enum 항목 (expected_value에 JSON)
INSERT INTO QC_Checklist_Items (item_name, expected_value, category)
VALUES ('Communication.Protocol', '["TCP/IP", "Modbus"]', 'Communication');
```

**관리 기능**:
- ItemName 수동 추가만 (자동 추가 없음)
- Spec 설정 (Min/Max 또는 Expected Value)
- Category 분류
- Active/Inactive 토글

### 3.2 Equipment_Checklist_Exceptions (신규)

**목적**: 특정 Configuration에서 Check list 항목 제외

**테이블 구조**:
```sql
CREATE TABLE Equipment_Checklist_Exceptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    configuration_id INTEGER NOT NULL,
    checklist_item_id INTEGER NOT NULL,

    reason TEXT NOT NULL,                    -- 제외 사유 (필수)
    approved_by TEXT,                        -- 승인자
    approved_date TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (configuration_id) REFERENCES Equipment_Configurations(id) ON DELETE CASCADE,
    FOREIGN KEY (checklist_item_id) REFERENCES QC_Checklist_Items(id) ON DELETE CASCADE,
    UNIQUE (configuration_id, checklist_item_id)
);
```

**사용 예시**:
```sql
-- "Single Port 150mm" Configuration에서 "Double Port 관련 항목" 제외
INSERT INTO Equipment_Checklist_Exceptions
(configuration_id, checklist_item_id, reason, approved_by)
VALUES (5, 12, 'Single Port 장비에는 해당 항목 없음', 'Admin');
```

### 3.3 QC Inspection Logic (재설계)

**기존 (Phase 1)**:
```python
# Configuration별로 매핑된 Check list 조회
checklist = get_mapped_checklist_items(configuration_id)
# 심각도별 가중치 적용
result = validate_with_severity(checklist, file_data)
```

**신규 (Phase 1.5)**:
```python
def qc_inspection_v2(file_data, configuration_id):
    """
    ItemName 기반 자동 매칭 QC 검수
    """
    # 1. 파일에서 ItemName 추출
    file_item_names = list(file_data.keys())

    # 2. QC_Checklist_Items 마스터에서 활성 항목 조회
    all_checklist_items = get_active_checklist_items()

    # 3. ItemName 매칭 (파일에 있는 항목만)
    matched_items = [
        item for item in all_checklist_items
        if item.item_name in file_item_names
    ]

    # 4. Configuration 예외 제거
    exception_item_ids = get_exception_item_ids(configuration_id)
    checklist_items = [
        item for item in matched_items
        if item.id not in exception_item_ids
    ]

    # 5. 각 항목 검증 (Pass/Fail만)
    results = []
    for item in checklist_items:
        file_value = file_data[item.item_name]
        is_valid = validate_item(item, file_value)

        results.append({
            'item_name': item.item_name,
            'file_value': file_value,
            'is_valid': is_valid,
            'spec': get_spec_display(item),
            'category': item.category
        })

    # 6. 전체 Pass/Fail 판정 (심각도 없음, 모든 항목 동일 중요도)
    failed_items = [r for r in results if r['is_valid'] == False]
    is_pass = len(failed_items) == 0

    return {
        'is_pass': is_pass,
        'total_count': len(results),
        'failed_count': len(failed_items),
        'results': results
    }

def validate_item(item, file_value):
    """
    단일 항목 검증
    """
    # Spec 범위 검증
    if item.spec_min and item.spec_max:
        try:
            val = float(file_value)
            return float(item.spec_min) <= val <= float(item.spec_max)
        except ValueError:
            return False

    # Expected Value 검증 (Pass/Fail)
    elif item.expected_value:
        # JSON 파싱 시도 (Enum)
        try:
            allowed_values = json.loads(item.expected_value)
            if isinstance(allowed_values, list):
                return file_value in allowed_values
        except:
            pass
        # 단순 문자열 비교
        return str(file_value).upper() == str(item.expected_value).upper()

    # Spec 없음 (항목 존재만 확인)
    else:
        return True

def get_spec_display(item):
    """
    Spec 표시 문자열 생성
    """
    if item.spec_min and item.spec_max:
        return f"{item.spec_min} ~ {item.spec_max}"
    elif item.expected_value:
        return item.expected_value
    else:
        return "N/A"
```

### 3.4 UI 설계

#### 3.4.1 QC Checklist Management
```
┌────────────────────────────────────────────────────────────────────────┐
│ QC Checklist Management (관리자 전용)                                  │
├────────────────────────────────────────────────────────────────────────┤
│ Filter: Category: [All ▼]  Status: [Active ▼]  Search: [_________]    │
├────────────────────────────────────────────────────────────────────────┤
│ ☑ │ ItemName                      │ Spec          │ Category    │ Act│
├────────────────────────────────────────────────────────────────────────┤
│ ☑ │ Module.Dsp.XDetector.Gain     │ 0.5 ~ 2.0     │ Performance │ ✓ │
│ ☑ │ Safety.EmergencyStop.Status   │ PASS          │ Safety      │ ✓ │
│ ☑ │ Temp.Chamber.SetPoint         │ 20.0 ~ 30.0   │ Temperature │ ✓ │
│ ☐ │ (Deprecated) Old.Parameter    │ -             │ Legacy      │ ✗ │
└────────────────────────────────────────────────────────────────────────┘

[Add Item]  [Edit Item]  [Deactivate]  [Delete]  [Import from CSV]

Note: ItemName은 수동으로만 추가됩니다. 파일에서 자동 추가되지 않습니다.
```

#### 3.4.2 Configuration Exceptions
```
┌─────────────────────────────────────────────────────────────────────────┐
│ Check list Exceptions: Single Port 150mm (NX-Hybrid WLI > 분리형)       │
├─────────────────────────────────────────────────────────────────────────┤
│ 제외된 항목들:                                                          │
│                                                                         │
│ ✗ Module.DoublePort.Interlock                                          │
│   사유: Single Port 장비에는 해당 항목 없음                            │
│   승인자: Admin  승인일: 2024-01-10                                     │
│                                                                         │
│ ✗ Wafer.Size.300mm.Calibration                                         │
│   사유: 150mm 전용 장비                                                 │
│   승인자: Admin  승인일: 2024-01-10                                     │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ [Add Exception]  [Remove Exception]  [View All Checklist Items]        │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 3.4.3 QC Inspection Result (간소화)
```
┌────────────────────────────────────────────────────────────────────────┐
│ QC Inspection Result                                                   │
├────────────────────────────────────────────────────────────────────────┤
│ Equipment: NX-Hybrid WLI > 분리형 > Single Port 150mm                 │
│ Serial: U27005-100225                                                  │
│                                                                        │
│ Overall Result: ❌ FAIL (2 / 53 items failed)                         │
├────────────────────────────────────────────────────────────────────────┤
│ Status │ ItemName                      │ File Value │ Spec          │
├────────────────────────────────────────────────────────────────────────┤
│ ❌     │ Module.Dsp.XDetector.Gain     │ 2.5        │ 0.5 ~ 2.0     │
│ ✅     │ Safety.EmergencyStop.Status   │ PASS       │ PASS          │
│ ✅     │ Temp.Chamber.SetPoint         │ 25.0       │ 20.0 ~ 30.0   │
│ ❌     │ Pressure.Vacuum.Max           │ 1.5e-4     │ 1.0e-5 ~ 1.0e-4│
│ ✅     │ ...                           │            │               │
└────────────────────────────────────────────────────────────────────────┘

[Export Report]  [View Details]  [Approve Override (관리자)]

Note: 모든 Check list 항목은 동일한 중요도로 평가됩니다 (심각도 없음).
```

---

## Database Schema

### 전체 ERD

```
┌─────────────────────┐
│ Equipment_Models    │ (신규)
│─────────────────────│
│ id (PK)             │
│ model_name (UNIQUE) │◄────┐
│ model_code          │     │
│ description         │     │
│ display_order       │     │
└─────────────────────┘     │
                            │
┌─────────────────────┐     │ 1:N
│ Equipment_Types     │ (수정)│
│─────────────────────│     │
│ id (PK)             │     │
│ model_id (FK)       │─────┘
│ type_name           │◄────┐
│ is_default          │     │
└─────────────────────┘     │
                            │
┌─────────────────────────┐ │ 1:N
│ Equipment_Configurations│ (신규)
│─────────────────────────│ │
│ id (PK)                 │ │
│ equipment_type_id (FK)  │─┘
│ config_name             │◄────┬───────┐
│ port_type (CHECK)       │     │       │
│ wafer_sizes (CHECK)     │     │       │
│ custom_options (JSON)   │     │       │
│ is_customer_specific    │     │       │
└─────────────────────────┘     │       │
                                │       │
┌─────────────────────────┐     │ 1:N   │ 1:N
│ Default_DB_Values       │ (수정)│       │
│─────────────────────────│     │       │
│ id (PK)                 │     │       │
│ equipment_type_id (FK)  │─────┘       │
│ configuration_id (FK)   │─────────────┘
│ parameter_name          │
│ default_value           │ (min_spec, max_spec 제거!)
│ module, part, data_type │
└─────────────────────────┘

┌─────────────────────────┐
│ QC_Checklist_Items      │ (수정)
│─────────────────────────│
│ id (PK)                 │◄────┐
│ item_name (UNIQUE)      │     │
│ spec_min, spec_max      │     │ (severity_level 제거!)
│ expected_value          │     │
│ category                │     │
│ is_active               │     │
└─────────────────────────┘     │
                                │ N:M (예외만)
┌─────────────────────────────┐ │
│ Equipment_Checklist_Exceptions│ (신규)
│─────────────────────────────│ │
│ id (PK)                     │ │
│ configuration_id (FK)       │─┤
│ checklist_item_id (FK)      │─┘
│ reason                      │
│ approved_by, approved_date  │
└─────────────────────────────┘

┌─────────────────────────┐
│ Shipped_Equipment       │ (신규)
│─────────────────────────│
│ id (PK)                 │◄────┐
│ equipment_type_id (FK)  │     │
│ configuration_id (FK)   │     │
│ serial_number (UNIQUE)  │     │
│ customer_name           │     │
│ ship_date               │     │
│ is_refit                │     │ 1:N
│ original_serial_number  │     │
└─────────────────────────┘     │
                                │
┌───────────────────────────────┐│
│ Shipped_Equipment_Parameters  │(신규)
│───────────────────────────────││
│ id (PK)                       ││
│ shipped_equipment_id (FK)     │┘
│ parameter_name                │
│ parameter_value               │
│ module, part, data_type       │
└───────────────────────────────┘
```

### 제거되는 테이블
- **Equipment_Checklist_Mapping**: ItemName 자동 매칭으로 대체

### 수정되는 테이블
- **Equipment_Types**: model_id FK 추가, type_name 의미 변경
- **Default_DB_Values**: configuration_id FK 추가, min_spec/max_spec 제거
- **QC_Checklist_Items**: severity_level 제거, spec 필드 추가

### 신규 테이블
- **Equipment_Models**: 3개
- **Equipment_Configurations**
- **Equipment_Checklist_Exceptions**
- **Shipped_Equipment**: 2개
- **Shipped_Equipment_Parameters**

**총 테이블 수**: 8개 (기존 2개 + 수정 3개 + 신규 5개)

---

## Migration Strategy

### 마이그레이션 우선순위

**Phase 1.5 (Week 1-3)**:
1. Equipment_Models 생성 및 초기 데이터
2. Equipment_Types 수정 (model_id 추가, 데이터 마이그레이션)
3. Equipment_Configurations 생성
4. Default_DB_Values 수정 (configuration_id 추가, spec 제거)
5. QC_Checklist_Items 수정 (severity 제거, spec 추가)
6. Equipment_Checklist_Exceptions 생성
7. Equipment_Checklist_Mapping 제거

**Phase 2 (Week 4-6)**:
1. Shipped_Equipment 생성
2. Shipped_Equipment_Parameters 생성
3. 기존 파일 일괄 임포트 (test 폴더)

### 마이그레이션 스크립트

#### Step 1: Equipment_Models 생성 및 데이터 추출
```python
def migrate_step1_create_models():
    """
    Equipment_Types에서 모델명 추출 → Equipment_Models 생성
    """
    # 1. Equipment_Models 테이블 생성
    conn.execute("""
        CREATE TABLE Equipment_Models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT NOT NULL UNIQUE,
            model_code TEXT,
            description TEXT,
            display_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. 기존 Equipment_Types.type_name에서 모델명 추출
    # 가정: type_name = "NX-Hybrid WLI", "NX-Mask", "NX-eView"
    existing_types = conn.execute("SELECT DISTINCT type_name FROM Equipment_Types").fetchall()

    model_names = set()
    for (type_name,) in existing_types:
        # 모델명 추출 로직 (휴리스틱)
        # 예: "NX-Hybrid WLI" → "NX-Hybrid WLI"
        model_name = extract_model_name(type_name)
        model_names.add(model_name)

    # 3. Equipment_Models에 삽입
    for idx, model_name in enumerate(sorted(model_names)):
        conn.execute("""
            INSERT INTO Equipment_Models (model_name, display_order)
            VALUES (?, ?)
        """, (model_name, idx))

    conn.commit()
    print(f"✅ {len(model_names)}개 모델 생성 완료")

def extract_model_name(type_name):
    """
    Equipment_Types.type_name에서 모델명 추출
    실제로는 test 폴더 구조 분석 필요
    """
    # 간단한 예시: 그대로 사용
    return type_name
```

#### Step 2: Equipment_Types 수정
```python
def migrate_step2_modify_types():
    """
    Equipment_Types에 model_id 추가, type_name을 AE 형태로 변경
    """
    # 1. 임시 백업 테이블 생성
    conn.execute("""
        CREATE TABLE Equipment_Types_Backup AS
        SELECT * FROM Equipment_Types
    """)

    # 2. Equipment_Types 재생성
    conn.execute("DROP TABLE Equipment_Types")
    conn.execute("""
        CREATE TABLE Equipment_Types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_id INTEGER NOT NULL,
            type_name TEXT NOT NULL,
            description TEXT,
            is_default BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (model_id) REFERENCES Equipment_Models(id) ON DELETE CASCADE,
            UNIQUE (model_id, type_name)
        )
    """)

    # 3. 데이터 마이그레이션
    backup_types = conn.execute("SELECT * FROM Equipment_Types_Backup").fetchall()

    for old_type in backup_types:
        old_id, old_type_name, old_desc = old_type[:3]

        # 모델명 추출
        model_name = extract_model_name(old_type_name)
        model_id = conn.execute(
            "SELECT id FROM Equipment_Models WHERE model_name = ?",
            (model_name,)
        ).fetchone()[0]

        # AE 형태 결정 (폴더 구조 분석 필요)
        # 가정: test 폴더의 "분리형 AE" or "일체형 AE"에서 파악
        ae_type = determine_ae_type(old_type_name)  # "분리형" or "일체형"

        # 삽입
        new_id = conn.execute("""
            INSERT INTO Equipment_Types (model_id, type_name, description)
            VALUES (?, ?, ?)
        """, (model_id, ae_type, old_desc)).lastrowid

        # ID 매핑 저장 (Default_DB_Values FK 업데이트용)
        id_mapping[old_id] = new_id

    conn.commit()
    print(f"✅ {len(backup_types)}개 Equipment_Types 마이그레이션 완료")

def determine_ae_type(old_type_name):
    """
    실제로는 test 폴더 구조 분석:
    - test/분리형 AE/04. NX-Hybrid WLI/ → "분리형"
    - test/일체형 AE/09. NX-eView/ → "일체형"
    """
    # 간단한 예시
    return "분리형"  # 실제로는 폴더 스캔 필요
```

#### Step 3: Default_DB_Values 수정
```python
def migrate_step3_modify_default_db():
    """
    Default_DB_Values에 configuration_id 추가, min_spec/max_spec 제거
    """
    # 1. 백업
    conn.execute("""
        CREATE TABLE Default_DB_Values_Backup AS
        SELECT * FROM Default_DB_Values
    """)

    # 2. 재생성
    conn.execute("DROP TABLE Default_DB_Values")
    conn.execute("""
        CREATE TABLE Default_DB_Values (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_type_id INTEGER NOT NULL,
            configuration_id INTEGER,
            parameter_name TEXT NOT NULL,
            default_value TEXT,
            module TEXT,
            part TEXT,
            data_type TEXT,
            is_performance BOOLEAN DEFAULT 0,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (equipment_type_id) REFERENCES Equipment_Types(id) ON DELETE CASCADE,
            FOREIGN KEY (configuration_id) REFERENCES Equipment_Configurations(id) ON DELETE SET NULL,
            UNIQUE (equipment_type_id, configuration_id, parameter_name)
        )
    """)

    # 3. 데이터 마이그레이션 (min_spec, max_spec 제외)
    backup_values = conn.execute("SELECT * FROM Default_DB_Values_Backup").fetchall()

    for old_value in backup_values:
        old_type_id = old_value[1]
        new_type_id = id_mapping[old_type_id]  # Step 2에서 생성된 매핑

        conn.execute("""
            INSERT INTO Default_DB_Values
            (equipment_type_id, configuration_id, parameter_name, default_value,
             module, part, data_type, is_performance, description)
            VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?)
        """, (
            new_type_id,
            old_value[2],  # parameter_name
            old_value[3],  # default_value
            old_value[6],  # module (min_spec, max_spec 건너뜀)
            old_value[7],  # part
            old_value[8],  # data_type
            old_value[9],  # is_performance
            old_value[10]  # description
        ))

    conn.commit()
    print(f"✅ {len(backup_values)}개 Default_DB_Values 마이그레이션 완료 (Spec 제거)")
```

#### Step 4: QC_Checklist_Items 수정
```python
def migrate_step4_modify_checklist():
    """
    QC_Checklist_Items에서 severity_level 제거, spec 필드 추가
    """
    # 1. 백업
    conn.execute("""
        CREATE TABLE QC_Checklist_Items_Backup AS
        SELECT * FROM QC_Checklist_Items
    """)

    # 2. 재생성
    conn.execute("DROP TABLE QC_Checklist_Items")
    conn.execute("""
        CREATE TABLE QC_Checklist_Items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL UNIQUE,
            spec_min TEXT,
            spec_max TEXT,
            expected_value TEXT,
            category TEXT,
            description TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 3. 데이터 마이그레이션 (severity_level 제외)
    backup_items = conn.execute("SELECT * FROM QC_Checklist_Items_Backup").fetchall()

    for old_item in backup_items:
        # validation_rule (JSON)에서 spec 추출
        validation_rule = json.loads(old_item[5]) if old_item[5] else {}

        spec_min = None
        spec_max = None
        expected_value = None

        if validation_rule.get('type') == 'range':
            spec_min = validation_rule.get('min')
            spec_max = validation_rule.get('max')
        elif validation_rule.get('type') == 'enum':
            expected_value = json.dumps(validation_rule.get('values'))
        elif validation_rule.get('type') == 'pattern':
            expected_value = validation_rule.get('pattern')

        conn.execute("""
            INSERT INTO QC_Checklist_Items
            (item_name, spec_min, spec_max, expected_value, category, description, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            old_item[1],  # item_name
            spec_min,
            spec_max,
            expected_value,
            old_item[4],  # category (is_common, severity_level 건너뜀)
            old_item[7],  # description
            1             # is_active
        ))

    conn.commit()
    print(f"✅ {len(backup_items)}개 QC_Checklist_Items 마이그레이션 완료 (Severity 제거, Spec 추가)")
```

#### Step 5: Equipment_Checklist_Mapping 제거
```python
def migrate_step5_remove_mapping():
    """
    Equipment_Checklist_Mapping 제거
    (ItemName 자동 매칭으로 대체되므로 불필요)
    """
    # 1. 데이터 백업 (혹시 모를 롤백용)
    conn.execute("""
        CREATE TABLE Equipment_Checklist_Mapping_Archive AS
        SELECT * FROM Equipment_Checklist_Mapping
    """)

    # 2. 테이블 삭제
    conn.execute("DROP TABLE Equipment_Checklist_Mapping")

    conn.commit()
    print("✅ Equipment_Checklist_Mapping 제거 완료 (Archive 테이블로 백업)")
```

#### Step 6: Phase 2 테이블 생성
```python
def migrate_step6_create_shipped_tables():
    """
    Shipped_Equipment, Shipped_Equipment_Parameters 생성
    """
    conn.execute("""
        CREATE TABLE Shipped_Equipment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_type_id INTEGER NOT NULL,
            configuration_id INTEGER NOT NULL,
            serial_number TEXT NOT NULL UNIQUE,
            customer_name TEXT NOT NULL,
            ship_date DATE,
            version TEXT,
            is_refit BOOLEAN DEFAULT 0,
            original_serial_number TEXT,
            notes TEXT,
            file_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (equipment_type_id) REFERENCES Equipment_Types(id) ON DELETE RESTRICT,
            FOREIGN KEY (configuration_id) REFERENCES Equipment_Configurations(id) ON DELETE RESTRICT
        )
    """)

    conn.execute("""
        CREATE TABLE Shipped_Equipment_Parameters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shipped_equipment_id INTEGER NOT NULL,
            parameter_name TEXT NOT NULL,
            parameter_value TEXT NOT NULL,
            module TEXT,
            part TEXT,
            data_type TEXT,
            FOREIGN KEY (shipped_equipment_id) REFERENCES Shipped_Equipment(id) ON DELETE CASCADE,
            UNIQUE (shipped_equipment_id, parameter_name)
        )
    """)

    # 인덱스 생성
    conn.execute("""
        CREATE INDEX idx_shipped_params_equipment
        ON Shipped_Equipment_Parameters(shipped_equipment_id)
    """)
    conn.execute("""
        CREATE INDEX idx_shipped_params_name
        ON Shipped_Equipment_Parameters(parameter_name)
    """)

    conn.commit()
    print("✅ Shipped_Equipment, Shipped_Equipment_Parameters 생성 완료")
```

### 롤백 전략

모든 마이그레이션 단계는 백업 테이블 생성:
- Equipment_Types_Backup
- Default_DB_Values_Backup
- QC_Checklist_Items_Backup
- Equipment_Checklist_Mapping_Archive

**롤백 스크립트**:
```python
def rollback_migration():
    """
    마이그레이션 롤백 (백업에서 복원)
    """
    # 1. 신규 테이블 삭제
    conn.execute("DROP TABLE IF EXISTS Equipment_Models")
    conn.execute("DROP TABLE IF EXISTS Equipment_Configurations")
    conn.execute("DROP TABLE IF EXISTS Equipment_Checklist_Exceptions")
    conn.execute("DROP TABLE IF EXISTS Shipped_Equipment")
    conn.execute("DROP TABLE IF EXISTS Shipped_Equipment_Parameters")

    # 2. 수정된 테이블 삭제 및 백업에서 복원
    conn.execute("DROP TABLE IF EXISTS Equipment_Types")
    conn.execute("ALTER TABLE Equipment_Types_Backup RENAME TO Equipment_Types")

    conn.execute("DROP TABLE IF EXISTS Default_DB_Values")
    conn.execute("ALTER TABLE Default_DB_Values_Backup RENAME TO Default_DB_Values")

    conn.execute("DROP TABLE IF EXISTS QC_Checklist_Items")
    conn.execute("ALTER TABLE QC_Checklist_Items_Backup RENAME TO QC_Checklist_Items")

    # 3. 제거된 테이블 복원
    conn.execute("ALTER TABLE Equipment_Checklist_Mapping_Archive RENAME TO Equipment_Checklist_Mapping")

    conn.commit()
    print("✅ 마이그레이션 롤백 완료")
```

---

## Implementation Roadmap

### Week 1: Phase 1.5 - Database & Services

**Day 1-2: Database Migration**
- [ ] Equipment_Models 테이블 생성
- [ ] Equipment_Types 수정 (model_id 추가)
- [ ] Equipment_Configurations 테이블 생성
- [ ] Default_DB_Values 수정 (configuration_id, spec 제거)
- [ ] 마이그레이션 스크립트 작성 및 테스트
- [ ] 롤백 스크립트 작성

**Day 3-4: Service Layer**
- [ ] `CategoryService` 생성
  - `get_all_models()`, `add_model()`, `delete_model()`
  - `get_types_by_model()`, `add_type()`, `delete_type()`
- [ ] `ConfigurationService` 생성
  - `get_configurations_by_type()`, `add_configuration()`, `delete_configuration()`
  - `get_default_values()` (우선순위 로직)
- [ ] `EquipmentService` 수정
  - 3단계 계층 지원
- [ ] ServiceFactory 업데이트

**Day 5: Testing**
- [ ] Unit tests for CategoryService
- [ ] Unit tests for ConfigurationService
- [ ] Integration tests (Model → Type → Configuration)
- [ ] Migration script validation

### Week 2: Phase 1.5 - UI

**Day 1-2: Hierarchy Tree View**
- [ ] Equipment Hierarchy Tree UI (Tkinter Treeview)
- [ ] 3단계 계층 표시 (Model → Type → Configuration)
- [ ] 아이콘, 색상 구분
- [ ] 우클릭 메뉴 (Add/Edit/Delete)

**Day 3: Configuration Management**
- [ ] Add Configuration Dialog
  - Port Type 드롭다운
  - Wafer Size 드롭다운
  - Custom Options JSON 편집기
  - Customer-specific 플래그
- [ ] Edit Configuration Dialog
- [ ] Delete Configuration (FK 제약 확인)

**Day 4: Default DB Management 개선**
- [ ] Configuration 선택 UI
- [ ] Configuration-specific vs Type-common 구분
- [ ] 우선순위 표시 (Override 표시)
- [ ] Convert between Configuration/Type common

**Day 5: Integration & Testing**
- [ ] UI/Service 통합 테스트
- [ ] End-to-End workflow test
- [ ] 사용자 시나리오 테스트

### Week 3: Check list System Redesign

**Day 1-2: Database & Logic**
- [ ] QC_Checklist_Items 수정 (spec 추가, severity 제거)
- [ ] Equipment_Checklist_Exceptions 테이블 생성
- [ ] Equipment_Checklist_Mapping 제거
- [ ] `qc_inspection_v2()` 구현
  - ItemName 자동 매칭
  - Exception 적용
  - Pass/Fail 판정 (심각도 없음)

**Day 3: UI - Checklist Management**
- [ ] QC Checklist Management Dialog (관리자 전용)
  - ItemName 수동 추가
  - Spec 설정 (Min/Max, Expected Value)
  - Category 분류
  - Active/Inactive 토글
- [ ] Import from CSV

**Day 4: UI - Exception Management**
- [ ] Configuration Exceptions Dialog
  - Configuration별 제외 항목 관리
  - 사유 입력 (필수)
  - 승인자, 승인일

**Day 5: QC Inspection Integration**
- [ ] QC Inspection UI 수정 (심각도 제거)
- [ ] Result 표시 간소화 (Pass/Fail만)
- [ ] Report 생성 업데이트
- [ ] End-to-End test

### Week 4: Phase 2 - Raw Data Management

**Day 1-2: Database & Service**
- [ ] Shipped_Equipment 테이블 생성
- [ ] Shipped_Equipment_Parameters 테이블 생성
- [ ] `ShippedEquipmentService` 생성
  - `import_from_file()` (파일명 파싱)
  - `get_shipped_equipment()` (필터링)
  - `get_parameter_history()` (통계용)

**Day 3: Import Logic**
- [ ] 파일명 파싱 (`{Serial}_{Customer}_{Model}.txt`)
- [ ] Model/Type/Configuration 자동 매칭
- [ ] 2000+ 파라미터 일괄 삽입 (성능 최적화)
- [ ] 리핏 오더 처리

**Day 4-5: UI**
- [ ] Shipped Equipment List View
  - 필터링 (Configuration, Customer, Date)
  - 정렬, 검색
- [ ] Import Dialog
  - 파일 선택
  - 자동 파싱 결과 표시
  - Configuration 선택
  - 리핏 플래그
- [ ] Parameter View (특정 장비의 파라미터 조회)

### Week 5: Bulk Import & Optimization

**Day 1-3: Bulk Import from test Folder**
- [ ] `test/분리형 AE/` 폴더 스캔
- [ ] `test/일체형 AE/` 폴더 스캔
- [ ] 파일명 → Configuration 자동 매칭
- [ ] 일괄 임포트 스크립트
- [ ] 진행상황 표시 (ProgressBar)
- [ ] 오류 처리 (매칭 실패 시)

**Day 4: Performance Optimization**
- [ ] Batch insert (1000 rows씩)
- [ ] 인덱스 최적화
- [ ] 쿼리 최적화 (N+1 문제 해결)
- [ ] 캐싱 전략

**Day 5: Testing**
- [ ] 대용량 데이터 테스트 (50+ 파일)
- [ ] 성능 벤치마크
- [ ] 메모리 사용량 확인

### Week 6: Integration, Testing & Documentation

**Day 1-2: End-to-End Testing**
- [ ] Full workflow test (Model 생성 → Configuration → Default DB → QC 검수 → 출고 데이터)
- [ ] Regression test (Phase 0, 1 기능)
- [ ] UI/UX test (사용성 검증)
- [ ] 버그 수정

**Day 3: Performance & Stability**
- [ ] 성능 테스트 (대용량 데이터)
- [ ] 메모리 누수 확인
- [ ] 동시성 테스트 (파일 잠금)
- [ ] 안정성 테스트 (장시간 실행)

**Day 4: Documentation**
- [ ] CLAUDE.md 업데이트
  - Phase 1.5-2 섹션 추가
  - Database Schema 업데이트
  - Workflow 업데이트
- [ ] PHASE1.5-2_IMPLEMENTATION.md 작성
  - 구현 상세
  - 설계 결정
  - 성능 지표
- [ ] USER_GUIDE.md 업데이트
  - 신규 기능 사용법
  - 스크린샷

**Day 5: Release Preparation**
- [ ] 버전 번호 업데이트 (v1.5.0)
- [ ] Release notes 작성
- [ ] 빌드 테스트 (scripts/build.bat)
- [ ] Git commit & tag
- [ ] 백업 생성

---

## Risk Management

### 고위험 (High Risk)

#### 1. 데이터 마이그레이션 실패
**리스크**: Equipment_Types 마이그레이션 중 데이터 손실 또는 FK 불일치

**완화 전략**:
- [ ] 마이그레이션 전 전체 DB 백업
- [ ] 각 단계마다 백업 테이블 생성
- [ ] 롤백 스크립트 사전 작성 및 테스트
- [ ] Staging 환경에서 먼저 테스트

**복구 계획**:
- 백업 DB에서 복원
- 롤백 스크립트 실행
- 마이그레이션 로그 분석 후 재시도

#### 2. test 폴더 구조 불일치
**리스크**: 파일명/폴더 구조가 가정과 다를 경우 자동 매칭 실패

**완화 전략**:
- [ ] test 폴더 전체 스캔 및 구조 분석
- [ ] 파일명 파싱 로직 다양한 패턴 지원
- [ ] 매칭 실패 시 수동 선택 UI 제공
- [ ] 매칭 로그 기록 (디버깅용)

**복구 계획**:
- 수동 매칭 UI로 전환
- 파싱 로직 수정 후 재임포트

### 중위험 (Medium Risk)

#### 3. 성능 저하 (대용량 파라미터)
**리스크**: 2000+ 파라미터 * 50+ 파일 = 100,000+ rows 삽입 시 성능 저하

**완화 전략**:
- [ ] Batch insert (executemany)
- [ ] Transaction 단위 조정
- [ ] 인덱스 최적화 (삽입 후 생성)
- [ ] 진행상황 표시 (사용자 피드백)

**목표 성능**:
- 파일 1개 임포트: < 5초
- 파일 50개 일괄 임포트: < 5분

#### 4. UI 복잡도 증가
**리스크**: 3단계 계층 + Configuration 옵션 → UI 복잡성 증가

**완화 전략**:
- [ ] Tree View로 직관적 표현
- [ ] Wizard 형식 Dialog (단계별 입력)
- [ ] Tooltip, 도움말 추가
- [ ] 기본값 제공 (자주 사용되는 조합)

**사용자 피드백**:
- Alpha 테스트 (내부)
- UI/UX 개선 반복

### 저위험 (Low Risk)

#### 5. Check list 마이그레이션
**리스크**: Severity → Spec 변환 중 정보 손실

**완화 전략**:
- [ ] validation_rule JSON에서 spec 정보 추출
- [ ] 변환 로직 테스트
- [ ] 백업 테이블 유지

**복구 계획**:
- QC_Checklist_Items_Backup에서 복원
- 수동 재설정

#### 6. Foreign Key 제약 위반
**리스크**: Configuration 삭제 시 Default_DB_Values 참조 오류

**완화 전략**:
- [ ] ON DELETE SET NULL (Configuration → Default_DB_Values)
- [ ] ON DELETE RESTRICT (Configuration → Shipped_Equipment)
- [ ] 삭제 전 참조 확인 UI

**복구 계획**:
- 트랜잭션 롤백
- 참조 데이터 먼저 정리 후 재시도

---

## Success Criteria

### Phase 1.5 (Equipment Hierarchy)

**필수 (Must-Have)**:
- [x] Equipment_Models, Equipment_Types, Equipment_Configurations 테이블 생성
- [ ] Model → Type → Configuration 3단계 Tree View UI
- [ ] Configuration 수동 생성 (Port/Wafer 드롭다운)
- [ ] Default_DB_Values Configuration-specific 지원
- [ ] 기존 데이터 무손실 마이그레이션
- [ ] 모든 테스트 통과 (20/20 유지)

**권장 (Should-Have)**:
- [ ] Custom Options JSON 편집기
- [ ] Customer-specific Configuration 플래그
- [ ] Default DB 우선순위 로직 (Configuration > Type)
- [ ] Configuration별 Default DB 조회 성능 < 100ms

**선택 (Nice-to-Have)**:
- [ ] Model/Type/Configuration Display Order 조정 (드래그 앤 드롭)
- [ ] Configuration 템플릿 (자주 사용되는 조합 저장)
- [ ] Bulk Configuration 생성 (여러 조합 한번에)

### Phase 2 (Raw Data Management)

**필수 (Must-Have)**:
- [ ] Shipped_Equipment, Shipped_Equipment_Parameters 테이블 생성
- [ ] 파일 임포트 기능 (파일명 파싱)
- [ ] Configuration 자동/수동 매칭
- [ ] 리핏 오더 추적
- [ ] test 폴더 일괄 임포트 (50+ 파일)

**권장 (Should-Have)**:
- [ ] 출고 장비 필터링/검색 UI
- [ ] 특정 파라미터 출고 이력 조회
- [ ] Import 오류 처리 (매칭 실패 시 수동 선택)
- [ ] 일괄 임포트 성능 < 5분 (50 파일)

**선택 (Nice-to-Have)**:
- [ ] 출고 데이터 통계 (월별, 고객별)
- [ ] 파라미터 값 분포 시각화
- [ ] 이상값 감지 (통계 기반)

### Check list System Redesign

**필수 (Must-Have)**:
- [ ] ItemName 기반 자동 매칭
- [ ] Equipment_Checklist_Exceptions 테이블 생성
- [ ] QC_Checklist_Items Spec 관리 (min/max, expected)
- [ ] 심각도 제거, Pass/Fail 판정만
- [ ] Configuration별 예외 관리 UI
- [ ] 기존 Check list 데이터 보존

**권장 (Should-Have)**:
- [ ] QC Checklist Management Dialog (관리자)
- [ ] Category별 필터링
- [ ] Active/Inactive 토글
- [ ] QC Inspection Result 간소화

**선택 (Nice-to-Have)**:
- [ ] Check list Import/Export (CSV)
- [ ] Check list 버전 관리 (이력)
- [ ] Check list 통계 (Pass 비율)

---

## Appendix

### A. 용어 정리

- **Model**: 장비 모델명 (예: "NX-Hybrid WLI", "NX-Mask")
- **Type**: AE 형태 (예: "분리형", "일체형")
- **Configuration**: Port 구성 + Wafer 크기 + 커스텀 옵션 조합
- **ItemName**: 파라미터의 고유 식별자 (예: "Module.Dsp.XDetector.Gain")
- **Cal Value**: 교정 값 (Calibration Value), Default DB에 저장
- **Spec**: 검수 기준값 (Specification), QC Check list에 저장
- **Refit**: 리핏 오더 (재가공 주문), 기존 장비를 수정하여 재출고

### B. 파일명 파싱 패턴

**표준 패턴**:
```
{Serial}_{Customer}_{Model}.txt
예: U27005-100225_Intel Hillsboro #3_NX-Hybrid WLI.txt

파싱 결과:
- serial_number: "U27005-100225"
- customer_name: "Intel Hillsboro #3"
- model_name: "NX-Hybrid WLI"
```

**리핏 패턴**:
```
{Serial}-R{N}_{Customer}_{Model}.txt
예: U27005-100225-R1_Intel Hillsboro (Refit)_NX-Hybrid WLI.txt

파싱 결과:
- serial_number: "U27005-100225-R1"
- is_refit: True
- original_serial_number: "U27005-100225"
- customer_name: "Intel Hillsboro (Refit)"
```

### C. JSON Custom Options 예시

```json
{
  "interferometer_version": "2.0",
  "chamber_count": 2,
  "has_auto_loader": true,
  "coating_type": "anti-reflective",
  "sensor_upgrade": "high-sensitivity",
  "software_version": "3.5.2",
  "special_notes": "Customer-requested configuration for cleanroom Class 10"
}
```

### D. 참조 문서

- CLAUDE.md - 프로젝트 전체 가이드
- PHASE1_IMPLEMENTATION.md - Phase 1 구현 상세
- PHASE1_PROGRESS.md - Phase 1 진행 기록
- PROJECT_STATUS.md - 전체 프로젝트 현황
- src/db_schema.py - 데이터베이스 스키마 정의

---

## 문서 변경 이력

### 2025-11-13
- 초안 작성
- Phase 1.5-2 전체 계획 수립
- Check list 시스템 재설계 반영
- Database Schema 정의
- Migration Strategy 작성
- 6주 Implementation Roadmap 작성
