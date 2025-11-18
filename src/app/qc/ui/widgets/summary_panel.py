"""
Summary Panel Widget - QC 검수 결과 요약 패널

검수 결과의 통계 정보를 표시하는 위젯
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from typing import Dict, Any


class SummaryPanelWidget(QWidget):
    """QC 검수 결과 요약 패널 위젯"""

    def __init__(self, parent=None):
        """초기화"""
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)

        # 전체 상태 표시
        self.status_label = QLabel('검수 대기 중')
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.status_label.setFont(font)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # 통계 그룹박스
        stats_group = QGroupBox('검수 통계')
        stats_layout = QVBoxLayout()

        # 통계 레이블들
        self.total_label = QLabel('전체 항목: -')
        self.passed_label = QLabel('통과: -')
        self.failed_label = QLabel('실패: -')
        self.pass_rate_label = QLabel('통과율: -')
        self.matched_label = QLabel('매칭: -')
        self.exception_label = QLabel('예외: -')

        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.passed_label)
        stats_layout.addWidget(self.failed_label)
        stats_layout.addWidget(self.pass_rate_label)
        stats_layout.addWidget(self.matched_label)
        stats_layout.addWidget(self.exception_label)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        layout.addStretch()

    def update_summary(self, inspection_result: Dict[str, Any]):
        """
        검수 결과 요약 업데이트

        Args:
            inspection_result: QCService.run_inspection() 결과
        """
        is_pass = inspection_result.get('is_pass', False)
        total = inspection_result.get('total_count', 0)
        passed = inspection_result.get('passed_count', 0)
        failed = inspection_result.get('failed_count', 0)
        matched = inspection_result.get('matched_count', 0)
        exception_count = inspection_result.get('exception_count', 0)

        # 상태 표시
        if is_pass:
            self.status_label.setText('✅ 검수 통과 (PASS)')
            self.status_label.setStyleSheet('color: green; background-color: #e8f5e9; padding: 10px;')
        else:
            self.status_label.setText('❌ 검수 실패 (FAIL)')
            self.status_label.setStyleSheet('color: red; background-color: #ffebee; padding: 10px;')

        # 통계 업데이트
        pass_rate = (passed / total * 100) if total > 0 else 0

        self.total_label.setText(f'전체 항목: {total}')
        self.passed_label.setText(f'통과: {passed}')
        self.passed_label.setStyleSheet('color: green;')

        self.failed_label.setText(f'실패: {failed}')
        if failed > 0:
            self.failed_label.setStyleSheet('color: red; font-weight: bold;')
        else:
            self.failed_label.setStyleSheet('color: green;')

        self.pass_rate_label.setText(f'통과율: {pass_rate:.1f}%')
        self.matched_label.setText(f'매칭: {matched}')
        self.exception_label.setText(f'예외: {exception_count}')

    def clear_summary(self):
        """요약 정보 초기화"""
        self.status_label.setText('검수 대기 중')
        self.status_label.setStyleSheet('')
        self.total_label.setText('전체 항목: -')
        self.passed_label.setText('통과: -')
        self.passed_label.setStyleSheet('')
        self.failed_label.setText('실패: -')
        self.failed_label.setStyleSheet('')
        self.pass_rate_label.setText('통과율: -')
        self.matched_label.setText('매칭: -')
        self.exception_label.setText('예외: -')
