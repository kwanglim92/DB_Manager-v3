# Default DB 관리 시스템 구현 계획

## 📋 현황 및 문제점

### 현재 상황
1. **복잡한 Configuration**: Configuration Name이 불필요하게 복잡
2. **혼란스러운 UI**: 어떤 조합을 선택해야 할지 불명확
3. **미완성 기능**: 많은 기능이 부분적으로만 구현됨
4. **데이터 구조 문제**: 실제 장비 구성과 맞지 않는 테이블 구조

### 핵심 문제
- **장비 구성 = AE + Cabinet + EFEM**인데 현재 시스템은 이를 제대로 반영하지 못함
- 옵션이 너무 많아서 Configuration으로 관리하기 어려움

## 🎯 개선 방향

### 1. 장비 구성 체계 단순화

```
기존: Model → Type → Configuration (복잡한 이름)
개선: Model → AE타입 → Cabinet타입 → EFEM타입 (드롭다운 선택)
```

### 2. 구성 요소 정의

#### 핵심 3요소
- **AE**: 일체형 / 분리형
- **Cabinet**: T1 / PB / 없음  
- **EFEM**: Single / Double / None

#### 추가 옵션 (JSON)
- Wafer 크기
- Chamber 수
- Auto Loader
- 고객별 커스터마이징

## 📁 구현된 파일

### 1. **DefaultDBService** (`src/app/services/default_db_service.py`)
- 장비 구성 관리 서비스
- 구성 코드 자동 생성 (M1_I_T1_S = Model1, 일체형, T1, Single)
- 파라미터 CRUD
- 구성 복사 기능
- 파일 가져오기/내보내기

### 2. **DefaultDBConfigDialog** (`src/app/dialogs/default_db_config_dialog.py`)
- 구성 선택 UI
- AE/Cabinet/EFEM 드롭다운
- 옵션 설정
- 구성 복사 다이얼로그

## 🔧 통합 방법

### Step 1: 서비스 초기화
```python
from app.services.default_db_service import DefaultDBService

# manager.py의 __init__에 추가
self.default_db_service = DefaultDBService(self.db_schema)
```

### Step 2: UI 통합
```python
from app.dialogs.default_db_config_dialog import DefaultDBConfigDialog

def open_config_dialog(self):
    """구성 선택 다이얼로그 열기"""
    model_id = self.get_selected_model_id()
    model_name = self.get_selected_model_name()
    
    dialog = DefaultDBConfigDialog(
        self.window,
        self.default_db_service,
        model_id,
        model_name,
        on_config_selected=self.on_config_selected
    )
    
def on_config_selected(self, config_id):
    """구성 선택 시 처리"""
    # 파라미터 로드
    params = self.default_db_service.get_parameters_grouped(config_id)
    
    # TreeView 업데이트
    self.update_parameter_tree(params)
```

### Step 3: 파라미터 관리 개선
```python
def add_parameter(self):
    """파라미터 추가 (개선)"""
    if not self.current_config_id:
        messagebox.showwarning("경고", "먼저 구성을 선택하세요.")
        return
    
    # 다이얼로그 표시
    param_data = self.show_parameter_dialog()
    
    if param_data:
        try:
            self.default_db_service.add_parameter(
                self.current_config_id, 
                param_data
            )
            self.refresh_parameters()
        except ValueError as e:
            messagebox.showerror("오류", str(e))
```

## 📊 UI 레이아웃 개선안

### 메인 Default DB 탭
```
┌────────────────────────────────────────────┐
│ 모델: [NX-Hybrid WLI ▼]  [구성 선택]       │
│ 현재 구성: 일체형 / T1 / Single            │
├────────────────────────────────────────────┤
│ [검색: ___________] [모듈: 전체 ▼]         │
├────────────────────────────────────────────┤
│ ▼ Temperature (25개)                       │
│   Temp.Chamber.Set     25.0℃    float     │
│   Temp.Chamber.Max     100.0℃   float     │
│ ▶ Pressure (18개)                          │
│ ▶ Motion (32개)                            │
├────────────────────────────────────────────┤
│ [추가] [수정] [삭제] [가져오기] [내보내기]  │
└────────────────────────────────────────────┘
```

## 🚀 구현 우선순위

### 즉시 가능 (1일)
1. ✅ DefaultDBService 통합
2. ✅ 구성 선택 다이얼로그 연결
3. ✅ 파라미터 추가/수정/삭제 개선

### 단기 (3일)
1. ⬜ 모듈별 그룹핑 TreeView
2. ⬜ 파일 가져오기/내보내기
3. ⬜ 구성 복사 기능

### 중기 (1주)
1. ⬜ 파라미터 검색 및 필터
2. ⬜ 변경 이력 추적
3. ⬜ 구성별 비교 뷰

## 📝 데이터베이스 마이그레이션

### 테이블 수정 SQL
```sql
-- Equipment_Configurations 재설계
ALTER TABLE Equipment_Configurations 
ADD COLUMN ae_type TEXT CHECK(ae_type IN ('일체형', '분리형'));

ALTER TABLE Equipment_Configurations 
ADD COLUMN cabinet_type TEXT CHECK(cabinet_type IN ('T1', 'PB', NULL));

ALTER TABLE Equipment_Configurations 
ADD COLUMN efem_type TEXT CHECK(efem_type IN ('Single', 'Double', 'None'));

-- config_code 자동 생성 (SQLite는 GENERATED 미지원, 트리거 사용)
CREATE TRIGGER generate_config_code
AFTER INSERT ON Equipment_Configurations
BEGIN
    UPDATE Equipment_Configurations 
    SET config_code = 'M' || NEW.model_id || '_' || 
                     CASE NEW.ae_type 
                         WHEN '일체형' THEN 'I' 
                         ELSE 'S' 
                     END || '_' ||
                     COALESCE(NEW.cabinet_type, 'NC') || '_' ||
                     CASE NEW.efem_type
                         WHEN 'Single' THEN 'S'
                         WHEN 'Double' THEN 'D'
                         ELSE 'N'
                     END
    WHERE id = NEW.id;
END;
```

### 기존 데이터 마이그레이션
```python
def migrate_existing_configurations():
    """기존 Configuration 데이터 마이그레이션"""
    
    # 기존 데이터 조회
    old_configs = db_schema.execute_query(
        "SELECT id, config_name FROM Equipment_Configurations"
    )
    
    for config_id, config_name in old_configs:
        # config_name 파싱하여 ae_type, cabinet_type, efem_type 추출
        # 예: "Single Port 150mm" → ae_type='일체형', efem_type='Single'
        
        ae_type = '일체형'  # 기본값
        cabinet_type = 'T1'  # 기본값
        efem_type = 'Single'  # 기본값
        
        if 'Double' in config_name:
            efem_type = 'Double'
        if '분리' in config_name:
            ae_type = '분리형'
            
        # 업데이트
        db_schema.execute_update("""
            UPDATE Equipment_Configurations 
            SET ae_type=?, cabinet_type=?, efem_type=?
            WHERE id=?
        """, (ae_type, cabinet_type, efem_type, config_id))
```

## ✅ 예상 효과

1. **사용성 향상**: 3개 드롭다운으로 구성 선택 완료
2. **관리 편의성**: 구성 코드 자동 생성으로 실수 방지
3. **확장성**: 옵션은 JSON으로 관리하여 유연성 확보
4. **성능**: 모듈별 그룹핑으로 대량 파라미터도 빠르게 표시

## 🔍 테스트 시나리오

### 1. 구성 생성 테스트
```python
# 새 구성 생성
config_id = default_db_service.get_or_create_configuration(
    model_id=1,
    ae_type='일체형',
    cabinet_type='T1',
    efem_type='Single'
)
assert config_id > 0
```

### 2. 파라미터 관리 테스트
```python
# 파라미터 추가
success = default_db_service.add_parameter(config_id, {
    'name': 'Test.Param',
    'value': '100',
    'module': 'Test',
    'data_type': 'int'
})
assert success == True

# 파라미터 조회
params = default_db_service.get_parameters_grouped(config_id)
assert 'Test' in params
```

### 3. 구성 복사 테스트
```python
# 구성 복사
new_config_id = default_db_service.copy_configuration(
    source_config_id=config_id,
    target_model_id=1,
    target_ae='분리형',
    target_cabinet='PB',
    target_efem='Double'
)
assert new_config_id != config_id
```

---

이 계획대로 진행하면 Default DB 관리가 훨씬 체계적이고 사용하기 쉬워질 것입니다.