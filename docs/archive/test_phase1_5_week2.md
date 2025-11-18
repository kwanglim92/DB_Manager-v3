# Phase 1.5 Week 2 Integration & Testing Plan

**날짜**: 2025-11-13
**대상**: Week 2 (Day 1-5) 구현 기능
**테스트 유형**: Integration & End-to-End

## 1. 테스트 개요

### 테스트 목표
- Week 2에서 구현한 모든 기능의 통합 테스트
- UI와 Service Layer 간 연동 검증
- End-to-End 사용자 워크플로우 테스트
- 프로덕션 준비 상태 확인

### 구현된 기능 (Week 2)
1. **Day 1-2**: Equipment Hierarchy Tree View UI
2. **Day 3**: Configuration Management Dialog
3. **Day 4**: Configuration-based Default DB 관리

## 2. 테스트 환경

### 필수 조건
- Python 3.7+
- 모든 의존성 설치 완료
- 데이터베이스: `data/db_manager.sqlite` (Phase 1.5 마이그레이션 완료)
- 관리자 모드 비밀번호: 1234

### 테스트 데이터
- Equipment Models: 8개 (migrate_phase1_5.py로 생성)
- Equipment Types: 기존 데이터
- Configurations: migrate_phase1_5.py로 생성된 데이터

## 3. UI/Service 통합 테스트

### 3.1 Equipment Hierarchy Dialog 통합 테스트

**테스트 ID**: WEEK2-INT-001
**목적**: Equipment Hierarchy Dialog와 CategoryService/ConfigurationService 연동 확인

**테스트 단계**:
1. ✅ **프로그램 시작**
   - `python src/main.py` 실행
   - 에러 없이 시작되는지 확인
   - ServiceFactory 초기화 로그 확인

2. ✅ **관리자 모드 진입**
   - 도움말 → 🔐 Maintenance
   - 비밀번호 입력: 1234
   - 관리자 모드 활성화 확인

3. ✅ **Equipment Hierarchy 다이얼로그 열기**
   - "🏗️ Equipment Hierarchy 관리" 버튼 클릭
   - 다이얼로그 정상 열림 확인
   - 3단계 Treeview 로드 확인 (Model → Type → Configuration)

4. ✅ **Model 조회**
   - 8개 Model 노드 표시 확인
   - 아이콘: 📁, 색상: 파랑

5. ✅ **Type 조회**
   - 각 Model 하위에 Type 표시 확인
   - 아이콘: 🔧, 색상: 초록

6. ✅ **Configuration 조회**
   - 각 Type 하위에 Configuration 표시 확인
   - 아이콘: ⚙️, 색상: 주황
   - Customer-Specific: ⚙️🌟 표시 확인

**예상 결과**:
- 모든 데이터 정상 로드
- Service Layer 호출 에러 없음
- Treeview 정상 렌더링

---

### 3.2 Configuration Dialog 통합 테스트

**테스트 ID**: WEEK2-INT-002
**목적**: Configuration 추가/수정 다이얼로그 연동 확인

**테스트 단계**:
1. ✅ **Add Configuration**
   - Type 노드 우클릭 → "Add Configuration"
   - ConfigurationDialog 열림 확인
   - Port Type 드롭다운: 4개 옵션
   - Wafer Size 드롭다운: 6개 옵션
   - Port/Wafer Count 스피너: > 0 검증

2. ✅ **Configuration 추가 테스트**
   - Configuration Name: "Test Config"
   - Port Type: "Double Port"
   - Port Count: 2
   - Wafer Size: "300mm"
   - Wafer Count: 1
   - Custom Options: `{"test": true}`
   - Description: "Test configuration"
   - 저장 클릭

3. ✅ **ConfigurationService 연동 확인**
   - `create_configuration()` 호출 확인
   - 데이터베이스 INSERT 확인
   - Treeview 자동 새로고침 확인

4. ✅ **Edit Configuration**
   - Configuration 노드 우클릭 → "Edit"
   - 기존 데이터 로드 확인 (get_configuration_by_id)
   - 수정: Port Count → 3
   - 저장 클릭
   - `update_configuration()` 호출 확인

5. ✅ **JSON Validation**
   - Custom Options: `{invalid json`
   - Validate JSON 버튼 클릭
   - 에러 메시지 표시 확인
   - 올바른 JSON: `{"valid": true}`
   - Auto-formatting 확인

**예상 결과**:
- 모든 CRUD 작업 정상 동작
- 검증 로직 정상 작동
- 데이터베이스 무결성 유지

---

### 3.3 Default DB Management 통합 테스트

**테스트 ID**: WEEK2-INT-003
**목적**: Configuration별 Default DB 관리 기능 연동 확인

**테스트 단계**:
1. ✅ **Default DB 관리 탭 열기**
   - QC 검수 탭 생성 확인
   - Default DB 관리 탭 생성 확인 (관리자 모드)

2. ✅ **Equipment Type 선택**
   - Equipment Type 콤보박스 선택
   - Configuration 콤보박스 자동 로드 확인
   - "All (Type Common)" 기본 선택 확인

3. ✅ **Type Common 모드**
   - "All (Type Common)" 선택
   - Default DB 파라미터 표시 확인
   - Scope 컬럼: 모두 "Type Common"

4. ✅ **Configuration 선택**
   - Configuration 콤보박스에서 특정 Configuration 선택
   - ConfigurationService.get_default_values_by_configuration() 호출 확인
   - Default DB 파라미터 표시 확인
   - Scope 컬럼: "Type Common" + "Configuration" 혼합

5. ✅ **Scope 구분 표시**
   - Type Common 파라미터: Scope = "Type Common"
   - Configuration-specific 파라미터: Scope = "Configuration"

**예상 결과**:
- Configuration 선택 시 자동 로드
- Scope 정확히 표시
- Service Layer 연동 정상

---

### 3.4 Convert 기능 UI 테스트

**테스트 ID**: WEEK2-INT-004
**목적**: Scope 전환 기능 UI 동작 확인 (로직은 미구현)

**테스트 단계**:
1. ✅ **Convert to Type Common**
   - Configuration 선택 상태
   - Configuration-specific 파라미터 선택
   - 우클릭 → "Convert to Type Common"
   - 권한 검증 확인 (admin_mode)
   - Scope 검증 확인
   - 확인 다이얼로그 표시
   - "구현 예정" 메시지 확인

2. ✅ **Convert to Configuration-specific**
   - Type Common 파라미터 선택
   - 우클릭 → "Convert to Configuration-specific"
   - 권한 검증 확인
   - Scope 검증 확인
   - 확인 다이얼로그 표시
   - "구현 예정" 메시지 확인

3. ✅ **권한 검증**
   - QC 엔지니어 모드 (admin_mode = False)
   - Convert 메뉴 클릭
   - "권한 없음" 메시지 확인

4. ✅ **Mode 검증**
   - "All (Type Common)" 모드
   - Convert 메뉴 클릭
   - "Configuration을 선택해야 함" 메시지 확인

**예상 결과**:
- UI 동작 정상
- 검증 로직 정상
- 에러 메시지 명확

---

## 4. End-to-End Workflow Test

### 4.1 완전한 Equipment Hierarchy 관리 워크플로우

**테스트 ID**: WEEK2-E2E-001
**시나리오**: 새 Model/Type/Configuration 생성 및 Default DB 관리

**워크플로우**:
```
1. 프로그램 시작
   ↓
2. 관리자 모드 진입 (비밀번호: 1234)
   ↓
3. Equipment Hierarchy 관리 열기
   ↓
4. 새 Model 추가
   - Model Name: "Test Model"
   - Order: 99
   ↓
5. 새 Type 추가 (Test Model 하위)
   - Type Name: "Test Type"
   ↓
6. 새 Configuration 추가 (Test Type 하위)
   - Configuration Name: "Test Config 1"
   - Port Type: "Single Port"
   - Port Count: 1
   - Wafer Size: "200mm"
   - Wafer Count: 1
   - Custom Options: {"test_mode": true}
   ↓
7. Configuration 수정
   - Port Count: 1 → 2
   ↓
8. Default DB 관리 탭으로 이동
   ↓
9. "Test Type" 선택
   ↓
10. Configuration 콤보박스에서 "Test Config 1" 선택
    ↓
11. Configuration별 Default DB 확인
    ↓
12. (선택) Configuration 삭제
    ↓
13. (선택) Type 삭제
    ↓
14. (선택) Model 삭제
```

**검증 항목**:
- ✅ 각 단계에서 에러 없음
- ✅ 데이터베이스 정상 저장
- ✅ UI 자동 새로고침
- ✅ FK 제약 정상 작동 (삭제 시 캐스케이드)
- ✅ Audit Trail 기록 (미구현이면 SKIP)

---

### 4.2 Configuration별 Default DB 전환 워크플로우

**테스트 ID**: WEEK2-E2E-002
**시나리오**: Configuration 간 Default DB 표시 전환

**워크플로우**:
```
1. Default DB 관리 탭 열기
   ↓
2. Equipment Type 선택 (예: "분리형 AE (Single Port 200mm)")
   ↓
3. Configuration 목록 확인 (3개 이상)
   ↓
4. "All (Type Common)" 선택
   - Scope 컬럼: 모두 "Type Common"
   - 파라미터 개수 기록
   ↓
5. Configuration 1 선택
   - Scope 컬럼: "Type Common" + "Configuration"
   - 파라미터 개수 확인 (>= Type Common)
   ↓
6. Configuration 2 선택
   - Scope 컬럼 확인
   - Configuration 1과 다를 수 있음
   ↓
7. "All (Type Common)" 재선택
   - 원래 파라미터 개수 일치 확인
```

**검증 항목**:
- ✅ Configuration 전환 시 즉시 로드
- ✅ Scope 정확히 표시
- ✅ 데이터 정합성
- ✅ 성능 (1초 이내 로드)

---

## 5. 사용자 시나리오 테스트

### 5.1 관리자 시나리오: 새 장비 구성 추가

**시나리오**:
신규 장비 모델이 출시되어, Equipment Hierarchy에 추가하고 Default DB를 설정해야 함.

**단계**:
1. ✅ 관리자 모드 진입
2. ✅ Equipment Hierarchy 열기
3. ✅ 새 Model 추가: "NX-Hybrid WLI Gen2"
4. ✅ 새 Type 추가: "일체형 AE (Double Port 300mm)"
5. ✅ 새 Configuration 추가:
   - "Standard (2P 300mm)"
   - "Extended (2P 300mm + Custom Loadport)"
6. ✅ Default DB 탭에서 Type 선택
7. ✅ Configuration 선택하여 Default DB 확인
8. ✅ (미구현) Default DB 파라미터 추가

**예상 결과**:
- 모든 작업 직관적
- 에러 없음
- 데이터 정합성 유지

---

### 5.2 QC 엔지니어 시나리오: Configuration 확인

**시나리오**:
출고 전 장비의 Configuration을 확인하고, Default DB를 조회해야 함.

**단계**:
1. ✅ QC 엔지니어 모드 진입 (비밀번호: 1234)
2. ✅ Equipment Hierarchy 열기
3. ✅ 해당 Model → Type → Configuration 찾기
4. ✅ Configuration 상세 정보 확인 (우클릭 → View Details)
5. ✅ Default DB 탭에서 Configuration별 Default DB 조회
6. ✅ Scope 확인 (Type Common vs Configuration)

**예상 결과**:
- 읽기 전용 접근 (QC 엔지니어는 수정 불가)
- 정보 조회 정상

---

## 6. 에러 시나리오 테스트

### 6.1 잘못된 입력 처리

**테스트 항목**:
- ✅ Configuration Name 누락
- ✅ Port Count = 0 (CHECK 제약 위반)
- ✅ Wafer Count = 0 (CHECK 제약 위반)
- ✅ 잘못된 JSON (Custom Options)
- ✅ 중복 Configuration Name (같은 Type 내)

**예상 동작**:
- 명확한 에러 메시지
- 데이터베이스 롤백
- UI 상태 유지

---

### 6.2 권한 에러

**테스트 항목**:
- ✅ QC 엔지니어가 Configuration 추가 시도
- ✅ 생산 엔지니어가 Equipment Hierarchy 접근 시도
- ✅ QC 엔지니어가 Convert 기능 사용 시도

**예상 동작**:
- "권한 없음" 메시지
- 작업 차단

---

### 6.3 FK 제약 에러

**테스트 항목**:
- ✅ Configuration이 있는 Type 삭제 시도
- ✅ Type이 있는 Model 삭제 시도

**예상 동작**:
- "하위 항목 존재" 경고
- 캐스케이드 삭제 확인 다이얼로그
- 정상 삭제 또는 취소

---

## 7. 성능 테스트

### 7.1 로딩 시간

**테스트 항목**:
- ✅ Equipment Hierarchy Dialog 초기 로딩: < 500ms
- ✅ Configuration 목록 로드: < 200ms
- ✅ Default DB 표시 전환: < 1초
- ✅ Treeview 새로고침: < 300ms

**측정 방법**:
- 콘솔 로그 타임스탬프 분석
- 사용자 체감 속도

---

### 7.2 대용량 데이터

**테스트 항목**:
- ✅ 50개 Configuration이 있는 Type 선택
- ✅ 1000개 Default DB 파라미터 표시
- ✅ Treeview 스크롤 성능

**예상 결과**:
- 지연 없음
- UI 응답성 유지

---

## 8. 호환성 테스트

### 8.1 레거시 데이터 호환성

**테스트 항목**:
- ✅ Phase 0 Equipment Types 정상 로드
- ✅ Phase 1 Check list 데이터 정상 로드
- ✅ 마이그레이션 전후 데이터 무결성

**검증 방법**:
- 데이터베이스 레코드 수 일치
- FK 관계 정상
- NULL 값 없음 (NOT NULL 필드)

---

## 9. 테스트 결과 요약

### 통합 테스트 결과
| 테스트 ID | 테스트명 | 상태 | 비고 |
|-----------|----------|------|------|
| WEEK2-INT-001 | Equipment Hierarchy Dialog 통합 | ⏳ 대기 | - |
| WEEK2-INT-002 | Configuration Dialog 통합 | ⏳ 대기 | - |
| WEEK2-INT-003 | Default DB Management 통합 | ⏳ 대기 | - |
| WEEK2-INT-004 | Convert 기능 UI | ⏳ 대기 | 로직 미구현 |

### E2E 테스트 결과
| 테스트 ID | 시나리오 | 상태 | 비고 |
|-----------|----------|------|------|
| WEEK2-E2E-001 | 완전한 Equipment Hierarchy 관리 | ⏳ 대기 | - |
| WEEK2-E2E-002 | Configuration별 Default DB 전환 | ⏳ 대기 | - |

### 사용자 시나리오 테스트 결과
| 시나리오 | 상태 | 비고 |
|----------|------|------|
| 관리자: 새 장비 구성 추가 | ⏳ 대기 | - |
| QC 엔지니어: Configuration 확인 | ⏳ 대기 | - |

### 발견된 이슈
| 이슈 ID | 설명 | 심각도 | 상태 |
|---------|------|--------|------|
| - | - | - | - |

---

## 10. 테스트 실행 방법

### 수동 테스트
```bash
# 1. 프로그램 실행
python src/main.py

# 2. 관리자 모드 진입
# - 도움말 → 🔐 Maintenance
# - 비밀번호: 1234

# 3. Equipment Hierarchy 관리 열기
# - "🏗️ Equipment Hierarchy 관리" 버튼 클릭

# 4. 테스트 시나리오 순차 진행
```

### 자동 테스트 (미구현)
```bash
# 추후 구현 예정
# python tools/test_phase1_5_week2_auto.py
```

---

## 11. 다음 단계

### Week 2 완료 후
- ✅ Week 2 Day 1-5 모두 완료
- ✅ CLAUDE.md 업데이트
- ✅ 커밋: Week 2 완료
- ⏳ Week 3 시작: Check list System Redesign

### 남은 작업 (Week 3+)
- ItemName 자동 매칭
- Equipment_Checklist_Exceptions 테이블
- QC Inspection v2 구현
- Convert 기능 로직 구현 (ConfigurationService)

---

**테스트 담당**: Claude Code
**테스트 일자**: 2025-11-13
**버전**: Phase 1.5 Week 2
