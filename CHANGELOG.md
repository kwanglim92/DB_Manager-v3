# Changelog

DB Manager 프로젝트의 모든 주요 변경사항을 기록합니다.

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