# Changelog

DB Manager 프로젝트의 모든 주요 변경사항을 기록합니다.

## [2.0.0] - 2025-11-18

### 🚀 QC 시스템 리팩토링 Phase 2-4 완료

#### 추가됨

**Services Layer (Phase 2)**
- `qc/services/` 디렉토리 생성 (서비스 레이어 구축)
- `QCService`: 통합 QC 검수 서비스
  - `run_inspection()`: 검수 실행
  - `get_inspection_summary()`: 결과 요약
  - `get_statistics()`: 통계 생성
- `SpecService`: Checklist Spec 관리
  - CRUD 작업 (생성, 조회, 수정, 삭제)
  - 예외 관리 (Configuration별)
  - 카테고리 조회
- `ReportService`: 검수 보고서 생성
  - Excel 보고서 (다중 시트)
  - CSV 보고서
  - 텍스트 요약 보고서
- `ConfigService`: 사용자 정의 설정 관리
  - Equipment Type 관리
  - Spec 파일 관리 (JSON)
  - Import/Export 기능

**UI Layer (Phase 3)**
- `qc/ui/` 디렉토리 생성 (UI 레이어 구축)
- `QCInspectionTab`: 통합 QC 검수 탭
  - 파일 선택 및 검수 실행
  - Configuration 선택
  - Excel/CSV 내보내기
- `qc/ui/widgets/` 재사용 가능한 위젯
  - `ResultTableWidget`: 검수 결과 테이블
  - `SummaryPanelWidget`: 검수 요약 패널

**Utils Layer (Phase 4)**
- `qc/utils/` 디렉토리 생성 (유틸리티 레이어)
- `DataProcessor`: 데이터 처리 유틸리티
  - DataFrame 변환 및 검증
  - 파라미터 추출
  - 결과 필터링
- `FileHandler`: 파일 I/O 유틸리티
  - CSV/Excel/TXT 파일 읽기
  - 파라미터 파싱
  - 파일 검증

#### 변경됨

**아키텍처 개선**
- 명확한 레이어 분리: `UI → Services → Core`
- 의존성 방향 정리
- 재사용 가능한 컴포넌트 구조
- 레거시 호환성 100% 유지

**파일 구조**
```
qc/
├── core/           # 핵심 비즈니스 로직
├── services/       # 서비스 레이어 (NEW)
├── ui/             # UI 레이어 (NEW)
└── utils/          # 유틸리티 (NEW)
```

#### 제거됨 (Phase 5)

- `unified_qc_system.py`: 사용하지 않음, 백업 후 제거

#### 보관됨 (나중에 제거 예정)

레거시 파일들은 `docs/archive/refactoring_phase2_backup_20251118/`에 백업:
- `qc_custom_config.py` → `ConfigService`로 대체
- `qc_reports.py` → `ReportService`로 대체
- `qc_utils.py` → `DataProcessor`, `FileHandler`로 대체
- `qc_integration.py`, `qc_simplified.py`, `qc_simplified_custom.py` → `QCInspectionTab`으로 통합 예정

#### 문서화

- `docs/API.md`: QC Services Layer API 문서 추가
- `docs/archive/refactoring_phase2_backup_20251118/README.md`: 마이그레이션 가이드
- `docs/REFACTORING_PLAN.md`: 리팩토링 계획서 (진행 상황 업데이트)

#### 개선 효과

- **코드 구조**: 명확한 책임 분리, 테스트 가능성 향상
- **재사용성**: 서비스 레이어를 통한 비즈니스 로직 재사용
- **확장성**: 새로운 기능 추가 용이
- **유지보수성**: 파일 수 감소 (진행 중), 코드 중복 제거

#### 성과 지표

- **파일 추가**: 14개 (Services: 4, UI: 3, Utils: 2, 기타: 5)
- **코드 라인**: +2,039 (새로운 구조)
- **아키텍처**: 3-Layer 구조 확립
- **하위 호환성**: 100% 유지

## [1.6.0] - 2025-11-18

### QC 시스템 리팩토링 Phase 1 완료

#### 추가됨
- **QC Core Layer 아키텍처**
  - `qc/core/` 디렉토리 생성
  - `InspectionEngine`: 검수 엔진 클래스 기반 구현
  - `ChecklistProvider`: Checklist 항목 제공자
  - `SpecMatcher`: Module.Part.ItemName 복합 키 매칭
  - `ChecklistItem`, `InspectionResult`: 데이터 모델

#### 변경됨
- **qc_inspection_v2.py 리팩토링**
  - 함수 기반 → 클래스 기반 아키텍처
  - Core Layer로 로직 위임
  - 하위 호환성 유지 (레거시 함수 wrapper로 유지)

#### 문서화
- `docs/PROJECT_STATUS.md`: 프로젝트 현황 보고서 작성
- `docs/REFACTORING_PLAN.md`: 리팩토링 계획서 작성
- 코드 중복 및 분산 문제 식별
- 새로운 아키텍처 설계 문서

#### 개선 효과
- 명확한 책임 분리 (Provider, Matcher, Engine)
- 테스트 가능성 향상 (의존성 주입)
- 코드 재사용성 증가
- 하위 호환성 100% 유지

## [1.5.0] - 2025-11-17

### Phase 1.5: Equipment Hierarchy System (진행중)

#### 추가됨
- 3단계 장비 계층 구조 (Model → Type → Configuration)
- Equipment_Models, Equipment_Configurations 테이블
- CategoryService, ConfigurationService 서비스
- Equipment Hierarchy Tree View UI
- Configuration 관리 다이얼로그
- Port/Wafer 드롭다운 제약으로 휴먼 에러 방지

#### 변경됨
- Equipment_Types: model_id FK 추가, type_name 의미 변경
- Default_DB_Values: configuration_id FK 추가, min_spec/max_spec 제거
- QC_Checklist_Items: severity_level 제거, spec 필드 추가

#### 제거됨
- Equipment_Checklist_Mapping 테이블 (ItemName 자동 매칭으로 대체)

## [1.1.0] - 2025-11-01

### Phase 1: Check list 기반 QC 강화 (완료)

#### 추가됨
- **3단계 권한 시스템**
  - 생산 엔지니어 (기본, 읽기 전용)
  - QC 엔지니어 (비밀번호: 1234)
  - 관리자 (비밀번호: 1234, Help 메뉴에서 진입)
  
- **Check list 시스템**
  - 21개 공통 Check list 항목
  - 심각도별 분류 (CRITICAL/HIGH/MEDIUM/LOW)
  - JSON 기반 검증 규칙
  - 동적 Check list 추가 기능
  
- **데이터베이스**
  - QC_Checklist_Items 테이블
  - Equipment_Checklist_Mapping 테이블
  - Equipment_Checklist_Exceptions 테이블
  - Checklist_Audit_Log 테이블
  
- **UI 컴포넌트**
  - Check list 관리 다이얼로그
  - QC 검수 결과 상세 뷰
  - Audit Log 조회 기능

#### 성능 개선
- Check list 조회: 0.01ms (캐시 활용, 257배 향상)
- 대규모 검증: 17,337 파라미터/초
- 메모리 사용량: 50MB 이하 유지

#### 테스트
- 20개 테스트 케이스 100% 통과
- End-to-End 테스트 11개 시나리오 검증
- 성능 테스트 5개 지표 달성

## [1.0.5] - 2025-11-04

### 시스템 정리 및 단일화

#### 변경됨
- main.py 단일 시스템으로 복원
- ServiceFactory 통합 완료
- Python 캐시 문제 해결

#### 제거됨
- main_optimized.py 및 관련 파일 43개 삭제
- app/core/ 디렉토리 (11개 파일)
- app/ui/ 디렉토리 (30개 파일)

## [1.0.0] - 2025-07-02

### 모듈화 프로젝트 완료

#### 추가됨
- **모듈 분리**
  - data_utils.py: 데이터 처리 유틸리티
  - config_manager.py: 설정 관리
  - file_service.py: 파일 I/O 처리
  - dialog_helpers.py: 대화상자 공통 기능
  
- **서비스 레이어**
  - ServiceFactory 패턴
  - 의존성 주입
  - 캐싱 서비스
  - 로깅 서비스

- **도움말 시스템**
  - 완전 모듈화된 도움말 시스템
  - 프로그램 정보 다이얼로그
  - 사용자 가이드 (탭 구조)
  - 문제 해결 가이드

#### 성능 개선
- 코드 크기: 28% 감소 (6,555 → 4,714 라인)
- 중복 코드: 90% 제거
- 모듈 구조: 5개 전문 모듈로 분리

## [0.9.0] - 2024년

### Phase 0: 기본 시스템 구축

#### 초기 기능
- **파일 비교 엔진**
  - CSV, Excel, DB 파일 지원
  - 다중 파일 동시 비교
  - 4개 스레드 병렬 처리
  
- **Mother DB 관리**
  - 장비별 기준 파라미터
  - 80% 자동 감지
  - 빠른 설정 기능
  
- **QC 검수**
  - 기본 Min/Max 검증
  - 누락 데이터 검사
  - 보고서 생성

- **데이터베이스**
  - Equipment_Types 테이블
  - Default_DB_Values 테이블
  - SQLite 로컬 DB

## 개발 로드맵

### 🚧 진행중
- Phase 1.5: Equipment Hierarchy System (2025-11)

### 📋 계획
- Phase 2: Raw Data Management
  - 출고 장비 데이터 추적
  - 리핏 오더 관리
  - 통계 분석
  
- Phase 3: 모듈 기반 아키텍처
  - 장비 구성 템플릿
  - 동적 DB 생성
  - 모듈별 파라미터 관리

---

각 버전의 상세 내용은 [docs/archive/](docs/archive/) 폴더의 문서를 참고하세요.