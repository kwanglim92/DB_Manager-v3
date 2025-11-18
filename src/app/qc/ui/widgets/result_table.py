"""
Result Table Widget - QC 검수 결과 테이블 위젯

재사용 가능한 결과 테이블 컴포넌트
"""

from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from typing import List, Dict, Any


class ResultTableWidget(QTableWidget):
    """QC 검수 결과 테이블 위젯"""

    def __init__(self, parent=None):
        """초기화"""
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """UI 설정"""
        # 기본 컬럼 설정
        self.setColumnCount(9)
        self.setHorizontalHeaderLabels([
            'Result', 'Display Name', 'Item Name', 'Module', 'Part',
            'Value', 'Spec', 'Category', 'Description'
        ])

        # 헤더 설정
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)

        # 테이블 설정
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSortingEnabled(True)

    def load_results(self, results: List[Dict[str, Any]]):
        """
        검수 결과 로드

        Args:
            results: QCService.run_inspection() 결과의 'results' 리스트
        """
        self.setRowCount(0)
        self.setSortingEnabled(False)

        for result in results:
            row = self.rowCount()
            self.insertRow(row)

            # Result (Pass/Fail)
            is_valid = result.get('is_valid', False)
            result_text = '✅ Pass' if is_valid else '❌ Fail'
            result_item = QTableWidgetItem(result_text)
            if not is_valid:
                result_item.setBackground(QColor(255, 200, 200))
            else:
                result_item.setBackground(QColor(200, 255, 200))
            result_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setItem(row, 0, result_item)

            # Display Name
            self.setItem(row, 1, QTableWidgetItem(result.get('display_name', '')))

            # Item Name
            self.setItem(row, 2, QTableWidgetItem(result.get('item_name', '')))

            # Module
            self.setItem(row, 3, QTableWidgetItem(result.get('module', '')))

            # Part
            self.setItem(row, 4, QTableWidgetItem(result.get('part', '')))

            # Value
            self.setItem(row, 5, QTableWidgetItem(str(result.get('file_value', ''))))

            # Spec
            self.setItem(row, 6, QTableWidgetItem(result.get('spec', '')))

            # Category
            self.setItem(row, 7, QTableWidgetItem(result.get('category', '')))

            # Description
            self.setItem(row, 8, QTableWidgetItem(result.get('description', '')))

        self.setSortingEnabled(True)
        self.resizeColumnsToContents()

    def get_failed_results(self) -> List[Dict]:
        """
        실패한 결과만 추출

        Returns:
            List[Dict]: 실패한 결과 목록
        """
        failed_results = []
        for row in range(self.rowCount()):
            result_item = self.item(row, 0)
            if result_item and '❌' in result_item.text():
                failed_results.append({
                    'display_name': self.item(row, 1).text() if self.item(row, 1) else '',
                    'value': self.item(row, 5).text() if self.item(row, 5) else '',
                    'spec': self.item(row, 6).text() if self.item(row, 6) else '',
                    'category': self.item(row, 7).text() if self.item(row, 7) else ''
                })
        return failed_results

    def clear_results(self):
        """결과 테이블 초기화"""
        self.setRowCount(0)
