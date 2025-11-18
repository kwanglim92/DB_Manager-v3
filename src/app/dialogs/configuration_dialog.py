"""
Configuration Management Dialog (Phase 1.5 Week 2 Day 3)

Equipment Configuration 추가/수정을 위한 상세 다이얼로그
- Port Type 드롭다운
- Wafer Size 드롭다운
- Custom Options JSON 편집기
- Customer-specific 플래그
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json


class ConfigurationDialog:
    """Configuration 추가/수정 다이얼로그"""

    # Port Type 옵션
    PORT_TYPES = [
        "Single Port",
        "Double Port",
        "Multi Port",
        "Custom"
    ]

    # Wafer Size 옵션 (단위: mm)
    WAFER_SIZES = [
        "150mm",
        "200mm",
        "300mm",
        "150/200mm",  # 복합
        "200/300mm",  # 복합
        "Custom"
    ]

    def __init__(self, parent, configuration_service, type_id, config=None):
        """
        Args:
            parent: 부모 윈도우
            configuration_service: ConfigurationService 인스턴스
            type_id: Equipment Type ID
            config: 수정할 Configuration (None이면 추가 모드)
        """
        self.parent = parent
        self.configuration_service = configuration_service
        self.type_id = type_id
        self.config = config
        self.result = None  # 생성/수정된 Configuration ID

        # 다이얼로그 생성
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add Configuration" if config is None else "Edit Configuration")
        self.dialog.geometry("600x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_ui()
        if config:
            self._load_data()

    def _create_ui(self):
        """UI 생성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 제목
        title_text = "Edit Configuration" if self.config else "Add Equipment Configuration"
        title_label = ttk.Label(
            main_frame,
            text=title_text,
            font=("Helvetica", 12, "bold")
        )
        title_label.pack(pady=(0, 15))

        # Configuration Name
        name_frame = ttk.Frame(main_frame)
        name_frame.pack(fill=tk.X, pady=5)

        ttk.Label(name_frame, text="Configuration Name:", width=20).pack(side=tk.LEFT)
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(name_frame, textvariable=self.name_var, width=40)
        name_entry.pack(side=tk.LEFT, padx=5)

        # Port Type
        port_frame = ttk.Frame(main_frame)
        port_frame.pack(fill=tk.X, pady=5)

        ttk.Label(port_frame, text="Port Type:", width=20).pack(side=tk.LEFT)
        self.port_type_var = tk.StringVar()
        port_combo = ttk.Combobox(
            port_frame,
            textvariable=self.port_type_var,
            values=self.PORT_TYPES,
            state="readonly",
            width=15
        )
        port_combo.pack(side=tk.LEFT, padx=5)
        port_combo.current(0)  # 기본: Single Port

        # Port Count (숫자 입력)
        ttk.Label(port_frame, text="Count:").pack(side=tk.LEFT, padx=(10, 5))
        self.port_count_var = tk.IntVar(value=1)
        port_spin = ttk.Spinbox(
            port_frame,
            from_=1,
            to=10,
            textvariable=self.port_count_var,
            width=5
        )
        port_spin.pack(side=tk.LEFT)

        # Wafer Size
        wafer_frame = ttk.Frame(main_frame)
        wafer_frame.pack(fill=tk.X, pady=5)

        ttk.Label(wafer_frame, text="Wafer Size:", width=20).pack(side=tk.LEFT)
        self.wafer_size_var = tk.StringVar()
        wafer_combo = ttk.Combobox(
            wafer_frame,
            textvariable=self.wafer_size_var,
            values=self.WAFER_SIZES,
            state="readonly",
            width=15
        )
        wafer_combo.pack(side=tk.LEFT, padx=5)
        wafer_combo.current(0)  # 기본: 150mm

        # Wafer Count (숫자 입력)
        ttk.Label(wafer_frame, text="Count:").pack(side=tk.LEFT, padx=(10, 5))
        self.wafer_count_var = tk.IntVar(value=1)
        wafer_spin = ttk.Spinbox(
            wafer_frame,
            from_=1,
            to=20,
            textvariable=self.wafer_count_var,
            width=5
        )
        wafer_spin.pack(side=tk.LEFT)

        # Separator
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)

        # Customer-Specific
        customer_frame = ttk.Frame(main_frame)
        customer_frame.pack(fill=tk.X, pady=5)

        self.is_customer_specific_var = tk.BooleanVar(value=False)
        customer_check = ttk.Checkbutton(
            customer_frame,
            text="Customer-Specific Configuration",
            variable=self.is_customer_specific_var,
            command=self._toggle_customer_fields
        )
        customer_check.pack(anchor=tk.W)

        # Customer Name (조건부 활성화)
        self.customer_name_frame = ttk.Frame(main_frame)
        self.customer_name_frame.pack(fill=tk.X, pady=5)

        ttk.Label(self.customer_name_frame, text="Customer Name:", width=20).pack(side=tk.LEFT)
        self.customer_name_var = tk.StringVar()
        self.customer_name_entry = ttk.Entry(
            self.customer_name_frame,
            textvariable=self.customer_name_var,
            width=40,
            state="disabled"
        )
        self.customer_name_entry.pack(side=tk.LEFT, padx=5)

        # Description
        desc_frame = ttk.Frame(main_frame)
        desc_frame.pack(fill=tk.X, pady=5)

        ttk.Label(desc_frame, text="Description:", width=20).pack(side=tk.LEFT, anchor=tk.N)
        self.description_text = tk.Text(desc_frame, height=3, width=40)
        self.description_text.pack(side=tk.LEFT, padx=5)

        # Separator
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)

        # Custom Options (JSON)
        json_label_frame = ttk.Frame(main_frame)
        json_label_frame.pack(fill=tk.X, pady=5)

        ttk.Label(
            json_label_frame,
            text="Custom Options (JSON):",
            font=("Helvetica", 10, "bold")
        ).pack(side=tk.LEFT)

        ttk.Button(
            json_label_frame,
            text="Validate JSON",
            command=self._validate_json,
            width=15
        ).pack(side=tk.RIGHT)

        # JSON 편집기
        json_frame = ttk.Frame(main_frame)
        json_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # 스크롤바
        json_scroll = ttk.Scrollbar(json_frame, orient=tk.VERTICAL)
        json_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.json_text = tk.Text(
            json_frame,
            height=10,
            yscrollcommand=json_scroll.set,
            font=("Courier New", 9)
        )
        self.json_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        json_scroll.config(command=self.json_text.yview)

        # 기본 JSON 템플릿
        default_json = {
            "interferometer_version": "2.0",
            "has_loadport": True,
            "chamber_type": "single"
        }
        self.json_text.insert("1.0", json.dumps(default_json, indent=2))

        # 힌트
        hint_label = ttk.Label(
            main_frame,
            text="💡 Tip: JSON 형식으로 커스텀 옵션을 입력하세요. 예: {\"key\": \"value\"}",
            foreground="gray",
            font=("Helvetica", 8)
        )
        hint_label.pack(pady=(5, 10))

        # 버튼 프레임
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=(10, 0))

        ttk.Button(
            btn_frame,
            text="Cancel",
            command=self.dialog.destroy,
            width=15
        ).pack(side=tk.LEFT, padx=5)

        save_text = "Update" if self.config else "Create"
        ttk.Button(
            btn_frame,
            text=save_text,
            command=self._save,
            width=15
        ).pack(side=tk.LEFT, padx=5)

    def _toggle_customer_fields(self):
        """Customer-specific 필드 활성화/비활성화"""
        if self.is_customer_specific_var.get():
            self.customer_name_entry.config(state="normal")
        else:
            self.customer_name_entry.config(state="disabled")
            self.customer_name_var.set("")

    def _validate_json(self):
        """JSON 유효성 검사"""
        json_str = self.json_text.get("1.0", tk.END).strip()

        if not json_str or json_str == "{}":
            messagebox.showinfo("Validation", "JSON is empty (will be saved as NULL)")
            return

        try:
            json_obj = json.loads(json_str)
            # 정렬된 JSON으로 재포맷
            formatted = json.dumps(json_obj, indent=2, sort_keys=True)
            self.json_text.delete("1.0", tk.END)
            self.json_text.insert("1.0", formatted)
            messagebox.showinfo("Validation", "✅ JSON is valid!")
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON Error", f"Invalid JSON:\n{str(e)}")

    def _load_data(self):
        """기존 Configuration 데이터 로드 (Edit 모드)"""
        if not self.config:
            return

        # Name
        self.name_var.set(self.config.configuration_name)

        # Port/Wafer
        self.port_count_var.set(self.config.port_count)
        self.wafer_count_var.set(self.config.wafer_count)

        # Port Type/Wafer Size는 역추론 (간단한 로직)
        # TODO: 더 정교한 매핑 필요
        if self.config.port_count == 1:
            self.port_type_var.set("Single Port")
        elif self.config.port_count == 2:
            self.port_type_var.set("Double Port")
        else:
            self.port_type_var.set("Multi Port")

        # Wafer Size (간단한 매핑)
        if self.config.wafer_count == 1:
            self.wafer_size_var.set("150mm")  # 기본값
        else:
            self.wafer_size_var.set("Custom")

        # Customer-specific
        if self.config.is_customer_specific:
            self.is_customer_specific_var.set(True)
            self.customer_name_var.set(self.config.customer_name or "")
            self._toggle_customer_fields()

        # Description
        if self.config.description:
            self.description_text.insert("1.0", self.config.description)

        # Custom Options
        if self.config.custom_options:
            self.json_text.delete("1.0", tk.END)
            formatted = json.dumps(self.config.custom_options, indent=2, sort_keys=True)
            self.json_text.insert("1.0", formatted)

    def _save(self):
        """Configuration 저장"""
        # 입력 검증
        config_name = self.name_var.get().strip()
        if not config_name:
            messagebox.showerror("Error", "Configuration Name is required")
            return

        port_count = self.port_count_var.get()
        wafer_count = self.wafer_count_var.get()

        if port_count <= 0 or wafer_count <= 0:
            messagebox.showerror("Error", "Port Count and Wafer Count must be > 0")
            return

        # Customer-specific 검증
        is_customer_specific = self.is_customer_specific_var.get()
        customer_name = self.customer_name_var.get().strip() if is_customer_specific else None

        if is_customer_specific and not customer_name:
            messagebox.showerror("Error", "Customer Name is required for Customer-Specific Configuration")
            return

        # Description
        description = self.description_text.get("1.0", tk.END).strip() or None

        # Custom Options (JSON)
        json_str = self.json_text.get("1.0", tk.END).strip()
        custom_options = None
        if json_str and json_str != "{}":
            try:
                custom_options = json.loads(json_str)
            except json.JSONDecodeError as e:
                messagebox.showerror("JSON Error", f"Invalid JSON:\n{str(e)}\n\nPlease validate JSON first.")
                return

        try:
            if self.config:
                # Update
                success = self.configuration_service.update_configuration(
                    config_id=self.config.id,
                    configuration_name=config_name,
                    port_count=port_count,
                    wafer_count=wafer_count,
                    custom_options=custom_options,
                    is_customer_specific=is_customer_specific,
                    customer_name=customer_name,
                    description=description
                )

                if success:
                    self.result = self.config.id
                    messagebox.showinfo("Success", "Configuration updated successfully")
                    self.dialog.destroy()
                else:
                    messagebox.showerror("Error", "Failed to update Configuration")
            else:
                # Create
                config_id = self.configuration_service.create_configuration(
                    type_id=self.type_id,
                    configuration_name=config_name,
                    port_count=port_count,
                    wafer_count=wafer_count,
                    custom_options=custom_options,
                    is_customer_specific=is_customer_specific,
                    customer_name=customer_name,
                    description=description
                )

                self.result = config_id
                messagebox.showinfo("Success", f"Configuration created successfully (ID: {config_id})")
                self.dialog.destroy()

        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save Configuration:\n{str(e)}")

    def get_result(self):
        """생성/수정된 Configuration ID 반환"""
        return self.result
