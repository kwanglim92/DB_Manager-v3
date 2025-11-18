# DB Manager

반도체 장비의 전체 생명주기 DB 관리를 위한 통합 솔루션

## 🎯 개요

DB Manager는 반도체 장비의 파라미터 관리, 품질 검증, 출고 관리를 위한 종합적인 데이터베이스 관리 시스템입니다. 장비별 최적 DB 관리, 옵션/구성별 가이드라인 제공, 출고 시 DB 적합성 자동 검증을 목표로 합니다.

## 🚀 Quick Start

### 요구사항
- Python 3.7 이상
- Windows/Linux/macOS

### 설치 및 실행

```bash
# 저장소 클론
git clone [repository-url]
cd DB_Manager

# 의존성 설치 (필요시)
pip install pandas numpy

# 프로그램 실행
python src/main.py
```

### 기본 사용법

1. **파일 비교**: `파일` → `파일 로드` (Ctrl+O)
2. **QC 검수**: QC 탭에서 파일 선택 후 검수 실행
3. **Mother DB 관리**: 관리자 모드 진입 후 Default DB 탭 사용

#### 사용자 모드
- **생산 엔지니어** (기본): 읽기 전용, DB 비교
- **QC 엔지니어**: `도구` → `사용자 모드 전환` (비밀번호: 1234)
- **관리자**: `도움말` → `🔐 Maintenance` (비밀번호: 1234)

## ✨ 주요 기능

### 📊 파일 비교 및 분석
- 다중 파일 동시 비교 (CSV, Excel, DB)
- 4개 스레드 병렬 처리로 빠른 비교
- 차이점 하이라이트 및 필터링
- 결과 Excel/CSV 내보내기

### 🗄️ Mother DB 관리
- 장비별 기준 파라미터 관리
- 80% 자동 감지 및 빠른 설정
- Configuration별 파라미터 관리
- 버전 관리 및 이력 추적

### 🔍 QC 검수 자동화
- Check list 기반 품질 검증
- 21개 공통 Check list 항목
- 심각도별 분류 (CRITICAL/HIGH/MEDIUM/LOW)
- 자동 Pass/Fail 판정
- HTML/Excel 보고서 생성

### ✅ Check list 시스템
- 공통/장비별 Check list 관리
- 동적 Check list 추가
- JSON 기반 검증 규칙
- Audit Trail (모든 변경 이력 기록)

### 📈 성능
- Check list 조회: 0.01ms (캐시 활용)
- 대규모 검증: 17,337 파라미터/초
- 메모리 효율: 50MB 이하 사용

## 📊 현재 상태

| Phase | 상태 | 설명 |
|-------|------|------|
| **Phase 0** | ✅ 완료 | 기본 시스템 구축 |
| **Phase 1** | ✅ 완료 | Check list 기반 QC 강화 |
| **Phase 1.5** | 🚧 진행중 | Equipment Hierarchy System |
| **Phase 2** | 📋 계획 | Raw Data Management |
| **Phase 3** | 📋 예정 | 모듈 기반 아키텍처 |

**현재 버전**: 1.5.0 (2025-11-17)

## 📁 프로젝트 구조

```
DB_Manager/
├── src/
│   ├── main.py              # 메인 진입점
│   └── app/
│       ├── manager.py       # 메인 GUI 관리
│       ├── schema.py        # 데이터베이스 스키마
│       ├── services/        # 서비스 레이어
│       ├── qc/             # QC 검수 시스템
│       └── dialogs/        # UI 다이얼로그
├── data/
│   └── db_manager.sqlite   # 로컬 데이터베이스
├── config/
│   └── settings.json       # 설정 파일
├── test/                   # 테스트 데이터
├── tools/                  # 개발 도구
└── docs/                   # 문서
```

## 🛠️ 기술 스택

- **언어**: Python 3.7+
- **GUI**: Tkinter (내장)
- **데이터베이스**: SQLite
- **데이터 처리**: Pandas, NumPy
- **아키텍처**: 서비스 레이어 패턴, 싱글톤 패턴

## 📖 문서

- [개발 가이드](docs/DEVELOPMENT.md) - 아키텍처, 개발 환경, 기여 방법
- [API 문서](docs/API.md) - 서비스 레이어 API, 데이터베이스 스키마
- [변경 사항](CHANGELOG.md) - 버전별 변경 이력
- [도구 사용법](tools/README.md) - 개발/디버그 도구

## 🧪 테스트

```bash
# Phase 1 기본 테스트
python tools/test_phase1.py

# End-to-End 테스트
python tools/test_phase1_e2e.py

# 성능 테스트
python tools/test_phase1_performance.py

# 종합 디버그
python tools/debug_toolkit.py
```

## 🤝 기여

프로젝트 기여를 환영합니다! [개발 가이드](docs/DEVELOPMENT.md)를 참고해주세요.

## 📝 라이선스

이 프로젝트는 내부 사용 목적으로 개발되었습니다.

## 📞 문의

프로젝트 관련 문의사항이 있으시면 이슈를 등록해주세요.

---

**DB Manager** - 반도체 장비 DB 관리의 모든 것