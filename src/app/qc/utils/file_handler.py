"""
File Handler - QC 검수 파일 I/O 유틸리티

파일 읽기/쓰기 및 파싱 기능
"""

import pandas as pd
from typing import Dict, Any, Optional, Tuple
import os


class FileHandler:
    """QC 검수 파일 I/O 유틸리티"""

    @staticmethod
    def read_file(
        file_path: str,
        file_format: Optional[str] = None
    ) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        파일 읽기

        Args:
            file_path: 파일 경로
            file_format: 파일 형식 ('csv', 'excel', 'txt', None=자동 감지)

        Returns:
            Tuple[DataFrame, error_message]: 데이터프레임과 오류 메시지
        """
        try:
            # 파일 존재 확인
            if not os.path.exists(file_path):
                return None, f"파일을 찾을 수 없음: {file_path}"

            # 파일 형식 자동 감지
            if not file_format:
                ext = os.path.splitext(file_path)[1].lower()
                if ext == '.csv':
                    file_format = 'csv'
                elif ext in ['.xlsx', '.xls']:
                    file_format = 'excel'
                elif ext == '.txt':
                    file_format = 'txt'
                else:
                    return None, f"지원하지 않는 파일 형식: {ext}"

            # 파일 읽기
            if file_format == 'csv':
                df = pd.read_csv(file_path)
            elif file_format == 'excel':
                df = pd.read_excel(file_path)
            elif file_format == 'txt':
                # Tab-separated 또는 comma-separated 시도
                try:
                    df = pd.read_csv(file_path, sep='\t')
                except:
                    df = pd.read_csv(file_path, sep=',')
            else:
                return None, f"알 수 없는 파일 형식: {file_format}"

            return df, None

        except Exception as e:
            return None, f"파일 읽기 오류: {e}"

    @staticmethod
    def parse_parameters(
        df: pd.DataFrame,
        item_name_column: str = 'ItemName',
        value_column: str = 'Value'
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        데이터프레임에서 파라미터 추출

        Args:
            df: 데이터프레임
            item_name_column: ItemName 컬럼명
            value_column: Value 컬럼명

        Returns:
            Tuple[Dict, error_message]: 파라미터 딕셔너리와 오류 메시지
        """
        try:
            # 컬럼 확인
            if item_name_column not in df.columns:
                # 대체 컬럼명 시도
                if 'Parameter' in df.columns:
                    item_name_column = 'Parameter'
                else:
                    return None, f"ItemName 컬럼을 찾을 수 없음: {list(df.columns)}"

            if value_column not in df.columns:
                return None, f"Value 컬럼을 찾을 수 없음: {list(df.columns)}"

            # 파라미터 추출
            parameters = {}
            for _, row in df.iterrows():
                item_name = row[item_name_column]
                value = row[value_column]

                if pd.notna(item_name):
                    parameters[str(item_name)] = value

            return parameters, None

        except Exception as e:
            return None, f"파라미터 파싱 오류: {e}"

    @staticmethod
    def load_and_parse(
        file_path: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        파일 로드 및 파라미터 파싱 (통합 함수)

        Args:
            file_path: 파일 경로

        Returns:
            Tuple[Dict, error_message]: 파라미터 딕셔너리와 오류 메시지
        """
        # 파일 읽기
        df, error = FileHandler.read_file(file_path)
        if error:
            return None, error

        # 파라미터 파싱
        parameters, error = FileHandler.parse_parameters(df)
        if error:
            return None, error

        return parameters, None

    @staticmethod
    def write_dataframe(
        df: pd.DataFrame,
        file_path: str,
        file_format: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        데이터프레임을 파일로 저장

        Args:
            df: 데이터프레임
            file_path: 저장 경로
            file_format: 파일 형식 ('csv', 'excel', None=자동 감지)

        Returns:
            Tuple[success, error_message]: 성공 여부와 오류 메시지
        """
        try:
            # 파일 형식 자동 감지
            if not file_format:
                ext = os.path.splitext(file_path)[1].lower()
                if ext == '.csv':
                    file_format = 'csv'
                elif ext in ['.xlsx', '.xls']:
                    file_format = 'excel'
                else:
                    return False, f"지원하지 않는 파일 형식: {ext}"

            # 파일 쓰기
            if file_format == 'csv':
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
            elif file_format == 'excel':
                df.to_excel(file_path, index=False, engine='openpyxl')
            else:
                return False, f"알 수 없는 파일 형식: {file_format}"

            return True, None

        except Exception as e:
            return False, f"파일 쓰기 오류: {e}"

    @staticmethod
    def validate_file(file_path: str) -> Tuple[bool, Optional[str]]:
        """
        파일 유효성 검증

        Args:
            file_path: 파일 경로

        Returns:
            Tuple[valid, error_message]: 유효성 여부와 오류 메시지
        """
        # 파일 존재 확인
        if not os.path.exists(file_path):
            return False, f"파일을 찾을 수 없음: {file_path}"

        # 파일 크기 확인
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return False, "파일이 비어있음"

        # 파일 형식 확인
        ext = os.path.splitext(file_path)[1].lower()
        supported_formats = ['.csv', '.xlsx', '.xls', '.txt']
        if ext not in supported_formats:
            return False, f"지원하지 않는 파일 형식: {ext}"

        return True, None
