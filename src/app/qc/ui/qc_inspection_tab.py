"""
QC Inspection Tab - 통합 QC 검수 탭

기존 qc_simplified.py + qc_simplified_custom.py 기능 통합
Services Layer를 사용하는 통합 UI
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QMessageBox, QSplitter, QComboBox, QGroupBox
)
from PyQt6.QtCore import Qt
from typing import Optional, Dict, Any

from ..services import QCService, ReportService
from .widgets.result_table import ResultTableWidget
from .widgets.summary_panel import SummaryPanelWidget


class QCInspectionTab(QWidget):
    """
    통합 QC 검수 탭

    Phase 2 리팩토링:
    - Services Layer 사용
    - 재사용 가능한 위젯 구성
    - 명확한 책임 분리
    """

    def __init__(self, parent=None, db_schema=None):
        """
        초기화

        Args:
            parent: 부모 위젯
            db_schema: 데이터베이스 스키마
        """
        super().__init__(parent)
        self.db_schema = db_schema

        # Services
        self.qc_service = QCService(db_schema)
        self.report_service = ReportService()

        # 검수 결과 저장
        self.inspection_result = None
        self.file_data = None

        self.setup_ui()

    def setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)

        # 상단: 파일 선택 및 실행
        top_layout = self.create_top_panel()
        layout.addLayout(top_layout)

        # 중앙: 결과 테이블 + 요약 패널
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 결과 테이블
        self.result_table = ResultTableWidget()
        splitter.addWidget(self.result_table)

        # 요약 패널
        self.summary_panel = SummaryPanelWidget()
        splitter.addWidget(self.summary_panel)

        # 비율 설정 (테이블 70%, 요약 30%)
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)

        layout.addWidget(splitter)

        # 하단: 내보내기 버튼
        bottom_layout = self.create_bottom_panel()
        layout.addLayout(bottom_layout)

    def create_top_panel(self) -> QHBoxLayout:
        """상단 패널 생성"""
        layout = QHBoxLayout()

        # Configuration 선택
        config_group = QGroupBox('Configuration')
        config_layout = QHBoxLayout()
        self.config_combo = QComboBox()
        self.config_combo.addItem('Type Common (예외 없음)', None)
        # TODO: DB에서 Configuration 목록 로드
        config_layout.addWidget(self.config_combo)
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # 파일 선택 버튼
        self.file_button = QPushButton('파일 선택')
        self.file_button.clicked.connect(self.select_file)
        layout.addWidget(self.file_button)

        # 선택된 파일 레이블
        self.file_label = QLabel('파일이 선택되지 않음')
        layout.addWidget(self.file_label)

        layout.addStretch()

        # 검수 실행 버튼
        self.run_button = QPushButton('검수 실행')
        self.run_button.clicked.connect(self.run_inspection)
        self.run_button.setEnabled(False)
        self.run_button.setStyleSheet('background-color: #4CAF50; color: white; font-weight: bold; padding: 5px;')
        layout.addWidget(self.run_button)

        return layout

    def create_bottom_panel(self) -> QHBoxLayout:
        """하단 패널 생성"""
        layout = QHBoxLayout()

        layout.addStretch()

        # Excel 내보내기 버튼
        self.export_excel_button = QPushButton('Excel로 내보내기')
        self.export_excel_button.clicked.connect(self.export_to_excel)
        self.export_excel_button.setEnabled(False)
        layout.addWidget(self.export_excel_button)

        # CSV 내보내기 버튼
        self.export_csv_button = QPushButton('CSV로 내보내기')
        self.export_csv_button.clicked.connect(self.export_to_csv)
        self.export_csv_button.setEnabled(False)
        layout.addWidget(self.export_csv_button)

        return layout

    def select_file(self):
        """파일 선택"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            '검수할 파일 선택',
            '',
            'All Files (*.*);;CSV Files (*.csv);;Excel Files (*.xlsx *.xls);;Text Files (*.txt)'
        )

        if file_path:
            # 파일 파싱 (간단한 구현, 추후 확장 필요)
            try:
                self.file_data = self.parse_file(file_path)
                self.file_label.setText(f'선택됨: {file_path}')
                self.run_button.setEnabled(True)
            except Exception as e:
                QMessageBox.critical(self, '오류', f'파일 파싱 실패: {e}')

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        파일 파싱 (간단한 구현)

        TODO: qc/utils/file_handler.py로 이동 필요

        Args:
            file_path: 파일 경로

        Returns:
            Dict: {ItemName: Value} 형태의 파일 데이터
        """
        # 간단한 CSV 파싱 예제
        import pandas as pd

        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        else:
            raise ValueError('지원하지 않는 파일 형식')

        # ItemName, Value 컬럼 찾기
        file_data = {}
        if 'ItemName' in df.columns and 'Value' in df.columns:
            for _, row in df.iterrows():
                file_data[row['ItemName']] = row['Value']
        elif 'Parameter' in df.columns and 'Value' in df.columns:
            for _, row in df.iterrows():
                file_data[row['Parameter']] = row['Value']
        else:
            raise ValueError('ItemName 또는 Value 컬럼을 찾을 수 없음')

        return file_data

    def run_inspection(self):
        """검수 실행"""
        if not self.file_data:
            QMessageBox.warning(self, '경고', '파일을 먼저 선택하세요.')
            return

        try:
            # Configuration ID 가져오기
            configuration_id = self.config_combo.currentData()

            # 검수 실행
            self.inspection_result = self.qc_service.run_inspection(
                self.file_data,
                configuration_id
            )

            # 결과 표시
            self.result_table.load_results(self.inspection_result.get('results', []))
            self.summary_panel.update_summary(self.inspection_result)

            # 내보내기 버튼 활성화
            self.export_excel_button.setEnabled(True)
            self.export_csv_button.setEnabled(True)

            # 결과 메시지
            if self.inspection_result.get('is_pass'):
                QMessageBox.information(self, '검수 완료', '✅ 검수를 통과했습니다!')
            else:
                failed_count = self.inspection_result.get('failed_count', 0)
                QMessageBox.warning(
                    self, '검수 실패',
                    f'❌ 검수에 실패했습니다.\n실패 항목: {failed_count}개'
                )

        except Exception as e:
            QMessageBox.critical(self, '오류', f'검수 중 오류 발생: {e}')
            import traceback
            traceback.print_exc()

    def export_to_excel(self):
        """Excel로 내보내기"""
        if not self.inspection_result:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Excel 파일 저장', '', 'Excel Files (*.xlsx)'
        )

        if file_path:
            success = self.report_service.export_to_excel(
                self.inspection_result,
                file_path,
                equipment_name='',
                equipment_type='',
                configuration_name=self.config_combo.currentText()
            )

            if success:
                QMessageBox.information(self, '완료', 'Excel 파일이 저장되었습니다.')
            else:
                QMessageBox.critical(self, '오류', 'Excel 파일 저장에 실패했습니다.')

    def export_to_csv(self):
        """CSV로 내보내기"""
        if not self.inspection_result:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, 'CSV 파일 저장', '', 'CSV Files (*.csv)'
        )

        if file_path:
            success = self.report_service.export_to_csv(
                self.inspection_result,
                file_path
            )

            if success:
                QMessageBox.information(self, '완료', 'CSV 파일이 저장되었습니다.')
            else:
                QMessageBox.critical(self, '오류', 'CSV 파일 저장에 실패했습니다.')
