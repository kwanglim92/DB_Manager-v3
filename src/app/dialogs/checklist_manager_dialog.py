"""
QC Checklist Management Dialog - Phase 1.5 Week 3 Day 3

ItemName 기반 Check list 관리 UI
- severity_level 제거
- spec_min, spec_max, expected_value, category, is_active 추가
- Import from CSV 기능
- Active/Inactive 토글

Author: Phase 1.5 Week 3
Date: 2025-11-13
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import csv


class ChecklistManagerDialog:
    """QC Checklist Management Dialog (관리자 전용)"""

    def __init__(self, parent, db_schema):
        """
        Args:
            parent: 부모 윈도우
            db_schema: DBSchema 인스턴스
        """
        self.parent = parent
        self.db_schema = db_schema

        # 다이얼로그 생성
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("QC Checklist 관리 (관리자 전용)")
        self.dialog.geometry("1200x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_ui()
        self._load_data()

    def _create_ui(self):
        """UI 생성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 제목
        title_label = ttk.Label(
            main_frame,
            text="QC Checklist 관리 (관리자 전용)",
            font=("Helvetica", 14, "bold")
        )
        title_label.pack(pady=(0, 10))

        # 탭 노트북
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 탭 생성
        self._create_checklist_tab()
        self._create_audit_log_tab()

        # 버튼 프레임
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=(10, 0))

        ttk.Button(
            btn_frame,
            text="닫기",
            command=self.dialog.destroy,
            width=15
        ).pack()

    def _create_checklist_tab(self):
        """QC Checklist 탭"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="QC Checklist")

        # 상단 버튼 프레임
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(
            btn_frame,
            text="➕ 추가",
            command=self._add_checklist_item,
            width=12
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            btn_frame,
            text="✏️ 수정",
            command=self._edit_checklist_item,
            width=12
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            btn_frame,
            text="❌ 삭제",
            command=self._delete_checklist_item,
            width=12
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            btn_frame,
            text="✅ Activate",
            command=self._activate_item,
            width=12
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            btn_frame,
            text="⏸️ Deactivate",
            command=self._deactivate_item,
            width=12
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            btn_frame,
            text="📥 Import CSV",
            command=self._import_from_csv,
            width=12
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            btn_frame,
            text="🔄 새로고침",
            command=self._refresh_checklist,
            width=12
        ).pack(side=tk.LEFT, padx=2)

        # 트리뷰 프레임
        tree_frame = ttk.Frame(tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 트리뷰
        columns = ("ID", "ItemName", "Spec (Min~Max)", "Expected Value", "Category", "Active", "Description")
        self.checklist_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="tree headings",
            selectmode="browse"
        )

        # 컬럼 설정
        self.checklist_tree.column("#0", width=0, stretch=False)
        self.checklist_tree.column("ID", width=50, anchor="center")
        self.checklist_tree.column("ItemName", width=250)
        self.checklist_tree.column("Spec (Min~Max)", width=150, anchor="center")
        self.checklist_tree.column("Expected Value", width=150, anchor="center")
        self.checklist_tree.column("Category", width=120, anchor="center")
        self.checklist_tree.column("Active", width=70, anchor="center")
        self.checklist_tree.column("Description", width=300)

        # 헤더 설정
        for col in columns:
            self.checklist_tree.heading(col, text=col, anchor="center")

        # 스크롤바
        scrollbar_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.checklist_tree.yview)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.checklist_tree.xview)
        self.checklist_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        # 배치
        self.checklist_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # 더블클릭 이벤트
        self.checklist_tree.bind("<Double-1>", lambda e: self._edit_checklist_item())

    def _create_audit_log_tab(self):
        """Audit Log 탭"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="변경 이력")

        # 상단 버튼 프레임
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(
            btn_frame,
            text="🔄 새로고침",
            command=self._refresh_audit_log,
            width=12
        ).pack(side=tk.LEFT, padx=2)

        # 트리뷰 프레임
        tree_frame = ttk.Frame(tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 트리뷰
        columns = ("ID", "작업", "대상 테이블", "대상 ID", "사용자", "사유", "시간")
        self.audit_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="tree headings",
            selectmode="browse"
        )

        # 컬럼 설정
        self.audit_tree.column("#0", width=0, stretch=False)
        self.audit_tree.column("ID", width=50, anchor="center")
        self.audit_tree.column("작업", width=100, anchor="center")
        self.audit_tree.column("대상 테이블", width=180)
        self.audit_tree.column("대상 ID", width=80, anchor="center")
        self.audit_tree.column("사용자", width=120)
        self.audit_tree.column("사유", width=300)
        self.audit_tree.column("시간", width=180)

        # 헤더 설정
        for col in columns:
            self.audit_tree.heading(col, text=col, anchor="center")

        # 스크롤바
        scrollbar_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.audit_tree.yview)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.audit_tree.xview)
        self.audit_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        # 배치
        self.audit_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

    def _load_data(self):
        """초기 데이터 로드"""
        self._refresh_checklist()
        self._refresh_audit_log()

    def _refresh_checklist(self):
        """QC Checklist 새로고침"""
        # 기존 항목 제거
        for item in self.checklist_tree.get_children():
            self.checklist_tree.delete(item)

        # 데이터 로드
        try:
            with self.db_schema.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, item_name, spec_min, spec_max, expected_value,
                           category, description, is_active
                    FROM QC_Checklist_Items
                    ORDER BY item_name
                """)
                items = cursor.fetchall()

                for item in items:
                    item_id = item[0]
                    item_name = item[1]
                    spec_min = item[2]
                    spec_max = item[3]
                    expected_value = item[4]
                    category = item[5] or "Uncategorized"
                    description = item[6] or ""
                    is_active = item[7]

                    # Spec 표시
                    if spec_min and spec_max:
                        spec_display = f"{spec_min} ~ {spec_max}"
                    else:
                        spec_display = "N/A"

                    # Expected Value 표시
                    if expected_value:
                        # JSON 파싱 시도
                        try:
                            parsed = json.loads(expected_value)
                            if isinstance(parsed, list):
                                expected_display = " / ".join(str(v) for v in parsed)
                            else:
                                expected_display = expected_value
                        except:
                            expected_display = expected_value
                    else:
                        expected_display = "N/A"

                    # Active 표시
                    active_display = "✓" if is_active else "✗"

                    # 태그 설정 (Active/Inactive 색상)
                    tag = "active" if is_active else "inactive"

                    self.checklist_tree.insert(
                        "",
                        tk.END,
                        values=(item_id, item_name, spec_display, expected_display,
                               category, active_display, description),
                        tags=(tag,)
                    )

                # 태그 색상 설정
                self.checklist_tree.tag_configure("active", background="#e6ffe6")
                self.checklist_tree.tag_configure("inactive", background="#ffe6e6")

        except Exception as e:
            messagebox.showerror("오류", f"Checklist 로드 실패:\n{str(e)}")

    def _refresh_audit_log(self):
        """Audit Log 새로고침"""
        # 기존 항목 제거
        for item in self.audit_tree.get_children():
            self.audit_tree.delete(item)

        # 데이터 로드
        try:
            with self.db_schema.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, action, target_table, target_id, reason, user, timestamp
                    FROM Checklist_Audit_Log
                    ORDER BY timestamp DESC
                    LIMIT 100
                """)
                logs = cursor.fetchall()

                for log in logs:
                    log_id = log[0]
                    action = log[1]
                    target_table = log[2]
                    target_id = log[3] if log[3] else "-"
                    reason = log[4] if log[4] else "-"
                    user = log[5] if log[5] else "시스템"
                    timestamp = log[6]

                    self.audit_tree.insert(
                        "",
                        tk.END,
                        values=(log_id, action, target_table, target_id, user, reason, timestamp)
                    )

        except Exception as e:
            messagebox.showerror("오류", f"Audit Log 로드 실패:\n{str(e)}")

    def _add_checklist_item(self):
        """Checklist 항목 추가"""
        dialog = ChecklistItemDialog(self.dialog, self.db_schema, mode="add")
        self.dialog.wait_window(dialog.dialog)

        if dialog.result:
            self._refresh_checklist()
            messagebox.showinfo("성공", "Checklist 항목이 추가되었습니다.")

    def _edit_checklist_item(self):
        """Checklist 항목 수정"""
        selected = self.checklist_tree.selection()
        if not selected:
            messagebox.showwarning("경고", "수정할 항목을 선택하세요.")
            return

        # 선택된 항목 ID 가져오기
        item_values = self.checklist_tree.item(selected[0], 'values')
        item_id = int(item_values[0])

        # 기존 데이터 로드
        try:
            with self.db_schema.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, item_name, spec_min, spec_max, expected_value,
                           category, description, is_active
                    FROM QC_Checklist_Items
                    WHERE id = ?
                """, (item_id,))
                item_data = cursor.fetchone()

            if item_data:
                dialog = ChecklistItemDialog(self.dialog, self.db_schema, mode="edit", item_data=item_data)
                self.dialog.wait_window(dialog.dialog)

                if dialog.result:
                    self._refresh_checklist()
                    messagebox.showinfo("성공", "Checklist 항목이 수정되었습니다.")

        except Exception as e:
            messagebox.showerror("오류", f"항목 로드 실패:\n{str(e)}")

    def _delete_checklist_item(self):
        """Checklist 항목 삭제"""
        selected = self.checklist_tree.selection()
        if not selected:
            messagebox.showwarning("경고", "삭제할 항목을 선택하세요.")
            return

        # 확인
        if not messagebox.askyesno("확인", "선택한 Checklist 항목을 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다."):
            return

        # 선택된 항목 ID 가져오기
        item_values = self.checklist_tree.item(selected[0], 'values')
        item_id = int(item_values[0])
        item_name = item_values[1]

        try:
            with self.db_schema.get_connection() as conn:
                cursor = conn.cursor()

                # Checklist 항목 삭제
                cursor.execute("DELETE FROM QC_Checklist_Items WHERE id = ?", (item_id,))

                # Audit Log 기록
                cursor.execute("""
                    INSERT INTO Checklist_Audit_Log
                    (action, target_table, target_id, old_value, reason, user, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                """, ("REMOVE", "QC_Checklist_Items", item_id, item_name,
                      "관리자에 의한 삭제", "Admin"))

                conn.commit()

            self._refresh_checklist()
            self._refresh_audit_log()
            messagebox.showinfo("성공", "Checklist 항목이 삭제되었습니다.")

        except Exception as e:
            messagebox.showerror("오류", f"삭제 실패:\n{str(e)}")

    def _activate_item(self):
        """항목 활성화"""
        self._toggle_active(True)

    def _deactivate_item(self):
        """항목 비활성화"""
        self._toggle_active(False)

    def _toggle_active(self, is_active):
        """항목 활성화/비활성화 토글"""
        selected = self.checklist_tree.selection()
        if not selected:
            messagebox.showwarning("경고", "항목을 선택하세요.")
            return

        # 선택된 항목 ID 가져오기
        item_values = self.checklist_tree.item(selected[0], 'values')
        item_id = int(item_values[0])
        item_name = item_values[1]

        action_text = "활성화" if is_active else "비활성화"

        try:
            with self.db_schema.get_connection() as conn:
                cursor = conn.cursor()

                # is_active 업데이트
                cursor.execute("""
                    UPDATE QC_Checklist_Items
                    SET is_active = ?
                    WHERE id = ?
                """, (1 if is_active else 0, item_id))

                # Audit Log 기록
                cursor.execute("""
                    INSERT INTO Checklist_Audit_Log
                    (action, target_table, target_id, new_value, reason, user, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                """, ("MODIFY", "QC_Checklist_Items", item_id, f"is_active={is_active}",
                      f"{action_text}", "Admin"))

                conn.commit()

            self._refresh_checklist()
            self._refresh_audit_log()
            messagebox.showinfo("성공", f"항목이 {action_text}되었습니다.")

        except Exception as e:
            messagebox.showerror("오류", f"{action_text} 실패:\n{str(e)}")

    def _import_from_csv(self):
        """CSV 파일에서 Checklist 항목 가져오기"""
        # 파일 선택
        file_path = filedialog.askopenfilename(
            title="CSV 파일 선택",
            filetypes=[("CSV 파일", "*.csv"), ("모든 파일", "*.*")]
        )

        if not file_path:
            return

        try:
            imported_count = 0
            error_count = 0
            errors = []

            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                # 필수 컬럼 확인
                required_columns = ['item_name']
                if not all(col in reader.fieldnames for col in required_columns):
                    messagebox.showerror("오류", f"CSV 파일에 필수 컬럼이 없습니다.\n필수: {', '.join(required_columns)}")
                    return

                with self.db_schema.get_connection() as conn:
                    cursor = conn.cursor()

                    for row_num, row in enumerate(reader, start=2):
                        try:
                            item_name = row['item_name'].strip()
                            if not item_name:
                                continue

                            spec_min = row.get('spec_min', '').strip() or None
                            spec_max = row.get('spec_max', '').strip() or None
                            expected_value = row.get('expected_value', '').strip() or None
                            category = row.get('category', '').strip() or None
                            description = row.get('description', '').strip() or None
                            is_active = row.get('is_active', '1').strip()

                            # is_active 변환
                            is_active = 1 if is_active in ['1', 'true', 'True', 'TRUE', 'yes'] else 0

                            # 중복 체크
                            cursor.execute("SELECT id FROM QC_Checklist_Items WHERE item_name = ?", (item_name,))
                            existing = cursor.fetchone()

                            if existing:
                                # 업데이트
                                cursor.execute("""
                                    UPDATE QC_Checklist_Items
                                    SET spec_min = ?, spec_max = ?, expected_value = ?,
                                        category = ?, description = ?, is_active = ?
                                    WHERE item_name = ?
                                """, (spec_min, spec_max, expected_value, category, description, is_active, item_name))
                            else:
                                # 삽입
                                cursor.execute("""
                                    INSERT INTO QC_Checklist_Items
                                    (item_name, spec_min, spec_max, expected_value, category, description, is_active)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)
                                """, (item_name, spec_min, spec_max, expected_value, category, description, is_active))

                            imported_count += 1

                        except Exception as e:
                            error_count += 1
                            errors.append(f"행 {row_num}: {str(e)}")

                    # Audit Log 기록
                    cursor.execute("""
                        INSERT INTO Checklist_Audit_Log
                        (action, target_table, reason, user, timestamp)
                        VALUES (?, ?, ?, ?, datetime('now'))
                    """, ("ADD", "QC_Checklist_Items", f"CSV Import: {imported_count}개 항목", "Admin"))

                    conn.commit()

            self._refresh_checklist()
            self._refresh_audit_log()

            # 결과 메시지
            result_msg = f"Import 완료:\n\n성공: {imported_count}개\n실패: {error_count}개"
            if errors:
                result_msg += f"\n\n오류 내역 (최대 5개):\n" + "\n".join(errors[:5])

            messagebox.showinfo("Import 완료", result_msg)

        except Exception as e:
            messagebox.showerror("오류", f"CSV Import 실패:\n{str(e)}")


class ChecklistItemDialog:
    """Checklist 항목 추가/수정 다이얼로그"""

    def __init__(self, parent, db_schema, mode="add", item_data=None):
        """
        Args:
            parent: 부모 윈도우
            db_schema: DBSchema 인스턴스
            mode: "add" 또는 "edit"
            item_data: 수정 모드일 때 기존 데이터 (tuple)
        """
        self.parent = parent
        self.db_schema = db_schema
        self.mode = mode
        self.item_data = item_data
        self.result = None

        # 다이얼로그 생성
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Checklist 항목 추가" if mode == "add" else "Checklist 항목 수정")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_ui()

        # 수정 모드일 경우 기존 데이터 로드
        if mode == "edit" and item_data:
            self._load_existing_data()

    def _create_ui(self):
        """UI 생성"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ItemName
        ttk.Label(main_frame, text="ItemName:").grid(row=0, column=0, sticky="w", pady=5)
        self.name_entry = ttk.Entry(main_frame, width=50)
        self.name_entry.grid(row=0, column=1, sticky="ew", pady=5, padx=(10, 0))

        # Spec Min
        ttk.Label(main_frame, text="Spec Min:").grid(row=1, column=0, sticky="w", pady=5)
        self.spec_min_entry = ttk.Entry(main_frame, width=50)
        self.spec_min_entry.grid(row=1, column=1, sticky="ew", pady=5, padx=(10, 0))

        # Spec Max
        ttk.Label(main_frame, text="Spec Max:").grid(row=2, column=0, sticky="w", pady=5)
        self.spec_max_entry = ttk.Entry(main_frame, width=50)
        self.spec_max_entry.grid(row=2, column=1, sticky="ew", pady=5, padx=(10, 0))

        # Expected Value
        ttk.Label(main_frame, text="Expected Value:").grid(row=3, column=0, sticky="w", pady=5)
        self.expected_entry = ttk.Entry(main_frame, width=50)
        self.expected_entry.grid(row=3, column=1, sticky="ew", pady=5, padx=(10, 0))

        # Expected Value 힌트
        hint_label = ttk.Label(
            main_frame,
            text='예: ["Pass", "Fail"] (JSON 배열) 또는 "OK" (문자열)',
            font=("Helvetica", 8),
            foreground="gray"
        )
        hint_label.grid(row=4, column=1, sticky="w", padx=(10, 0))

        # Category
        ttk.Label(main_frame, text="Category:").grid(row=5, column=0, sticky="w", pady=5)
        self.category_combo = ttk.Combobox(
            main_frame,
            values=["Performance", "Safety", "Configuration", "Communication", "Information", "Uncategorized"],
            width=47
        )
        self.category_combo.current(0)  # Performance 기본값
        self.category_combo.grid(row=5, column=1, sticky="ew", pady=5, padx=(10, 0))

        # Description
        ttk.Label(main_frame, text="Description:").grid(row=6, column=0, sticky="nw", pady=5)
        self.desc_text = tk.Text(main_frame, width=50, height=5)
        self.desc_text.grid(row=6, column=1, sticky="ew", pady=5, padx=(10, 0))

        # Active 체크박스
        self.active_var = tk.BooleanVar(value=True)
        self.active_check = ttk.Checkbutton(
            main_frame,
            text="Active (활성화)",
            variable=self.active_var
        )
        self.active_check.grid(row=7, column=1, sticky="w", pady=5, padx=(10, 0))

        # 버튼 프레임
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=8, column=0, columnspan=2, pady=(20, 0))

        ttk.Button(
            btn_frame,
            text="저장",
            command=self._save,
            width=15
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="취소",
            command=self.dialog.destroy,
            width=15
        ).pack(side=tk.LEFT, padx=5)

        main_frame.grid_columnconfigure(1, weight=1)

    def _load_existing_data(self):
        """기존 데이터 로드 (수정 모드)"""
        if not self.item_data:
            return

        # item_data: (id, item_name, spec_min, spec_max, expected_value, category, description, is_active)
        self.name_entry.insert(0, self.item_data[1] or "")
        self.spec_min_entry.insert(0, self.item_data[2] or "")
        self.spec_max_entry.insert(0, self.item_data[3] or "")
        self.expected_entry.insert(0, self.item_data[4] or "")

        category = self.item_data[5] or "Uncategorized"
        self.category_combo.set(category)

        description = self.item_data[6] or ""
        self.desc_text.insert("1.0", description)

        is_active = self.item_data[7]
        self.active_var.set(bool(is_active))

        # 수정 모드에서는 ItemName 변경 불가
        self.name_entry.config(state="readonly")

    def _save(self):
        """저장"""
        # 입력 값 가져오기
        item_name = self.name_entry.get().strip()
        spec_min = self.spec_min_entry.get().strip() or None
        spec_max = self.spec_max_entry.get().strip() or None
        expected_value = self.expected_entry.get().strip() or None
        category = self.category_combo.get().strip() or None
        description = self.desc_text.get("1.0", tk.END).strip() or None
        is_active = 1 if self.active_var.get() else 0

        # 유효성 검사
        if not item_name:
            messagebox.showwarning("경고", "ItemName을 입력하세요.")
            return

        # Spec 검증: Min과 Max는 함께 입력되어야 함
        if (spec_min and not spec_max) or (not spec_min and spec_max):
            messagebox.showwarning("경고", "Spec Min과 Max는 함께 입력해야 합니다.")
            return

        # Expected Value JSON 검증
        if expected_value:
            try:
                # JSON 파싱 시도
                json.loads(expected_value)
            except json.JSONDecodeError:
                # JSON이 아니면 단순 문자열로 처리 (오류 아님)
                pass

        # 저장
        try:
            with self.db_schema.get_connection() as conn:
                cursor = conn.cursor()

                if self.mode == "add":
                    # 중복 체크
                    cursor.execute("SELECT id FROM QC_Checklist_Items WHERE item_name = ?", (item_name,))
                    if cursor.fetchone():
                        messagebox.showerror("오류", f"'{item_name}' 항목이 이미 존재합니다.")
                        return

                    # 삽입
                    cursor.execute("""
                        INSERT INTO QC_Checklist_Items
                        (item_name, spec_min, spec_max, expected_value, category, description, is_active)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (item_name, spec_min, spec_max, expected_value, category, description, is_active))

                    new_id = cursor.lastrowid

                    # Audit Log 기록
                    cursor.execute("""
                        INSERT INTO Checklist_Audit_Log
                        (action, target_table, target_id, new_value, reason, user, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                    """, ("ADD", "QC_Checklist_Items", new_id, item_name, "신규 항목 추가", "Admin"))

                else:  # edit
                    item_id = self.item_data[0]

                    # 업데이트
                    cursor.execute("""
                        UPDATE QC_Checklist_Items
                        SET spec_min = ?, spec_max = ?, expected_value = ?,
                            category = ?, description = ?, is_active = ?
                        WHERE id = ?
                    """, (spec_min, spec_max, expected_value, category, description, is_active, item_id))

                    # Audit Log 기록
                    cursor.execute("""
                        INSERT INTO Checklist_Audit_Log
                        (action, target_table, target_id, new_value, reason, user, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                    """, ("MODIFY", "QC_Checklist_Items", item_id, item_name, "항목 수정", "Admin"))

                conn.commit()

            self.result = True
            self.dialog.destroy()

        except Exception as e:
            messagebox.showerror("오류", f"저장 실패:\n{str(e)}")
