# 📋 QC 검수 탭 UI 단계적 전환 계획

## 🎯 전략
기존 UI를 유지하면서 새로운 간소화 UI를 병행 운영하여, 충분한 테스트와 검증 후 전환

## 📅 단계별 로드맵

### 🔵 Phase 1: 프로토타입 개발 (Week 1)
**목표**: 독립적인 간소화 UI 프로토타입 생성

#### 1.1 독립 테스트 모듈 생성
```python
# test_simplified_qc_ui.py
class SimplifiedQCTab:
    """간소화된 QC 검수 UI 프로토타입"""
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.create_simplified_ui()
```

#### 1.2 핵심 기능만 구현
- Equipment Type 선택
- 파일 선택 및 자동 로드
- QC_Spec_Master 기반 단순 비교
- Pass/Fail 결과 표시
- 기본 내보내기

#### 1.3 독립 실행 가능한 테스트 앱
```python
# standalone_qc_test.py
if __name__ == "__main__":
    root = tk.Tk()
    root.title("QC 검수 간소화 UI 테스트")
    
    # 기존 탭
    notebook = ttk.Notebook(root)
    old_tab = create_old_qc_tab()
    notebook.add(old_tab, text="기존 QC 검수")
    
    # 새 탭
    new_tab = SimplifiedQCTab(notebook)
    notebook.add(new_tab.frame, text="간소화 QC 검수 (Beta)")
    
    root.mainloop()
```

### 🟢 Phase 2: A/B 테스트 모드 (Week 2-3)
**목표**: 실제 환경에서 병행 운영하며 비교 검증

#### 2.1 설정 파일에 모드 추가
```json
// config/settings.json
{
    "qc_ui_mode": {
        "enabled": true,
        "mode": "both",  // "legacy" | "simplified" | "both"
        "default_tab": "legacy",
        "show_comparison": true
    }
}
```

#### 2.2 메인 앱에 토글 기능 추가
```python
class DBManager:
    def create_qc_check_tab(self):
        """QC 검수 탭 생성 - 모드 선택 가능"""
        
        # 설정 읽기
        ui_mode = self.config.get('qc_ui_mode', {}).get('mode', 'legacy')
        
        if ui_mode == 'both':
            # 서브 탭으로 두 버전 모두 표시
            self.qc_notebook = ttk.Notebook(self.qc_check_frame)
            
            # 기존 UI
            self.create_legacy_qc_ui(self.qc_notebook)
            
            # 간소화 UI (Beta)
            self.create_simplified_qc_ui(self.qc_notebook)
            
        elif ui_mode == 'simplified':
            self.create_simplified_qc_ui(self.qc_check_frame)
        else:
            self.create_legacy_qc_ui(self.qc_check_frame)
```

#### 2.3 사용 통계 수집
```python
class UsageTracker:
    """UI 사용 패턴 추적"""
    def __init__(self):
        self.stats = {
            'legacy': {'count': 0, 'time': 0, 'errors': 0},
            'simplified': {'count': 0, 'time': 0, 'errors': 0}
        }
    
    def track_usage(self, ui_type, action, duration=None):
        """사용 통계 기록"""
        self.stats[ui_type]['count'] += 1
        if duration:
            self.stats[ui_type]['time'] += duration
    
    def generate_report(self):
        """비교 리포트 생성"""
        return {
            'total_usage': self.stats,
            'preference': 'simplified' if self.stats['simplified']['count'] > 
                         self.stats['legacy']['count'] else 'legacy',
            'avg_time': {
                'legacy': self.stats['legacy']['time'] / max(1, self.stats['legacy']['count']),
                'simplified': self.stats['simplified']['time'] / max(1, self.stats['simplified']['count'])
            }
        }
```

### 🟡 Phase 3: 피드백 수집 및 개선 (Week 4-5)
**목표**: 사용자 피드백 기반 개선

#### 3.1 피드백 수집 시스템
```python
class FeedbackDialog:
    """사용자 피드백 수집"""
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("QC UI 피드백")
        
        # 평가 항목
        self.create_rating_section()
        self.create_comment_section()
        self.create_preference_section()
    
    def create_rating_section(self):
        """평가 섹션"""
        criteria = [
            "사용 편의성",
            "처리 속도",
            "결과 가독성",
            "기능 완성도"
        ]
        
        for criterion in criteria:
            frame = ttk.Frame(self.dialog)
            ttk.Label(frame, text=criterion).pack(side=tk.LEFT)
            ttk.Scale(frame, from_=1, to=5).pack(side=tk.LEFT)
            frame.pack()
```

#### 3.2 개선 사항 추적
```markdown
## 피드백 로그

### Week 4 피드백
- ✅ 파일 다중 선택 기능 필요
- ✅ 결과 필터링 옵션 추가
- ⏳ 컬럼 너비 조정 기능
- ⏳ 키보드 단축키 지원

### Week 5 개선
- 구현: 다중 파일 선택
- 구현: Fail 항목만 보기 필터
- 예정: 사용자 정의 컬럼 너비
```

### 🔴 Phase 4: 점진적 전환 (Week 6-7)
**목표**: 검증된 UI로 순차적 전환

#### 4.1 전환 시나리오
```python
class TransitionManager:
    """UI 전환 관리"""
    
    TRANSITION_STAGES = {
        'stage_1': {
            'date': '2025-12-01',
            'action': 'show_notification',
            'message': '새로운 간소화 UI가 베타 테스트 중입니다'
        },
        'stage_2': {
            'date': '2025-12-08', 
            'action': 'set_default',
            'config': {'default_tab': 'simplified'}
        },
        'stage_3': {
            'date': '2025-12-15',
            'action': 'deprecate_legacy',
            'show_warning': True
        },
        'stage_4': {
            'date': '2025-12-22',
            'action': 'remove_legacy',
            'backup': True
        }
    }
    
    def check_transition_stage(self):
        """현재 전환 단계 확인"""
        from datetime import datetime
        current_date = datetime.now()
        
        for stage, config in self.TRANSITION_STAGES.items():
            stage_date = datetime.strptime(config['date'], '%Y-%m-%d')
            if current_date >= stage_date:
                self.execute_stage_action(stage, config)
```

#### 4.2 롤백 계획
```python
class RollbackManager:
    """문제 발생 시 롤백"""
    
    def create_backup(self):
        """현재 상태 백업"""
        import shutil
        import datetime
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_files = [
            'src/app/manager.py',
            'src/app/qc.py',
            'config/settings.json'
        ]
        
        for file in backup_files:
            shutil.copy(file, f"{file}.backup_{timestamp}")
    
    def rollback_to_legacy(self):
        """기존 UI로 즉시 롤백"""
        self.config['qc_ui_mode']['mode'] = 'legacy'
        self.config['qc_ui_mode']['force_legacy'] = True
        self.save_config()
        messagebox.showinfo("롤백", "기존 UI로 복원되었습니다")
```

### ⚫ Phase 5: 완전 전환 및 정리 (Week 8)
**목표**: 레거시 코드 제거 및 최종 정리

#### 5.1 코드 정리
- 기존 UI 코드를 archive 폴더로 이동
- 불필요한 조건문 제거
- 문서 업데이트

#### 5.2 최종 구조
```python
# src/app/qc_simplified.py
class QCInspectionTab:
    """최종 간소화된 QC 검수 탭"""
    
    def __init__(self, parent, db_schema):
        self.parent = parent
        self.db_schema = db_schema
        self.qc_spec_service = QCSpecService(db_schema)
        
        # UI 생성
        self.create_ui()
        
    def create_ui(self):
        """간소화된 UI 생성"""
        # 제어 패널
        self.create_control_panel()
        
        # 결과 테이블
        self.create_results_table()
        
        # 요약 패널
        self.create_summary_panel()
```

## 🧪 테스트 계획

### 단위 테스트
```python
# tests/test_simplified_qc.py
class TestSimplifiedQC(unittest.TestCase):
    def test_file_loading(self):
        """파일 로딩 테스트"""
        pass
    
    def test_spec_matching(self):
        """스펙 매칭 테스트"""
        pass
    
    def test_pass_fail_logic(self):
        """Pass/Fail 판정 테스트"""
        pass
```

### 통합 테스트
```python
# tests/test_qc_integration.py
class TestQCIntegration(unittest.TestCase):
    def test_end_to_end_flow(self):
        """전체 플로우 테스트"""
        # 1. Equipment 선택
        # 2. 파일 로드
        # 3. 검수 실행
        # 4. 결과 확인
        # 5. 내보내기
        pass
```

### 성능 테스트
```python
# tests/test_performance.py
class TestPerformance(unittest.TestCase):
    def test_large_file_handling(self):
        """대용량 파일 처리"""
        # 1000+ 항목 파일 테스트
        pass
    
    def test_ui_responsiveness(self):
        """UI 반응 속도"""
        # 클릭 -> 결과 표시 시간 측정
        pass
```

## 📊 성공 지표

### 정량적 지표
- **처리 시간**: 기존 대비 50% 단축
- **클릭 수**: 6회 → 2회
- **오류율**: 1% 미만
- **사용자 만족도**: 4.0/5.0 이상

### 정성적 지표
- 직관적인 UI
- 학습 곡선 감소
- 유지보수 용이성
- 확장 가능성

## 🚦 Go/No-Go 결정 기준

### Go 조건 (전환 진행)
- ✅ 핵심 기능 100% 동작
- ✅ 성능 지표 달성
- ✅ 사용자 선호도 70% 이상
- ✅ 중대 버그 없음

### No-Go 조건 (전환 보류)
- ❌ 데이터 정합성 문제
- ❌ 성능 저하
- ❌ 사용자 저항 심각
- ❌ 호환성 문제

## 📝 체크리스트

### Phase 1 완료 조건
- [ ] 프로토타입 완성
- [ ] 독립 실행 가능
- [ ] 기본 기능 동작

### Phase 2 완료 조건
- [ ] A/B 테스트 환경 구축
- [ ] 사용 통계 수집 시작
- [ ] 초기 피드백 수집

### Phase 3 완료 조건
- [ ] 피드백 20건 이상
- [ ] 주요 개선 사항 반영
- [ ] 안정성 검증

### Phase 4 완료 조건
- [ ] 전환 계획 공지
- [ ] 롤백 계획 준비
- [ ] 사용자 교육 자료

### Phase 5 완료 조건
- [ ] 레거시 코드 정리
- [ ] 문서 업데이트
- [ ] 최종 검증

---
*작성일: 2025-11-17*
*목적: 안전한 UI 전환을 위한 단계적 접근*
*예상 기간: 8주*