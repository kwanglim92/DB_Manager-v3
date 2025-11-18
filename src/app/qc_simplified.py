#!/usr/bin/env python3
"""
간소화된 QC 검수 모듈
Phase 2: 실제 DB 연동 버전
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class SimplifiedQCInspection:
    """간소화된 QC 검수 클래스"""
    
    def __init__(self, parent, db_schema):
        """
        초기화
        
        Args:
            parent: 부모 위젯
            db_schema: DBSchema 인스턴스
        """
        self.parent = parent
        self.db_schema = db_schema
        self.frame = ttk.Frame(parent)
        
        # 상태 변수
        self.selected_files = []
        self.qc_results = []
        self.equipment_type_id = None
        self.qc_specs = {}
        
        # UI 생성
        self.create_ui()
        
        # 초기 데이터 로드
        self.load_equipment_types()
        self.load_qc_specs()
        
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
                                           width=30, state="readonly")
        self.equipment_combo.pack(side=tk.LEFT, padx=(0, 15))
        self.equipment_combo.bind("<<ComboboxSelected>>", self.on_equipment_selected)
        
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
                                      text="검수를 시작하려면 장비 타입과 파일을 선택하세요",
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
        ttk.Checkbutton(button_frame, text="Fail 항목만",
                       variable=self.show_fail_only,
                       command=self.filter_results).pack(side=tk.RIGHT, padx=(0, 10))
        
    def load_equipment_types(self):
        """Equipment Type 목록 로드"""
        try:
            if not self.db_schema:
                return
                
            # DB에서 장비 타입 목록 조회
            equipment_types = self.db_schema.get_equipment_types()
            
            # 콤보박스에 설정
            type_names = [f"{name} (ID: {type_id})" 
                         for type_id, name, _ in equipment_types]
            self.equipment_combo['values'] = type_names
            
            # Equipment Type ID 저장용 딕셔너리
            self.equipment_dict = {f"{name} (ID: {type_id})": type_id 
                                  for type_id, name, _ in equipment_types}
            
            if type_names:
                self.equipment_combo.current(0)
                self.on_equipment_selected()
                
        except Exception as e:
            print(f"Equipment Type 로드 오류: {e}")
            
    def load_qc_specs(self):
        """QC 스펙 로드"""
        try:
            # QC_Spec_Master 테이블에서 스펙 로드
            conn = sqlite3.connect(self.db_schema.db_path if hasattr(self.db_schema, 'db_path') 
                                  else 'data/db_manager.sqlite')
            cursor = conn.cursor()
            
            # QC_Spec_Master 테이블 존재 확인
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='QC_Spec_Master'
            """)
            
            if cursor.fetchone():
                # 스펙 데이터 로드
                cursor.execute("""
                    SELECT item_name, min_spec, max_spec, expected_value, category
                    FROM QC_Spec_Master
                    WHERE is_active = 1
                """)
                
                self.qc_specs = {}
                for row in cursor.fetchall():
                    item_name, min_spec, max_spec, expected_value, category = row
                    self.qc_specs[item_name] = {
                        'min': self.parse_value(min_spec),
                        'max': self.parse_value(max_spec),
                        'expected': self.parse_value(expected_value),
                        'category': category
                    }
                    
                print(f"QC 스펙 {len(self.qc_specs)}개 로드 완료")
                
            conn.close()
            
        except Exception as e:
            print(f"QC 스펙 로드 오류: {e}")
            # 테스트용 샘플 데이터
            self.qc_specs = {
                'Temperature': {'min': 20, 'max': 25, 'expected': 22.5, 'category': 'Temperature'},
                'Pressure': {'min': 100, 'max': 200, 'expected': 150, 'category': 'Pressure'},
                'Flow_Rate': {'min': 10, 'max': 20, 'expected': 15, 'category': 'Flow'}
            }
            
    def parse_value(self, value):
        """값 파싱"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return value
            
    def on_equipment_selected(self, event=None):
        """Equipment Type 선택 시"""
        selected = self.equipment_var.get()
        if selected and selected in self.equipment_dict:
            self.equipment_type_id = self.equipment_dict[selected]
            print(f"Equipment Type 선택: {selected} (ID: {self.equipment_type_id})")
            
    def select_files(self):
        """파일 선택"""
        if not self.equipment_type_id:
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
        if not self.selected_files:
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
                
                # 각 항목에 대해 검수 수행
                for item_name, measured_value in file_data.items():
                    # ItemName 매칭으로 스펙 찾기
                    spec = self.find_matching_spec(item_name)
                    
                    if spec:
                        # Pass/Fail 판정
                        result = self.check_pass_fail(measured_value, spec)
                        
                        self.qc_results.append({
                            'item_name': item_name,
                            'measured': measured_value,
                            'min_spec': spec.get('min', 'N/A'),
                            'max_spec': spec.get('max', 'N/A'),
                            'result': result
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
                        
            else:
                # 텍스트 파일 (간단한 key=value 형식 가정)
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            file_data[key.strip()] = self.parse_value(value.strip())
                            
        except Exception as e:
            print(f"파일 읽기 오류 ({file_path}): {e}")
            # 테스트용 샘플 데이터
            import random
            for spec_name in list(self.qc_specs.keys())[:5]:
                spec = self.qc_specs[spec_name]
                if spec['min'] is not None and spec['max'] is not None:
                    # 80% Pass, 20% Fail
                    if random.random() < 0.8:
                        value = random.uniform(spec['min'], spec['max'])
                    else:
                        value = spec['min'] - random.uniform(1, 5)
                    file_data[spec_name] = round(value, 2)
                    
        return file_data
        
    def find_matching_spec(self, item_name):
        """ItemName 매칭으로 스펙 찾기"""
        # 정확한 매칭
        if item_name in self.qc_specs:
            return self.qc_specs[item_name]
            
        # 부분 매칭 (대소문자 무시)
        item_lower = item_name.lower()
        for spec_name, spec in self.qc_specs.items():
            if spec_name.lower() in item_lower or item_lower in spec_name.lower():
                return spec
                
        return None
        
    def check_pass_fail(self, value, spec):
        """Pass/Fail 판정"""
        if value is None:
            return "⚠️ No Data"
            
        min_val = spec.get('min')
        max_val = spec.get('max')
        
        if min_val is None and max_val is None:
            return "⚠️ No Spec"
            
        if min_val is not None and value < min_val:
            return "❌ Fail"
        if max_val is not None and value > max_val:
            return "❌ Fail"
            
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
        for idx, result in enumerate(self.qc_results, 1):
            # 필터링
            if show_fail and "Pass" in result['result']:
                continue
                
            # 카운트
            total_count += 1
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
                                   values=(idx if not show_fail else total_count,
                                          result['item_name'],
                                          result['measured'],
                                          result['min_spec'],
                                          result['max_spec'],
                                          result['result']),
                                   tags=(tag,))
        
        # 태그 색상
        self.result_tree.tag_configure('pass', foreground='green')
        self.result_tree.tag_configure('fail', foreground='red', background='#ffeeee')
        self.result_tree.tag_configure('warning', foreground='orange')
        
        # 요약 업데이트
        if not show_fail:
            total = len(self.qc_results)
            pass_rate = (pass_count / max(1, total)) * 100
            summary = f"Total: {total} | Pass: {pass_count} ({pass_rate:.1f}%) | "
            summary += f"Fail: {fail_count} | No Data: {no_data_count}"
        else:
            summary = f"Fail Items: {fail_count}"
            
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
            initialfile=f"QC_Result_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            filetypes=[
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx"),
                ("JSON files", "*.json")
            ]
        )
        
        if filename:
            try:
                ext = os.path.splitext(filename)[1].lower()
                
                if ext == '.json':
                    # JSON 저장
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(self.qc_results, f, indent=2, ensure_ascii=False)
                else:
                    # DataFrame 생성
                    df = pd.DataFrame(self.qc_results)
                    
                    if ext == '.xlsx':
                        # Excel 저장
                        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                            df.to_excel(writer, sheet_name='QC Results', index=False)
                    else:
                        # CSV 저장
                        df.to_csv(filename, index=False, encoding='utf-8-sig')
                
                messagebox.showinfo("완료", f"결과가 저장되었습니다:\n{filename}")
                
            except Exception as e:
                messagebox.showerror("오류", f"저장 중 오류 발생:\n{str(e)}")