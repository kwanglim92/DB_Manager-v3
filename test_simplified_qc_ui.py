#!/usr/bin/env python3
"""
간소화된 QC 검수 UI 프로토타입
Phase 1: 독립적인 테스트 모듈 - Custom Configuration 버전
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from datetime import datetime
import json
import os
import sys

# Custom QC 모듈 import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.app.qc_custom_config import CustomQCConfig
from src.app.dialogs.qc_spec_editor_dialog import QCSpecEditorDialog

class SimplifiedQCTab:
    """간소화된 QC 검수 UI - Custom Configuration 버전"""
    
    def __init__(self, parent, root_window=None):
        self.parent = parent
        self.root_window = root_window  # 설정 다이얼로그용
        self.frame = ttk.Frame(parent)
        self.selected_files = []
        self.qc_results = []
        
        # Custom Configuration 로드
        self.config = CustomQCConfig(config_path="qc_custom_config.json")
        self.ensure_default_config()
        
        # UI 생성
        self.create_ui()
    
    def ensure_default_config(self):
        """기본 설정 확인 및 생성"""
        # Equipment Types이 없으면 기본값 추가
        if not self.config.get_equipment_types():
            # 기본 Equipment Types 추가
            default_types = [
                "Standard Model",
                "Advanced Model", 
                "Custom Model",
                "Test Configuration"
            ]
            
            for eq_type in default_types:
                self.config.add_equipment_type(eq_type)
                
                # 각 타입별 기본 스펙 추가
                if eq_type == "Standard Model":
                    specs = [
                        {'item_name': 'Temperature', 'min_spec': 20, 'max_spec': 25, 'unit': '°C', 'enabled': True},
                        {'item_name': 'Pressure', 'min_spec': 100, 'max_spec': 200, 'unit': 'kPa', 'enabled': True},
                        {'item_name': 'Flow_Rate', 'min_spec': 10, 'max_spec': 20, 'unit': 'L/min', 'enabled': True}
                    ]
                elif eq_type == "Advanced Model":
                    specs = [
                        {'item_name': 'Temperature', 'min_spec': 18, 'max_spec': 28, 'unit': '°C', 'enabled': True},
                        {'item_name': 'Pressure', 'min_spec': 80, 'max_spec': 220, 'unit': 'kPa', 'enabled': True},
                        {'item_name': 'Voltage', 'min_spec': 3.2, 'max_spec': 3.4, 'unit': 'V', 'enabled': True},
                        {'item_name': 'Current', 'min_spec': 0.8, 'max_spec': 1.2, 'unit': 'A', 'enabled': True}
                    ]
                else:
                    # 기본 빈 스펙
                    specs = [
                        {'item_name': 'Item_1', 'min_spec': 0, 'max_spec': 100, 'unit': '', 'enabled': True},
                        {'item_name': 'Item_2', 'min_spec': 0, 'max_spec': 100, 'unit': '', 'enabled': True}
                    ]
                
                self.config.update_specs(eq_type, specs)
            
            self.config.save_config()
    
    def create_ui(self):
        """간소화된 UI 생성"""
        
        # 1. 제어 패널 (한 줄)
        control_panel = ttk.Frame(self.frame)
        control_panel.pack(fill=tk.X, padx=10, pady=5)
        
        # Equipment Type 선택
        ttk.Label(control_panel, text="Equipment Type:", 
                 font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.equipment_var = tk.StringVar()
        self.equipment_combo = ttk.Combobox(control_panel, 
                                           textvariable=self.equipment_var,
                                           values=self.config.get_equipment_types(),
                                           width=20, state="readonly")
        self.equipment_combo.pack(side=tk.LEFT, padx=(0, 15))
        equipment_types = self.config.get_equipment_types()
        if equipment_types:
            self.equipment_combo.set(equipment_types[0])
        
        # 설정 편집 버튼
        self.config_btn = ttk.Button(control_panel, text="⚙️ 설정",
                                    command=self.edit_config)
        self.config_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 파일 선택 버튼
        self.select_btn = ttk.Button(control_panel, text="📁 파일 선택",
                                    command=self.select_files)
        self.select_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 새로고침 버튼
        self.refresh_btn = ttk.Button(control_panel, text="🔄 새로고침",
                                     command=self.refresh_results)
        self.refresh_btn.pack(side=tk.LEFT)
        
        # 선택된 파일 표시
        self.file_label = ttk.Label(control_panel, text="파일 미선택",
                                   font=("Segoe UI", 9), foreground="gray")
        self.file_label.pack(side=tk.LEFT, padx=(20, 0))
        
        # 2. 결과 테이블
        result_frame = ttk.LabelFrame(self.frame, text="📊 검수 결과", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 트리뷰 생성
        columns = ('item_name', 'measured', 'min_spec', 'max_spec', 'result')
        self.result_tree = ttk.Treeview(result_frame, columns=columns, 
                                       show='headings', height=15)
        
        # 컬럼 헤더 설정
        headers = {
            'item_name': 'Item Name',
            'measured': '측정값',
            'min_spec': 'Min Spec',
            'max_spec': 'Max Spec',
            'result': '결과'
        }
        
        widths = {
            'item_name': 150,
            'measured': 100,
            'min_spec': 80,
            'max_spec': 80,
            'result': 80
        }
        
        for col in columns:
            self.result_tree.heading(col, text=headers[col])
            self.result_tree.column(col, width=widths[col])
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(result_frame, orient="vertical",
                                command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=scrollbar.set)
        
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 3. 요약 패널
        summary_frame = ttk.LabelFrame(self.frame, text="📈 검수 요약", padding=10)
        summary_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 요약 정보
        self.summary_label = ttk.Label(summary_frame, 
                                      text="대기 중...",
                                      font=("Segoe UI", 11))
        self.summary_label.pack(side=tk.LEFT)
        
        # 내보내기 버튼
        self.export_btn = ttk.Button(summary_frame, text="📥 결과 내보내기",
                                    command=self.export_results, state='disabled')
        self.export_btn.pack(side=tk.RIGHT)
        
        # Pass 항목만 보기 체크박스
        self.show_fail_only = tk.BooleanVar()
        ttk.Checkbutton(summary_frame, text="Fail 항목만 보기",
                       variable=self.show_fail_only,
                       command=self.filter_results).pack(side=tk.RIGHT, padx=(0, 20))
    
    def select_files(self):
        """파일 선택"""
        files = filedialog.askopenfilenames(
            title="QC 검수할 파일 선택",
            filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"), 
                      ("All files", "*.*")]
        )
        
        if files:
            self.selected_files = files
            # 파일명 표시
            if len(files) == 1:
                filename = os.path.basename(files[0])
                self.file_label.config(text=filename, foreground="black")
            else:
                self.file_label.config(text=f"{len(files)}개 파일 선택됨", 
                                     foreground="black")
            
            # 자동으로 검수 실행
            self.run_qc_inspection()
    
    def edit_config(self):
        """설정 편집 다이얼로그 열기"""
        if self.root_window:
            dialog = QCSpecEditorDialog(self.root_window, self.config)
            if dialog.result:
                # 설정이 변경되면 저장 및 UI 업데이트
                self.config = dialog.result
                self.config.save_config()
                
                # Equipment Type 콤보박스 업데이트
                self.equipment_combo['values'] = self.config.get_equipment_types()
                equipment_types = self.config.get_equipment_types()
                if equipment_types:
                    # 현재 선택된 타입이 여전히 존재하면 유지
                    current = self.equipment_var.get()
                    if current in equipment_types:
                        self.equipment_combo.set(current)
                    else:
                        self.equipment_combo.set(equipment_types[0])
                
                messagebox.showinfo("완료", "설정이 저장되었습니다")
    
    def run_qc_inspection(self):
        """QC 검수 실행"""
        if not self.selected_files:
            messagebox.showwarning("경고", "파일을 먼저 선택하세요")
            return
        
        # 선택된 Equipment Type 가져오기
        selected_type = self.equipment_var.get()
        if not selected_type:
            messagebox.showwarning("경고", "Equipment Type을 선택하세요")
            return
        
        # 해당 타입의 스펙 가져오기
        specs = self.config.get_specs(selected_type)
        if not specs:
            messagebox.showwarning("경고", f"{selected_type}에 대한 스펙이 정의되지 않았습니다.\n⚙️ 설정 버튼으로 스펙을 추가하세요.")
            return
        
        # 결과 초기화
        self.qc_results = []
        
        # 샘플 데이터 생성 (실제는 파일에서 읽음)
        import random
        for spec_item in specs:
            if not spec_item.get('enabled', True):
                continue  # 비활성화된 항목은 건너뛰기
            
            item_name = spec_item['item_name']
            min_spec = spec_item['min_spec']
            max_spec = spec_item['max_spec']
            unit = spec_item.get('unit', '')
            
            # 측정값 생성 (일부는 스펙 벗어나게)
            if random.random() > 0.8:  # 20% 확률로 Fail
                measured = min_spec - random.uniform(1, 5)
            else:
                measured = random.uniform(min_spec, max_spec)
            
            # Pass/Fail 판정
            pass_fail = "✅ Pass" if min_spec <= measured <= max_spec else "❌ Fail"
            
            self.qc_results.append({
                'item_name': item_name,
                'measured': round(measured, 2),
                'min_spec': min_spec,
                'max_spec': max_spec,
                'unit': unit,
                'result': pass_fail
            })
        
        # 결과 표시
        self.display_results()
    
    def display_results(self):
        """결과 표시"""
        # 트리뷰 초기화
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        # 필터링
        show_fail = self.show_fail_only.get()
        
        # 결과 추가
        pass_count = 0
        fail_count = 0
        
        for result in self.qc_results:
            if show_fail and "Pass" in result['result']:
                continue
                
            # Pass/Fail 카운트
            if "Pass" in result['result']:
                pass_count += 1
                tag = 'pass'
            else:
                fail_count += 1
                tag = 'fail'
            
            # 단위 포함한 값 표시
            unit = result.get('unit', '')
            measured_str = f"{result['measured']}{unit}" if unit else str(result['measured'])
            min_str = f"{result['min_spec']}{unit}" if unit else str(result['min_spec'])
            max_str = f"{result['max_spec']}{unit}" if unit else str(result['max_spec'])
            
            # 트리뷰에 추가
            self.result_tree.insert('', 'end', 
                                   values=(result['item_name'],
                                          measured_str,
                                          min_str,
                                          max_str,
                                          result['result']),
                                   tags=(tag,))
        
        # 태그 색상 설정
        self.result_tree.tag_configure('pass', foreground='green')
        self.result_tree.tag_configure('fail', foreground='red', 
                                      background='#ffeeee')
        
        # 요약 업데이트
        total = len(self.qc_results)
        pass_rate = (pass_count / max(1, total)) * 100 if total > 0 else 0
        
        summary_text = f"Total: {total} | "
        summary_text += f"Pass: {pass_count} ({pass_rate:.1f}%) | "
        summary_text += f"Fail: {fail_count}"
        
        self.summary_label.config(text=summary_text)
        
        # 내보내기 버튼 활성화
        self.export_btn.config(state='normal' if self.qc_results else 'disabled')
    
    def filter_results(self):
        """결과 필터링"""
        self.display_results()
    
    def refresh_results(self):
        """결과 새로고침"""
        if self.selected_files:
            self.run_qc_inspection()
        else:
            messagebox.showinfo("알림", "선택된 파일이 없습니다")
    
    def export_results(self):
        """결과 내보내기"""
        if not self.qc_results:
            return
        
        # 파일 저장 다이얼로그
        filename = filedialog.asksaveasfilename(
            title="검수 결과 저장",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")]
        )
        
        if filename:
            # DataFrame 생성
            df = pd.DataFrame(self.qc_results)
            
            # 저장
            if filename.endswith('.xlsx'):
                df.to_excel(filename, index=False)
            else:
                df.to_csv(filename, index=False)
            
            messagebox.showinfo("완료", f"결과가 저장되었습니다:\n{filename}")


def main():
    """독립 실행 테스트"""
    root = tk.Tk()
    root.title("간소화된 QC 검수 UI - Custom Configuration")
    root.geometry("900x650")
    
    # 스타일 설정
    style = ttk.Style()
    style.theme_use('clam')
    
    # 탭 생성
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # 간소화 탭 (root_window 전달)
    simplified_tab = SimplifiedQCTab(notebook, root_window=root)
    notebook.add(simplified_tab.frame, text="Custom QC 검수 (독립형)")
    
    # 비교용 빈 탭 (기존 UI 자리)
    legacy_frame = ttk.Frame(notebook)
    ttk.Label(legacy_frame, text="기존 QC 검수 UI 위치\n(DB 기반)",
             font=("Segoe UI", 14)).pack(pady=50)
    notebook.add(legacy_frame, text="기존 QC 검수")
    
    # 정보 표시
    info_text = """
    🧪 Custom Configuration QC 검수 UI
    
    주요 특징:
    • DB 독립적 Equipment Type 관리
    • 사용자 정의 QC 스펙 설정
    • JSON 기반 설정 저장/로드
    • 설정 편집 GUI 제공
    
    테스트 방법:
    1. ⚙️ 설정 버튼으로 Equipment Type 추가/편집
    2. 각 Type별 검수 항목 정의
    3. Equipment Type 선택
    4. 파일 선택 → 자동 검수
    5. 결과 확인 및 내보내기
    
    💡 Equipment Types과 스펙은 완전히 사용자가 정의합니다!
       Default DB와 완전히 독립적으로 작동합니다.
    """
    
    info_frame = ttk.Frame(root)
    info_frame.pack(fill=tk.X, padx=10, pady=5)
    ttk.Label(info_frame, text=info_text, justify=tk.LEFT,
             font=("Segoe UI", 9)).pack()
    
    root.mainloop()

if __name__ == "__main__":
    main()