#!/usr/bin/env python3
"""
QC 스펙 편집 다이얼로그
사용자가 Equipment Type과 QC 항목들을 직접 정의
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from typing import Optional, Dict, List

class QCSpecEditorDialog:
    """QC 스펙 편집 다이얼로그"""
    
    def __init__(self, parent, custom_config):
        """
        초기화
        
        Args:
            parent: 부모 윈도우
            custom_config: CustomQCConfig 인스턴스
        """
        self.parent = parent
        self.custom_config = custom_config
        self.dialog = None
        self.result = False
        
    def show(self):
        """다이얼로그 표시"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("QC 스펙 설정 편집")
        self.dialog.geometry("800x600")
        
        # 다이얼로그를 중앙에 배치
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # UI 생성
        self.create_ui()
        
        # 모달 다이얼로그로 실행
        self.dialog.wait_window()
        return self.result
        
    def create_ui(self):
        """UI 생성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 왼쪽: Equipment Type 관리
        self.create_equipment_panel(main_frame)
        
        # 오른쪽: 스펙 항목 관리
        self.create_spec_panel(main_frame)
        
        # 하단: 버튼
        self.create_button_panel()
        
    def create_equipment_panel(self, parent):
        """Equipment Type 관리 패널"""
        # 프레임
        eq_frame = ttk.LabelFrame(parent, text="Equipment Types", padding="10")
        eq_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5))
        
        # 리스트박스
        listbox_frame = ttk.Frame(eq_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.eq_listbox = tk.Listbox(listbox_frame, 
                                     yscrollcommand=scrollbar.set,
                                     width=25, height=15)
        self.eq_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.eq_listbox.yview)
        
        # 선택 이벤트
        self.eq_listbox.bind('<<ListboxSelect>>', self.on_equipment_selected)
        
        # 버튼
        button_frame = ttk.Frame(eq_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(button_frame, text="추가", 
                  command=self.add_equipment_type,
                  width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="삭제", 
                  command=self.remove_equipment_type,
                  width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="이름변경",
                  command=self.rename_equipment_type,
                  width=8).pack(side=tk.LEFT, padx=2)
        
        # Equipment Type 목록 로드
        self.load_equipment_types()
        
    def create_spec_panel(self, parent):
        """스펙 항목 관리 패널"""
        # 프레임
        spec_frame = ttk.LabelFrame(parent, text="QC Spec Items", padding="10")
        spec_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 트리뷰
        tree_frame = ttk.Frame(spec_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('item_name', 'min_spec', 'max_spec', 'unit', 'enabled')
        self.spec_tree = ttk.Treeview(tree_frame, columns=columns,
                                      show='headings', height=15)
        
        # 컬럼 설정
        headers = {
            'item_name': 'Item Name',
            'min_spec': 'Min Spec',
            'max_spec': 'Max Spec', 
            'unit': 'Unit',
            'enabled': 'Enabled'
        }
        
        widths = {
            'item_name': 150,
            'min_spec': 80,
            'max_spec': 80,
            'unit': 60,
            'enabled': 60
        }
        
        for col in columns:
            self.spec_tree.heading(col, text=headers[col])
            self.spec_tree.column(col, width=widths[col])
            
        # 스크롤바
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical",
                                   command=self.spec_tree.yview)
        self.spec_tree.configure(yscrollcommand=v_scrollbar.set)
        
        # 배치
        self.spec_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 더블클릭 편집
        self.spec_tree.bind('<Double-1>', self.edit_spec_item)
        
        # 버튼
        button_frame = ttk.Frame(spec_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(button_frame, text="항목 추가",
                  command=self.add_spec_item,
                  width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="항목 편집",
                  command=self.edit_spec_item,
                  width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="항목 삭제",
                  command=self.remove_spec_item,
                  width=10).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(button_frame, orient='vertical').pack(side=tk.LEFT, 
                                                           fill=tk.Y, padx=10)
        
        ttk.Button(button_frame, text="가져오기",
                  command=self.import_specs,
                  width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="내보내기",
                  command=self.export_specs,
                  width=10).pack(side=tk.LEFT, padx=2)
        
    def create_button_panel(self):
        """하단 버튼 패널"""
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        ttk.Button(button_frame, text="저장",
                  command=self.save_and_close,
                  width=10).pack(side=tk.RIGHT, padx=2)
        ttk.Button(button_frame, text="취소",
                  command=self.dialog.destroy,
                  width=10).pack(side=tk.RIGHT, padx=2)
        
    def load_equipment_types(self):
        """Equipment Type 목록 로드"""
        self.eq_listbox.delete(0, tk.END)
        for eq_type in self.custom_config.get_equipment_types():
            self.eq_listbox.insert(tk.END, eq_type)
            
        if self.eq_listbox.size() > 0:
            self.eq_listbox.selection_set(0)
            self.on_equipment_selected()
            
    def on_equipment_selected(self, event=None):
        """Equipment Type 선택 시"""
        selection = self.eq_listbox.curselection()
        if not selection:
            return
            
        eq_type = self.eq_listbox.get(selection[0])
        self.current_equipment = eq_type
        self.load_spec_items(eq_type)
        
    def load_spec_items(self, equipment_type):
        """스펙 항목 로드"""
        # 트리뷰 초기화
        for item in self.spec_tree.get_children():
            self.spec_tree.delete(item)
            
        # 스펙 로드
        specs = self.custom_config.get_specs(equipment_type)
        for spec in specs:
            values = (
                spec.get('item_name', ''),
                spec.get('min_spec', ''),
                spec.get('max_spec', ''),
                spec.get('unit', ''),
                '✓' if spec.get('enabled', True) else ''
            )
            self.spec_tree.insert('', 'end', values=values)
            
    def add_equipment_type(self):
        """Equipment Type 추가"""
        name = tk.simpledialog.askstring("추가", 
                                        "새 Equipment Type 이름:")
        if name and name.strip():
            if self.custom_config.add_equipment_type(name.strip()):
                self.load_equipment_types()
                # 새로 추가한 항목 선택
                for i in range(self.eq_listbox.size()):
                    if self.eq_listbox.get(i) == name.strip():
                        self.eq_listbox.selection_clear(0, tk.END)
                        self.eq_listbox.selection_set(i)
                        self.on_equipment_selected()
                        break
            else:
                messagebox.showwarning("경고", "이미 존재하는 이름입니다.")
                
    def remove_equipment_type(self):
        """Equipment Type 삭제"""
        selection = self.eq_listbox.curselection()
        if not selection:
            messagebox.showwarning("경고", "삭제할 항목을 선택하세요.")
            return
            
        eq_type = self.eq_listbox.get(selection[0])
        if messagebox.askyesno("확인", f"'{eq_type}'을(를) 삭제하시겠습니까?"):
            if self.custom_config.remove_equipment_type(eq_type):
                self.load_equipment_types()
                
    def rename_equipment_type(self):
        """Equipment Type 이름 변경"""
        selection = self.eq_listbox.curselection()
        if not selection:
            messagebox.showwarning("경고", "변경할 항목을 선택하세요.")
            return
            
        old_name = self.eq_listbox.get(selection[0])
        new_name = tk.simpledialog.askstring("이름 변경", 
                                            "새 이름:",
                                            initialvalue=old_name)
        if new_name and new_name != old_name:
            # 이름 변경 로직
            equipment_types = self.custom_config.get_equipment_types()
            idx = equipment_types.index(old_name)
            equipment_types[idx] = new_name
            
            # 스펙 데이터 이동
            specs = self.custom_config.get_specs(old_name)
            self.custom_config.config['equipment_types'] = equipment_types
            self.custom_config.config['specs'][new_name] = specs
            del self.custom_config.config['specs'][old_name]
            
            self.custom_config.save_config()
            self.load_equipment_types()
            
    def add_spec_item(self):
        """스펙 항목 추가"""
        if not hasattr(self, 'current_equipment'):
            messagebox.showwarning("경고", "먼저 Equipment Type을 선택하세요.")
            return
            
        # 입력 다이얼로그
        dialog = SpecItemDialog(self.dialog)
        result = dialog.show()
        
        if result:
            self.custom_config.add_spec_item(self.current_equipment, result)
            self.load_spec_items(self.current_equipment)
            
    def edit_spec_item(self, event=None):
        """스펙 항목 편집"""
        selection = self.spec_tree.selection()
        if not selection:
            if event:  # 더블클릭인 경우
                return
            messagebox.showwarning("경고", "편집할 항목을 선택하세요.")
            return
            
        item = self.spec_tree.item(selection[0])
        values = item['values']
        
        # 현재 값으로 다이얼로그 초기화
        current_spec = {
            'item_name': values[0],
            'min_spec': values[1],
            'max_spec': values[2],
            'unit': values[3],
            'enabled': values[4] == '✓'
        }
        
        dialog = SpecItemDialog(self.dialog, current_spec)
        result = dialog.show()
        
        if result:
            # 기존 항목 업데이트
            specs = self.custom_config.get_specs(self.current_equipment)
            for i, spec in enumerate(specs):
                if spec['item_name'] == current_spec['item_name']:
                    specs[i] = result
                    break
            self.custom_config.update_specs(self.current_equipment, specs)
            self.load_spec_items(self.current_equipment)
            
    def remove_spec_item(self):
        """스펙 항목 삭제"""
        selection = self.spec_tree.selection()
        if not selection:
            messagebox.showwarning("경고", "삭제할 항목을 선택하세요.")
            return
            
        item = self.spec_tree.item(selection[0])
        item_name = item['values'][0]
        
        if messagebox.askyesno("확인", f"'{item_name}'을(를) 삭제하시겠습니까?"):
            self.custom_config.remove_spec_item(self.current_equipment, item_name)
            self.load_spec_items(self.current_equipment)
            
    def import_specs(self):
        """스펙 가져오기"""
        filename = filedialog.askopenfilename(
            title="스펙 파일 선택",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            if self.custom_config.import_from_file(filename):
                self.load_equipment_types()
                messagebox.showinfo("완료", "스펙을 가져왔습니다.")
            else:
                messagebox.showerror("오류", "파일을 가져올 수 없습니다.")
                
    def export_specs(self):
        """스펙 내보내기"""
        filename = filedialog.asksaveasfilename(
            title="스펙 저장",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            if self.custom_config.export_to_file(filename):
                messagebox.showinfo("완료", f"스펙을 저장했습니다:\n{filename}")
            else:
                messagebox.showerror("오류", "파일을 저장할 수 없습니다.")
                
    def save_and_close(self):
        """저장하고 닫기"""
        self.custom_config.save_config()
        self.result = True
        self.dialog.destroy()


class SpecItemDialog:
    """스펙 항목 입력 다이얼로그"""
    
    def __init__(self, parent, initial_values=None):
        """
        초기화
        
        Args:
            parent: 부모 윈도우
            initial_values: 초기값 딕셔너리
        """
        self.parent = parent
        self.initial_values = initial_values or {}
        self.result = None
        
    def show(self):
        """다이얼로그 표시"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("스펙 항목 편집")
        self.dialog.geometry("400x250")
        
        # 중앙 배치
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # UI 생성
        self.create_ui()
        
        # 모달 다이얼로그
        self.dialog.wait_window()
        return self.result
        
    def create_ui(self):
        """UI 생성"""
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 입력 필드
        fields = [
            ("Item Name:", 'item_name', str),
            ("Min Spec:", 'min_spec', float),
            ("Max Spec:", 'max_spec', float),
            ("Unit:", 'unit', str)
        ]
        
        self.entries = {}
        for i, (label, key, dtype) in enumerate(fields):
            ttk.Label(frame, text=label).grid(row=i, column=0, 
                                             sticky=tk.W, pady=5)
            
            entry = ttk.Entry(frame, width=30)
            entry.grid(row=i, column=1, pady=5)
            
            # 초기값 설정
            if key in self.initial_values:
                entry.insert(0, str(self.initial_values[key]))
                
            self.entries[key] = (entry, dtype)
            
        # Enabled 체크박스
        self.enabled_var = tk.BooleanVar(
            value=self.initial_values.get('enabled', True)
        )
        ttk.Checkbutton(frame, text="Enabled", 
                       variable=self.enabled_var).grid(row=len(fields), 
                                                       column=1, 
                                                       sticky=tk.W, 
                                                       pady=10)
        
        # 버튼
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=len(fields)+1, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="확인",
                  command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="취소",
                  command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        
    def ok_clicked(self):
        """확인 버튼 클릭"""
        try:
            result = {}
            for key, (entry, dtype) in self.entries.items():
                value = entry.get().strip()
                if key == 'item_name' and not value:
                    messagebox.showwarning("경고", "Item Name은 필수입니다.")
                    return
                    
                if value:
                    if dtype == float:
                        result[key] = float(value)
                    else:
                        result[key] = value
                else:
                    result[key] = None
                    
            result['enabled'] = self.enabled_var.get()
            
            self.result = result
            self.dialog.destroy()
            
        except ValueError as e:
            messagebox.showerror("오류", f"잘못된 입력값: {e}")


# 간단한 import 지원
import tkinter.simpledialog as simpledialog
tk.simpledialog = simpledialog