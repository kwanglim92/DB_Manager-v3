# Custom QC Configuration System
## DB 독립적인 Equipment Type 및 QC 스펙 관리 시스템

### 개요
사용자의 요청에 따라 Default DB에서 Equipment Type을 가져오는 대신, 사용자가 임의로 정의한 Equipment Type과 QC 검수 항목을 독립적으로 관리할 수 있는 시스템을 구현했습니다.

> 💡 **핵심 요구사항**: "장비 Type은 Default DB 값에서 가져오는게 아니라 내가 선정한 임의의 옵션처럼 고르고 거기에 내가 항목들을 적는게 좋을것 같아"

### 주요 특징

#### 1. **완전한 DB 독립성**
- Default DB와 완전히 분리된 독립적인 설정 시스템
- JSON 파일 기반 설정 저장/로드
- 사용자가 모든 Equipment Type과 스펙을 자유롭게 정의

#### 2. **유연한 Equipment Type 관리**
- Equipment Type 추가/수정/삭제 자유
- 각 Type별 독립적인 QC 검수 항목 설정
- 한국어/영어 혼용 가능한 이름 지원

#### 3. **사용자 친화적 인터페이스**
- GUI 기반 설정 편집 다이얼로그
- 실시간 설정 변경 및 적용
- 간소화된 QC 검수 UI와 완벽한 통합

### 시스템 구성

```
src/app/
├── qc_custom_config.py          # Custom Configuration 핵심 모듈
├── qc_simplified_custom.py      # Custom Config 기반 QC 검수 모듈
└── dialogs/
    └── qc_spec_editor_dialog.py # GUI 설정 편집 다이얼로그

test_simplified_qc_ui.py         # 통합 테스트 UI (Custom Config 적용)
qc_custom_config.json            # 사용자 정의 설정 파일
```

### 사용 방법

#### 1. Equipment Type 추가
```python
from src.app.qc_custom_config import CustomQCConfig

config = CustomQCConfig()
config.add_equipment_type("고객맞춤형 모델 A")
config.add_equipment_type("특수 장비 Type B")
```

#### 2. QC 검수 항목 정의
```python
specs = [
    {
        'item_name': '온도_센서',
        'min_spec': 20.0,
        'max_spec': 25.0,
        'unit': '°C',
        'enabled': True
    },
    {
        'item_name': '압력_게이지',
        'min_spec': 100.0,
        'max_spec': 200.0,
        'unit': 'kPa',
        'enabled': True
    }
]
config.update_specs("고객맞춤형 모델 A", specs)
```

#### 3. GUI에서 설정 편집
```python
# test_simplified_qc_ui.py 실행
# ⚙️ 설정 버튼 클릭
# Equipment Type 및 스펙 편집
# 저장 후 즉시 적용
```

### 설정 파일 구조 (JSON)

```json
{
  "version": "1.0.0",
  "equipment_types": [
    "Standard Model",
    "Advanced Model",
    "고객맞춤형 모델 A",
    "특수 장비 Type B"
  ],
  "specs": {
    "고객맞춤형 모델 A": [
      {
        "item_name": "온도_센서_1",
        "min_spec": 20.0,
        "max_spec": 25.0,
        "unit": "°C",
        "enabled": true
      },
      {
        "item_name": "압력_게이지",
        "min_spec": 100.0,
        "max_spec": 200.0,
        "unit": "kPa",
        "enabled": true
      }
    ]
  },
  "last_modified": "2024-01-17T10:30:00"
}
```

### 테스트 방법

#### 1. 기능 테스트
```bash
python test_custom_config_functionality.py
```

#### 2. UI 테스트
```bash
python test_simplified_qc_ui.py
```

### 장점

1. **완전한 자유도**: DB 스키마에 제약받지 않고 자유로운 설정
2. **빠른 적용**: 설정 변경 즉시 적용, DB 마이그레이션 불필요
3. **백업 용이**: JSON 파일 복사로 간단한 백업/복원
4. **다중 설정**: 여러 설정 파일을 만들어 상황별 사용 가능
5. **버전 관리**: Git으로 설정 변경 이력 추적 가능

### 마이그레이션 가이드

#### 기존 DB 기반 → Custom Configuration
1. 기존 DB의 Equipment Type 목록 확인
2. CustomQCConfig에 동일한 Type 추가
3. 각 Type별 QC 스펙 정의
4. test_simplified_qc_ui.py로 테스트
5. 메인 애플리케이션에 통합

### 향후 개선 사항

1. **설정 템플릿**: 자주 사용하는 설정을 템플릿으로 저장
2. **설정 공유**: 팀 간 설정 파일 공유 기능
3. **설정 검증**: 스펙 범위 유효성 자동 검증
4. **설정 히스토리**: 설정 변경 이력 관리
5. **클라우드 동기화**: 설정 파일 클라우드 백업

### FAQ

**Q: DB와 Custom Config를 동시에 사용할 수 있나요?**
A: 네, 가능합니다. 사용자가 선택할 수 있도록 옵션을 제공할 수 있습니다.

**Q: 기존 데이터와 호환되나요?**
A: JSON 형식이므로 간단한 변환 스크립트로 기존 데이터를 가져올 수 있습니다.

**Q: 여러 사용자가 동시에 사용할 수 있나요?**
A: 각 사용자별로 다른 설정 파일을 사용하면 됩니다.

---

✅ **결론**: 사용자의 요구사항대로 Equipment Type과 QC 스펙을 DB와 완전히 독립적으로 관리할 수 있는 시스템을 성공적으로 구현했습니다.