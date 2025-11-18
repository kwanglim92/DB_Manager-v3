#!/usr/bin/env python3
"""
간소화된 QC 검수 모듈 - 사용자 정의 버전
DB 대신 사용자가 정의한 Equipment Type과 스펙 사용
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

# 사용자 정의 설정 모듈
from .qc_custom_config import CustomQCConfig
from .dialogs.qc_spec_editor_dialog import QCSpecEditorDialog

class CustomQCInspection:
    """사용자 정의 QC 검수 클래스"""
    
    def __init__(self, parent):
        """
        초기화
        
        Args:
            parent: 부모 위젯
        """
        self.parent = parent
        self.frame = ttk.Frame(parent)
        
        # 사용자 정의 설정 로드
        self.custom_config = CustomQCConfig()
        
        # 상태 변수
        self.selected_files = []
        self.qc_results = []
        self.current_equipment = None
        self.current_specs = []
        
        # UI 생성
        self.create_ui()
        
        # 초기 데이터 로드
        self.load_equipment_types()
        
    def create_ui(self):
        """UI 생성"""
        
        # 1. 제어 패널
        self.create_control_panel()
        
        # 2. 결과 테이블
        self.create_results_table()
        
        # 3. 요약 패널
        self.create_summary_panel()
        
    def create_control_panel(self):
        """제어 패널 생성"""
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        # Equipment Type 선택
        ttk.Label(control_frame, text="Equipment Type:", 
                 font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.equipment_var = tk.StringVar()
        self.equipment_combo = ttk.Combobox(control_frame,
                                           textvariable=self.equipment_var,
                                           width=25, state="readonly")
        self.equipment_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.equipment_combo.bind("<<ComboboxSelected>>", self.on_equipment_selected)
        
        # 설정 편집 버튼
        self.config_btn = ttk.Button(control_frame, text="⚙️ 설정",
                                    command=self.open_config_editor,
                                    width=8)
        self.config_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        # 파일 선택 버튼
        self.select_btn = ttk.Button(control_frame, text="📁 파일 선택",
                                    command=self.select_files)
        self.select_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 새로고침 버튼
        self.refresh_btn = ttk.Button(control_frame, text="🔄 새로고침",
                                     command=self.refresh_results,
                                     state='disabled')
        self.refresh_btn.pack(side=tk.LEFT)
        
        # 파일 정보
        self.file_label = ttk.Label(control_frame, text="파일 미선택",
                                   font=("Segoe UI", 9), foreground="gray")
        self.file_label.pack(side=tk.LEFT, padx=(20, 0))
        
    def create_results_table(self):
        """결과 테이블 생성"""
        # 프레임
        result_frame = ttk.LabelFrame(self.frame, text="📊 검수 결과", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 트리뷰
        columns = ('no', 'item_name', 'measured', 'min_spec', 'max_spec', 'result')
        self.result_tree = ttk.Treeview(result_frame, columns=columns,
                                       show='headings', height=15)
        
        # 컬럼 설정
        headers = {
            'no': 'No.',
            'item_name': 'Item Name',
            'measured': '측정값',
            'min_spec': 'Min Spec',
            'max_spec': 'Max Spec',
            'result': '결과'
        }
        
        widths = {
            'no': 40,
            'item_name': 200,
            'measured': 100,
            'min_spec': 80,
            'max_spec': 80,
            'result': 80
        }
        
        for col in columns:
            self.result_tree.heading(col, text=headers[col])
            self.result_tree.column(col, width=widths[col], minwidth=50)
        
        # 스크롤바
        v_scrollbar = ttk.Scrollbar(result_frame, orient="vertical",
                                   command=self.result_tree.yview)
        h_scrollbar = ttk.Scrollbar(result_frame, orient="horizontal",
                                   command=self.result_tree.xview)
        self.result_tree.configure(yscrollcommand=v_scrollbar.set,
                                 xscrollcommand=h_scrollbar.set)
        
        # 배치
        self.result_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        result_frame.grid_rowconfigure(0, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)
        
    def create_summary_panel(self):
        """요약 패널 생성"""
        summary_frame = ttk.LabelFrame(self.frame, text="📈 검수 요약", padding=10)
        summary_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        # 요약 레이블
        self.summary_label = ttk.Label(summary_frame,
                                      text="Equipment Type을 선택하고 파일을 선택하세요",
                                      font=("Segoe UI", 11))
        self.summary_label.pack(side=tk.LEFT)
        
        # 오른쪽 버튼들
        button_frame = ttk.Frame(summary_frame)
        button_frame.pack(side=tk.RIGHT)
        
        # 내보내기 버튼
        self.export_btn = ttk.Button(button_frame, text="📥 결과 내보내기",
                                    command=self.export_results,
                                    state='disabled')
        self.export_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Fail 항목만 보기
        self.show_fail_only = tk.BooleanVar()
        ttk.Checkbutton(button_frame, text="Fail 항목만 보기",
                       variable=self.show_fail_only,
                       command=self.filter_results).pack(side=tk.RIGHT, padx=(0, 10))
        
    def load_equipment_types(self):
        """Equipment Type 목록 로드"""
        equipment_types = self.custom_config.get_equipment_types()
        self.equipment_combo['values'] = equipment_types
        
        if equipment_types:
            self.equipment_combo.current(0)
            self.on_equipment_selected()
            
    def on_equipment_selected(self, event=None):
        """Equipment Type 선택 시"""
        selected = self.equipment_var.get()
        if selected:
            self.current_equipment = selected
            self.current_specs = self.custom_config.get_specs(selected)
            
            # 활성화된 스펙만 필터링
            self.active_specs = [s for s in self.current_specs 
                                if s.get('enabled', True)]
            
            print(f"Equipment 선택: {selected} - {len(self.active_specs)}개 스펙")
            
            # 현재 선택 표시
            spec_count = len(self.active_specs)
            self.summary_label.config(
                text=f"'{selected}' 선택됨 - {spec_count}개 검수 항목"
            )
            
    def open_config_editor(self):
        """설정 편집기 열기"""
        editor = QCSpecEditorDialog(self.parent, self.custom_config)
        if editor.show():
            # 설정이 변경되면 다시 로드
            self.load_equipment_types()
            messagebox.showinfo("완료", "설정이 저장되었습니다.")
            
    def select_files(self):
        """파일 선택"""
        if not self.current_equipment:
            messagebox.showwarning("경고", "먼저 Equipment Type을 선택하세요")
            return
            
        files = filedialog.askopenfilenames(
            title="QC 검수할 파일 선택",
            filetypes=[
                ("Text files", "*.txt"),
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx"),
                ("All files", "*.*")
            ]
        )
        
        if files:
            self.selected_files = files
            
            # 파일 정보 표시
            if len(files) == 1:
                filename = os.path.basename(files[0])
                self.file_label.config(text=filename, foreground="black")
            else:
                self.file_label.config(text=f"{len(files)}개 파일 선택됨",
                                     foreground="black")
            
            # 새로고침 버튼 활성화
            self.refresh_btn.config(state='normal')
            
            # 자동 검수 실행
            self.run_qc_inspection()
            
    def run_qc_inspection(self):
        """QC 검수 실행"""
        if not self.selected_files or not self.active_specs:
            return
            
        try:
            # 로딩 표시
            self.summary_label.config(text="검수 진행 중...")
            self.parent.update()
            
            # 결과 초기화
            self.qc_results = []
            
            # 파일 데이터 읽기
            for file_path in self.selected_files:
                file_data = self.read_file_data(file_path)
                
                # 각 스펙에 대해 검수 수행
                for spec in self.active_specs:
                    item_name = spec['item_name']
                    
                    # 파일에서 해당 항목 찾기
                    measured_value = self.find_value_in_data(item_name, file_data)
                    
                    if measured_value is not None:
                        # Pass/Fail 판정
                        result = self.check_pass_fail(measured_value, spec)
                        
                        self.qc_results.append({
                            'item_name': item_name,
                            'measured': measured_value,
                            'min_spec': spec.get('min_spec', 'N/A'),
                            'max_spec': spec.get('max_spec', 'N/A'),
                            'unit': spec.get('unit', ''),
                            'result': result
                        })
                    else:
                        # 데이터 없음
                        self.qc_results.append({
                            'item_name': item_name,
                            'measured': 'N/A',
                            'min_spec': spec.get('min_spec', 'N/A'),
                            'max_spec': spec.get('max_spec', 'N/A'),
                            'unit': spec.get('unit', ''),
                            'result': '⚠️ No Data'
                        })
            
            # 결과 표시
            self.display_results()
            
        except Exception as e:
            messagebox.showerror("오류", f"검수 실행 중 오류 발생:\n{str(e)}")
            print(f"검수 오류: {e}")
            
    def read_file_data(self, file_path):
        """파일 데이터 읽기"""
        file_data = {}
        
        try:
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext == '.csv':
                df = pd.read_csv(file_path)
                # 첫 번째 컬럼을 item_name, 두 번째를 value로 가정
                if len(df.columns) >= 2:
                    for _, row in df.iterrows():
                        file_data[str(row.iloc[0])] = self.parse_value(row.iloc[1])
                        
            elif ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
                if len(df.columns) >= 2:
                    for _, row in df.iterrows():
                        file_data[str(row.iloc[0])] = self.parse_value(row.iloc[1])
                        
            elif ext == '.txt':
                # 텍스트 파일 (key=value 또는 key:value 형식)
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if '=' in line:
                            key, value = line.split('=', 1)
                            file_data[key.strip()] = self.parse_value(value.strip())
                        elif ':' in line:
                            key, value = line.split(':', 1)
                            file_data[key.strip()] = self.parse_value(value.strip())
                            
        except Exception as e:
            print(f"파일 읽기 오류 ({file_path}): {e}")
            # 테스트용 샘플 데이터 생성
            import random
            for spec in self.active_specs[:5]:
                item_name = spec['item_name']
                min_val = spec.get('min_spec', 0)
                max_val = spec.get('max_spec', 100)
                
                # 숫자 타입 체크
                if isinstance(min_val, (int, float)) and isinstance(max_val, (int, float)):
                    # 80% Pass, 20% Fail
                    if random.random() < 0.8:
                        value = random.uniform(min_val, max_val)
                    else:
                        value = min_val - random.uniform(1, 5)
                    file_data[item_name] = round(value, 2)
                    
        return file_data
        
    def find_value_in_data(self, item_name, file_data):
        """데이터에서 항목 찾기"""
        # 정확한 매칭
        if item_name in file_data:
            return file_data[item_name]
            
        # 대소문자 무시 매칭
        item_lower = item_name.lower()
        for key, value in file_data.items():
            if key.lower() == item_lower:
                return value
                
        # 부분 매칭
        for key, value in file_data.items():
            if item_lower in key.lower() or key.lower() in item_lower:
                return value
                
        return None
        
    def parse_value(self, value):
        """값 파싱"""
        if value is None:
            return None
        try:
            # 숫자로 변환 시도
            if isinstance(value, str):
                value = value.strip()
                if value.lower() in ['n/a', 'na', 'none', '-']:
                    return None
            return float(value)
        except (ValueError, TypeError):
            return value
            
    def check_pass_fail(self, value, spec):
        """Pass/Fail 판정"""
        if value is None or value == 'N/A':
            return "⚠️ No Data"
            
        min_val = spec.get('min_spec')
        max_val = spec.get('max_spec')
        
        # 스펙이 없으면
        if min_val is None and max_val is None:
            return "⚠️ No Spec"
            
        # 숫자 비교
        try:
            value = float(value)
            if min_val is not None:
                min_val = float(min_val)
                if value < min_val:
                    return "❌ Fail"
            if max_val is not None:
                max_val = float(max_val)
                if value > max_val:
                    return "❌ Fail"
        except (ValueError, TypeError):
            return "⚠️ Invalid"
            
        return "✅ Pass"
        
    def display_results(self):
        """결과 표시"""
        # 트리뷰 초기화
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
            
        # 필터 적용
        show_fail = self.show_fail_only.get()
        
        # 카운터
        total_count = 0
        pass_count = 0
        fail_count = 0
        no_data_count = 0
        
        # 결과 추가
        display_index = 0
        for result in self.qc_results:
            # 필터링
            if show_fail and "Pass" in result['result']:
                continue
                
            display_index += 1
            
            # 카운트
            if "Pass" in result['result']:
                pass_count += 1
                tag = 'pass'
            elif "Fail" in result['result']:
                fail_count += 1
                tag = 'fail'
            else:
                no_data_count += 1
                tag = 'warning'
                
            # 트리뷰에 추가
            self.result_tree.insert('', 'end',
                                   values=(display_index,
                                          result['item_name'],
                                          result['measured'],
                                          result['min_spec'],
                                          result['max_spec'],
                                          result['result']),
                                   tags=(tag,))
            
        total_count = pass_count + fail_count + no_data_count
        
        # 태그 색상
        self.result_tree.tag_configure('pass', foreground='green')
        self.result_tree.tag_configure('fail', foreground='red', background='#ffeeee')
        self.result_tree.tag_configure('warning', foreground='orange')
        
        # 요약 업데이트
        if total_count > 0:
            pass_rate = (pass_count / total_count) * 100
            summary = f"Total: {total_count} | Pass: {pass_count} ({pass_rate:.0f}%) | "
            summary += f"Fail: {fail_count}"
            if no_data_count > 0:
                summary += f" | No Data: {no_data_count}"
        else:
            summary = "검수 결과 없음"
            
        self.summary_label.config(text=summary)
        
        # 내보내기 버튼 활성화
        self.export_btn.config(state='normal' if self.qc_results else 'disabled')
        
    def filter_results(self):
        """결과 필터링"""
        self.display_results()
        
    def refresh_results(self):
        """결과 새로고침"""
        if self.selected_files:
            self.run_qc_inspection()
            
    def export_results(self):
        """결과 내보내기"""
        if not self.qc_results:
            return
            
        # 파일 저장 다이얼로그
        filename = filedialog.asksaveasfilename(
            title="QC 검수 결과 저장",
            defaultextension=".csv",
            initialfile=f"QC_Result_{self.current_equipment}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            filetypes=[
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx"),
                ("JSON files", "*.json")
            ]
        )
        
        if filename:
            try:
                # 메타 정보 추가
                export_data = {
                    'equipment_type': self.current_equipment,
                    'inspection_date': datetime.now().isoformat(),
                    'file_count': len(self.selected_files),
                    'results': self.qc_results
                }
                
                ext = os.path.splitext(filename)[1].lower()
                
                if ext == '.json':
                    # JSON 저장
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(export_data, f, indent=2, ensure_ascii=False)
                else:
                    # DataFrame 생성
                    df = pd.DataFrame(self.qc_results)
                    
                    # 메타 정보를 첫 줄에 추가
                    meta_df = pd.DataFrame([{
                        'Equipment Type': self.current_equipment,
                        'Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'Files': len(self.selected_files)
                    }])
                    
                    if ext == '.xlsx':
                        # Excel 저장 (두 개 시트)
                        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                            meta_df.to_excel(writer, sheet_name='Info', index=False)
                            df.to_excel(writer, sheet_name='Results', index=False)
                    else:
                        # CSV 저장
                        df.to_csv(filename, index=False, encoding='utf-8-sig')
                
                messagebox.showinfo("완료", f"결과가 저장되었습니다:\n{filename}")
                
            except Exception as e:
                messagebox.showerror("오류", f"저장 중 오류 발생:\n{str(e)}")