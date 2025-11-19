# Custom QC Configuration 통합 구현 계획

## 개요

QC 스펙 관리 탭에서 Equipment Type별로 검수 기준(Min/Max)을 정의하고, QC 검수 탭에서 정의된 스펙을 불러와 실제 DB 파일을 검수하는 시스템 구축

## 핵심 개념

```
QC 스펙 관리 탭 (데이터 정의)
    ↓
    저장 (JSON)
    ↓
QC 검수 탭 (데이터 사용)
```

**흐름:**
1. **QC 스펙 관리 탭**: Equipment Type별로 검수 기준(Min/Max) 정의하고 저장
2. **QC 검수 탭**: 저장된 스펙을 불러와서 실제 파일 검수

---

## Phase 1: QC 스펙 관리 탭 (데이터 정의 및 저장)

### 목표
Equipment Type별 QC 스펙을 정의하고 JSON에 저장

### UI 구조

```
┌─────────────────────────────────────────────────────────┐
│ QC 스펙 관리 탭                                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ [Equipment Type 선택]                                    │
│  ○ Standard Model  ○ Advanced Model  ○ Custom Model     │
│  [➕ 새 Type 추가]  [✏️ Type 이름 변경]  [🗑️ Type 삭제]  │
│                                                          │
│ [QC Spec Master Management]                             │
│  [➕ Add QC Spec] [✏️ Edit] [🗑️ Delete] [📥 Import] [📤 Export] │
│  🔎 Search: [_________________] [Clear]                 │
│                                                          │
│ [QC Spec Master List]                                   │
│ ┌────┬─────────┬─────┬─────┬────┬────────┬────────┐   │
│ │No. │Item Name│Min  │Max  │Unit│Category│Desc... │   │
│ ├────┼─────────┼─────┼─────┼────┼────────┼────────┤   │
│ │ 1  │Temperature│20 │ 25  │°C  │Std Model│...    │   │
│ │ 2  │Pressure   │100│200  │kPa │Std Model│...    │   │
│ └────┴─────────┴─────┴─────┴────┴────────┴────────┘   │
│                                                          │
│ Status: Standard Model - 5개 항목 로드됨                │
└─────────────────────────────────────────────────────────┘
```

### 주요 기능

#### 1. Equipment Type 관리
- **토글 방식 선택**: 라디오버튼으로 Equipment Type 선택
- **추가**: 새 Equipment Type 생성
- **이름 변경**: 기존 Type의 이름 수정
- **삭제**: Type 및 관련 스펙 전체 삭제

#### 2. QC 스펙 CRUD
- **추가 (Add QC Spec)**: 
  - Item Name, Min Spec, Max Spec, Unit, Description 입력
  - 선택된 Equipment Type에 추가
  
- **편집 (Edit Selected)**:
  - 선택된 항목의 Min/Max 값 수정
  - Item Name은 변경 불가
  
- **삭제 (Delete Selected)**:
  - 선택된 항목 삭제
  - 다중 선택 지원

#### 3. Import/Export
- **Import CSV**: CSV 파일에서 QC 스펙 일괄 가져오기
  - 필수 컬럼: Item Name, Min Spec, Max Spec
  - 선택 컬럼: Unit, Description
  
- **Export CSV**: 현재 Equipment Type의 스펙을 CSV로 저장

#### 4. 검색 기능
- Item Name 또는 Description으로 실시간 검색
- Clear 버튼으로 검색 초기화

### 데이터 구조

**JSON 저장 형식 (qc_custom_config.json)**:
```json
{
  "version": "1.0.0",
  "equipment_types": [
    "Standard Model",
    "Advanced Model",
    "Custom Model"
  ],
  "specs": {
    "Standard Model": [
      {
        "item_name": "Temperature",
        "min_spec": 20.0,
        "max_spec": 25.0,
        "unit": "°C",
        "enabled": true,
        "description": "온도 센서 검수"
      },
      {
        "item_name": "Pressure",
        "min_spec": 100.0,
        "max_spec": 200.0,
        "unit": "kPa",
        "enabled": true,
        "description": "압력 게이지 검수"
      }
    ]
  },
  "last_modified": "2025-01-17T12:00:00"
}
```

---

## Phase 2: QC 검수 탭 (저장된 스펙으로 검수)

### 목표
QC 스펙 관리 탭에서 저장한 스펙을 불러와서 검수

### UI 구조

```
┌─────────────────────────────────────────────────────────┐
│ QC 검수 탭                                               │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ [Equipment Type 선택]                                    │
│  ○ Standard Model  ○ Advanced Model  ○ Custom Model     │
│  [⚙️ 스펙 관리로 이동]                                   │
│                                                          │
│ [검수 파일]                                              │
│  선택된 파일: sample_db.txt (또는 현재 로드된 파일)      │
│                                                          │
│ [검수 실행]                                              │
│  [▶️ QC 검수 실행]  [📊 결과 내보내기]                  │
│  Status: 대기 중...                                      │
│                                                          │
│ [검수 결과]                                              │
│ ┌────┬─────────┬─────┬─────┬────┬─────┬────┬─────┐    │
│ │No. │Item Name│Min  │Max  │Unit│Meas.│Res.│Dev. │    │
│ ├────┼─────────┼─────┼─────┼────┼─────┼────┼─────┤    │
│ │ 1  │Temp     │20   │25   │°C  │22.5 │✅  │     │    │
│ │ 2  │Pressure │100  │200  │kPa │250  │❌  │▲50  │    │
│ └────┴─────────┴─────┴─────┴────┴─────┴────┴─────┘    │
│                                                          │
│ 검수 요약: Total 2개 | ✅ Pass 1개 (50%) | ❌ Fail 1개  │
└─────────────────────────────────────────────────────────┘
```

### 주요 기능

#### 1. Equipment Type 선택
- 토글 방식으로 검수할 Equipment Type 선택
- 선택된 Type의 스펙이 자동으로 로드됨

#### 2. 검수 실행
- **데이터 소스**: 현재 로드된 merged_df 사용
- **검수 로직**:
  ```python
  for each spec in selected_equipment_type:
      측정값 = merged_df에서 ItemName 찾기
      if min_spec ≤ 측정값 ≤ max_spec:
          result = "✅ Pass"
      else:
          result = "❌ Fail"
          deviation = 측정값 - 스펙 계산
  ```

#### 3. 결과 표시
- **컬럼 구조**: No. | Item Name | Min Spec | Max Spec | Unit | Measured Value | Result | Deviation | File
- **색상 구분**:
  - ✅ Pass: 초록색
  - ❌ Fail: 빨간색 + 배경색
  - ⚠️ Error: 회색 (값 변환 불가)

#### 4. 편차(Deviation) 계산
- 스펙 미달: `▼ {차이값}`
- 스펙 초과: `▲ {차이값}`
- 정상 범위: 빈 칸

#### 5. 검수 요약
- Total 항목 수
- Pass 개수 및 비율
- Fail 개수

#### 6. 결과 내보내기
- CSV 또는 Excel 형식으로 저장
- 모든 컬럼 포함

---

## 핵심 데이터 흐름

### 1. QC 스펙 정의 흐름
```
QC 스펙 관리 탭
    ↓
[Equipment Type: Standard Model 선택]
    ↓
[Add QC Spec 버튼 클릭]
    ↓
ItemName: Temperature
Min Spec: 20
Max Spec: 25
Unit: °C
    ↓
[저장] → qc_custom_config.json에 저장
```

### 2. QC 검수 흐름
```
QC 검수 탭
    ↓
[Equipment Type: Standard Model 선택]
    ↓
[▶️ QC 검수 실행 클릭]
    ↓
qc_custom_config.json에서 Standard Model 스펙 로드
    ↓
merged_df에서 Temperature 값 찾기
    ↓
20 ≤ 측정값 ≤ 25 → Pass/Fail 판별
    ↓
결과 테이블에 표시
```

---

## 구현 순서

### Step 1: CustomQCConfig 클래스 확인
- 이미 구현 완료
- `src/app/qc_custom_config.py`

### Step 2: QC 스펙 관리 탭 구현 (3-4시간)
1. `create_qc_spec_management_tab()` 메서드 작성
2. Equipment Type 토글 UI 구현
3. QC 스펙 CRUD 기능 구현
4. 검색 기능 구현
5. Import/Export CSV 기능 구현

### Step 3: QC 검수 탭 구현 (2-3시간)
1. `create_enhanced_qc_tab()` 메서드 수정
2. Equipment Type 선택 UI 구현
3. `run_custom_qc_inspection()` 검수 로직 구현
4. 결과 표시 및 색상 구분
5. 편차 계산 로직
6. 결과 내보내기 기능

### Step 4: 테스트 (1-2시간)
1. Equipment Type 추가/수정/삭제 테스트
2. QC 스펙 추가/수정/삭제 테스트
3. CSV Import/Export 테스트
4. QC 검수 실행 및 결과 확인
5. Pass/Fail 판별 정확성 검증
6. 결과 내보내기 테스트

---

## 예상 소요 시간

| 작업 항목 | 예상 시간 |
|---------|---------|
| QC 스펙 관리 탭 구현 | 3-4시간 |
| QC 검수 탭 구현 | 2-3시간 |
| 테스트 및 디버깅 | 1-2시간 |
| **총계** | **6-9시간** |

---

## 주요 클래스 및 메서드

### DBManager 클래스 추가 메서드

```python
# QC 스펙 관리 탭
def create_qc_spec_management_tab(self)
def refresh_equipment_type_radios(self)
def load_qc_specs_for_selected_type(self)
def add_equipment_type_dialog(self)
def rename_equipment_type_dialog(self)
def delete_equipment_type_dialog(self)
def add_qc_spec_dialog(self)
def edit_qc_spec_dialog(self)
def delete_selected_qc_specs(self)
def filter_qc_specs(self)
def import_qc_specs_csv(self)
def export_qc_specs_csv(self)

# QC 검수 탭
def create_enhanced_qc_tab(self)  # 수정
def run_custom_qc_inspection(self)
def export_qc_inspection_results(self)
def goto_qc_spec_management_tab(self)
```

### CustomQCConfig 클래스 (기존)

```python
def get_equipment_types(self) -> List[str]
def add_equipment_type(self, type_name: str) -> bool
def remove_equipment_type(self, type_name: str) -> bool
def get_specs(self, equipment_type: str) -> List[Dict]
def update_specs(self, equipment_type: str, specs: List[Dict]) -> bool
def add_spec_item(self, equipment_type: str, item: Dict) -> bool
def remove_spec_item(self, equipment_type: str, item_name: str) -> bool
def save_config(self) -> bool
def load_config(self) -> Dict
```

---

## 성공 기준

### Phase 1 완료 조건
- [x] Equipment Type을 토글로 선택 가능
- [x] Equipment Type 추가/수정/삭제 가능
- [x] QC 스펙 추가/수정/삭제 가능
- [x] 검색 기능 동작
- [x] CSV Import/Export 동작
- [x] JSON 파일에 정상 저장

### Phase 2 완료 조건
- [x] Equipment Type 선택 시 스펙 자동 로드
- [x] QC 검수 실행 시 Pass/Fail 정확히 판별
- [x] 결과 테이블에 색상 구분 표시
- [x] 편차 계산 정확
- [x] 검수 요약 통계 정확
- [x] 결과 내보내기 정상 동작

---

## 주의사항

1. **Default DB와의 독립성 유지**
   - QC 스펙은 완전히 Custom Config만 사용
   - DB의 Default Values와 연동하지 않음

2. **데이터 일관성**
   - Equipment Type 삭제 시 관련 스펙도 함께 삭제
   - JSON 저장 실패 시 롤백 필요

3. **사용자 경험**
   - 스펙이 없는 Equipment Type으로 검수 시도 시 명확한 안내
   - 검수 결과를 직관적으로 표시 (색상, 아이콘)

4. **성능**
   - 대량 데이터 검수 시 배치 처리 고려
   - UI 응답성 유지 (비동기 처리 검토)

---

## 향후 개선 사항

1. **다중 파일 검수**
   - 여러 파일을 동시에 검수
   - 파일별 결과 비교

2. **검수 히스토리**
   - 검수 이력 저장
   - 시간별 Pass/Fail 추세 분석

3. **알림 기능**
   - Fail 항목 임계값 설정
   - 자동 알림 발송

4. **템플릿 관리**
   - 자주 사용하는 스펙 세트를 템플릿으로 저장
   - 빠른 적용

5. **통계 차트**
   - Pass/Fail 비율 차트
   - 항목별 트렌드 분석

---

## 참고 파일

- `src/app/qc_custom_config.py` - Custom QC Configuration 클래스
- `src/app/dialogs/qc_spec_editor_dialog.py` - GUI 편집 다이얼로그 (참고용)
- `test_simplified_qc_ui.py` - 프로토타입 UI (참고용)
- `docs/CUSTOM_QC_CONFIGURATION.md` - 기능 상세 문서

---

## 결론

이 구현을 통해 사용자는:
1. DB와 독립적으로 QC 검수 기준을 자유롭게 정의
2. Equipment Type별로 체계적으로 스펙 관리
3. 간편하게 검수 실행 및 결과 확인
4. Pass/Fail 판별을 명확하게 확인

**핵심**: "내가 정의한 기준으로 불러온 파일을 검수한다"
