# QC 검수와 Default DB 분리 계획

## 🎯 설계 목표

1. **Default DB**: 순수한 장비 파라미터 설정값만 관리
2. **QC Spec Master**: 모든 QC 검사 기준 중앙 관리
3. **자동 매칭**: ItemName 기반으로 자동 연결
4. **유지보수 최소화**: 한 곳에서만 관리

## 📊 새로운 테이블 구조

### 1. Default_DB_Values (수정)
```sql
-- Min/Max Spec 제거, 순수 설정값만
CREATE TABLE Default_DB_Values (
    id INTEGER PRIMARY KEY,
    configuration_id INTEGER NOT NULL,
    parameter_name TEXT NOT NULL,  -- ItemName
    default_value TEXT,             -- 설정값
    
    -- 분류용 메타데이터
    module TEXT,
    sub_module TEXT,
    data_type TEXT,
    unit TEXT,
    
    -- 설명
    description TEXT,
    
    FOREIGN KEY (configuration_id) REFERENCES Equipment_Configurations(id),
    UNIQUE(configuration_id, parameter_name)
);
```

### 2. QC_Spec_Master (신규)
```sql
-- 모든 QC 검사 기준 중앙 관리
CREATE TABLE QC_Spec_Master (
    id INTEGER PRIMARY KEY,
    item_name TEXT NOT NULL UNIQUE,  -- 매칭 키
    
    -- 스펙 정보
    min_spec TEXT,
    max_spec TEXT,
    expected_value TEXT,  -- 'PASS', 'ON' 등
    
    -- 검사 타입
    check_type TEXT CHECK(check_type IN ('range', 'exact', 'boolean', 'exists')),
    
    -- 분류
    category TEXT,  -- 'Safety', 'Process', 'Performance'
    severity TEXT CHECK(severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
    
    -- 상태
    is_active BOOLEAN DEFAULT 1,
    is_common BOOLEAN DEFAULT 1,  -- 공통 항목 여부
    
    -- 설명
    description TEXT,
    validation_rule TEXT,  -- JSON 형식 추가 규칙
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. QC_Equipment_Exceptions (개선)
```sql
-- 특정 장비/구성에서 제외할 QC 항목
CREATE TABLE QC_Equipment_Exceptions (
    id INTEGER PRIMARY KEY,
    configuration_id INTEGER,  -- NULL이면 전체 모델 적용
    model_id INTEGER,          -- NULL이면 configuration만 적용
    spec_master_id INTEGER NOT NULL,
    
    reason TEXT NOT NULL,
    approved_by TEXT,
    
    FOREIGN KEY (spec_master_id) REFERENCES QC_Spec_Master(id),
    UNIQUE(configuration_id, model_id, spec_master_id)
);
```

### 4. QC_Spec_Overrides (신규)
```sql
-- 특정 장비/구성의 스펙 오버라이드
CREATE TABLE QC_Spec_Overrides (
    id INTEGER PRIMARY KEY,
    spec_master_id INTEGER NOT NULL,
    configuration_id INTEGER,
    
    -- 오버라이드 값
    min_spec_override TEXT,
    max_spec_override TEXT,
    expected_value_override TEXT,
    
    reason TEXT,
    approved_by TEXT,
    
    FOREIGN KEY (spec_master_id) REFERENCES QC_Spec_Master(id),
    FOREIGN KEY (configuration_id) REFERENCES Equipment_Configurations(id),
    UNIQUE(spec_master_id, configuration_id)
);
```

## 🔄 워크플로우

### Default DB 관리 (단순화)
```python
class DefaultDBManager:
    def add_parameter(self, config_id, param_name, value):
        """순수 파라미터 값만 저장"""
        # Min/Max 스펙 없음
        # 단순 설정값만 관리
        self.db.add_default_value(
            configuration_id=config_id,
            parameter_name=param_name,
            default_value=value,
            module=self.detect_module(param_name)
        )
```

### QC Spec 관리 (중앙화)
```python
class QCSpecManager:
    def add_spec(self, item_name, min_spec, max_spec, category='General'):
        """QC 스펙 중앙 등록"""
        self.db.add_qc_spec(
            item_name=item_name,
            min_spec=min_spec,
            max_spec=max_spec,
            check_type='range',
            category=category,
            is_common=True  # 기본적으로 모든 장비 적용
        )
    
    def add_exception(self, config_id, item_name, reason):
        """특정 구성에서 제외"""
        spec_id = self.get_spec_id(item_name)
        self.db.add_exception(
            configuration_id=config_id,
            spec_master_id=spec_id,
            reason=reason
        )
```

### QC 검수 (자동 매칭)
```python
class QCInspection:
    def inspect(self, config_id, file_data):
        """파일 데이터 QC 검수"""
        results = []
        
        # 1. 파일의 ItemName 추출
        file_items = file_data.keys()
        
        # 2. QC Spec Master에서 매칭되는 항목 조회
        specs = self.get_active_specs_for_items(file_items)
        
        # 3. 예외 항목 제외
        exceptions = self.get_exceptions(config_id)
        specs = [s for s in specs if s.id not in exceptions]
        
        # 4. 오버라이드 적용
        overrides = self.get_overrides(config_id)
        for spec in specs:
            if spec.id in overrides:
                spec.apply_override(overrides[spec.id])
        
        # 5. 검사 실행
        for spec in specs:
            item_name = spec.item_name
            if item_name in file_data:
                value = file_data[item_name]
                result = self.check_value(value, spec)
                results.append({
                    'item_name': item_name,
                    'value': value,
                    'spec': f"{spec.min_spec}~{spec.max_spec}",
                    'pass': result,
                    'severity': spec.severity
                })
        
        return results
```

## 📋 구현 단계

### Phase 1: 데이터베이스 마이그레이션 (1일)
1. ✅ QC_Spec_Master 테이블 생성
2. ✅ 기존 Default_DB_Values의 min/max_spec → QC_Spec_Master로 이동
3. ✅ Default_DB_Values에서 spec 컬럼 제거
4. ✅ QC_Equipment_Exceptions 테이블 개선

### Phase 2: 서비스 레이어 수정 (2일)
1. ⬜ DefaultDBService: spec 관련 코드 제거
2. ⬜ QCSpecService: 신규 생성
3. ⬜ QCInspectionService: ItemName 매칭 로직 구현

### Phase 3: UI 수정 (2일)
1. ⬜ Default DB 탭: Min/Max 입력 필드 제거
2. ⬜ QC Spec 관리 탭: 신규 추가
3. ⬜ QC 검수 탭: 새로운 로직 적용

## 🎯 장점

### 1. **유지보수성 향상**
- QC 항목 추가: 한 곳에서만 추가하면 모든 장비 적용
- 스펙 변경: 중앙에서 한 번만 수정

### 2. **데이터 일관성**
- 중복 제거: 같은 스펙을 여러 곳에 저장하지 않음
- 표준화: 모든 장비가 동일한 QC 기준 사용

### 3. **유연성**
- 예외 처리: 특정 장비만 제외 가능
- 오버라이드: 특정 장비만 다른 스펙 적용 가능

### 4. **성능**
- ItemName 인덱스로 빠른 매칭
- 캐싱으로 반복 조회 최적화

## 📊 UI 레이아웃

### Default DB 관리 탭 (단순화)
```
┌─────────────────────────────────────────┐
│ 장비 구성: 일체형 / T1 / Single         │
├─────────────────────────────────────────┤
│ Parameter Name    | Default Value | Unit │
│ ──────────────────────────────────────── │
│ Temp.Chamber.Set  | 25.0         | ℃   │
│ Pressure.Main     | 1.0e-5       | Torr │
│ (Min/Max 스펙 필드 제거됨)               │
└─────────────────────────────────────────┘
```

### QC Spec 관리 탭 (신규)
```
┌─────────────────────────────────────────┐
│ QC Spec Master                          │
├─────────────────────────────────────────┤
│ [검색: ________] [카테고리: 전체 ▼]     │
├─────────────────────────────────────────┤
│ ItemName          | Min  | Max  | Type  │
│ ──────────────────────────────────────── │
│ Temp.Chamber.Set  | 20   | 30   | CRIT  │
│ Pressure.Main     | 1e-6 | 1e-4 | HIGH  │
│                                          │
│ [추가] [수정] [삭제] [일괄 가져오기]     │
└─────────────────────────────────────────┘
```

### QC 검수 결과 (개선)
```
┌─────────────────────────────────────────┐
│ QC 검수 결과                            │
├─────────────────────────────────────────┤
│ 총 검사: 150개 (파일 항목)              │
│ QC 매칭: 45개 (QC Spec 존재)            │
│ 통과: 43개, 실패: 2개                   │
├─────────────────────────────────────────┤
│ ItemName          | Value | Spec | Pass │
│ ──────────────────────────────────────── │
│ Temp.Chamber.Set  | 35    | 20~30| ❌   │
│ Pressure.Main     | 1e-5  | ~1e-4| ✅   │
└─────────────────────────────────────────┘
```

## 🔧 마이그레이션 스크립트

```python
def migrate_specs_to_master():
    """기존 Default_DB의 스펙을 QC_Spec_Master로 이동"""
    
    # 1. 모든 unique parameter_name과 spec 조회
    query = """
    SELECT DISTINCT parameter_name, min_spec, max_spec
    FROM Default_DB_Values
    WHERE min_spec IS NOT NULL OR max_spec IS NOT NULL
    """
    
    specs = db.execute_query(query)
    
    # 2. QC_Spec_Master에 삽입
    for param_name, min_spec, max_spec in specs:
        # 카테고리 추론
        category = 'General'
        if 'Temp' in param_name:
            category = 'Temperature'
        elif 'Pressure' in param_name:
            category = 'Pressure'
        elif 'Safety' in param_name:
            category = 'Safety'
            
        # severity 추론
        severity = 'MEDIUM'
        if 'Safety' in param_name or 'Limit' in param_name:
            severity = 'CRITICAL'
        elif 'Process' in param_name:
            severity = 'HIGH'
            
        db.execute_insert("""
            INSERT OR IGNORE INTO QC_Spec_Master
            (item_name, min_spec, max_spec, check_type, category, severity)
            VALUES (?, ?, ?, 'range', ?, ?)
        """, (param_name, min_spec, max_spec, category, severity))
    
    # 3. Default_DB_Values에서 spec 컬럼 제거
    # SQLite는 ALTER TABLE DROP COLUMN 미지원
    # 새 테이블 생성 후 데이터 복사 필요
    
    print(f"✅ {len(specs)}개 스펙을 QC_Spec_Master로 이동 완료")
```

## ✅ 예상 효과

### Before (현재)
- QC 항목 추가 시: 10개 장비 × 3개 구성 = 30번 수정
- 스펙 변경 시: 모든 장비 개별 수정
- 데이터 중복: 같은 스펙이 여러 곳에 저장

### After (개선)
- QC 항목 추가 시: 1번만 추가
- 스펙 변경 시: 1번만 수정
- 데이터 중복: 제로

## 🚀 실행 계획

1. **백업**: 현재 데이터베이스 백업
2. **마이그레이션**: 스펙 데이터 이동
3. **서비스 수정**: 분리된 로직 구현
4. **UI 업데이트**: 새로운 탭과 기능
5. **테스트**: 기존 기능 동작 확인
6. **문서화**: 사용자 가이드 업데이트

이렇게 분리하면 장기적으로 유지보수가 훨씬 쉬워지고, 사용자도 헷갈리지 않습니다.