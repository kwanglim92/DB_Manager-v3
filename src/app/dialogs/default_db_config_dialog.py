"""
Default DB 구성 선택 다이얼로그
AE/Cabinet/EFEM 조합으로 구성을 선택하는 간단한 UI
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
from typing import Optional, Dict, Callable

class DefaultDBConfigDialog:
    """Default DB 구성 선택 다이얼로그"""
    
    def __init__(self, parent, db_service, model_id: int, model_name: str,
                 on_config_selected: Optional[Callable] = None):
        """
        Args:
            parent: 부모 윈도우
            db_service: DefaultDBService 인스턴스
            model_id: 선택된 모델 ID
            model_name: 모델명
            on_config_selected: 구성 선택 시 콜백 함수
        """
        self.parent = parent
        self.db_service = db_service
        self.model_id = model_id
        self.model_name = model_name
        self.on_config_selected = on_config_selected
        self.selected_config_id = None
        
        self.create_dialog()
        
    def create_dialog(self):
        """다이얼로그 생성"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(f"장비 구성 선택 - {self.model_name}")
        self.dialog.geometry("500x400")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # 중앙 배치
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - 250
        y = (self.dialog.winfo_screenheight() // 2) - 200
        self.dialog.geometry(f"500x400+{x}+{y}")
        
        self.create_widgets()
        
    def create_widgets(self):
        """위젯 생성"""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 제목
        title_label = ttk.Label(main_frame, text=f"모델: {self.model_name}", 
                               font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # 구성 선택 프레임
        config_frame = ttk.LabelFrame(main_frame, text="장비 구성 선택", padding="10")
        config_frame.pack(fill=tk.X, pady=10)
        
        # AE 타입 선택
        ae_frame = ttk.Frame(config_frame)
        ae_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(ae_frame, text="AE 타입:", width=15).pack(side=tk.LEFT)
        self.ae_var = tk.StringVar(value="일체형")
        ae_combo = ttk.Combobox(ae_frame, textvariable=self.ae_var,
                                values=self.db_service.AE_TYPES,
                                state="readonly", width=20)
        ae_combo.pack(side=tk.LEFT, padx=5)
        ae_combo.bind('<<ComboboxSelected>>', self.on_config_changed)
        
        # Cabinet 타입 선택
        cabinet_frame = ttk.Frame(config_frame)
        cabinet_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(cabinet_frame, text="Cabinet 타입:", width=15).pack(side=tk.LEFT)
        self.cabinet_var = tk.StringVar(value="T1")
        cabinet_combo = ttk.Combobox(cabinet_frame, textvariable=self.cabinet_var,
                                     values=["T1", "PB", "없음"],
                                     state="readonly", width=20)
        cabinet_combo.pack(side=tk.LEFT, padx=5)
        cabinet_combo.bind('<<ComboboxSelected>>', self.on_config_changed)
        
        # EFEM 타입 선택
        efem_frame = ttk.Frame(config_frame)
        efem_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(efem_frame, text="EFEM 타입:", width=15).pack(side=tk.LEFT)
        self.efem_var = tk.StringVar(value="Single")
        efem_combo = ttk.Combobox(efem_frame, textvariable=self.efem_var,
                                  values=self.db_service.EFEM_TYPES,
                                  state="readonly", width=20)
        efem_combo.pack(side=tk.LEFT, padx=5)
        efem_combo.bind('<<ComboboxSelected>>', self.on_config_changed)
        
        # 구성 코드 표시
        code_frame = ttk.Frame(config_frame)
        code_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(code_frame, text="구성 코드:").pack(side=tk.LEFT)
        self.code_label = ttk.Label(code_frame, text="", font=('Courier', 10, 'bold'))
        self.code_label.pack(side=tk.LEFT, padx=10)
        
        # 옵션 프레임 (접을 수 있음)
        self.options_frame = ttk.LabelFrame(main_frame, text="추가 옵션 (선택사항)", 
                                           padding="10")
        self.options_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Wafer 크기
        wafer_frame = ttk.Frame(self.options_frame)
        wafer_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(wafer_frame, text="Wafer 크기:", width=15).pack(side=tk.LEFT)
        self.wafer_var = tk.StringVar(value="200mm")
        wafer_combo = ttk.Combobox(wafer_frame, textvariable=self.wafer_var,
                                   values=["150mm", "200mm", "300mm"],
                                   state="readonly", width=20)
        wafer_combo.pack(side=tk.LEFT, padx=5)
        
        # Chamber 수
        chamber_frame = ttk.Frame(self.options_frame)
        chamber_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(chamber_frame, text="Chamber 수:", width=15).pack(side=tk.LEFT)
        self.chamber_var = tk.StringVar(value="2")
        chamber_spin = ttk.Spinbox(chamber_frame, from_=1, to=4, 
                                   textvariable=self.chamber_var,
                                   width=20)
        chamber_spin.pack(side=tk.LEFT, padx=5)
        
        # Auto Loader
        auto_frame = ttk.Frame(self.options_frame)
        auto_frame.pack(fill=tk.X, pady=5)
        
        self.auto_loader_var = tk.BooleanVar(value=False)
        auto_check = ttk.Checkbutton(auto_frame, text="Auto Loader 포함",
                                     variable=self.auto_loader_var)
        auto_check.pack(side=tk.LEFT, padx=(120, 0))
        
        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # 구성 복사 버튼
        copy_btn = ttk.Button(button_frame, text="다른 구성에서 복사",
                             command=self.copy_from_other)
        copy_btn.pack(side=tk.LEFT, padx=5)
        
        # 취소/확인 버튼
        cancel_btn = ttk.Button(button_frame, text="취소",
                               command=self.dialog.destroy)
        cancel_btn.pack(side=tk.RIGHT, padx=5)
        
        ok_btn = ttk.Button(button_frame, text="확인",
                           command=self.on_ok)
        ok_btn.pack(side=tk.RIGHT, padx=5)
        
        # 초기 구성 코드 업데이트
        self.update_config_code()
        
    def on_config_changed(self, event=None):
        """구성 변경 시 호출"""
        self.update_config_code()
        
    def update_config_code(self):
        """구성 코드 업데이트"""
        ae_type = self.ae_var.get()
        cabinet_type = self.cabinet_var.get() if self.cabinet_var.get() != "없음" else None
        efem_type = self.efem_var.get()
        
        # 코드 생성
        ae_code = 'I' if ae_type == '일체형' else 'S'
        cabinet_code = cabinet_type or 'NC'
        efem_code = efem_type[0] if efem_type != 'None' else 'N'
        
        code = f"M{self.model_id}_{ae_code}_{cabinet_code}_{efem_code}"
        self.code_label.config(text=code)
        
    def get_options(self) -> Dict:
        """옵션 정보 수집"""
        return {
            'wafer_size': self.wafer_var.get(),
            'chamber_count': int(self.chamber_var.get()),
            'auto_loader': self.auto_loader_var.get()
        }
        
    def copy_from_other(self):
        """다른 구성에서 복사"""
        # 복사 다이얼로그 표시
        copy_dialog = CopyConfigDialog(self.dialog, self.db_service, 
                                      self.model_id, self.on_copy_selected)
        
    def on_copy_selected(self, source_config_id: int):
        """복사할 구성이 선택되었을 때"""
        ae_type = self.ae_var.get()
        cabinet_type = self.cabinet_var.get() if self.cabinet_var.get() != "없음" else None
        efem_type = self.efem_var.get()
        
        try:
            # 구성 복사
            new_config_id = self.db_service.copy_configuration(
                source_config_id, self.model_id, 
                ae_type, cabinet_type, efem_type
            )
            
            self.selected_config_id = new_config_id
            messagebox.showinfo("성공", "구성이 복사되었습니다.")
            
        except Exception as e:
            messagebox.showerror("오류", f"복사 실패: {str(e)}")
            
    def on_ok(self):
        """확인 버튼 클릭"""
        ae_type = self.ae_var.get()
        cabinet_type = self.cabinet_var.get() if self.cabinet_var.get() != "없음" else None
        efem_type = self.efem_var.get()
        options = self.get_options()
        
        try:
            # 구성 생성 또는 조회
            config_id = self.db_service.get_or_create_configuration(
                self.model_id, ae_type, cabinet_type, efem_type, options
            )
            
            self.selected_config_id = config_id
            
            # 콜백 호출
            if self.on_config_selected:
                self.on_config_selected(config_id)
                
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("오류", f"구성 생성 실패: {str(e)}")


class CopyConfigDialog:
    """구성 복사 다이얼로그"""
    
    def __init__(self, parent, db_service, current_model_id: int, 
                 on_selected: Callable):
        self.parent = parent
        self.db_service = db_service
        self.current_model_id = current_model_id
        self.on_selected = on_selected
        
        self.create_dialog()
        
    def create_dialog(self):
        """다이얼로그 생성"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("구성 복사")
        self.dialog.geometry("400x300")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # 중앙 배치
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - 200
        y = (self.dialog.winfo_screenheight() // 2) - 150
        self.dialog.geometry(f"400x300+{x}+{y}")
        
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 설명
        ttk.Label(main_frame, text="복사할 구성을 선택하세요:").pack(pady=5)
        
        # 구성 목록
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 리스트박스
        self.config_list = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                      height=10)
        self.config_list.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.config_list.yview)
        
        # 구성 목록 로드
        self.load_configurations()
        
        # 버튼
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="취소",
                  command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="선택",
                  command=self.on_select).pack(side=tk.RIGHT, padx=5)
        
    def load_configurations(self):
        """구성 목록 로드"""
        # TODO: 실제 구성 목록 조회 구현
        # 임시 데이터
        configs = [
            (1, "일체형 / T1 / Single"),
            (2, "분리형 / PB / Double"),
            (3, "일체형 / T1 / None")
        ]
        
        for config_id, display_name in configs:
            self.config_list.insert(tk.END, f"{display_name} (ID: {config_id})")
            
    def on_select(self):
        """선택 버튼 클릭"""
        selection = self.config_list.curselection()
        if not selection:
            messagebox.showwarning("경고", "구성을 선택하세요.")
            return
            
        # ID 추출 (간단한 파싱)
        selected_text = self.config_list.get(selection[0])
        config_id = int(selected_text.split("ID: ")[1].split(")")[0])
        
        self.on_selected(config_id)
        self.dialog.destroy()