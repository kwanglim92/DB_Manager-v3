# CLAUDE.md

이 파일은 Claude Code (claude.ai/code)가 이 레포지토리에서 작업할 때 필요한 가이드를 제공합니다.

## 프로젝트 개요

DB Manager는 반도체 장비의 전체 생명주기를 관리하는 종합 데이터베이스 관리 시스템입니다. 서비스 지향 아키텍처와 SQLite 백엔드, Tkinter GUI를 사용하여 장비 파라미터, 품질 관리(QC) 검수, 출고 프로세스를 관리합니다.

**주요 언어**: Python 3.7+
**현재 버전**: 1.5.0

## 실행 및 테스트

### 기본 명령어

```bash
# 애플리케이션 실행
python src/main.py

# 종합 테스트 실행
python tools/comprehensive_test.py

# 개별 테스트 스위트 실행
python tools/test_runner.py data        # 데이터 유틸리티만
python tools/test_runner.py schema      # 데이터베이스 스키마만
python tools/test_runner.py services    # 서비스 레이어만

# 디버그 및 진단
python tools/debug_toolkit.py           # 전체 시스템 진단
python tools/debug_toolkit.py health    # 데이터베이스 상태만
python tools/debug_toolkit.py equipment # 장비 유형만
python tools/debug_toolkit.py services  # 서비스 레이어 상태
```

### 개발 워크플로우

1. **변경 전**: `python tools/debug_toolkit.py` 실행하여 시스템 상태 확인
2. **변경 후**: `python tools/test_runner.py` 실행하여 빠른 검증
3. **커밋 전**: `python tools/comprehensive_test.py` 실행하여 전체 테스트 수행

## 아키텍처

### 3계층 아키텍처

```
┌─────────────────────────────────┐
│      GUI Layer (Tkinter)        │  ← manager.py, dialogs/
├─────────────────────────────────┤
│     Service Layer (Business)    │  ← services/*, ServiceFactory
├─────────────────────────────────┤
│   Data Layer (SQLite + Files)   │  ← schema.py, DBSchema
└─────────────────────────────────┘
```

### 핵심 디자인 패턴

- **서비스 패턴**: `src/app/services/`에서 비즈니스 로직 캡슐화
- **팩토리 패턴**: `ServiceFactory`가 서비스 인스턴스 생성 및 관리
- **싱글톤 패턴**: `ServiceRegistry`, `CacheService`로 공유 상태 관리
- **의존성 주입**: 서비스는 생성자를 통해 의존성 받음
- **어댑터 패턴**: `LegacyAdapter`가 기존 코드와 신규 서비스 연결
- **컨텍스트 매니저**: `DBSchema.get_connection()`으로 안전한 DB 접근

### 서비스 레이어 구조

모든 서비스는 `src/app/services/`에서 인터페이스 기반으로 구현됩니다:

- **EquipmentService**: 장비 유형 관리
- **ChecklistService**: QC Check list 항목 및 검증
- **CategoryService**: 장비 모델/타입 계층 관리 (Phase 1.5)
- **ConfigurationService**: 장비 Configuration 및 기준값 관리 (Phase 1.5)
- **ShippedEquipmentService**: 출고 장비 Raw Data 관리 (Phase 2)

서비스는 `ServiceFactory(db_schema)`를 통해 생성되고 `services/interfaces/`의 인터페이스를 통해 접근합니다.

## 데이터베이스 스키마

### 핵심 테이블 계층 구조

```
Equipment_Models (최상위)
  └─ Equipment_Types (분리형/일체형)
       └─ Equipment_Configurations (Port/Wafer/Custom)
            └─ Default_DB_Values (파라미터 기준값)
```

### QC 시스템 테이블

- **QC_Checklist_Items**: 검증 패턴이 포함된 마스터 Check list
- **Equipment_Checklist_Mapping**: 장비별 Check list 매핑
- **QC_Checklist_Audit_Log**: 모든 변경 사항을 타임스탬프와 함께 추적

### 중요한 데이터베이스 세부사항

1. **Default_DB_Values**는 복합 유니크 제약 조건 사용: `(equipment_type_id, configuration_id, parameter_name)`
2. **Configuration 우선순위**: Configuration별 값이 Type 레벨 기본값을 오버라이드
3. **Check list 검증**: `parameter_pattern` 컬럼에서 정규식 패턴 사용
4. **감사 로깅**: 모든 Check list 변경사항이 감사 로그 테이블에 추적됨

## 코드 작성 패턴

### 서비스 사용 패턴

```python
from app.services import ServiceFactory

# db_schema로 초기화
factory = ServiceFactory(db_schema)

# 서비스 획득 (사용 불가능하면 None 반환)
equipment_service = factory.get_equipment_service()
checklist_service = factory.get_checklist_service()
config_service = factory.get_configuration_service()

# 항상 서비스 사용 가능 여부 확인
if checklist_service:
    result = checklist_service.validate_parameter(...)
```

### 데이터베이스 접근 패턴

```python
# 데이터베이스 연결 시 반드시 컨텍스트 매니저 사용
with self.db_schema.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT ...")
    results = cursor.fetchall()
    conn.commit()  # 데이터 수정 시만 커밋
```

### 레거시 코드 통합

코드베이스는 모놀리식에서 서비스 기반으로 전환 중입니다:

```python
# 기존 패턴 (일부 파일에 여전히 존재)
from app.manager import DBManager
# GUI 코드에서 직접 데이터베이스 접근

# 새로운 패턴 (권장)
from app.services import ServiceFactory
# 서비스 레이어가 모든 비즈니스 로직 처리
```

코드 수정 시 주의사항:
- 새 기능은 새로운 서비스 레이어 사용
- 기존 레거시 코드 경로를 중단하지 않기
- 서비스는 `USE_NEW_SERVICES` 플래그로 사용 가능 여부 확인

## QC 시스템 세부사항

### Check list 검증 플로우

1. **패턴 매칭**: Check list 항목은 `parameter_pattern`에서 정규식 사용
2. **심각도 레벨**: CRITICAL, HIGH, MEDIUM, LOW
3. **검증 규칙**: `validation_rule` 컬럼에 JSON 형식으로 저장
4. **우선순위 시스템**: 높은 우선순위 항목이 먼저 검사됨

### 21개 공통 Check list 항목

시스템은 21개의 미리 정의된 공통 Check list 항목을 포함합니다(Phase 1). 장비별 항목은 `Equipment_Checklist_Mapping`을 통해 추가할 수 있습니다.

### QC 탭 UI

- **Simplified QC System**: `simplified_qc_system.py`가 간소화된 UI 제공
- **Enhanced QC**: `enhanced_qc.py`가 고급 검수 기능 추가
- **Custom Specs**: `qc_custom_config.py`가 장비별 사양 관리

## 접근 제어

3가지 사용자 모드 (테스트용 비밀번호: 1234):

1. **생산 엔지니어** (기본): 읽기 전용, 파일 비교
2. **QC 엔지니어**: QC 검수 및 Check list 관리
3. **관리자**: Default DB 및 시스템 설정 포함 전체 접근

모드 전환은 `manager.py`의 메뉴 항목을 통해 처리됩니다.

## 성능 특성

- **Check list 조회**: ~0.01ms (캐시 활성화 시)
- **대규모 검증**: 17,337+ 파라미터/초
- **메모리 사용량**: 일반적으로 50MB 이하
- **파일 비교**: 4스레드 병렬 처리

## 중요한 제약사항

### 데이터 무결성

1. **장비 계층 구조**: Model → Type → Configuration 체인 유지 필수
2. **유니크 제약 조건**: 장비 유형 이름, Configuration별 파라미터 이름
3. **외래 키**: Cascading delete 미활성화 - 삭제 전 의존성 확인 필요
4. **감사 추적**: Check list 감사 기록은 절대 삭제 금지

### 파일 처리

1. **지원 형식**: CSV, Excel (.xlsx, .xls), DB 파일
2. **인코딩**: 기본 UTF-8, 레거시 파일의 EUC-KR 처리 지원
3. **대용량 파일**: 10MB 초과 파일은 pandas 청킹 사용
4. **Module/Part 감지**: 파라미터 이름 패턴에서 자동 감지

### UI 스레딩

1. **장시간 작업**: `app.loading`의 `LoadingDialog` 사용
2. **파일 처리**: GUI 정지 방지를 위해 항상 별도 스레드에서 실행
3. **진행률 업데이트**: 점진적 업데이트를 위한 콜백 패턴 사용

## 일반적인 함정

1. **서비스 레이어 우회 금지**: 비즈니스 로직은 항상 서비스 사용, GUI에서 직접 DB 접근 금지
2. **컨텍스트 매니저 사용 필수**: 데이터베이스 연결 시 반드시 `with get_connection():` 사용
3. **서비스 가용성 확인**: 서비스를 사용 불가능할 수 있으므로 항상 사용 전 확인
4. **트랜잭션 안전성**: 문장별 커밋이 아닌 모든 관련 변경 후 커밋
5. **캐시 무효화**: 데이터 변경 시 `cache_service.invalidate()` 호출
6. **파라미터 명명**: 장비 파라미터는 점 표기법 사용: `Module.Part.Parameter`

## 테스트 철학

1. **단위 테스트**: 개별 서비스를 독립적으로 테스트
2. **통합 테스트**: 서비스 간 상호작용 테스트
3. **E2E 테스트**: 파일 로드부터 보고서 생성까지 전체 워크플로우 테스트
4. **성능 테스트**: 대용량 데이터셋에서 성능 저하 추적

기능 추가 시:
- `tools/test_runner.py`에 단위 테스트 추가
- `tools/comprehensive_test.py`에 통합 테스트 추가
- 새로운 진단이 필요하면 `tools/debug_toolkit.py` 업데이트

## 파일 구조 참고사항

### 핵심 파일

- `src/main.py`: 애플리케이션 진입점
- `src/app/manager.py`: 메인 GUI 컨트롤러 (1000+ 줄, 리팩토링 중)
- `src/app/schema.py`: 데이터베이스 스키마 정의
- `src/app/services/service_factory.py`: 서비스 생성 및 DI

### 레거시 vs 신규 코드

- **레거시**: `manager.py`에서 직접 DB 접근, 모놀리식 메서드
- **신규**: 서비스 기반, 관심사 분리, `services/` 디렉토리에 위치
- **전환 플래그**: `USE_NEW_SERVICES`, `USE_NEW_CONFIG`, `USE_NEW_DB_SYSTEM`

### 다이얼로그 구성

모든 다이얼로그 클래스는 `src/app/dialogs/`에 위치:
- 패턴 준수: `*_dialog.py` 파일에 `*Dialog` 클래스
- `dialog_helpers.py`의 `center_dialog()` 사용
- OK/취소 버튼이 있는 모달 다이얼로그

## 한국어 언어 컨텍스트

이 코드베이스는 이중 언어(한국어 + 영어)입니다:
- UI 레이블 및 메시지: 한국어 (한글)
- 코드, 변수, 주석: 주로 영어
- 데이터베이스 내용: 혼합 (장비명은 한국어, 파라미터는 영어)
- 문서: 한국어 (README, docs/) 및 영어 (코드 주석)

기능 추가 시:
- 변수/함수명은 영어로 유지
- UI 텍스트는 일관성을 위해 한국어로 작성
- 주석은 두 언어 모두 가능하지만 코드 명확성을 위해 영어 권장
