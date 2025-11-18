"""
QC 데이터 모델
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ChecklistItem:
    """Check list 항목 데이터 클래스"""
    id: int
    item_name: str
    module: Optional[str]
    part: Optional[str]
    spec_min: Optional[str]
    spec_max: Optional[str]
    expected_value: Optional[str]
    category: Optional[str]
    description: Optional[str]
    is_active: bool

    @property
    def display_name(self) -> str:
        """표시용 이름 (Module.Part.ItemName 형식)"""
        if self.module or self.part:
            parts = []
            if self.module:
                parts.append(self.module)
            if self.part:
                parts.append(self.part)
            return f"{'.'.join(parts)}.{self.item_name}"
        return self.item_name

    @property
    def composite_key(self) -> tuple:
        """복합 키 (Module, Part, ItemName)"""
        return (self.module, self.part, self.item_name)


@dataclass
class InspectionResult:
    """검수 결과 데이터 클래스"""
    item_name: str
    module: Optional[str]
    part: Optional[str]
    display_name: str
    file_value: any
    is_valid: bool
    spec: str
    category: str
    description: str

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            'item_name': self.item_name,
            'module': self.module,
            'part': self.part,
            'display_name': self.display_name,
            'file_value': self.file_value,
            'is_valid': self.is_valid,
            'spec': self.spec,
            'category': self.category,
            'description': self.description
        }
