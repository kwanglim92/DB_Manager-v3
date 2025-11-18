"""
Equipment Hierarchy 관리 다이얼로그 (Phase 1.5)

Model → Type → Configuration 3단계 계층 구조를 관리합니다.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json

from .configuration_dialog import ConfigurationDialog


class EquipmentHierarchyDialog:
    """Equipment Hierarchy 관리 다이얼로그"""

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
        self.category_service = service_factory.get_category_service()
        self.configuration_service = service_factory.get_configuration_service()

        # 다이얼로그 생성
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Equipment Hierarchy 관리")
        self.dialog.geometry("1200x800")
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
            text="Equipment Hierarchy 관리 (관리자 전용)",
            font=("Helvetica", 14, "bold")
        )
        title_label.pack(pady=(0, 10))

        # 정보 레이블
        info_label = ttk.Label(
            main_frame,
            text="📁 Model → 🔧 Type → ⚙️ Configuration 계층 구조",
            font=("Helvetica", 10)
        )
        info_label.pack(pady=(0, 5))

        # 툴바 프레임
        toolbar_frame = ttk.Frame(main_frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(
            toolbar_frame,
            text="🔄 새로고침",
            command=self._refresh,
            width=15
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            toolbar_frame,
            text="➕ Add Model (모델명)",
            command=self._add_model,
            width=20
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            toolbar_frame,
            text="🔧 Add Type (AE 형태)",
            command=self._add_type,
            width=20
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            toolbar_frame,
            text="⚙️ Add Config (구성)",
            command=self._add_configuration,
            width=20
        ).pack(side=tk.LEFT, padx=2)

        # Tree View 프레임
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # 스크롤바
        scrollbar_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Tree View
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("type", "details", "count"),
            show="tree headings",
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set,
            selectmode="browse"
        )
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)

        # 컬럼 설정
        self.tree.heading("#0", text="Name")
        self.tree.heading("type", text="Type")
        self.tree.heading("details", text="Details")
        self.tree.heading("count", text="Count")

        self.tree.column("#0", width=300, minwidth=200)
        self.tree.column("type", width=100, minwidth=80)
        self.tree.column("details", width=400, minwidth=300)
        self.tree.column("count", width=100, minwidth=80)

        # 우클릭 메뉴
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="✏️ Edit", command=self._edit_selected)
        self.context_menu.add_command(label="❌ Delete", command=self._delete_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="➕ Add Child", command=self._add_child)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="ℹ️ View Details", command=self._view_details)

        # 이벤트 바인딩
        self.tree.bind("<Button-3>", self._show_context_menu)  # 우클릭
        self.tree.bind("<Double-1>", self._on_double_click)  # 더블클릭

        # 태그 색상 설정
        self.tree.tag_configure("model", foreground="#0066CC", font=("Helvetica", 10, "bold"))
        self.tree.tag_configure("type", foreground="#006600", font=("Helvetica", 10))
        self.tree.tag_configure("configuration", foreground="#CC6600", font=("Helvetica", 9))
        self.tree.tag_configure("customer_specific", foreground="#CC0066", font=("Helvetica", 9, "italic"))

        # 버튼 프레임
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=(10, 0))

        ttk.Button(
            btn_frame,
            text="닫기",
            command=self.dialog.destroy,
            width=15
        ).pack()

    def _load_data(self):
        """데이터 로드 및 Tree 구성"""
        try:
            # Tree 초기화
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Full Hierarchy 조회
            hierarchy = self.configuration_service.get_full_hierarchy()

            # Model → Type → Configuration 계층 구조 구축
            for model_data in hierarchy:
                model = model_data['model']
                types = model_data['types']

                # Model 노드 추가
                model_id = f"model_{model.id}"
                type_count = len(types)
                self.tree.insert(
                    "",
                    "end",
                    model_id,
                    text=f"📁 {model.model_name}",
                    values=("Model", model.description or "", f"{type_count} types"),
                    tags=("model",),
                    open=True
                )

                # Type 노드 추가
                for type_data in types:
                    eq_type = type_data['type']
                    configurations = type_data['configurations']

                    type_id = f"type_{eq_type.id}"
                    config_count = len(configurations)
                    self.tree.insert(
                        model_id,
                        "end",
                        type_id,
                        text=f"  🔧 {eq_type.type_name}",
                        values=("Type", eq_type.description or "", f"{config_count} configs"),
                        tags=("type",),
                        open=True
                    )

                    # Configuration 노드 추가
                    for config_data in configurations:
                        config = config_data['configuration']
                        default_value_count = config_data['default_value_count']

                        config_id = f"config_{config.id}"
                        details = f"Port: {config.port_count}, Wafer: {config.wafer_count}"
                        if config.is_customer_specific:
                            details += f" | Customer: {config.customer_name}"
                            tag = "customer_specific"
                            icon = "⚙️🌟"
                        else:
                            tag = "configuration"
                            icon = "    ⚙️"

                        self.tree.insert(
                            type_id,
                            "end",
                            config_id,
                            text=f"{icon} {config.configuration_name}",
                            values=("Configuration", details, f"{default_value_count} params"),
                            tags=(tag,)
                        )

        except Exception as e:
            messagebox.showerror("오류", f"데이터 로드 실패:\n{str(e)}")

    def _refresh(self):
        """데이터 새로고침"""
        self._load_data()
        messagebox.showinfo("완료", "데이터를 새로고침했습니다.")

    def _show_context_menu(self, event):
        """우클릭 메뉴 표시"""
        # 클릭한 위치의 아이템 선택
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def _on_double_click(self, event):
        """더블클릭 이벤트"""
        self._view_details()

    def _get_selected_item_info(self):
        """선택된 아이템 정보 반환"""
        selection = self.tree.selection()
        if not selection:
            return None, None, None

        item_id = selection[0]

        if item_id.startswith("model_"):
            return "model", int(item_id.split("_")[1]), item_id
        elif item_id.startswith("type_"):
            return "type", int(item_id.split("_")[1]), item_id
        elif item_id.startswith("config_"):
            return "configuration", int(item_id.split("_")[1]), item_id

        return None, None, None

    # ==================== Add Operations ====================

    def _add_model(self):
        """Model 추가"""
        # Simple dialog
        model_name = simpledialog.askstring(
            "Add Equipment Model",
            "Model Name:",
            parent=self.dialog
        )

        if not model_name:
            return

        description = simpledialog.askstring(
            "Add Equipment Model",
            "Description (선택):",
            parent=self.dialog
        )

        try:
            model_id = self.category_service.create_model(
                model_name=model_name,
                description=description
            )
            messagebox.showinfo("성공", f"Model '{model_name}' 추가 완료 (ID: {model_id})")
            self._refresh()

            # Type 추가 안내
            response = messagebox.askyesno(
                "Type 추가",
                f"Model '{model_name}'이(가) 추가되었습니다.\n\n"
                f"바로 Type (AE 형태)을 추가하시겠습니까?\n"
                f"(예: 분리형, 일체형)"
            )

            if response:
                self._add_type_for_model(model_id)

        except Exception as e:
            messagebox.showerror("오류", f"Model 추가 실패:\n{str(e)}")

    def _add_type(self):
        """Type 추가"""
        item_type, item_id, _ = self._get_selected_item_info()

        # Model 선택 확인
        model_id = None
        if item_type == "model":
            model_id = item_id
        elif item_type == "type":
            # Type의 부모 Model 찾기
            parent = self.tree.parent(self.tree.selection()[0])
            if parent and parent.startswith("model_"):
                model_id = int(parent.split("_")[1])

        if not model_id:
            # Model 목록에서 선택
            models = self.category_service.get_all_models()
            if not models:
                messagebox.showwarning("경고", "먼저 Model을 추가해주세요.")
                return

            # Model 선택 다이얼로그
            model_dialog = tk.Toplevel(self.dialog)
            model_dialog.title("Model 선택")
            model_dialog.geometry("400x150")
            model_dialog.transient(self.dialog)
            model_dialog.grab_set()

            tk.Label(model_dialog, text="장비 모델 선택:", font=("Segoe UI", 10)).pack(pady=10)

            model_var = tk.StringVar()
            model_map = {m.model_name: m.id for m in models}
            model_combo = ttk.Combobox(model_dialog,
                                      textvariable=model_var,
                                      values=list(model_map.keys()),
                                      state="readonly", width=35)
            model_combo.pack(pady=5)
            if model_combo['values']:
                model_combo.current(0)

            selected_model_id = [None]  # 클로저용 리스트

            def on_confirm():
                selected_name = model_var.get()
                if selected_name:
                    selected_model_id[0] = model_map[selected_name]
                    model_dialog.destroy()
                else:
                    messagebox.showwarning("경고", "모델을 선택해주세요.")

            def on_cancel():
                model_dialog.destroy()

            button_frame = ttk.Frame(model_dialog)
            button_frame.pack(pady=15)
            ttk.Button(button_frame, text="확인", command=on_confirm, width=10).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="취소", command=on_cancel, width=10).pack(side=tk.LEFT, padx=5)

            model_dialog.wait_window()

            if not selected_model_id[0]:
                return  # 사용자가 취소함

            model_id = selected_model_id[0]

        type_name = simpledialog.askstring(
            "Add Equipment Type",
            "Type Name (예: 분리형, 일체형):",
            parent=self.dialog
        )

        if not type_name:
            return

        description = simpledialog.askstring(
            "Add Equipment Type",
            "Description (선택):",
            parent=self.dialog
        )

        try:
            type_id = self.category_service.create_type(
                model_id=model_id,
                type_name=type_name,
                description=description
            )
            messagebox.showinfo("성공", f"Type '{type_name}' 추가 완료 (ID: {type_id})")
            self._refresh()
        except Exception as e:
            messagebox.showerror("오류", f"Type 추가 실패:\n{str(e)}")

    def _add_configuration(self):
        """Configuration 추가 - 상세 다이얼로그 필요 (Week 2 Day 3)"""
        item_type, item_id, _ = self._get_selected_item_info()

        # Type 선택 확인
        type_id = None
        if item_type == "type":
            type_id = item_id
        elif item_type == "configuration":
            # Configuration의 부모 Type 찾기
            parent = self.tree.parent(self.tree.selection()[0])
            if parent and parent.startswith("type_"):
                type_id = int(parent.split("_")[1])

        if not type_id:
            messagebox.showwarning("경고", "Type을 선택하거나 Configuration을 선택해주세요.")
            return

        # ConfigurationDialog 열기 (Week 2 Day 3)
        dialog = ConfigurationDialog(
            parent=self.dialog,
            configuration_service=self.configuration_service,
            type_id=type_id,
            config=None  # 추가 모드
        )

        # 다이얼로그가 닫힐 때까지 대기
        self.dialog.wait_window(dialog.dialog)

        # 결과 확인 및 새로고침
        if dialog.get_result():
            self._refresh()

    def _add_child(self):
        """선택된 항목에 맞는 자식 추가"""
        item_type, _, _ = self._get_selected_item_info()

        if item_type == "model":
            self._add_type()
        elif item_type == "type":
            self._add_configuration()
        else:
            messagebox.showwarning("경고", "Model 또는 Type을 선택해주세요.")

    # ==================== Edit/Delete Operations ====================

    def _edit_selected(self):
        """선택된 항목 수정"""
        item_type, item_id, _ = self._get_selected_item_info()

        if not item_type:
            messagebox.showwarning("경고", "항목을 선택해주세요.")
            return

        if item_type == "model":
            self._edit_model(item_id)
        elif item_type == "type":
            self._edit_type(item_id)
        elif item_type == "configuration":
            self._edit_configuration(item_id)

    def _edit_model(self, model_id):
        """Model 수정"""
        # TODO: 상세 Edit Dialog 구현
        model = self.category_service.get_model_by_id(model_id)
        if not model:
            messagebox.showerror("오류", "Model을 찾을 수 없습니다.")
            return

        new_name = simpledialog.askstring(
            "Edit Model",
            "Model Name:",
            parent=self.dialog,
            initialvalue=model.model_name
        )

        if not new_name or new_name == model.model_name:
            return

        try:
            self.category_service.update_equipment_model(
                model_id=model_id,
                model_name=new_name
            )
            messagebox.showinfo("성공", "Model 수정 완료")
            self._refresh()
        except Exception as e:
            messagebox.showerror("오류", f"Model 수정 실패:\n{str(e)}")

    def _edit_type(self, type_id):
        """Type 수정"""
        # TODO: 상세 Edit Dialog 구현
        eq_type = self.category_service.get_equipment_type_by_id(type_id)
        if not eq_type:
            messagebox.showerror("오류", "Type을 찾을 수 없습니다.")
            return

        new_name = simpledialog.askstring(
            "Edit Type",
            "Type Name:",
            parent=self.dialog,
            initialvalue=eq_type.type_name
        )

        if not new_name or new_name == eq_type.type_name:
            return

        try:
            self.category_service.update_equipment_type(
                type_id=type_id,
                type_name=new_name
            )
            messagebox.showinfo("성공", "Type 수정 완료")
            self._refresh()
        except Exception as e:
            messagebox.showerror("오류", f"Type 수정 실패:\n{str(e)}")

    def _edit_configuration(self, config_id):
        """Configuration 수정"""
        # 기존 Configuration 조회
        try:
            config = self.configuration_service.get_configuration_by_id(config_id)
            if not config:
                messagebox.showerror("오류", "Configuration을 찾을 수 없습니다.")
                return

            # ConfigurationDialog 열기 (Week 2 Day 3)
            dialog = ConfigurationDialog(
                parent=self.dialog,
                configuration_service=self.configuration_service,
                type_id=config.equipment_type_id,
                config=config  # 수정 모드
            )

            # 다이얼로그가 닫힐 때까지 대기
            self.dialog.wait_window(dialog.dialog)

            # 결과 확인 및 새로고침
            if dialog.get_result():
                self._refresh()

        except Exception as e:
            messagebox.showerror("오류", f"Configuration 수정 실패:\n{str(e)}")

    def _delete_selected(self):
        """선택된 항목 삭제"""
        item_type, item_id, _ = self._get_selected_item_info()

        if not item_type:
            messagebox.showwarning("경고", "항목을 선택해주세요.")
            return

        # 확인 메시지
        item_text = self.tree.item(self.tree.selection()[0])['text']
        confirm = messagebox.askyesno(
            "삭제 확인",
            f"{item_type.upper()}을(를) 삭제하시겠습니까?\n\n{item_text}\n\n⚠️ 하위 항목도 모두 삭제됩니다.",
            icon='warning'
        )

        if not confirm:
            return

        try:
            if item_type == "model":
                self.category_service.delete_equipment_model(item_id)
            elif item_type == "type":
                self.category_service.delete_equipment_type(item_id)
            elif item_type == "configuration":
                self.configuration_service.delete_configuration(item_id)

            messagebox.showinfo("성공", f"{item_type.upper()} 삭제 완료")
            self._refresh()
        except Exception as e:
            messagebox.showerror("오류", f"삭제 실패:\n{str(e)}")

    def _add_type_for_model(self, model_id: int):
        """특정 Model에 Type 추가 (Add Model 후 연속 추가용)"""
        # Type 이름 입력
        type_name = simpledialog.askstring(
            "Add Equipment Type",
            "Type Name (AE 형태, 예: 분리형, 일체형):",
            parent=self.dialog
        )

        if not type_name:
            return

        # 설명 입력
        description = simpledialog.askstring(
            "Add Equipment Type",
            "Description (선택):",
            parent=self.dialog
        )

        try:
            # Type 생성
            type_id = self.category_service.create_type(
                model_id=model_id,
                type_name=type_name.strip(),
                description=description.strip() if description else None
            )

            messagebox.showinfo("성공", f"Type '{type_name}' 추가 완료 (ID: {type_id})")

            # Configuration 추가 안내 (선택)
            response = messagebox.askyesno(
                "Configuration 추가",
                "Configuration도 추가하시겠습니까?\n"
                "(Port 구성, Wafer 크기 등)"
            )

            if response:
                # Configuration 추가 다이얼로그 열기
                from app.dialogs.configuration_dialog import ConfigurationDialog
                ConfigurationDialog(
                    parent=self.dialog,
                    configuration_service=self.configuration_service,
                    type_id=type_id,
                    config=None  # 새 Configuration
                )

            self._refresh()

        except Exception as e:
            messagebox.showerror("오류", f"Type 추가 실패:\n{str(e)}")

    def _view_details(self):
        """선택된 항목 상세 정보 표시"""
        item_type, item_id, _ = self._get_selected_item_info()

        if not item_type:
            return

        try:
            if item_type == "model":
                model = self.category_service.get_model_by_id(item_id)
                details = f"Model ID: {model.id}\n"
                details += f"Model Name: {model.model_name}\n"
                details += f"Model Code: {model.model_code or 'N/A'}\n"
                details += f"Description: {model.description or 'N/A'}\n"
                details += f"Display Order: {model.display_order}\n"
                details += f"Created: {model.created_at}\n"

            elif item_type == "type":
                eq_type = self.category_service.get_equipment_type_by_id(type_id)
                details = f"Type ID: {eq_type.id}\n"
                details += f"Model ID: {eq_type.model_id}\n"
                details += f"Type Name: {eq_type.type_name}\n"
                details += f"Description: {eq_type.description or 'N/A'}\n"
                details += f"Default: {eq_type.is_default}\n"
                details += f"Created: {eq_type.created_at}\n"

            elif item_type == "configuration":
                config = self.configuration_service.get_configuration_by_id(item_id)
                details = f"Configuration ID: {config.id}\n"
                details += f"Type ID: {config.type_id}\n"
                details += f"Configuration Name: {config.configuration_name}\n"
                details += f"Port Count: {config.port_count}\n"
                details += f"Wafer Count: {config.wafer_count}\n"
                details += f"Customer-Specific: {config.is_customer_specific}\n"
                if config.is_customer_specific:
                    details += f"Customer: {config.customer_name}\n"
                details += f"Description: {config.description or 'N/A'}\n"
                details += f"Created: {config.created_at}\n"

                if config.custom_options:
                    details += f"\nCustom Options:\n{json.dumps(config.custom_options, indent=2)}\n"

            messagebox.showinfo("Details", details)
        except Exception as e:
            messagebox.showerror("오류", f"상세 정보 조회 실패:\n{str(e)}")
