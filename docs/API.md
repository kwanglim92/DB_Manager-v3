# API 문서

DB Manager의 주요 API와 데이터베이스 스키마를 설명합니다.

## 📊 Database Schema

### Core Tables

#### Equipment_Models
장비 모델 최상위 계층
```sql
CREATE TABLE Equipment_Models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL UNIQUE,  -- "NX-Hybrid WLI", "NX-Mask"
    model_code TEXT,
    description TEXT,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Equipment_Types
각 모델의 AE 형태 관리
```sql
CREATE TABLE Equipment_Types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER,                  -- FK to Equipment_Models (Phase 1.5)
    type_name TEXT NOT NULL,          -- "분리형", "일체형"
    description TEXT,
    is_default BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES Equipment_Models(id),
    UNIQUE (model_id, type_name)
);
```

#### Equipment_Configurations
Port 구성, Wafer 크기, 커스터마이징
```sql
CREATE TABLE Equipment_Configurations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_type_id INTEGER NOT NULL,
    config_name TEXT NOT NULL,
    port_type TEXT CHECK(port_type IN ('Single Port', 'Double Port', 'Multi Port', NULL)),
    wafer_sizes TEXT CHECK(wafer_sizes IN ('150mm', '200mm', '300mm', '150/200mm', '200/300mm', NULL)),
    custom_options TEXT,              -- JSON format
    is_customer_specific BOOLEAN DEFAULT 0,
    customer_name TEXT,
    is_default BOOLEAN DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equipment_type_id) REFERENCES Equipment_Types(id),
    UNIQUE (equipment_type_id, config_name)
);
```

#### Default_DB_Values
Configuration별 기준 파라미터 값
```sql
CREATE TABLE Default_DB_Values (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_type_id INTEGER NOT NULL,
    configuration_id INTEGER,         -- NULL = Type 공통
    parameter_name TEXT NOT NULL,
    default_value TEXT,
    module TEXT,
    part TEXT,
    data_type TEXT,
    is_performance BOOLEAN DEFAULT 0,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equipment_type_id) REFERENCES Equipment_Types(id),
    FOREIGN KEY (configuration_id) REFERENCES Equipment_Configurations(id),
    UNIQUE (equipment_type_id, configuration_id, parameter_name)
);
```

#### QC_Checklist_Items
Check list 항목 및 Spec 관리
```sql
CREATE TABLE QC_Checklist_Items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT NOT NULL UNIQUE,
    parameter_pattern TEXT,           -- 정규식 패턴
    spec_min TEXT,                   -- Phase 1.5: spec 추가
    spec_max TEXT,
    expected_value TEXT,
    category TEXT,
    description TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔌 Service Layer APIs

### ServiceFactory

서비스 인스턴스 생성 및 관리

```python
from app.services import ServiceFactory

# 초기화
factory = ServiceFactory(db_schema)

# 서비스 획득
equipment_service = factory.get_equipment_service()
checklist_service = factory.get_checklist_service()
category_service = factory.get_category_service()
configuration_service = factory.get_configuration_service()
```

### EquipmentService

장비 관련 비즈니스 로직

```python
class IEquipmentService:
    def get_equipment_types(self) -> List[Dict]:
        """모든 장비 유형 조회"""
        
    def get_equipment_type(self, type_id: int) -> Dict:
        """특정 장비 유형 조회"""
        
    def add_equipment_type(self, name: str, desc: str) -> int:
        """새 장비 유형 추가"""
        
    def update_equipment_type(self, type_id: int, name: str, desc: str) -> bool:
        """장비 유형 수정"""
        
    def delete_equipment_type(self, type_id: int) -> bool:
        """장비 유형 삭제"""
        
    def get_default_values(self, type_id: int, config_id: int = None) -> List[Dict]:
        """기준값 조회 (Configuration 우선순위 적용)"""
```

### ChecklistService

Check list 관리

```python
class IChecklistService:
    def get_common_checklist_items(self) -> List[Dict]:
        """공통 Check list 항목 조회"""
        
    def get_equipment_checklist(self, equipment_type_id: int) -> List[Dict]:
        """장비별 Check list 조회 (공통 + 장비특화)"""
        
    def add_checklist_item(self, item_name: str, pattern: str, 
                          spec_min: str = None, spec_max: str = None,
                          expected_value: str = None, category: str = None) -> int:
        """Check list 항목 추가"""
        
    def validate_parameter(self, equipment_type_id: int, config_id: int,
                          parameter_name: str, value: str) -> Dict:
        """파라미터 검증
        Returns: {
            'is_checklist': bool,
            'is_valid': bool,
            'item_name': str,
            'message': str
        }
        """
        
    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        """변경 이력 조회"""
```

### CategoryService (Phase 1.5)

Model/Type 계층 관리

```python
class CategoryService:
    def get_all_models(self) -> List[Dict]:
        """모든 모델 조회"""
        
    def add_model(self, model_name: str, model_code: str = None) -> int:
        """새 모델 추가"""
        
    def get_types_by_model(self, model_id: int) -> List[Dict]:
        """모델의 Type 목록 조회"""
        
    def add_type(self, model_id: int, type_name: str) -> int:
        """Type 추가 (분리형/일체형)"""
```

### ConfigurationService (Phase 1.5)

Configuration 관리

```python
class ConfigurationService:
    def get_configurations_by_type(self, type_id: int) -> List[Dict]:
        """Type의 Configuration 목록 조회"""
        
    def add_configuration(self, type_id: int, config_name: str,
                         port_type: str = None, wafer_sizes: str = None,
                         custom_options: str = None) -> int:
        """Configuration 추가"""
        
    def get_default_values(self, type_id: int, config_id: int) -> List[Dict]:
        """Configuration별 기준값 조회 (우선순위 적용)"""
```

## 🔄 Service Interfaces

모든 서비스는 인터페이스 기반:

```python
# services/interfaces/base_interface.py
from abc import ABC, abstractmethod

class IService(ABC):
    @abstractmethod
    def initialize(self):
        pass

# 각 서비스별 인터페이스
from .base_interface import IService

class IEquipmentService(IService):
    # 메서드 정의...
```

## 📝 사용 예제

### 장비 Configuration 생성

```python
# 서비스 초기화
factory = ServiceFactory(db_schema)
config_service = factory.get_configuration_service()

# Configuration 추가
config_id = config_service.add_configuration(
    type_id=1,
    config_name="Single Port 150mm",
    port_type="Single Port",
    wafer_sizes="150mm",
    custom_options=json.dumps({
        "interferometer_version": "2.0",
        "has_auto_loader": True
    })
)
```

### Check list 검증

```python
checklist_service = factory.get_checklist_service()

# 파라미터 검증
result = checklist_service.validate_parameter(
    equipment_type_id=1,
    config_id=config_id,
    parameter_name="Temp.Chamber.SetPoint",
    value="25.0"
)

if result['is_checklist'] and not result['is_valid']:
    print(f"검증 실패: {result['message']}")
```

### 계층 구조 조회

```python
category_service = factory.get_category_service()

# Model → Type → Configuration 계층 구조
models = category_service.get_all_models()
for model in models:
    types = category_service.get_types_by_model(model['id'])
    for type in types:
        configs = config_service.get_configurations_by_type(type['id'])
        print(f"{model['model_name']} > {type['type_name']}")
        for config in configs:
            print(f"  └─ {config['config_name']}")
```

## 🔐 권한 관리

```python
# 권한 레벨
class AccessLevel(Enum):
    PRODUCTION = 0  # 생산 엔지니어
    QC = 1         # QC 엔지니어
    ADMIN = 2      # 관리자

# 권한 확인
if access_control.can_manage_checklist():
    # Check list 관리 가능
    pass
    
if access_control.can_access_default_db():
    # Default DB 관리 가능
    pass
```

---

더 자세한 구현 예제는 소스 코드를 참고하세요.