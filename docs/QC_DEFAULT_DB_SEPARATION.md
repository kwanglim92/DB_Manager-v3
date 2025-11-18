# QC 검수와 Default DB 완전 분리 설계

## 🎯 핵심 개념

### 역할 분리
- **Default DB**: 장비 구성별 **기본값(Cal 값)**만 관리
- **QC Checklist**: 모든 **검증 기준(Spec)**을 중앙 관리

## 📊 테이블 구조 재설계

### 1. Default_DB_Values (Spec 제거)
```sql
CREATE TABLE Default_DB_Values (
    id INTEGER PRIMARY KEY,
    configuration_id INTEGER NOT NULL,
    parameter_name TEXT NOT NULL,
    default_value TEXT,  -- Cal 값만 저장
    -- min_spec, max_spec 제거!
    module TEXT,
    sub_module TEXT,
    data_type TEXT,
    unit TEXT,
    FOREIGN KEY (configuration_id) REFERENCES Equipment_Configurations(id),
    UNIQUE(configuration_id, parameter_name)
);
```

### 2. QC_Master_Specs (신규 - 중앙 Spec 관리)
```sql
CREATE TABLE QC_Master_Specs (
    id INTEGER PRIMARY KEY,
    item_name TEXT NOT NULL UNIQUE,  -- 파라미터명 (ItemName)
    
    -- Spec 정보
    min_spec TEXT,
    max_spec TEXT,
    expected_value TEXT,  -- 'PASS', 'FAIL', 'ON', 'OFF' 등
    
    -- 분류
    category TEXT,  -- 'Safety', 'Temperature', 'Pressure', 'Motion'
    subcategory TEXT,  -- 'Critical', 'Performance', 'General'
    
    -- 검증 타입
    check_type TEXT CHECK(check_type IN ('range', 'exact', 'boolean', 'pattern')),
    
    -- 메타데이터
    description TEXT,
    is_active BOOLEAN DEFAULT 1,
    is_common BOOLEAN DEFAULT 1,  -- 장비 공통 항목
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. QC_Equipment_Overrides (장비별 예외)
```sql
CREATE TABLE QC_Equipment_Overrides (
    id INTEGER PRIMARY KEY,
    equipment_type_id INTEGER,  -- NULL이면 모델 전체
    configuration_id INTEGER,    -- NULL이면 타입 전체
    spec_id INTEGER NOT NULL,
    
    -- Override 값 (NULL이면 기본값 사용)
    override_min_spec TEXT,
    override_max_spec TEXT,
    override_expected_value TEXT,
    
    -- 비활성화 옵션
    is_excluded BOOLEAN DEFAULT 0,  -- 이 장비에서는 검사 안 함
    
    reason TEXT,
    approved_by TEXT,
    
    FOREIGN KEY (spec_id) REFERENCES QC_Master_Specs(id),
    UNIQUE(equipment_type_id, configuration_id, spec_id)
);
```

## 🔧 QC 검수 워크플로우

### 1. 파일 로드
```python
def load_qc_file(file_path):
    """QC 검수할 파일 로드"""
    # CSV/Excel/Text 파일 파싱
    data = parse_file(file_path)
    
    # ItemName과 Value 추출
    parameters = {}
    for row in data:
        item_name = row['ItemName']
        value = row['Value']
        parameters[item_name] = value
    
    return parameters
```

### 2. Spec 매칭 및 검증
```python
class QCValidator:
    def __init__(self, db_schema):
        self.db_schema = db_schema
        self.specs_cache = {}
        
    def validate_parameters(self, parameters: Dict, 
                           equipment_type_id: int = None,
                           configuration_id: int = None) -> Dict:
        """
        파라미터 검증
        
        Args:
            parameters: {ItemName: Value} 딕셔너리
            equipment_type_id: 장비 타입 (옵션)
            configuration_id: 구성 ID (옵션)
        """
        results = {
            'passed': [],
            'failed': [],
            'skipped': [],
            'summary': {}
        }
        
        # 1. Master Spec 조회
        master_specs = self.get_master_specs()
        
        # 2. Override 조회 (있다면)
        overrides = {}
        if equipment_type_id or configuration_id:
            overrides = self.get_overrides(equipment_type_id, configuration_id)
        
        # 3. 각 파라미터 검증
        for item_name, value in parameters.items():
            # Spec 찾기
            spec = self.find_spec(item_name, master_specs, overrides)
            
            if not spec:
                results['skipped'].append({
                    'item_name': item_name,
                    'value': value,
                    'reason': 'No spec defined'
                })
                continue
            
            # 검증 수행
            is_valid = self.check_value(value, spec)
            
            result_entry = {
                'item_name': item_name,
                'value': value,
                'spec': spec,
                'is_valid': is_valid
            }
            
            if is_valid:
                results['passed'].append(result_entry)
            else:
                results['failed'].append(result_entry)
        
        # 4. 요약 생성
        results['summary'] = {
            'total': len(parameters),
            'passed': len(results['passed']),
            'failed': len(results['failed']),
            'skipped': len(results['skipped']),
            'pass_rate': len(results['passed']) / len(parameters) * 100 if parameters else 0
        }
        
        return results
    
    def find_spec(self, item_name: str, master_specs: Dict, overrides: Dict):
        """ItemName에 해당하는 Spec 찾기"""
        # 1. Override 확인
        if item_name in overrides:
            if overrides[item_name].get('is_excluded'):
                return None  # 이 항목은 검사 안 함
            return overrides[item_name]
        
        # 2. Master Spec 확인
        if item_name in master_specs:
            return master_specs[item_name]
        
        # 3. 패턴 매칭 (정규식)
        for spec_name, spec in master_specs.items():
            if self.match_pattern(item_name, spec.get('pattern')):
                return spec
        
        return None
    
    def check_value(self, value, spec):
        """값 검증"""
        check_type = spec.get('check_type', 'range')
        
        if check_type == 'range':
            # 범위 검증
            try:
                val = float(value)
                min_spec = float(spec['min_spec']) if spec.get('min_spec') else None
                max_spec = float(spec['max_spec']) if spec.get('max_spec') else None
                
                if min_spec is not None and val < min_spec:
                    return False
                if max_spec is not None and val > max_spec:
                    return False
                return True
            except:
                return False
                
        elif check_type == 'exact':
            # 정확한 값 비교
            return str(value).upper() == str(spec['expected_value']).upper()
            
        elif check_type == 'boolean':
            # Boolean 검증 (0/1, ON/OFF, TRUE/FALSE)
            value_str = str(value).upper()
            expected = str(spec['expected_value']).upper()
            
            true_values = ['1', 'ON', 'TRUE', 'ENABLE', 'ENABLED']
            false_values = ['0', 'OFF', 'FALSE', 'DISABLE', 'DISABLED']
            
            if expected in true_values:
                return value_str in true_values
            elif expected in false_values:
                return value_str in false_values
            else:
                return value_str == expected
                
        elif check_type == 'pattern':
            # 정규식 패턴 매칭
            import re
            pattern = spec.get('expected_value', '')
            return bool(re.match(pattern, str(value)))
            
        return True
```

## 🖥️ UI 분리

### QC Master Spec 관리 화면
```
┌─────────────────────────────────────────────┐
│ QC Master Spec 관리                         │
├─────────────────────────────────────────────┤
│ [검색: ___________] [카테고리: 전체 ▼]      │
├─────────────────────────────────────────────┤
│ ItemName           | Min  | Max  | Type     │
│ ─────────────────────────────────────────── │
│ Temp.Chamber.Set   | 20   | 30   | range    │
│ Safety.Emergency   | -    | PASS | exact    │
│ Pressure.Vacuum    | -    | 1e-5 | range    │
│ Motion.Speed       | 0    | 100  | range    │
├─────────────────────────────────────────────┤
│ [추가] [수정] [삭제] [일괄 가져오기]         │
└─────────────────────────────────────────────┘
```

### QC 검수 화면
```
┌─────────────────────────────────────────────┐
│ QC 검수                                     │
├─────────────────────────────────────────────┤
│ 파일: [선택...] 또는 [폴더 선택]            │
│ 장비: [선택 안 함 ▼] (공통 Spec만 사용)     │
├─────────────────────────────────────────────┤
│ [검수 시작]                                  │
├─────────────────────────────────────────────┤
│ 결과:                                        │
│ ✅ PASS: 95개 (89%)                         │
│ ❌ FAIL: 10개 (9%)                          │
│ ⏭️ SKIP: 2개 (2%)                           │
│                                              │
│ 상세 내역:                                   │
│ ItemName         | Value | Spec   | Result  │
│ Temp.Chamber.Set | 25    | 20-30  | ✅ PASS │
│ Pressure.Vacuum  | 2e-4  | <1e-5  | ❌ FAIL │
└─────────────────────────────────────────────┘
```

## 🎯 장점

### 1. 중앙 관리
- Spec 한 곳에서만 관리
- 업데이트가 모든 장비에 즉시 반영
- 일관성 보장

### 2. 유연성
- 장비별 Override 가능
- 특정 항목 제외 가능
- 다양한 검증 타입 지원

### 3. 단순성
- Default DB는 Cal 값만
- QC는 Spec만
- 역할이 명확

## 📝 마이그레이션 계획

### Step 1: 기존 Spec 추출
```python
def migrate_specs_to_master():
    """기존 Default_DB_Values의 Spec을 Master로 이동"""
    
    # 모든 Spec 수집
    specs = {}
    rows = db.execute("SELECT DISTINCT parameter_name, min_spec, max_spec FROM Default_DB_Values WHERE min_spec IS NOT NULL OR max_spec IS NOT NULL")
    
    for param_name, min_spec, max_spec in rows:
        if param_name not in specs:
            specs[param_name] = {
                'min_spec': min_spec,
                'max_spec': max_spec,
                'check_type': 'range'
            }
    
    # Master Spec 테이블에 삽입
    for item_name, spec in specs.items():
        db.execute("""
            INSERT INTO QC_Master_Specs 
            (item_name, min_spec, max_spec, check_type, category)
            VALUES (?, ?, ?, ?, ?)
        """, (item_name, spec['min_spec'], spec['max_spec'], 'range', 'General'))
    
    # Default_DB_Values에서 Spec 컬럼 제거
    # (새 테이블 생성 후 데이터 복사)
```

### Step 2: UI 분리
- Default DB 탭에서 Min/Max Spec 입력 제거
- QC Master Spec 관리 탭 추가
- QC 검수 탭 수정 (Master Spec 사용)

### Step 3: 서비스 분리
- DefaultDBService: Cal 값만
- QCSpecService: Spec 관리
- QCValidator: 검증 로직

## 🚀 구현 우선순위

1. **즉시 (1일)**
   - QC_Master_Specs 테이블 생성
   - 기존 Spec 마이그레이션
   
2. **단기 (3일)**
   - QCValidator 클래스 구현
   - QC Master Spec 관리 UI
   
3. **중기 (1주)**
   - Override 기능
   - 일괄 가져오기/내보내기
   - 검증 리포트

이렇게 분리하면 관리가 훨씬 편하고, 확장성도 좋아집니다!