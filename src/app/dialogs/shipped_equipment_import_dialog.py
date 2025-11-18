"""
Shipped Equipment Import 다이얼로그 (Phase 2)

파일에서 출고 장비 데이터를 임포트합니다.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from datetime import date, datetime


class ShippedEquipmentImportDialog:
    """Shipped Equipment Import 다이얼로그"""

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

        # 파싱 결과
        self.parse_result = None
        self.selected_file_path = None

        # 다이얼로그 생성
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Import Shipped Equipment")
        self.dialog.geometry("900x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_ui()

    def _create_ui(self):
        """UI 생성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 제목
        title_label = ttk.Label(
            main_frame,
            text="📥 Import Shipped Equipment",
            font=("Helvetica", 14, "bold")
        )
        title_label.pack(pady=(0, 10))

        # Step 1: 파일 선택
        step1_frame = ttk.LabelFrame(main_frame, text="Step 1: Select File", padding="10")
        step1_frame.pack(fill=tk.X, pady=(0, 10))

        file_select_frame = ttk.Frame(step1_frame)
        file_select_frame.pack(fill=tk.X)

        ttk.Label(file_select_frame, text="File:").pack(side=tk.LEFT, padx=(0, 5))

        self.file_path_entry = ttk.Entry(file_select_frame, width=60)
        self.file_path_entry.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            file_select_frame,
            text="Browse...",
            command=self._browse_file,
            width=12
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            file_select_frame,
            text="Parse",
            command=self._parse_file,
            width=10
        ).pack(side=tk.LEFT)

        # Step 2: 파싱 결과 표시
        step2_frame = ttk.LabelFrame(main_frame, text="Step 2: Parsing Result", padding="10")
        step2_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 파싱 결과 정보
        result_info_frame = ttk.Frame(step2_frame)
        result_info_frame.pack(fill=tk.X, pady=(0, 10))

        # 좌측 컬럼
        left_col = ttk.Frame(result_info_frame)
        left_col.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(left_col, text="Serial Number:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.serial_value_label = ttk.Label(left_col, text="-", foreground="blue")
        self.serial_value_label.grid(row=0, column=1, sticky=tk.W, padx=(5, 0), pady=2)

        ttk.Label(left_col, text="Customer:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.customer_value_label = ttk.Label(left_col, text="-", foreground="blue")
        self.customer_value_label.grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=2)

        ttk.Label(left_col, text="Model:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.model_value_label = ttk.Label(left_col, text="-", foreground="blue")
        self.model_value_label.grid(row=2, column=1, sticky=tk.W, padx=(5, 0), pady=2)

        # 우측 컬럼
        right_col = ttk.Frame(result_info_frame)
        right_col.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(20, 0))

        ttk.Label(right_col, text="Total Parameters:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.params_value_label = ttk.Label(right_col, text="-", foreground="blue")
        self.params_value_label.grid(row=0, column=1, sticky=tk.W, padx=(5, 0), pady=2)

        ttk.Label(right_col, text="Auto-Matched Config:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.auto_config_value_label = ttk.Label(right_col, text="-", foreground="green")
        self.auto_config_value_label.grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=2)

        ttk.Label(right_col, text="Parse Status:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.status_value_label = ttk.Label(right_col, text="-", foreground="gray")
        self.status_value_label.grid(row=2, column=1, sticky=tk.W, padx=(5, 0), pady=2)

        # Step 3: Configuration 선택
        step3_frame = ttk.LabelFrame(main_frame, text="Step 3: Select Configuration", padding="10")
        step3_frame.pack(fill=tk.X, pady=(0, 10))

        config_frame = ttk.Frame(step3_frame)
        config_frame.pack(fill=tk.X)

        ttk.Label(config_frame, text="Configuration:").pack(side=tk.LEFT, padx=(0, 5))

        self.config_combo = ttk.Combobox(config_frame, width=40, state="readonly")
        self.config_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.config_combo.bind("<<ComboboxSelected>>", self._on_config_selected)

        ttk.Label(config_frame, text="(Auto-matched if available)").pack(side=tk.LEFT)

        # Step 4: 추가 옵션
        step4_frame = ttk.LabelFrame(main_frame, text="Step 4: Additional Options", padding="10")
        step4_frame.pack(fill=tk.X, pady=(0, 10))

        # Ship Date
        ship_date_frame = ttk.Frame(step4_frame)
        ship_date_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(ship_date_frame, text="Ship Date:").pack(side=tk.LEFT, padx=(0, 5))
        self.ship_date_entry = ttk.Entry(ship_date_frame, width=12)
        self.ship_date_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.ship_date_entry.insert(0, date.today().strftime("%Y-%m-%d"))

        ttk.Label(ship_date_frame, text="(YYYY-MM-DD)").pack(side=tk.LEFT)

        # Refit 플래그
        refit_frame = ttk.Frame(step4_frame)
        refit_frame.pack(fill=tk.X, pady=(0, 5))

        self.is_refit_var = tk.BooleanVar(value=False)
        self.is_refit_check = ttk.Checkbutton(
            refit_frame,
            text="This is a Refit Order",
            variable=self.is_refit_var,
            command=self._toggle_refit_options
        )
        self.is_refit_check.pack(side=tk.LEFT)

        # Refit 옵션 (조건부 표시)
        self.refit_options_frame = ttk.Frame(step4_frame)

        original_serial_frame = ttk.Frame(self.refit_options_frame)
        original_serial_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(original_serial_frame, text="Original Serial Number:").pack(side=tk.LEFT, padx=(20, 5))
        self.original_serial_entry = ttk.Entry(original_serial_frame, width=25)
        self.original_serial_entry.pack(side=tk.LEFT)

        # Notes
        notes_frame = ttk.Frame(step4_frame)
        notes_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        ttk.Label(notes_frame, text="Notes:").pack(anchor=tk.W, pady=(0, 5))
        self.notes_text = tk.Text(notes_frame, height=4, width=70)
        self.notes_text.pack(fill=tk.BOTH, expand=True)

        # 하단 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            button_frame,
            text="Import",
            command=self._import,
            width=15
        ).pack(side=tk.RIGHT, padx=(5, 0))

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.dialog.destroy,
            width=15
        ).pack(side=tk.RIGHT)

        # Configuration 로드
        self._load_configurations()

    def _browse_file(self):
        """파일 선택"""
        file_path = filedialog.askopenfilename(
            parent=self.dialog,
            title="Select Equipment File",
            filetypes=[
                ("Text Files", "*.txt"),
                ("All Files", "*.*")
            ]
        )

        if file_path:
            self.file_path_entry.delete(0, tk.END)
            self.file_path_entry.insert(0, file_path)
            self.selected_file_path = file_path

    def _parse_file(self):
        """파일 파싱"""
        file_path = self.file_path_entry.get().strip()

        if not file_path:
            messagebox.showwarning("No File", "Please select a file first.")
            return

        if not Path(file_path).exists():
            messagebox.showerror("File Not Found", f"File not found: {file_path}")
            return

        try:
            # 파일 파싱
            self.parse_result = self.shipped_service.parse_equipment_file(file_path)

            if not self.parse_result.success:
                messagebox.showerror("Parse Error", f"Failed to parse file:\n{self.parse_result.error_message}")
                self._clear_parse_result()
                return

            # 파싱 결과 표시
            self.serial_value_label.config(text=self.parse_result.serial_number)
            self.customer_value_label.config(text=self.parse_result.customer_name)
            self.model_value_label.config(text=self.parse_result.model_name)
            self.params_value_label.config(text=str(self.parse_result.total_count))
            self.status_value_label.config(text="✓ Success", foreground="green")

            # Configuration 자동 매칭
            matched_config_id = self.shipped_service.match_configuration(self.parse_result.model_name)

            if matched_config_id:
                # Configuration Combo에서 선택
                for idx, (config_id, _) in enumerate(self.config_options):
                    if config_id == matched_config_id:
                        self.config_combo.current(idx)
                        self.auto_config_value_label.config(text="✓ Matched", foreground="green")
                        break
            else:
                self.auto_config_value_label.config(text="✗ No Match", foreground="red")

            messagebox.showinfo("Parse Success", f"File parsed successfully!\n\nTotal Parameters: {self.parse_result.total_count}")

        except Exception as e:
            messagebox.showerror("Parse Error", f"Failed to parse file:\n{e}")
            self._clear_parse_result()

    def _clear_parse_result(self):
        """파싱 결과 초기화"""
        self.parse_result = None
        self.serial_value_label.config(text="-")
        self.customer_value_label.config(text="-")
        self.model_value_label.config(text="-")
        self.params_value_label.config(text="-")
        self.auto_config_value_label.config(text="-", foreground="gray")
        self.status_value_label.config(text="-", foreground="gray")

    def _load_configurations(self):
        """Configuration 목록 로드"""
        configurations = []
        if self.configuration_service:
            all_configs = self.configuration_service.get_all_configurations()
            configurations = [(c.id, f"{c.configuration_name} ({c.type_name or 'Unknown'})") for c in all_configs]

        self.config_options = configurations
        self.config_combo['values'] = [name for _, name in configurations]

        if configurations:
            self.config_combo.current(0)

    def _on_config_selected(self, event):
        """Configuration 선택 이벤트"""
        pass  # 현재는 별도 처리 불필요

    def _toggle_refit_options(self):
        """Refit 옵션 표시/숨김"""
        if self.is_refit_var.get():
            self.refit_options_frame.pack(fill=tk.X, pady=(5, 0))
        else:
            self.refit_options_frame.pack_forget()

    def _import(self):
        """임포트 실행"""
        # 파싱 결과 확인
        if not self.parse_result or not self.parse_result.success:
            messagebox.showwarning("No Parse Result", "Please parse a file first.")
            return

        # Configuration 선택 확인
        selected_idx = self.config_combo.current()
        if selected_idx < 0:
            messagebox.showwarning("No Configuration", "Please select a configuration.")
            return

        configuration_id = self.config_options[selected_idx][0]

        # Ship Date 파싱
        ship_date_str = self.ship_date_entry.get().strip()
        ship_date_obj = None
        if ship_date_str:
            try:
                ship_date_obj = datetime.strptime(ship_date_str, "%Y-%m-%d").date()
            except ValueError:
                messagebox.showwarning("Invalid Date", "Ship Date format should be YYYY-MM-DD")
                return

        # Refit 옵션
        is_refit = self.is_refit_var.get()
        original_serial = None
        if is_refit:
            original_serial = self.original_serial_entry.get().strip()
            if not original_serial:
                messagebox.showwarning("Missing Original Serial", "Please enter the original serial number for refit orders.")
                return

        # Notes
        notes = self.notes_text.get("1.0", tk.END).strip()

        # 확인 다이얼로그
        confirm_message = (
            f"Import Equipment:\n\n"
            f"Serial: {self.parse_result.serial_number}\n"
            f"Customer: {self.parse_result.customer_name}\n"
            f"Model: {self.parse_result.model_name}\n"
            f"Parameters: {self.parse_result.total_count}\n"
            f"Configuration: {self.config_combo.get()}\n"
            f"Ship Date: {ship_date_str}\n"
            f"Refit: {'Yes' if is_refit else 'No'}\n"
            f"\nProceed with import?"
        )

        confirm = messagebox.askyesno("Confirm Import", confirm_message)
        if not confirm:
            return

        try:
            # Import 실행
            file_path = self.file_path_entry.get().strip()

            # ShippedEquipmentService.import_from_file() 사용하지 않고 직접 생성
            # (ship_date, is_refit, original_serial_number, notes를 전달하기 위해)

            # 1. Equipment Type 조회
            config = self.configuration_service.get_configuration_by_id(configuration_id)
            if not config:
                messagebox.showerror("Error", "Configuration not found.")
                return

            # 2. Shipped Equipment 생성
            equipment_id = self.shipped_service.create_shipped_equipment(
                equipment_type_id=config.type_id,
                configuration_id=configuration_id,
                serial_number=self.parse_result.serial_number,
                customer_name=self.parse_result.customer_name,
                ship_date=ship_date_obj,
                is_refit=is_refit,
                original_serial_number=original_serial if is_refit else None,
                notes=notes if notes else None
            )

            # 3. 파라미터 일괄 삽입
            param_count = self.shipped_service.add_parameters_bulk(equipment_id, self.parse_result.parameters)

            messagebox.showinfo(
                "Import Success",
                f"Equipment imported successfully!\n\n"
                f"Equipment ID: {equipment_id}\n"
                f"Serial: {self.parse_result.serial_number}\n"
                f"Parameters: {param_count}"
            )

            # 다이얼로그 닫기
            self.dialog.destroy()

        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import equipment:\n{e}")
            import traceback
            traceback.print_exc()
