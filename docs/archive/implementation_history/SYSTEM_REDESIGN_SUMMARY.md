# 시스템 재설계 통합 계획서

**작성일**: 2025-11-17
**목적**: Default DB 관리 단순화 및 QC 검수 분리

## 🎯 핵심 목표

1. **Default DB 단순화**: 복잡한 Configuration을 AE/Cabinet/EFEM 3요소로 단순화
2. **QC/DB 분리**: Min/Max Spec을 Default DB에서 분리하여 QC 전용 테이블로 이동
3. **유지보수성 향상**: 중복 제거, 중앙 관리로 관리 포인트 최소화

## 📊 주요 변경사항

### 1. Default DB 관리 시스템 재설계

#### Before (현재 문제)
- Configuration Name이 복잡하고 관리 어려움
- 장비 구성이 실제와 맞지 않음
- UI가 혼란스러움

#### After (개선)
- **3요소 구성**: AE (일체형/분리형) + Cabinet (T1/PB/없음) + EFEM (Single/Double/None)
- **자동 코드 생성**: M1_I_T1_S (Model1, 일체형, T1, Single)
- **옵션 JSON 관리**: 복잡한 옵션은 별도 JSON으로

### 2. QC와 Default DB 분리

#### Before (현재 문제)
- Default_DB_Values에 min_spec, max_spec 포함
- QC 항목 추가 시 모든 장비에 개별 등록 필요
- 데이터 중복 심각

#### After (개선)
- **Default_DB_Values**: 순수 설정값만 (min/max spec 제거)
- **QC_Spec_Master**: 모든 QC 스펙 중앙 관리
- **ItemName 매칭**: 자동으로 QC 스펙 연결

## 🏗️ 새로운 아키텍처

### 테이블 구조

```sql
-- 1. Equipment_Configurations (재설계)
CREATE TABLE Equipment_Configurations (
    id INTEGER PRIMARY KEY,
    model_id INTEGER,
    ae_type TEXT CHECK(ae_type IN ('일체형', '분리형')),
    cabinet_type TEXT CHECK(cabinet_type IN ('T1', 'PB', NULL)),
    efem_type TEXT CHECK(efem_type IN ('Single', 'Double', 'None')),
    config_code TEXT,  -- 자동 생성: M1_I_T1_S
    options TEXT,      -- JSON: {"wafer_size": "200mm", ...}
    UNIQUE(model_id, ae_type, cabinet_type, efem_type)
);

-- 2. Default_DB_Values (수정: spec 제거)
CREATE TABLE Default_DB_Values (
    id INTEGER PRIMARY KEY,
    configuration_id INTEGER,
    parameter_name TEXT,  -- ItemName
    default_value TEXT,   -- 설정값만
    module TEXT,
    sub_module TEXT,
    data_type TEXT,
    unit TEXT,
    -- min_spec, max_spec 제거!
);

-- 3. QC_Spec_Master (신규: QC 스펙 중앙 관리)
CREATE TABLE QC_Spec_Master (
    id INTEGER PRIMARY KEY,
    item_name TEXT UNIQUE,  -- ItemName으로 매칭
    min_spec TEXT,
    max_spec TEXT,
    expected_value TEXT,
    check_type TEXT,  -- 'range', 'exact', 'boolean'
    category TEXT,    -- 'Safety', 'Process', 'Performance'
    severity TEXT,    -- 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    is_active BOOLEAN DEFAULT 1
);
```

## 📈 개선 효과

| 측면 | Before | After | 개선율 |
|------|--------|-------|--------|
| **Configuration 관리** | 복잡한 이름 수동 입력 | 3개 드롭다운 선택 | 80% 간소화 |
| **QC 항목 추가** | 30번 (10장비×3구성) | 1번 | 97% 감소 |
| **스펙 변경** | 모든 장비 개별 수정 | 1곳에서만 수정 | 95% 감소 |
| **데이터 중복** | 높음 | 없음 | 100% 제거 |
| **유지보수 시간** | 시간당 5개 항목 | 시간당 50개 항목 | 10배 향상 |

## 🔧 구현 계획

### Phase 1: 데이터베이스 재구조화 (Day 1)
- [x] 새로운 테이블 설계
- [ ] 마이그레이션 스크립트 작성
- [ ] 기존 데이터 백업
- [ ] 테이블 생성 및 데이터 이동

### Phase 2: 서비스 레이어 구현 (Day 2-3)
- [x] DefaultDBService 작성
- [ ] QCSpecService 작성
- [ ] 기존 서비스 수정
- [ ] 테스트 코드 작성

### Phase 3: UI 개선 (Day 4-5)
- [x] DefaultDBConfigDialog 작성
- [ ] QC Spec 관리 UI 추가
- [ ] Default DB 탭 수정
- [ ] QC 검수 탭 수정

### Phase 4: 통합 및 테스트 (Day 6-7)
- [ ] 전체 통합
- [ ] 기능 테스트
- [ ] 성능 테스트
- [ ] 사용자 피드백

## 💡 핵심 기능

### Default DB 관리
```python
# 구성 선택 (3개 드롭다운)
config = select_configuration(
    ae_type="일체형",
    cabinet_type="T1", 
    efem_type="Single"
)

# 파라미터 추가 (스펙 없이)
add_parameter(
    name="Temp.Chamber.Set",
    value="25.0",
    module="Temperature"
)
```

### QC Spec 관리
```python
# QC 스펙 추가 (한 번만)
add_qc_spec(
    item_name="Temp.Chamber.Set",
    min_spec="20",
    max_spec="30",
    category="Temperature",
    severity="CRITICAL"
)

# 자동 적용: 모든 장비에서 이 ItemName 사용 시 자동 검사
```

### QC 검수
```python
# ItemName 기반 자동 매칭
def qc_inspection(file_data):
    for item_name, value in file_data.items():
        if spec := get_qc_spec(item_name):  # 자동 매칭
            if not check_range(value, spec.min, spec.max):
                fail(item_name, value, spec)
```

## ⚠️ 주의사항

1. **데이터 백업 필수**: 마이그레이션 전 반드시 백업
2. **단계적 적용**: 한 번에 모두 변경하지 말고 단계적으로
3. **사용자 교육**: 새로운 UI와 개념 설명 필요
4. **호환성**: 기존 데이터와의 호환성 유지

## 📊 성공 지표

- [ ] Configuration 생성 시간 50% 단축
- [ ] QC 항목 관리 시간 90% 단축
- [ ] 사용자 만족도 향상
- [ ] 데이터 일관성 100% 달성
- [ ] 중복 데이터 0%

## 🚀 다음 단계

1. **즉시**: 데이터베이스 백업 및 마이그레이션 스크립트 실행
2. **Day 1-2**: 서비스 레이어 통합
3. **Day 3-4**: UI 수정 및 테스트
4. **Day 5**: 프로덕션 배포

---

**결론**: 이 재설계로 시스템이 훨씬 단순하고 관리하기 쉬워지며, 특히 QC 항목 관리가 획기적으로 개선됩니다.