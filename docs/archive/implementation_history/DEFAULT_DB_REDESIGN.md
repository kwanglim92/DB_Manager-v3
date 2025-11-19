# Default DB 관리 시스템 재설계 제안

## 🎯 문제점 분석

### 현재 시스템의 문제점
1. **Configuration 과도한 복잡성**: Configuration Name이 불필요하게 복잡
2. **계층 구조 혼란**: Model → Type → Configuration 구조가 실제 장비 구성과 맞지 않음
3. **UI/UX 문제**: 사용자가 어떤 조합을 선택해야 하는지 불명확
4. **데이터 관리 어려움**: 옵션이 너무 많아 관리가 어려움

## 📊 새로운 장비 구성 체계

### 1. 장비 구성 요소 정의

```
장비 = AE + Cabinet + EFEM + 옵션
```

#### AE (Atomic Element)
- **일체형 (Integrated)**: AE와 제어부가 통합
- **분리형 (Separated)**: AE와 제어부가 분리

#### Cabinet
- **T1**: 기본형 캐비닛
- **PB**: 고급형 캐비닛

#### EFEM (Equipment Front End Module)
- **Single**: 단일 포트
- **Double**: 이중 포트
- **None**: EFEM 없음

#### 옵션 (JSON 관리)
```json
{
  "wafer_size": "200mm",
  "chamber_count": 2,
  "auto_loader": true,
  "special_coating": "anti-reflective",
  "customer_options": {
    "feature_x": true,
    "custom_sensor": "type-A"
  }
}
```

### 2. 새로운 테이블 구조

#### Equipment_Models (유지)
```sql
CREATE TABLE Equipment_Models (
    id INTEGER PRIMARY KEY,
    model_name TEXT UNIQUE,  -- "NX-Hybrid WLI", "NX-Mask"
    description TEXT
);
```

#### Equipment_Configurations (재설계)
```sql
CREATE TABLE Equipment_Configurations (
    id INTEGER PRIMARY KEY,
    model_id INTEGER,
    
    -- 3가지 핵심 구성 요소
    ae_type TEXT CHECK(ae_type IN ('일체형', '분리형')),
    cabinet_type TEXT CHECK(cabinet_type IN ('T1', 'PB', NULL)),
    efem_type TEXT CHECK(efem_type IN ('Single', 'Double', 'None')),
    
    -- 자동 생성되는 구성 코드
    config_code TEXT GENERATED ALWAYS AS (
        model_id || '_' || ae_type || '_' || 
        COALESCE(cabinet_type, 'NC') || '_' || efem_type
    ) STORED,
    
    -- 옵션은 JSON으로
    options TEXT,  -- JSON
    
    -- 고객 특화
    is_customer_specific BOOLEAN DEFAULT 0,
    customer_name TEXT,
    
    FOREIGN KEY (model_id) REFERENCES Equipment_Models(id),
    UNIQUE(model_id, ae_type, cabinet_type, efem_type, customer_name)
);
```

#### Default_DB_Values (단순화)
```sql
CREATE TABLE Default_DB_Values (
    id INTEGER PRIMARY KEY,
    configuration_id INTEGER NOT NULL,
    
    parameter_name TEXT NOT NULL,
    default_value TEXT,
    
    -- 그룹핑을 위한 필드
    module TEXT,  -- "Temperature", "Pressure", "Motion"
    sub_module TEXT,  -- "Chamber1", "LoadLock"
    
    -- 메타데이터
    data_type TEXT,  -- "float", "int", "string", "bool"
    unit TEXT,  -- "℃", "Torr", "mm/s"
    
    FOREIGN KEY (configuration_id) REFERENCES Equipment_Configurations(id),
    UNIQUE(configuration_id, parameter_name)
);
```

## 🖥️ UI/UX 개선안

### 1. Default DB 관리 탭 재설계

```
┌─────────────────────────────────────────────────────┐
│ Default DB 관리                                     │
├─────────────────────────────────────────────────────┤
│ 모델 선택: [NX-Hybrid WLI ▼]                        │
│                                                      │
│ 구성 선택:                                          │
│   AE: [일체형 ▼]  Cabinet: [T1 ▼]  EFEM: [Single ▼]│
│                                                      │
│ [새 구성] [구성 복사] [구성 삭제]                    │
├─────────────────────────────────────────────────────┤
│ 파라미터 관리                                        │
│                                                      │
│ 모듈별 보기: [▼ Temperature (25)]                   │
│              [▶ Pressure (18)]                      │
│              [▶ Motion (32)]                        │
│                                                      │
│ Parameter Name     | Default | Unit | Type          │
│ ─────────────────────────────────────────────────── │
│ Temp.Chamber.Set   | 25.0    | ℃   | float        │
│ Temp.Chamber.Max   | 100.0   | ℃   | float        │
│ Temp.LoadLock.Set  | 23.0    | ℃   | float        │
│                                                      │
│ [파라미터 추가] [수정] [삭제] [일괄 가져오기]        │
└─────────────────────────────────────────────────────┘
```

### 2. 파라미터 추가/수정 다이얼로그

```
┌─────────────────────────────────────────┐
│ 파라미터 추가                           │
├─────────────────────────────────────────┤
│ 모듈: [Temperature ▼]                   │
│ 서브모듈: [Chamber1 ▼] [+새 서브모듈]   │
│                                          │
│ 파라미터명: [___________________]       │
│ 기본값: [___________]                   │
│ 단위: [℃ ▼]                            │
│ 타입: [float ▼]                         │
│                                          │
│ ☐ 모든 구성에 적용                      │
│ ☐ 현재 구성에만 적용                    │
│                                          │
│         [취소]  [확인]                   │
└─────────────────────────────────────────┤
```

## 🔧 기능 구현 우선순위

### Phase 1: 핵심 기능 (1주)
1. ✅ 테이블 구조 마이그레이션
2. ✅ 구성 선택 UI (AE/Cabinet/EFEM 드롭다운)
3. ✅ 파라미터 CRUD 기능
4. ✅ 모듈별 그룹핑 표시

### Phase 2: 편의 기능 (1주)
1. ⬜ 구성 복사 기능
2. ⬜ 일괄 가져오기/내보내기
3. ⬜ 파라미터 검색 및 필터
4. ⬜ 변경 이력 추적

### Phase 3: 고급 기능 (1주)
1. ⬜ 구성별 비교 뷰
2. ⬜ 파라미터 템플릿
3. ⬜ 버전 관리
4. ⬜ 권한별 접근 제어

## 📝 구현 코드 예시

### 1. 구성 선택 로직

```python
class DefaultDBManager:
    def __init__(self, db_schema):
        self.db_schema = db_schema
        self.current_config = None
        
    def get_configuration(self, model_id, ae_type, cabinet_type, efem_type):
        """특정 구성의 ID 조회 또는 생성"""
        config = self.db_schema.get_configuration(
            model_id=model_id,
            ae_type=ae_type,
            cabinet_type=cabinet_type,
            efem_type=efem_type
        )
        
        if not config:
            # 구성이 없으면 새로 생성
            config_id = self.db_schema.create_configuration(
                model_id=model_id,
                ae_type=ae_type,
                cabinet_type=cabinet_type,
                efem_type=efem_type
            )
            return config_id
        
        return config['id']
    
    def load_parameters(self, config_id):
        """구성의 파라미터 로드"""
        params = self.db_schema.get_default_values(config_id)
        
        # 모듈별로 그룹핑
        grouped = {}
        for param in params:
            module = param['module'] or 'General'
            if module not in grouped:
                grouped[module] = []
            grouped[module].append(param)
        
        return grouped
```

### 2. 파라미터 관리

```python
def add_parameter(self, config_id, param_data):
    """파라미터 추가"""
    # 중복 확인
    existing = self.db_schema.get_parameter(
        config_id=config_id,
        parameter_name=param_data['name']
    )
    
    if existing:
        raise ValueError(f"파라미터 '{param_data['name']}'가 이미 존재합니다.")
    
    # 추가
    self.db_schema.add_default_value(
        configuration_id=config_id,
        parameter_name=param_data['name'],
        default_value=param_data['value'],
        module=param_data['module'],
        sub_module=param_data['sub_module'],
        data_type=param_data['type'],
        unit=param_data['unit']
    )
    
    return True

def copy_configuration(self, source_config_id, target_ae, target_cabinet, target_efem):
    """구성 복사"""
    # 소스 파라미터 조회
    source_params = self.db_schema.get_default_values(source_config_id)
    
    # 타겟 구성 생성
    target_config_id = self.get_configuration(
        model_id=self.current_model_id,
        ae_type=target_ae,
        cabinet_type=target_cabinet,
        efem_type=target_efem
    )
    
    # 파라미터 복사
    for param in source_params:
        self.db_schema.add_default_value(
            configuration_id=target_config_id,
            parameter_name=param['parameter_name'],
            default_value=param['default_value'],
            module=param['module'],
            sub_module=param['sub_module'],
            data_type=param['data_type'],
            unit=param['unit']
        )
    
    return target_config_id
```

## 🎯 즉시 실행 가능한 개선사항

1. **Configuration Name 제거**: 자동 생성 코드 사용
2. **3가지 핵심 구성만 관리**: AE/Cabinet/EFEM
3. **옵션은 JSON으로**: 복잡한 옵션은 별도 관리
4. **모듈별 그룹 표시**: 파라미터를 모듈별로 묶어서 표시
5. **구성 복사 기능**: 비슷한 구성을 쉽게 생성

이렇게 단순화하면 사용자가 이해하기 쉽고 관리도 편해집니다.