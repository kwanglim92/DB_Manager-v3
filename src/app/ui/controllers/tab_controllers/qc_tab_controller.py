"""
QC Tab Controller - Tkinter 기반 QC 검수 탭 컨트롤러

새로운 QC Services Layer를 활용하여 구현
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

# QC Services Layer 임포트
from app.qc.services import QCService, ReportService
from app.qc.utils import FileHandler


class QCTabController:
    """
    QC 검수 탭 컨트롤러

    새로운 QC Services Layer를 활용한 Tkinter 기반 UI
    """

    def __init__(self, parent_frame, manager):
        """
        초기화

        Args:
            parent_frame: 부모 프레임 (ttk.Frame)
            manager: DBManager 인스턴스
        """
        self.parent_frame = parent_frame
        self.manager = manager
        self.db_schema = manager.db_schema

        # Services 초기화
        self.qc_service = QCService(self.db_schema)
        self.report_service = ReportService()
        self.file_handler = FileHandler()

        # 상태 변수
        self.selected_files = []
        self.inspection_result = None
        self.file_data = None
        self.equipment_type_id = None

        # UI 생성
        self.create_ui()

        # 초기 데이터 로드
        self.load_equipment_types()

    def create_ui(self):
        """UI 생성"""
        # 메인 컨테이너
        main_container = ttk.Frame(self.parent_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 1. 제어 패널
        self.create_control_panel(main_container)

        # 2. 필터 패널
        self.create_filter_panel(main_container)

        # 3. 결과 테이블
        self.create_results_table(main_container)

        # 4. 요약 패널
        self.create_summary_panel(main_container)

        # 5. 액션 버튼
        self.create_action_buttons(main_container)

    def create_control_panel(self, parent):
        """제어 패널 생성"""
        control_frame = ttk.LabelFrame(parent, text="🎯 QC 검수 설정", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 5))

        # Equipment Type 선택
        type_frame = ttk.Frame(control_frame)
        type_frame.pack(fill=tk.X)

        ttk.Label(type_frame, text="Equipment Type:",
                 font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(0, 5))

        self.equipment_var = tk.StringVar()
        self.equipment_combo = ttk.Combobox(type_frame,
                                           textvariable=self.equipment_var,
                                           width=30, state="readonly")
        self.equipment_combo.pack(side=tk.LEFT, padx=(0, 15))
        self.equipment_combo.bind("<<ComboboxSelected>>", self.on_equipment_selected)

        # 파일 선택 버튼
        self.select_btn = ttk.Button(type_frame, text="📁 파일 선택",
                                    command=self.select_files)
        self.select_btn.pack(side=tk.LEFT, padx=(0, 10))

        # QC 검수 실행 버튼
        self.inspect_btn = ttk.Button(type_frame, text="🔍 검수 실행",
                                     command=self.run_inspection,
                                     state='disabled')
        self.inspect_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 새로고침 버튼
        self.refresh_btn = ttk.Button(type_frame, text="🔄 새로고침",
                                     command=self.refresh_results,
                                     state='disabled')
        self.refresh_btn.pack(side=tk.LEFT)

        # 파일 정보
        self.file_label = ttk.Label(type_frame, text="파일 미선택",
                                   font=("Segoe UI", 9), foreground="gray")
        self.file_label.pack(side=tk.LEFT, padx=(20, 0))

    def create_filter_panel(self, parent):
        """필터 패널 생성"""
        filter_frame = ttk.LabelFrame(parent, text="🔎 필터", padding=10)
        filter_frame.pack(fill=tk.X, pady=(0, 5))

        # Module 필터
        ttk.Label(filter_frame, text="Module:").pack(side=tk.LEFT, padx=(0, 5))
        self.module_var = tk.StringVar(value="All")
        self.module_combo = ttk.Combobox(filter_frame,
                                        textvariable=self.module_var,
                                        width=20, state="readonly")
        self.module_combo['values'] = ["All"]
        self.module_combo.pack(side=tk.LEFT, padx=(0, 15))
        self.module_combo.bind("<<ComboboxSelected>>", self.apply_filters)

        # Part 필터
        ttk.Label(filter_frame, text="Part:").pack(side=tk.LEFT, padx=(0, 5))
        self.part_var = tk.StringVar(value="All")
        self.part_combo = ttk.Combobox(filter_frame,
                                      textvariable=self.part_var,
                                      width=20, state="readonly")
        self.part_combo['values'] = ["All"]
        self.part_combo.pack(side=tk.LEFT, padx=(0, 15))
        self.part_combo.bind("<<ComboboxSelected>>", self.apply_filters)

        # 결과 필터
        ttk.Label(filter_frame, text="결과:").pack(side=tk.LEFT, padx=(0, 5))
        self.result_var = tk.StringVar(value="All")
        self.result_combo = ttk.Combobox(filter_frame,
                                        textvariable=self.result_var,
                                        width=15, state="readonly")
        self.result_combo['values'] = ["All", "Pass", "Fail"]
        self.result_combo.pack(side=tk.LEFT)
        self.result_combo.bind("<<ComboboxSelected>>", self.apply_filters)

    def create_results_table(self, parent):
        """결과 테이블 생성"""
        result_frame = ttk.LabelFrame(parent, text="📊 검수 결과", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        # 트리뷰 컬럼
        columns = ('no', 'display_name', 'file_value', 'spec', 'result', 'category')
        self.result_tree = ttk.Treeview(result_frame, columns=columns,
                                       show='headings', height=15)

        # 컬럼 설정
        headers = {
            'no': 'No.',
            'display_name': 'Item Name',
            'file_value': 'Measured Value',
            'spec': 'Spec',
            'result': 'Result',
            'category': 'Category'
        }

        widths = {
            'no': 50,
            'display_name': 250,
            'file_value': 150,
            'spec': 150,
            'result': 80,
            'category': 120
        }

        for col in columns:
            self.result_tree.heading(col, text=headers[col],
                                    command=lambda c=col: self.sort_by_column(c))
            self.result_tree.column(col, width=widths[col], anchor='center')

        # 스크롤바
        v_scrollbar = ttk.Scrollbar(result_frame, orient="vertical",
                                   command=self.result_tree.yview)
        h_scrollbar = ttk.Scrollbar(result_frame, orient="horizontal",
                                   command=self.result_tree.xview)
        self.result_tree.configure(yscrollcommand=v_scrollbar.set,
                                  xscrollcommand=h_scrollbar.set)

        # 배치
        self.result_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')

        result_frame.grid_rowconfigure(0, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)

        # 태그 설정 (Pass/Fail 색상)
        self.result_tree.tag_configure('pass', background='#d4edda')
        self.result_tree.tag_configure('fail', background='#f8d7da')

    def create_summary_panel(self, parent):
        """요약 패널 생성"""
        summary_frame = ttk.LabelFrame(parent, text="📈 검수 요약", padding=10)
        summary_frame.pack(fill=tk.X, pady=(0, 5))

        # 통계 레이블들
        stats_frame = ttk.Frame(summary_frame)
        stats_frame.pack(fill=tk.X)

        self.total_label = ttk.Label(stats_frame, text="전체: 0",
                                    font=("Segoe UI", 10, "bold"))
        self.total_label.pack(side=tk.LEFT, padx=10)

        self.pass_label = ttk.Label(stats_frame, text="Pass: 0",
                                   font=("Segoe UI", 10), foreground="green")
        self.pass_label.pack(side=tk.LEFT, padx=10)

        self.fail_label = ttk.Label(stats_frame, text="Fail: 0",
                                   font=("Segoe UI", 10), foreground="red")
        self.fail_label.pack(side=tk.LEFT, padx=10)

        self.rate_label = ttk.Label(stats_frame, text="합격률: 0%",
                                   font=("Segoe UI", 10, "bold"))
        self.rate_label.pack(side=tk.LEFT, padx=10)

        # 결과 메시지
        self.result_msg_label = ttk.Label(stats_frame, text="",
                                         font=("Segoe UI", 11, "bold"))
        self.result_msg_label.pack(side=tk.LEFT, padx=20)

    def create_action_buttons(self, parent):
        """액션 버튼 생성"""
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X)

        # 보고서 생성 버튼
        self.report_btn = ttk.Button(action_frame, text="📄 보고서 생성",
                                    command=self.generate_report,
                                    state='disabled')
        self.report_btn.pack(side=tk.LEFT, padx=5)

        # Excel 내보내기 버튼
        self.export_btn = ttk.Button(action_frame, text="📊 Excel 내보내기",
                                    command=self.export_to_excel,
                                    state='disabled')
        self.export_btn.pack(side=tk.LEFT, padx=5)

    def load_equipment_types(self):
        """Equipment Type 목록 로드"""
        try:
            if not self.db_schema:
                self.manager.update_log("❌ DB Schema가 초기화되지 않음")
                return

            # DB에서 Equipment Type 조회
            equipment_types = self.db_schema.get_all_equipment_types()

            if equipment_types:
                type_names = [f"{et['id']}: {et['type_name']}" for et in equipment_types]
                self.equipment_combo['values'] = type_names
                self.manager.update_log(f"✅ {len(equipment_types)}개 장비 타입 로드됨")
            else:
                self.equipment_combo['values'] = []
                self.manager.update_log("⚠️ 등록된 장비 타입이 없습니다")

        except Exception as e:
            self.manager.update_log(f"❌ 장비 타입 로드 실패: {e}")
            import traceback
            traceback.print_exc()

    def on_equipment_selected(self, event=None):
        """Equipment Type 선택 이벤트"""
        selected = self.equipment_var.get()
        if selected:
            # "ID: Name" 형식에서 ID 추출
            self.equipment_type_id = int(selected.split(":")[0])
            self.manager.update_log(f"✅ 선택된 장비 타입 ID: {self.equipment_type_id}")

            # 파일이 선택되어 있으면 검수 버튼 활성화
            if self.selected_files:
                self.inspect_btn.config(state='normal')

    def select_files(self):
        """파일 선택"""
        try:
            files = filedialog.askopenfilenames(
                title="QC 검수 파일 선택",
                filetypes=[
                    ("Text files", "*.txt"),
                    ("All files", "*.*")
                ]
            )

            if files:
                self.selected_files = list(files)
                file_count = len(files)
                self.file_label.config(
                    text=f"{file_count}개 파일 선택됨",
                    foreground="blue"
                )
                self.manager.update_log(f"✅ {file_count}개 파일 선택됨")

                # Equipment Type이 선택되어 있으면 검수 버튼 활성화
                if self.equipment_type_id:
                    self.inspect_btn.config(state='normal')

        except Exception as e:
            messagebox.showerror("오류", f"파일 선택 중 오류:\n{str(e)}")
            self.manager.update_log(f"❌ 파일 선택 오류: {e}")

    def run_inspection(self):
        """QC 검수 실행"""
        try:
            if not self.selected_files:
                messagebox.showwarning("경고", "파일을 먼저 선택하세요")
                return

            if not self.equipment_type_id:
                messagebox.showwarning("경고", "Equipment Type을 먼저 선택하세요")
                return

            self.manager.update_log("🔍 QC 검수 시작...")

            # 파일 로드
            self.file_data = self.file_handler.load_files(self.selected_files)

            if not self.file_data:
                messagebox.showerror("오류", "파일 로드 실패")
                return

            self.manager.update_log(f"✅ 파일 로드 완료: {len(self.file_data)} 항목")

            # QC 검수 실행
            self.inspection_result = self.qc_service.run_inspection(
                self.file_data,
                configuration_id=self.equipment_type_id
            )

            # 결과 표시
            self.display_results()

            # 버튼 활성화
            self.refresh_btn.config(state='normal')
            self.report_btn.config(state='normal')
            self.export_btn.config(state='normal')

            self.manager.update_log("✅ QC 검수 완료")

        except Exception as e:
            messagebox.showerror("오류", f"QC 검수 중 오류:\n{str(e)}")
            self.manager.update_log(f"❌ QC 검수 오류: {e}")
            import traceback
            traceback.print_exc()

    def display_results(self):
        """검수 결과 표시"""
        if not self.inspection_result:
            return

        # 트리뷰 초기화
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)

        # 결과 데이터
        results = self.inspection_result.get('results', [])

        # 필터용 데이터 수집
        modules = set()
        parts = set()

        # 트리뷰에 데이터 추가
        for idx, result in enumerate(results, 1):
            display_name = result.get('display_name', '')
            file_value = result.get('file_value', 'N/A')
            spec = result.get('spec', '')
            is_valid = result.get('is_valid', False)
            category = result.get('category', '')
            module = result.get('module', '')
            part = result.get('part', '')

            # 필터 데이터 수집
            if module:
                modules.add(module)
            if part:
                parts.add(part)

            # 결과 태그
            result_text = "Pass" if is_valid else "Fail"
            tag = 'pass' if is_valid else 'fail'

            self.result_tree.insert('', 'end', values=(
                idx,
                display_name,
                file_value,
                spec,
                result_text,
                category
            ), tags=(tag,))

        # 필터 콤보박스 업데이트
        self.module_combo['values'] = ["All"] + sorted(list(modules))
        self.part_combo['values'] = ["All"] + sorted(list(parts))

        # 요약 정보 업데이트
        self.update_summary()

    def update_summary(self):
        """요약 정보 업데이트"""
        if not self.inspection_result:
            return

        total = self.inspection_result.get('total_count', 0)
        passed = self.inspection_result.get('passed_count', 0)
        failed = self.inspection_result.get('failed_count', 0)
        is_pass = self.inspection_result.get('is_pass', False)

        # 합격률 계산
        pass_rate = (passed / total * 100) if total > 0 else 0

        # 레이블 업데이트
        self.total_label.config(text=f"전체: {total}")
        self.pass_label.config(text=f"Pass: {passed}")
        self.fail_label.config(text=f"Fail: {failed}")
        self.rate_label.config(text=f"합격률: {pass_rate:.1f}%")

        # 결과 메시지
        if is_pass:
            self.result_msg_label.config(text="✅ 검수 합격", foreground="green")
        else:
            self.result_msg_label.config(text="❌ 검수 불합격", foreground="red")

    def apply_filters(self, event=None):
        """필터 적용"""
        if not self.inspection_result:
            return

        # 현재 필터 값
        module_filter = self.module_var.get()
        part_filter = self.part_var.get()
        result_filter = self.result_var.get()

        # 트리뷰 초기화
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)

        # 필터링된 결과 표시
        results = self.inspection_result.get('results', [])
        filtered_idx = 1

        for result in results:
            module = result.get('module', '')
            part = result.get('part', '')
            is_valid = result.get('is_valid', False)

            # 필터 조건 확인
            if module_filter != "All" and module != module_filter:
                continue
            if part_filter != "All" and part != part_filter:
                continue
            if result_filter == "Pass" and not is_valid:
                continue
            if result_filter == "Fail" and is_valid:
                continue

            # 트리뷰에 추가
            display_name = result.get('display_name', '')
            file_value = result.get('file_value', 'N/A')
            spec = result.get('spec', '')
            category = result.get('category', '')

            result_text = "Pass" if is_valid else "Fail"
            tag = 'pass' if is_valid else 'fail'

            self.result_tree.insert('', 'end', values=(
                filtered_idx,
                display_name,
                file_value,
                spec,
                result_text,
                category
            ), tags=(tag,))

            filtered_idx += 1

    def refresh_results(self):
        """결과 새로고침"""
        if self.selected_files and self.equipment_type_id:
            self.run_inspection()
        else:
            messagebox.showwarning("경고", "파일과 장비 타입을 먼저 선택하세요")

    def generate_report(self):
        """보고서 생성"""
        try:
            if not self.inspection_result:
                messagebox.showwarning("경고", "검수 결과가 없습니다")
                return

            # 저장 위치 선택
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialfile=f"QC_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )

            if file_path:
                # 보고서 생성
                report = self.report_service.generate_summary_report(
                    self.inspection_result
                )

                # 장비 정보 추가
                header = f"Equipment Type: {self.equipment_var.get()}\n"
                header += f"File(s): {', '.join([os.path.basename(f) for f in self.selected_files])}\n"
                header += "=" * 50 + "\n\n"

                # 파일로 저장
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(header + report)

                messagebox.showinfo("완료", f"보고서가 저장되었습니다:\n{file_path}")
                self.manager.update_log(f"✅ 보고서 생성 완료: {file_path}")

        except Exception as e:
            messagebox.showerror("오류", f"보고서 생성 중 오류:\n{str(e)}")
            self.manager.update_log(f"❌ 보고서 생성 오류: {e}")

    def export_to_excel(self):
        """Excel로 내보내기"""
        try:
            if not self.inspection_result:
                messagebox.showwarning("경고", "검수 결과가 없습니다")
                return

            # 저장 위치 선택
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialfile=f"QC_Results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )

            if file_path:
                # DataFrame 생성
                results = self.inspection_result.get('results', [])
                df_data = []

                for idx, result in enumerate(results, 1):
                    df_data.append({
                        'No.': idx,
                        'Item Name': result.get('display_name', ''),
                        'Module': result.get('module', ''),
                        'Part': result.get('part', ''),
                        'Measured Value': result.get('file_value', 'N/A'),
                        'Spec': result.get('spec', ''),
                        'Result': 'Pass' if result.get('is_valid', False) else 'Fail',
                        'Category': result.get('category', '')
                    })

                df = pd.DataFrame(df_data)
                df.to_excel(file_path, index=False, sheet_name='QC Results')

                messagebox.showinfo("완료", f"Excel 파일이 저장되었습니다:\n{file_path}")
                self.manager.update_log(f"✅ Excel 내보내기 완료: {file_path}")

        except Exception as e:
            messagebox.showerror("오류", f"Excel 내보내기 중 오류:\n{str(e)}")
            self.manager.update_log(f"❌ Excel 내보내기 오류: {e}")

    def sort_by_column(self, col):
        """컬럼 정렬"""
        # 트리뷰 항목 가져오기
        items = [(self.result_tree.set(item, col), item)
                for item in self.result_tree.get_children('')]

        # 정렬
        items.sort()

        # 재배치
        for index, (val, item) in enumerate(items):
            self.result_tree.move(item, '', index)
