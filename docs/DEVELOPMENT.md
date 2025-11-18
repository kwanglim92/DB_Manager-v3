# 개발 가이드

DB Manager 개발에 필요한 정보를 제공합니다.

## 🏗️ 아키텍처

### 전체 구조

```
┌─────────────────────────────────────┐
│           GUI Layer                  │
│         (Tkinter UI)                │
├─────────────────────────────────────┤
│        Service Layer                │
│   (비즈니스 로직, 서비스 패턴)        │
├─────────────────────────────────────┤
│         Data Layer                  │
│    (SQLite DB, File I/O)           │
└─────────────────────────────────────┘
```

### 주요 컴포넌트

#### 1. GUI Layer (`src/app/`)
- **manager.py**: 메인 윈도우 및 UI 관리
- **dialogs/**: 각종 다이얼로그 (Check list, Configuration 등)
- **simplified_qc_system.py**: QC 검수 UI

#### 2. Service Layer (`src/app/services/`)
- **ServiceFactory**: 서비스 생성 및 관리
- **EquipmentService**: 장비 관련 비즈니스 로직
- **ChecklistService**: Check list 관리
- **CategoryService**: Model/Type 계층 관리
- **ConfigurationService**: Configuration 관리

#### 3. Data Layer
- **schema.py**: 데이터베이스 스키마 정의
- **db_schema.py**: 레거시 호환 스키마
- **SQLite Database**: 로컬 데이터 저장

### 디자인 패턴

- **서비스 패턴**: 비즈니스 로직 캡슐화
- **팩토리 패턴**: ServiceFactory를 통한 서비스 생성
- **싱글톤 패턴**: ServiceRegistry, 캐시 서비스
- **의존성 주입**: 서비스 간 느슨한 결합

## 🛠️ 개발 환경 설정

### 1. 저장소 클론

```bash
git clone [repository-url]
cd DB_Manager
```

### 2. Python 환경

```bash
# 가상환경 생성 (권장)
python -m venv venv

# 활성화
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 의존성 설치
pip install pandas numpy
```

### 3. 개발 도구

- **IDE**: VS Code, PyCharm 권장
- **Python**: 3.7 이상
- **Git**: 버전 관리

## 📝 코딩 가이드라인

### Python 스타일

- **PEP 8** 준수
- **들여쓰기**: 4 spaces
- **최대 라인 길이**: 120자
- **인코딩**: UTF-8

### 명명 규칙

```python
# 클래스: PascalCase
class EquipmentService:
    pass

# 함수/메서드: snake_case
def get_equipment_list():
    pass

# 상수: UPPER_SNAKE_CASE
MAX_RETRY_COUNT = 3

# Private: 언더스코어 prefix
def _internal_method():
    pass
```

### 주석 및 문서화

```python
def calculate_similarity(text1: str, text2: str) -> float:
    """
    두 텍스트의 유사도를 계산합니다.
    
    Args:
        text1: 첫 번째 텍스트
        text2: 두 번째 텍스트
        
    Returns:
        0.0 ~ 1.0 사이의 유사도 값
        
    Example:
        >>> calculate_similarity("hello", "hallo")
        0.8
    """
    pass
```

## 🧪 테스트

### 단위 테스트

```python
# tools/test_*.py 파일에서 테스트 작성
import unittest

class TestEquipmentService(unittest.TestCase):
    def test_get_equipment_list(self):
        # 준비
        service = EquipmentService()
        
        # 실행
        result = service.get_equipment_list()
        
        # 검증
        self.assertIsNotNone(result)
        self.assertGreater(len(result), 0)
```

### 테스트 실행

```bash
# 개별 테스트
python tools/test_phase1.py

# 통합 테스트
python tools/test_phase1_e2e.py

# 디버그
python tools/debug_toolkit.py
```

## 🔧 디버깅

### 로깅 사용

```python
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def process_data(data):
    logger.debug(f"Processing {len(data)} items")
    try:
        # 처리 로직
        result = transform(data)
        logger.info("Processing completed successfully")
        return result
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise
```

### 디버그 도구

```bash
# 시스템 상태 확인
python tools/debug_toolkit.py health

# 장비 데이터 확인
python tools/debug_toolkit.py equipment

# 서비스 상태 확인
python tools/debug_toolkit.py services
```

## 📦 빌드 및 배포

### 실행 파일 생성

```bash
# PyInstaller 설치
pip install pyinstaller

# 빌드 스크립트 실행
cd scripts
build.bat  # Windows
```

### 배포 체크리스트

- [ ] 모든 테스트 통과
- [ ] 버전 번호 업데이트
- [ ] CHANGELOG.md 업데이트
- [ ] 데이터베이스 마이그레이션 확인
- [ ] 문서 업데이트

## 🤝 기여 방법

### 1. 이슈 생성
- 버그 리포트
- 기능 제안
- 개선 사항

### 2. 브랜치 전략

```bash
# 기능 개발
git checkout -b feature/new-feature

# 버그 수정
git checkout -b fix/bug-description

# 문서 작업
git checkout -b docs/update-readme
```

### 3. 커밋 메시지

```
type(scope): subject

body (optional)

footer (optional)
```

예시:
```
feat(checklist): Add dynamic checklist management

- Implement CRUD operations for checklist items
- Add validation rules support
- Create audit trail logging

Closes #123
```

### 4. Pull Request
- 명확한 제목과 설명
- 관련 이슈 링크
- 테스트 결과 포함

## 📚 참고 자료

### 내부 문서
- [API 문서](API.md)
- [데이터베이스 스키마](API.md#database-schema)
- [서비스 레이어 API](API.md#service-layer)

### 외부 자료
- [Python 공식 문서](https://docs.python.org/3/)
- [Tkinter 튜토리얼](https://docs.python.org/3/library/tkinter.html)
- [SQLite 문서](https://www.sqlite.org/docs.html)
- [Pandas 문서](https://pandas.pydata.org/docs/)

## ❓ FAQ

### Q: 새로운 서비스를 추가하려면?
1. `services/interfaces/`에 인터페이스 정의
2. `services/`에 구현 클래스 작성
3. `ServiceFactory`에 등록
4. 테스트 작성

### Q: 데이터베이스 스키마를 변경하려면?
1. `schema.py` 수정
2. 마이그레이션 스크립트 작성
3. 기존 데이터 백업
4. 테스트 환경에서 검증

### Q: UI 컴포넌트를 추가하려면?
1. `dialogs/` 폴더에 새 다이얼로그 생성
2. `manager.py`에서 호출 메서드 추가
3. 메뉴 또는 버튼에 연결

---

추가 질문이나 도움이 필요하면 이슈를 등록해주세요.