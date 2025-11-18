#!/usr/bin/env python3
"""
QC 간소화 UI 통합 모듈
기존 UI와 새 UI를 병행 운영하기 위한 통합 레이어
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime
from typing import Optional

# 간소화된 QC 모듈 임포트
try:
    from .qc_simplified import SimplifiedQCInspection
    SIMPLIFIED_QC_AVAILABLE = True
except ImportError:
    SIMPLIFIED_QC_AVAILABLE = False
    print("Warning: Simplified QC module not available")

class QCModeSelector:
    """QC UI 모드 선택 및 관리"""
    
    # UI 모드 상수
    MODE_LEGACY = 'legacy'
    MODE_SIMPLIFIED = 'simplified'
    MODE_BOTH = 'both'
    
    def __init__(self, parent, db_schema, config_path='config/qc_ui_config.json'):
        """
        초기화
        
        Args:
            parent: 부모 위젯
            db_schema: DBSchema 인스턴스
            config_path: 설정 파일 경로
        """
        self.parent = parent
        self.db_schema = db_schema
        self.config_path = config_path
        
        # 설정 로드
        self.config = self.load_config()
        
        # 사용 통계
        self.usage_stats = {
            'legacy': {'count': 0, 'time': 0, 'last_used': None},
            'simplified': {'count': 0, 'time': 0, 'last_used': None}
        }
        
        # 프레임 생성
        self.frame = ttk.Frame(parent)
        
        # UI 생성
        self.create_ui()
        
    def load_config(self):
        """설정 파일 로드"""
        default_config = {
            'mode': self.MODE_BOTH,  # 기본값: 두 버전 모두 표시
            'default_tab': self.MODE_LEGACY,
            'show_mode_selector': True,
            'collect_stats': True,
            'transition_date': None
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
        except Exception as e:
            print(f"설정 파일 로드 오류: {e}")
            
        return default_config
        
    def save_config(self):
        """설정 파일 저장"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"설정 파일 저장 오류: {e}")
            
    def create_ui(self):
        """UI 생성"""
        mode = self.config.get('mode', self.MODE_BOTH)
        
        if mode == self.MODE_BOTH:
            # 두 버전 모두 표시
            self.create_both_ui()
        elif mode == self.MODE_SIMPLIFIED and SIMPLIFIED_QC_AVAILABLE:
            # 간소화 버전만
            self.create_simplified_only()
        else:
            # 레거시 버전만
            self.create_legacy_only()
            
    def create_both_ui(self):
        """두 버전 병행 UI"""
        # 모드 선택 패널
        if self.config.get('show_mode_selector', True):
            self.create_mode_selector()
            
        # 탭 노트북
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 레거시 탭
        self.legacy_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.legacy_frame, text="기존 QC 검수")
        self.create_legacy_ui(self.legacy_frame)
        
        # 간소화 탭
        if SIMPLIFIED_QC_AVAILABLE:
            self.simplified_tab = SimplifiedQCInspection(self.notebook, self.db_schema)
            self.notebook.add(self.simplified_tab.frame, text="간소화 QC 검수 (Beta)")
        
        # 기본 탭 선택
        default_tab = self.config.get('default_tab', self.MODE_LEGACY)
        if default_tab == self.MODE_SIMPLIFIED and SIMPLIFIED_QC_AVAILABLE:
            self.notebook.select(1)
        else:
            self.notebook.select(0)
            
        # 탭 변경 이벤트 추적
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
    def create_mode_selector(self):
        """모드 선택 패널"""
        selector_frame = ttk.Frame(self.frame)
        selector_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 안내 메시지
        ttk.Label(selector_frame, 
                 text="🔬 QC 검수 UI 선택 (A/B 테스트 중)",
                 font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        
        # 피드백 버튼
        ttk.Button(selector_frame,
                  text="📝 피드백",
                  command=self.show_feedback_dialog).pack(side=tk.RIGHT, padx=(5, 0))
        
        # 통계 버튼
        ttk.Button(selector_frame,
                  text="📊 사용 통계",
                  command=self.show_usage_stats).pack(side=tk.RIGHT, padx=(5, 0))
        
    def create_legacy_ui(self, parent):
        """레거시 UI 생성 (플레이스홀더)"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(frame,
                 text="기존 QC 검수 UI",
                 font=("Segoe UI", 14)).pack(pady=20)
        
        ttk.Label(frame,
                 text="여기에 기존 복잡한 UI가 표시됩니다\n"
                      "(Check List Focused, Full Inspection 등)",
                 font=("Segoe UI", 10),
                 foreground="gray").pack()
        
        # 실제 구현 시 여기에 기존 QC UI 코드 연결
        # self.create_original_qc_ui(frame)
        
    def create_simplified_only(self):
        """간소화 버전만 표시"""
        if SIMPLIFIED_QC_AVAILABLE:
            self.simplified_tab = SimplifiedQCInspection(self.frame, self.db_schema)
            self.simplified_tab.frame.pack(fill=tk.BOTH, expand=True)
        
    def create_legacy_only(self):
        """레거시 버전만 표시"""
        self.create_legacy_ui(self.frame)
        
    def on_tab_changed(self, event):
        """탭 변경 이벤트"""
        if not self.config.get('collect_stats', True):
            return
            
        try:
            selected_index = self.notebook.index("current")
            mode = self.MODE_LEGACY if selected_index == 0 else self.MODE_SIMPLIFIED
            
            # 통계 업데이트
            self.usage_stats[mode]['count'] += 1
            self.usage_stats[mode]['last_used'] = datetime.now().isoformat()
            
            # 세션 시작 시간 기록
            self.session_start = datetime.now()
            self.current_mode = mode
            
        except Exception as e:
            print(f"탭 변경 추적 오류: {e}")
            
    def show_feedback_dialog(self):
        """피드백 다이얼로그"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("QC UI 피드백")
        dialog.geometry("400x500")
        
        # 헤더
        header_frame = ttk.Frame(dialog)
        header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        ttk.Label(header_frame,
                 text="QC 검수 UI 피드백",
                 font=("Segoe UI", 14, "bold")).pack()
        
        ttk.Label(header_frame,
                 text="새로운 간소화 UI에 대한 의견을 들려주세요",
                 font=("Segoe UI", 9)).pack(pady=(5, 0))
        
        # 평가 섹션
        rating_frame = ttk.LabelFrame(dialog, text="평가", padding=10)
        rating_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.ratings = {}
        criteria = [
            ("사용 편의성", "ease_of_use"),
            ("처리 속도", "speed"),
            ("결과 가독성", "readability"),
            ("기능 완성도", "completeness")
        ]
        
        for label, key in criteria:
            row = ttk.Frame(rating_frame)
            row.pack(fill=tk.X, pady=5)
            
            ttk.Label(row, text=label, width=15).pack(side=tk.LEFT)
            
            var = tk.IntVar(value=3)
            self.ratings[key] = var
            
            scale = ttk.Scale(row, from_=1, to=5, variable=var,
                            orient=tk.HORIZONTAL, length=200)
            scale.pack(side=tk.LEFT, padx=(10, 10))
            
            value_label = ttk.Label(row, text="3")
            value_label.pack(side=tk.LEFT)
            
            # 값 표시 업데이트
            scale.config(command=lambda v, l=value_label: l.config(text=str(int(float(v)))))
        
        # 선호도
        pref_frame = ttk.LabelFrame(dialog, text="선호도", padding=10)
        pref_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.preference_var = tk.StringVar(value="both")
        ttk.Radiobutton(pref_frame, text="기존 UI 선호",
                       variable=self.preference_var,
                       value="legacy").pack(anchor=tk.W)
        ttk.Radiobutton(pref_frame, text="간소화 UI 선호",
                       variable=self.preference_var,
                       value="simplified").pack(anchor=tk.W)
        ttk.Radiobutton(pref_frame, text="둘 다 좋음",
                       variable=self.preference_var,
                       value="both").pack(anchor=tk.W)
        
        # 코멘트
        comment_frame = ttk.LabelFrame(dialog, text="추가 의견", padding=10)
        comment_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.comment_text = tk.Text(comment_frame, height=5, width=40)
        self.comment_text.pack(fill=tk.BOTH, expand=True)
        
        # 버튼
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=(10, 20))
        
        ttk.Button(button_frame,
                  text="제출",
                  command=lambda: self.submit_feedback(dialog)).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame,
                  text="취소",
                  command=dialog.destroy).pack(side=tk.RIGHT)
        
    def submit_feedback(self, dialog):
        """피드백 제출"""
        feedback = {
            'timestamp': datetime.now().isoformat(),
            'ratings': {k: v.get() for k, v in self.ratings.items()},
            'preference': self.preference_var.get(),
            'comment': self.comment_text.get('1.0', 'end-1c'),
            'usage_stats': self.usage_stats.copy()
        }
        
        # 피드백 저장
        feedback_file = 'data/qc_ui_feedback.json'
        try:
            feedbacks = []
            if os.path.exists(feedback_file):
                with open(feedback_file, 'r', encoding='utf-8') as f:
                    feedbacks = json.load(f)
                    
            feedbacks.append(feedback)
            
            os.makedirs(os.path.dirname(feedback_file), exist_ok=True)
            with open(feedback_file, 'w', encoding='utf-8') as f:
                json.dump(feedbacks, f, indent=2, ensure_ascii=False)
                
            messagebox.showinfo("감사합니다", "피드백이 저장되었습니다!")
            dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("오류", f"피드백 저장 실패:\n{str(e)}")
            
    def show_usage_stats(self):
        """사용 통계 표시"""
        stats_window = tk.Toplevel(self.parent)
        stats_window.title("QC UI 사용 통계")
        stats_window.geometry("400x300")
        
        # 통계 계산
        total_legacy = self.usage_stats['legacy']['count']
        total_simplified = self.usage_stats['simplified']['count']
        total = total_legacy + total_simplified
        
        if total > 0:
            legacy_percent = (total_legacy / total) * 100
            simplified_percent = (total_simplified / total) * 100
        else:
            legacy_percent = simplified_percent = 0
            
        # 표시
        frame = ttk.Frame(stats_window, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame,
                 text="📊 QC UI 사용 통계",
                 font=("Segoe UI", 14, "bold")).pack(pady=(0, 20))
        
        # 통계 테이블
        stats_text = f"""
기존 UI:
  • 사용 횟수: {total_legacy}회 ({legacy_percent:.1f}%)
  • 마지막 사용: {self.usage_stats['legacy']['last_used'] or 'N/A'}

간소화 UI:
  • 사용 횟수: {total_simplified}회 ({simplified_percent:.1f}%)
  • 마지막 사용: {self.usage_stats['simplified']['last_used'] or 'N/A'}

총 사용: {total}회
선호 UI: {'간소화' if total_simplified > total_legacy else '기존'} UI
        """
        
        ttk.Label(frame,
                 text=stats_text,
                 font=("Segoe UI", 10),
                 justify=tk.LEFT).pack()
        
        # 닫기 버튼
        ttk.Button(frame,
                  text="닫기",
                  command=stats_window.destroy).pack(pady=(20, 0))


class QCTabManager:
    """QC 탭 관리자 - 메인 앱 통합용"""
    
    @staticmethod
    def create_qc_tab(parent, db_schema, config=None):
        """
        QC 탭 생성 (설정에 따라 레거시/간소화/병행 모드)
        
        Args:
            parent: 부모 위젯
            db_schema: DBSchema 인스턴스
            config: 설정 딕셔너리 (선택)
            
        Returns:
            QCModeSelector 인스턴스
        """
        # 설정 로드
        if config is None:
            config_path = 'config/settings.json'
            try:
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        settings = json.load(f)
                        config = settings.get('qc_ui', {})
                else:
                    config = {}
            except:
                config = {}
        
        # QC 모드 선택기 생성
        selector = QCModeSelector(parent, db_schema)
        
        # 설정 적용
        if config:
            selector.config.update(config)
            selector.save_config()
            
        return selector