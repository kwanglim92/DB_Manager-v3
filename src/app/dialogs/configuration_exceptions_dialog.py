"""
Configuration Exceptions Dialog - Phase 1.5 Week 3 Day 4

Configuration별 QC Checklist 예외 관리 UI
- Configuration 선택
- 제외 항목 관리 (추가/삭제)
- 사유 입력 (필수)
- 승인자, 승인일 기록

Author: Phase 1.5 Week 3
Date: 2025-11-13
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime


class ConfigurationExceptionsDialog:
    """Configuration별 Checklist 예외 관리 Dialog"""

    def __init__(self, parent, db_schema):
        """
        Args:
            parent: 부모 윈도우
            db_schema: DBSchema 인스턴스
        """
        self.parent = parent
        self.db_schema = db_schema
        self.current_configuration_id = None

        # 다이얼로그 생성
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Configuration Checklist Exceptions (관리자 전용)")
        self.dialog.geometry("1000x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_ui()
        self._load_configurations()

    def _create_ui(self):
        """UI 생성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 제목
        title_label = ttk.Label(
            main_frame,
            text="Configuration Checklist Exceptions 관리",
            font=("Helvetica", 14, "bold")
        )
        title_label.pack(pady=(0, 10))

        # 설명
        desc_label = ttk.Label(
            main_frame,
            text="특정 Configuration에서 제외할 Checklist 항목을 관리합니다.",
            foreground="gray"
        )
        desc_label.pack(pady=(0, 10))

        # Configuration 선택 프레임
        config_frame = ttk.LabelFrame(main_frame, text="Configuration 선택", padding="10")
        config_frame.pack(fill=tk.X, pady=(0, 10))

        # Equipment Model 선택
        ttk.Label(config_frame, text="Equipment Model:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.model_combo = ttk.Combobox(config_frame, state="readonly", width=30)
        self.model_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.model_combo.bind("<<ComboboxSelected>>", lambda e: self._on_model_selected())

        # Equipment Type 선택
        ttk.Label(config_frame, text="Equipment Type:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.type_combo = ttk.Combobox(config_frame, state="readonly", width=30)
        self.type_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.type_combo.bind("<<ComboboxSelected>>", lambda e: self._on_type_selected())

        # Configuration 선택
        ttk.Label(config_frame, text="Configuration:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.config_combo = ttk.Combobox(config_frame, state="readonly", width=30)
        self.config_combo.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        self.config_combo.bind("<<ComboboxSelected>>", lambda e: self._on_configuration_selected())

        config_frame.grid_columnconfigure(1, weight=1)

        # 예외 목록 프레임
        exceptions_frame = ttk.LabelFrame(main_frame, text="적용된 예외 항목", padding="10")
        exceptions_frame.pack(fill=tk.BOTH, expand=True)

        # 버튼 프레임
        btn_frame = ttk.Frame(exceptions_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(
            btn_frame,
            text="➕ 예외 추가",
            command=self._add_exception,
            width=15
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            btn_frame,
            text="❌ 예외 제거",
            command=self._remove_exception,
            width=15
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            btn_frame,
            text="🔄 새로고침",
            command=self._refresh_exceptions,
            width=15
        ).pack(side=tk.LEFT, padx=2)

        # 트리뷰 프레임
        tree_frame = ttk.Frame(exceptions_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # 트리뷰
        columns = ("ID", "ItemName", "사유", "승인자", "승인일")
        self.exceptions_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="tree headings",
            selectmode="browse"
        )

        # 컬럼 설정
        self.exceptions_tree.column("#0", width=0, stretch=False)
        self.exceptions_tree.column("ID", width=50, anchor="center")
        self.exceptions_tree.column("ItemName", width=250)
        self.exceptions_tree.column("사유", width=300)
        self.exceptions_tree.column("승인자", width=120, anchor="center")
        self.exceptions_tree.column("승인일", width=150, anchor="center")

        # 헤더 설정
        for col in columns:
            self.exceptions_tree.heading(col, text=col, anchor="center")

        # 스크롤바
        scrollbar_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.exceptions_tree.yview)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.exceptions_tree.xview)
        self.exceptions_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        # 배치
        self.exceptions_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # 닫기 버튼
        close_btn_frame = ttk.Frame(main_frame)
        close_btn_frame.pack(pady=(10, 0))

        ttk.Button(
            close_btn_frame,
            text="닫기",
            command=self.dialog.destroy,
            width=15
        ).pack()

    def _load_configurations(self):
        """Equipment Models 로드"""
        try:
            with self.db_schema.get_connection() as conn:
                cursor = conn.cursor()

                # Equipment Models 로드
                cursor.execute("""
                    SELECT id, model_name
                    FROM Equipment_Models
                    ORDER BY display_order, model_name
                """)
                models = cursor.fetchall()

                self.model_combo['values'] = [f"{m[0]}: {m[1]}" for m in models]
                if models:
                    self.model_combo.current(0)
                    self._on_model_selected()

        except Exception as e:
            messagebox.showerror("오류", f"Configuration 로드 실패:\n{str(e)}")

    def _on_model_selected(self):
        """Model 선택 시 Types 로드"""
        selected = self.model_combo.get()
        if not selected:
            return

        model_id = int(selected.split(":")[0])

        try:
            with self.db_schema.get_connection() as conn:
                cursor = conn.cursor()

                # Equipment Types 로드
                cursor.execute("""
                    SELECT id, type_name
                    FROM Equipment_Types
                    WHERE model_id = ?
                    ORDER BY type_name
                """, (model_id,))
                types = cursor.fetchall()

                self.type_combo['values'] = [f"{t[0]}: {t[1]}" for t in types]
                if types:
                    self.type_combo.current(0)
                    self._on_type_selected()
                else:
                    self.type_combo['values'] = []
                    self.config_combo['values'] = []

        except Exception as e:
            messagebox.showerror("오류", f"Equipment Type 로드 실패:\n{str(e)}")

    def _on_type_selected(self):
        """Type 선택 시 Configurations 로드"""
        selected = self.type_combo.get()
        if not selected:
            return

        type_id = int(selected.split(":")[0])

        try:
            with self.db_schema.get_connection() as conn:
                cursor = conn.cursor()

                # Equipment Configurations 로드
                cursor.execute("""
                    SELECT id, config_name, port_type, wafer_sizes, customer_name
                    FROM Equipment_Configurations
                    WHERE equipment_type_id = ?
                    ORDER BY config_name
                """, (type_id,))
                configs = cursor.fetchall()

                config_values = []
                for c in configs:
                    config_id, config_name, port_type, wafer_sizes, customer_name = c
                    display = f"{config_id}: {config_name}"
                    if customer_name:
                        display += f" (Customer: {customer_name})"
                    config_values.append(display)

                self.config_combo['values'] = config_values
                if configs:
                    self.config_combo.current(0)
                    self._on_configuration_selected()
                else:
                    self.config_combo['values'] = []
                    self.current_configuration_id = None
                    self._refresh_exceptions()

        except Exception as e:
            messagebox.showerror("오류", f"Configuration 로드 실패:\n{str(e)}")

    def _on_configuration_selected(self):
        """Configuration 선택 시 예외 목록 로드"""
        selected = self.config_combo.get()
        if not selected:
            self.current_configuration_id = None
            self._refresh_exceptions()
            return

        self.current_configuration_id = int(selected.split(":")[0])
        self._refresh_exceptions()

    def _refresh_exceptions(self):
        """예외 목록 새로고침"""
        # 기존 항목 제거
        for item in self.exceptions_tree.get_children():
            self.exceptions_tree.delete(item)

        if not self.current_configuration_id:
            return

        # 데이터 로드
        try:
            with self.db_schema.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT
                        e.id,
                        c.item_name,
                        e.reason,
                        e.approved_by,
                        e.approved_date
                    FROM Equipment_Checklist_Exceptions e
                    JOIN QC_Checklist_Items c ON e.checklist_item_id = c.id
                    WHERE e.configuration_id = ?
                    ORDER BY c.item_name
                """, (self.current_configuration_id,))
                exceptions = cursor.fetchall()

                for exc in exceptions:
                    exc_id, item_name, reason, approved_by, approved_date = exc

                    approved_by_display = approved_by or "-"
                    approved_date_display = approved_date or "-"

                    self.exceptions_tree.insert(
                        "",
                        tk.END,
                        values=(exc_id, item_name, reason, approved_by_display, approved_date_display)
                    )

        except Exception as e:
            messagebox.showerror("오류", f"예외 목록 로드 실패:\n{str(e)}")

    def _add_exception(self):
        """예외 추가"""
        if not self.current_configuration_id:
            messagebox.showwarning("경고", "Configuration을 먼저 선택하세요.")
            return

        # 예외 추가 Dialog 열기
        dialog = AddExceptionDialog(self.dialog, self.db_schema, self.current_configuration_id)
        self.dialog.wait_window(dialog.dialog)

        if dialog.result:
            self._refresh_exceptions()
            messagebox.showinfo("성공", "예외가 추가되었습니다.")

    def _remove_exception(self):
        """예외 제거"""
        selected = self.exceptions_tree.selection()
        if not selected:
            messagebox.showwarning("경고", "제거할 예외를 선택하세요.")
            return

        # 확인
        if not messagebox.askyesno("확인", "선택한 예외를 제거하시겠습니까?"):
            return

        # 선택된 예외 ID 가져오기
        item_values = self.exceptions_tree.item(selected[0], 'values')
        exception_id = int(item_values[0])
        item_name = item_values[1]

        try:
            with self.db_schema.get_connection() as conn:
                cursor = conn.cursor()

                # 예외 삭제
                cursor.execute("DELETE FROM Equipment_Checklist_Exceptions WHERE id = ?", (exception_id,))

                # Audit Log 기록
                cursor.execute("""
                    INSERT INTO Checklist_Audit_Log
                    (action, target_table, target_id, old_value, reason, user, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                """, ("REMOVE", "Equipment_Checklist_Exceptions", exception_id, item_name,
                      "예외 제거", "Admin"))

                conn.commit()

            self._refresh_exceptions()
            messagebox.showinfo("성공", "예외가 제거되었습니다.")

        except Exception as e:
            messagebox.showerror("오류", f"예외 제거 실패:\n{str(e)}")


class AddExceptionDialog:
    """예외 추가 다이얼로그"""

    def __init__(self, parent, db_schema, configuration_id):
        """
        Args:
            parent: 부모 윈도우
            db_schema: DBSchema 인스턴스
            configuration_id: Configuration ID
        """
        self.parent = parent
        self.db_schema = db_schema
        self.configuration_id = configuration_id
        self.result = None

        # 다이얼로그 생성
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("예외 추가")
        self.dialog.geometry("600x450")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_ui()
        self._load_available_items()

    def _create_ui(self):
        """UI 생성"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Checklist 항목 선택
        ttk.Label(main_frame, text="제외할 Checklist 항목:").pack(anchor="w", pady=(0, 5))

        # 리스트박스 + 스크롤바
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        self.items_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            selectmode=tk.SINGLE,
            height=10
        )
        scrollbar.config(command=self.items_listbox.yview)

        self.items_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 사유 입력 (필수)
        ttk.Label(main_frame, text="사유 (필수):").pack(anchor="w", pady=(10, 5))
        self.reason_text = tk.Text(main_frame, height=5)
        self.reason_text.pack(fill=tk.X, pady=(0, 10))

        # 승인자
        ttk.Label(main_frame, text="승인자:").pack(anchor="w", pady=(0, 5))
        self.approver_entry = ttk.Entry(main_frame)
        self.approver_entry.pack(fill=tk.X, pady=(0, 10))
        self.approver_entry.insert(0, "Admin")

        # 버튼 프레임
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=(10, 0))

        ttk.Button(
            btn_frame,
            text="추가",
            command=self._add,
            width=15
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="취소",
            command=self.dialog.destroy,
            width=15
        ).pack(side=tk.LEFT, padx=5)

    def _load_available_items(self):
        """추가 가능한 Checklist 항목 로드 (이미 예외로 추가된 항목 제외)"""
        try:
            with self.db_schema.get_connection() as conn:
                cursor = conn.cursor()

                # 이미 예외로 추가된 항목 제외
                cursor.execute("""
                    SELECT id, item_name
                    FROM QC_Checklist_Items
                    WHERE is_active = 1
                      AND id NOT IN (
                          SELECT checklist_item_id
                          FROM Equipment_Checklist_Exceptions
                          WHERE configuration_id = ?
                      )
                    ORDER BY item_name
                """, (self.configuration_id,))
                items = cursor.fetchall()

                self.available_items = items
                for item in items:
                    item_id, item_name = item
                    self.items_listbox.insert(tk.END, f"{item_id}: {item_name}")

        except Exception as e:
            messagebox.showerror("오류", f"Checklist 항목 로드 실패:\n{str(e)}")

    def _add(self):
        """예외 추가"""
        # Checklist 항목 선택 확인
        selection = self.items_listbox.curselection()
        if not selection:
            messagebox.showwarning("경고", "제외할 Checklist 항목을 선택하세요.")
            return

        selected_index = selection[0]
        checklist_item_id = self.available_items[selected_index][0]

        # 사유 확인
        reason = self.reason_text.get("1.0", tk.END).strip()
        if not reason:
            messagebox.showwarning("경고", "사유를 입력하세요.")
            return

        # 승인자
        approver = self.approver_entry.get().strip() or "Admin"

        # 승인일 (현재 시각)
        approved_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 추가
        try:
            with self.db_schema.get_connection() as conn:
                cursor = conn.cursor()

                # 예외 추가
                cursor.execute("""
                    INSERT INTO Equipment_Checklist_Exceptions
                    (configuration_id, checklist_item_id, reason, approved_by, approved_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (self.configuration_id, checklist_item_id, reason, approver, approved_date))

                exception_id = cursor.lastrowid

                # Audit Log 기록
                cursor.execute("""
                    INSERT INTO Checklist_Audit_Log
                    (action, target_table, target_id, new_value, reason, user, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                """, ("ADD", "Equipment_Checklist_Exceptions", exception_id,
                      f"config_id={self.configuration_id}, item_id={checklist_item_id}",
                      reason, approver))

                conn.commit()

            self.result = True
            self.dialog.destroy()

        except Exception as e:
            messagebox.showerror("오류", f"예외 추가 실패:\n{str(e)}")
