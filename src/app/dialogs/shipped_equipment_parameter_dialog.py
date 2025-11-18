"""
Shipped Equipment Parameter View 다이얼로그 (Phase 2)

특정 출고 장비의 파라미터를 조회하고 표시합니다.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv


class ShippedEquipmentParameterDialog:
    """Shipped Equipment Parameter View 다이얼로그"""

    def __init__(self, parent, db_schema, service_factory, equipment_id):
        """
        Args:
            parent: 부모 윈도우
            db_schema: DBSchema 인스턴스
            service_factory: ServiceFactory 인스턴스
            equipment_id: Shipped Equipment ID
        """
        self.parent = parent
        self.db_schema = db_schema
        self.service_factory = service_factory
        self.shipped_service = service_factory.get_shipped_equipment_service()
        self.equipment_id = equipment_id

        # 장비 정보 및 파라미터
        self.equipment = None
        self.parameters = []
        self.filtered_parameters = []

        # 검색 텍스트
        self.search_text = ""

        # 다이얼로그 생성
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Equipment Parameters")
        self.dialog.geometry("1200x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._load_equipment()
        self._create_ui()
        self._load_parameters()

    def _load_equipment(self):
        """장비 정보 로드"""
        if not self.shipped_service:
            return

        self.equipment = self.shipped_service.get_shipped_equipment_by_id(self.equipment_id)

    def _create_ui(self):
        """UI 생성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 제목
        if self.equipment:
            title_text = f"📊 Parameters - {self.equipment.serial_number}"
        else:
            title_text = "📊 Equipment Parameters"

        title_label = ttk.Label(
            main_frame,
            text=title_text,
            font=("Helvetica", 14, "bold")
        )
        title_label.pack(pady=(0, 10))

        # 장비 정보 프레임
        if self.equipment:
            info_frame = ttk.LabelFrame(main_frame, text="Equipment Information", padding="10")
            info_frame.pack(fill=tk.X, pady=(0, 10))

            info_grid = ttk.Frame(info_frame)
            info_grid.pack(fill=tk.X)

            # 좌측
            left_col = ttk.Frame(info_grid)
            left_col.pack(side=tk.LEFT, fill=tk.X, expand=True)

            ttk.Label(left_col, text="Serial Number:").grid(row=0, column=0, sticky=tk.W, pady=2)
            ttk.Label(left_col, text=self.equipment.serial_number, foreground="blue").grid(row=0, column=1, sticky=tk.W, padx=(5, 0), pady=2)

            ttk.Label(left_col, text="Customer:").grid(row=1, column=0, sticky=tk.W, pady=2)
            ttk.Label(left_col, text=self.equipment.customer_name, foreground="blue").grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=2)

            ttk.Label(left_col, text="Model:").grid(row=2, column=0, sticky=tk.W, pady=2)
            ttk.Label(left_col, text=self.equipment.model_name or "-", foreground="blue").grid(row=2, column=1, sticky=tk.W, padx=(5, 0), pady=2)

            # 우측
            right_col = ttk.Frame(info_grid)
            right_col.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(30, 0))

            ttk.Label(right_col, text="Configuration:").grid(row=0, column=0, sticky=tk.W, pady=2)
            ttk.Label(right_col, text=self.equipment.configuration_name or "-", foreground="blue").grid(row=0, column=1, sticky=tk.W, padx=(5, 0), pady=2)

            ship_date_str = self.equipment.ship_date.strftime("%Y-%m-%d") if self.equipment.ship_date else "-"
            ttk.Label(right_col, text="Ship Date:").grid(row=1, column=0, sticky=tk.W, pady=2)
            ttk.Label(right_col, text=ship_date_str, foreground="blue").grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=2)

            refit_str = "Yes" if self.equipment.is_refit else "No"
            ttk.Label(right_col, text="Refit:").grid(row=2, column=0, sticky=tk.W, pady=2)
            ttk.Label(right_col, text=refit_str, foreground="red" if self.equipment.is_refit else "green").grid(row=2, column=1, sticky=tk.W, padx=(5, 0), pady=2)

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
            text="📁 Export CSV",
            command=self._export_csv,
            width=12
        ).pack(side=tk.LEFT, padx=2)

        # 검색 입력 (우측)
        search_frame = ttk.Frame(toolbar_frame)
        search_frame.pack(side=tk.RIGHT, padx=2)

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))

        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry.bind("<Return>", lambda e: self._apply_search())

        ttk.Button(
            search_frame,
            text="Go",
            command=self._apply_search,
            width=5
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            search_frame,
            text="Clear",
            command=self._clear_search,
            width=6
        ).pack(side=tk.LEFT)

        # Treeview 프레임
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Treeview 생성
        columns = ("Parameter Name", "Value", "Module", "Part", "Data Type")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)

        # 컬럼 설정
        self.tree.heading("Parameter Name", text="Parameter Name")
        self.tree.heading("Value", text="Value")
        self.tree.heading("Module", text="Module")
        self.tree.heading("Part", text="Part")
        self.tree.heading("Data Type", text="Data Type")

        self.tree.column("Parameter Name", width=300)
        self.tree.column("Value", width=150)
        self.tree.column("Module", width=150)
        self.tree.column("Part", width=150)
        self.tree.column("Data Type", width=100)

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

        # 하단 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 0))

        # 통계 레이블 (좌측)
        self.stats_label = ttk.Label(button_frame, text="Total: 0 parameters")
        self.stats_label.pack(side=tk.LEFT)

        ttk.Button(
            button_frame,
            text="Close",
            command=self.dialog.destroy,
            width=15
        ).pack(side=tk.RIGHT)

    def _load_parameters(self):
        """파라미터 로드"""
        if not self.shipped_service:
            return

        # 파라미터 조회
        self.parameters = self.shipped_service.get_parameters_by_equipment(self.equipment_id)
        self.filtered_parameters = self.parameters.copy()

        # Treeview에 표시
        self._update_tree()

    def _update_tree(self):
        """Treeview 업데이트"""
        # 기존 데이터 삭제
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 필터링된 파라미터 표시
        for param in self.filtered_parameters:
            self.tree.insert("", tk.END, values=(
                param.parameter_name,
                param.parameter_value,
                param.module or "",
                param.part or "",
                param.data_type or ""
            ))

        # 통계 업데이트
        self.stats_label.config(text=f"Total: {len(self.filtered_parameters)} parameters (of {len(self.parameters)})")

    def _apply_search(self):
        """검색 적용"""
        self.search_text = self.search_entry.get().strip().lower()

        if not self.search_text:
            self.filtered_parameters = self.parameters.copy()
        else:
            # 파라미터 이름, 값, 모듈, 파트에서 검색
            self.filtered_parameters = [
                p for p in self.parameters
                if self.search_text in (p.parameter_name or "").lower()
                or self.search_text in (p.parameter_value or "").lower()
                or self.search_text in (p.module or "").lower()
                or self.search_text in (p.part or "").lower()
            ]

        self._update_tree()

    def _clear_search(self):
        """검색 초기화"""
        self.search_entry.delete(0, tk.END)
        self.search_text = ""
        self.filtered_parameters = self.parameters.copy()
        self._update_tree()

    def _refresh(self):
        """새로고침"""
        self._load_parameters()

    def _export_csv(self):
        """CSV로 내보내기"""
        if not self.filtered_parameters:
            messagebox.showinfo("No Data", "No parameters to export.")
            return

        # 파일 선택
        file_path = filedialog.asksaveasfilename(
            parent=self.dialog,
            title="Export Parameters to CSV",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            initialfile=f"{self.equipment.serial_number}_parameters.csv" if self.equipment else "parameters.csv"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # 헤더
                writer.writerow(["Parameter Name", "Value", "Module", "Part", "Data Type"])

                # 데이터
                for param in self.filtered_parameters:
                    writer.writerow([
                        param.parameter_name,
                        param.parameter_value,
                        param.module or "",
                        param.part or "",
                        param.data_type or ""
                    ])

            messagebox.showinfo("Export Success", f"Exported {len(self.filtered_parameters)} parameters to:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export CSV:\n{e}")
