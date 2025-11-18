"""
Shipped Equipment List 관리 다이얼로그 (Phase 2)

출고 장비 목록을 표시하고, 필터링/검색/정렬 기능을 제공합니다.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from typing import Optional, List


class ShippedEquipmentListDialog:
    """Shipped Equipment List 다이얼로그"""

    def __init__(self, parent, db_schema, service_factory):
        """
        Args:
            parent: 부모 윈도우
            db_schema: DBSchema 인스턴스
            service_factory: ServiceFactory 인스턴스
        """
        self.parent = parent
        self.db_schema = db_schema
        self.service_factory = service_factory
        self.shipped_service = service_factory.get_shipped_equipment_service()
        self.configuration_service = service_factory.get_configuration_service()

        # 필터 상태
        self.filter_configuration = None
        self.filter_customer = None
        self.filter_date_from = None
        self.filter_date_to = None
        self.search_text = ""

        # 다이얼로그 생성
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Shipped Equipment 목록")
        self.dialog.geometry("1400x800")
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
            text="📦 Shipped Equipment 목록",
            font=("Helvetica", 14, "bold")
        )
        title_label.pack(pady=(0, 10))

        # 툴바 프레임
        toolbar_frame = ttk.Frame(main_frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(
            toolbar_frame,
            text="🔄 Refresh",
            command=self._refresh,
            width=12
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            toolbar_frame,
            text="📥 Import",
            command=self._import_equipment,
            width=12
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            toolbar_frame,
            text="🔍 Filter",
            command=self._toggle_filter,
            width=12
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            toolbar_frame,
            text="❌ Clear Filter",
            command=self._clear_filter,
            width=12
        ).pack(side=tk.LEFT, padx=2)

        # 검색 입력 (우측)
        search_frame = ttk.Frame(toolbar_frame)
        search_frame.pack(side=tk.RIGHT, padx=2)

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))

        self.search_entry = ttk.Entry(search_frame, width=25)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry.bind("<Return>", lambda e: self._apply_search())

        ttk.Button(
            search_frame,
            text="Go",
            command=self._apply_search,
            width=5
        ).pack(side=tk.LEFT)

        # 필터 프레임 (토글 가능)
        self.filter_frame = ttk.LabelFrame(main_frame, text="필터", padding="10")
        self.filter_visible = False  # 초기에는 숨김

        filter_row1 = ttk.Frame(self.filter_frame)
        filter_row1.pack(fill=tk.X, pady=(0, 5))

        # Configuration 필터
        ttk.Label(filter_row1, text="Configuration:", width=15).pack(side=tk.LEFT, padx=(0, 5))
        self.filter_config_combo = ttk.Combobox(filter_row1, width=25, state="readonly")
        self.filter_config_combo.pack(side=tk.LEFT, padx=(0, 20))

        # Customer 필터
        ttk.Label(filter_row1, text="Customer:", width=12).pack(side=tk.LEFT, padx=(0, 5))
        self.filter_customer_combo = ttk.Combobox(filter_row1, width=25, state="readonly")
        self.filter_customer_combo.pack(side=tk.LEFT)

        filter_row2 = ttk.Frame(self.filter_frame)
        filter_row2.pack(fill=tk.X, pady=(0, 5))

        # Date From
        ttk.Label(filter_row2, text="Date From:", width=15).pack(side=tk.LEFT, padx=(0, 5))
        self.filter_date_from_entry = ttk.Entry(filter_row2, width=12)
        self.filter_date_from_entry.pack(side=tk.LEFT, padx=(0, 20))

        # Date To
        ttk.Label(filter_row2, text="Date To:", width=12).pack(side=tk.LEFT, padx=(0, 5))
        self.filter_date_to_entry = ttk.Entry(filter_row2, width=12)
        self.filter_date_to_entry.pack(side=tk.LEFT, padx=(0, 20))

        # Apply Filter 버튼
        ttk.Button(
            filter_row2,
            text="Apply Filter",
            command=self._apply_filter,
            width=12
        ).pack(side=tk.LEFT)

        # Treeview 프레임
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # Treeview 생성
        columns = ("Serial", "Customer", "Model", "Type", "Configuration", "Ship Date", "Refit")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)

        # 컬럼 설정
        self.tree.heading("Serial", text="Serial Number")
        self.tree.heading("Customer", text="Customer")
        self.tree.heading("Model", text="Model")
        self.tree.heading("Type", text="Type")
        self.tree.heading("Configuration", text="Configuration")
        self.tree.heading("Ship Date", text="Ship Date")
        self.tree.heading("Refit", text="Refit")

        self.tree.column("Serial", width=150)
        self.tree.column("Customer", width=200)
        self.tree.column("Model", width=150)
        self.tree.column("Type", width=150)
        self.tree.column("Configuration", width=200)
        self.tree.column("Ship Date", width=100)
        self.tree.column("Refit", width=80)

        # 스크롤바
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # 배치
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # 우클릭 메뉴
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="📊 View Parameters", command=self._view_parameters)
        self.context_menu.add_command(label="🗑️ Delete", command=self._delete_equipment)

        self.tree.bind("<Button-3>", self._show_context_menu)

        # 하단 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        # 통계 레이블 (좌측)
        self.stats_label = ttk.Label(button_frame, text="Total: 0 equipment")
        self.stats_label.pack(side=tk.LEFT)

        ttk.Button(
            button_frame,
            text="Close",
            command=self.dialog.destroy,
            width=15
        ).pack(side=tk.RIGHT)

    def _toggle_filter(self):
        """필터 영역 토글"""
        if self.filter_visible:
            self.filter_frame.pack_forget()
            self.filter_visible = False
        else:
            self.filter_frame.pack(fill=tk.X, pady=(0, 10), after=self.dialog.winfo_children()[0].winfo_children()[2])
            self.filter_visible = True
            self._load_filter_options()

    def _load_filter_options(self):
        """필터 옵션 로드"""
        # Configuration 목록
        configurations = []
        if self.configuration_service:
            all_configs = self.configuration_service.get_all_configurations()
            configurations = [f"{c.configuration_name}" for c in all_configs]

        self.filter_config_combo['values'] = ["(All)"] + configurations
        self.filter_config_combo.current(0)

        # Customer 목록 (DB에서 가져오기)
        customers = []
        if self.shipped_service:
            with self.db_schema.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT customer_name FROM Shipped_Equipment ORDER BY customer_name")
                customers = [row[0] for row in cursor.fetchall()]

        self.filter_customer_combo['values'] = ["(All)"] + customers
        self.filter_customer_combo.current(0)

    def _apply_filter(self):
        """필터 적용"""
        # Configuration 필터
        config_text = self.filter_config_combo.get()
        if config_text and config_text != "(All)":
            self.filter_configuration = config_text
        else:
            self.filter_configuration = None

        # Customer 필터
        customer_text = self.filter_customer_combo.get()
        if customer_text and customer_text != "(All)":
            self.filter_customer = customer_text
        else:
            self.filter_customer = None

        # Date 필터
        date_from_text = self.filter_date_from_entry.get().strip()
        date_to_text = self.filter_date_to_entry.get().strip()

        if date_from_text:
            try:
                self.filter_date_from = datetime.strptime(date_from_text, "%Y-%m-%d").date()
            except ValueError:
                messagebox.showwarning("Invalid Date", "Date From format should be YYYY-MM-DD")
                return
        else:
            self.filter_date_from = None

        if date_to_text:
            try:
                self.filter_date_to = datetime.strptime(date_to_text, "%Y-%m-%d").date()
            except ValueError:
                messagebox.showwarning("Invalid Date", "Date To format should be YYYY-MM-DD")
                return
        else:
            self.filter_date_to = None

        self._load_data()

    def _clear_filter(self):
        """필터 초기화"""
        self.filter_configuration = None
        self.filter_customer = None
        self.filter_date_from = None
        self.filter_date_to = None
        self.search_text = ""

        if self.filter_visible:
            self.filter_config_combo.current(0)
            self.filter_customer_combo.current(0)
            self.filter_date_from_entry.delete(0, tk.END)
            self.filter_date_to_entry.delete(0, tk.END)

        self.search_entry.delete(0, tk.END)
        self._load_data()

    def _apply_search(self):
        """검색 적용"""
        self.search_text = self.search_entry.get().strip()
        self._load_data()

    def _load_data(self):
        """데이터 로드"""
        # 기존 데이터 삭제
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not self.shipped_service:
            return

        # 모든 Shipped Equipment 조회
        equipments = self.shipped_service.get_all_shipped_equipment()

        # 필터 적용
        filtered_equipments = []
        for eq in equipments:
            # Configuration 필터
            if self.filter_configuration and eq.configuration_name != self.filter_configuration:
                continue

            # Customer 필터
            if self.filter_customer and eq.customer_name != self.filter_customer:
                continue

            # Date 필터
            if eq.ship_date:
                if self.filter_date_from and eq.ship_date < self.filter_date_from:
                    continue
                if self.filter_date_to and eq.ship_date > self.filter_date_to:
                    continue

            # 검색 필터 (Serial, Customer, Model, Type, Configuration)
            if self.search_text:
                search_lower = self.search_text.lower()
                if not any([
                    search_lower in (eq.serial_number or "").lower(),
                    search_lower in (eq.customer_name or "").lower(),
                    search_lower in (eq.model_name or "").lower(),
                    search_lower in (eq.type_name or "").lower(),
                    search_lower in (eq.configuration_name or "").lower()
                ]):
                    continue

            filtered_equipments.append(eq)

        # Treeview에 추가
        for eq in filtered_equipments:
            ship_date_str = eq.ship_date.strftime("%Y-%m-%d") if eq.ship_date else ""
            refit_str = "Yes" if eq.is_refit else "No"

            self.tree.insert("", tk.END, values=(
                eq.serial_number,
                eq.customer_name,
                eq.model_name or "",
                eq.type_name or "",
                eq.configuration_name or "",
                ship_date_str,
                refit_str
            ), tags=(str(eq.id),))

        # 통계 업데이트
        self.stats_label.config(text=f"Total: {len(filtered_equipments)} equipment")

    def _refresh(self):
        """새로고침"""
        self._load_data()

    def _show_context_menu(self, event):
        """우클릭 메뉴 표시"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def _view_parameters(self):
        """파라미터 조회"""
        selected = self.tree.selection()
        if not selected:
            return

        item = selected[0]
        tags = self.tree.item(item, "tags")
        if not tags:
            return

        equipment_id = int(tags[0])

        # Parameter View Dialog 열기 (별도 구현 필요)
        from .shipped_equipment_parameter_dialog import ShippedEquipmentParameterDialog
        ShippedEquipmentParameterDialog(
            self.dialog,
            self.db_schema,
            self.service_factory,
            equipment_id
        )

    def _delete_equipment(self):
        """장비 삭제"""
        selected = self.tree.selection()
        if not selected:
            return

        item = selected[0]
        tags = self.tree.item(item, "tags")
        if not tags:
            return

        equipment_id = int(tags[0])
        values = self.tree.item(item, "values")
        serial_number = values[0]

        # 확인 다이얼로그
        confirm = messagebox.askyesno(
            "Delete Equipment",
            f"Are you sure you want to delete equipment '{serial_number}'?\n\n"
            "This will also delete all associated parameters (CASCADE).",
            icon="warning"
        )

        if not confirm:
            return

        # 삭제
        try:
            self.shipped_service.delete_shipped_equipment(equipment_id)
            messagebox.showinfo("Success", f"Equipment '{serial_number}' deleted successfully.")
            self._refresh()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete equipment: {e}")

    def _import_equipment(self):
        """장비 임포트"""
        # Import Dialog 열기 (별도 구현 필요)
        from .shipped_equipment_import_dialog import ShippedEquipmentImportDialog
        dialog = ShippedEquipmentImportDialog(
            self.dialog,
            self.db_schema,
            self.service_factory
        )

        # Import 완료 후 새로고침
        self.dialog.wait_window(dialog.dialog)
        self._refresh()
