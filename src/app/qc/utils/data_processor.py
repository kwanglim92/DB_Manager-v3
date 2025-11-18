"""
Data Processor - QC 검수 데이터 처리 유틸리티

기존 qc_utils.py의 QCDataProcessor 기능 개선
"""

import pandas as pd
from typing import Dict, List, Any, Optional, Tuple


class DataProcessor:
    """QC 검수 데이터 처리 유틸리티"""

    @staticmethod
    def create_safe_dataframe(
        data: Any,
        expected_columns: List[str]
    ) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        안전한 데이터프레임 생성

        Args:
            data: 데이터
            expected_columns: 예상 컬럼 목록

        Returns:
            Tuple[DataFrame, error_message]: 데이터프레임과 오류 메시지
        """
        try:
            df = pd.DataFrame(data, columns=expected_columns)
            return df, None
        except Exception as e:
            error_msg = f"데이터프레임 생성 오류: {str(e)}\n데이터 형태: {type(data)}"
            return None, error_msg

    @staticmethod
    def dataframe_to_dict(
        df: pd.DataFrame,
        key_column: str,
        value_column: str
    ) -> Dict[str, Any]:
        """
        데이터프레임을 딕셔너리로 변환

        Args:
            df: 데이터프레임
            key_column: 키로 사용할 컬럼명
            value_column: 값으로 사용할 컬럼명

        Returns:
            Dict: {key: value} 딕셔너리
        """
        if key_column not in df.columns or value_column not in df.columns:
            raise ValueError(f"컬럼을 찾을 수 없음: {key_column} 또는 {value_column}")

        return dict(zip(df[key_column], df[value_column]))

    @staticmethod
    def extract_parameters(
        df: pd.DataFrame,
        item_name_col: str = 'ItemName',
        value_col: str = 'Value',
        module_col: Optional[str] = None,
        part_col: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        데이터프레임에서 파라미터 추출

        Args:
            df: 데이터프레임
            item_name_col: ItemName 컬럼명
            value_col: Value 컬럼명
            module_col: Module 컬럼명 (옵션)
            part_col: Part 컬럼명 (옵션)

        Returns:
            Dict: 파라미터 딕셔너리
        """
        parameters = {}

        for _, row in df.iterrows():
            item_name = row[item_name_col]
            value = row[value_col]

            # 복합 키 지원 (Module.Part.ItemName)
            if module_col and part_col and module_col in df.columns and part_col in df.columns:
                module = row[module_col] if pd.notna(row[module_col]) else None
                part = row[part_col] if pd.notna(row[part_col]) else None

                # 복합 키로 저장
                key = (module, part, item_name)
                parameters[key] = value
            else:
                # 단순 키로 저장
                parameters[item_name] = value

        return parameters

    @staticmethod
    def validate_data_structure(
        data: Any,
        required_fields: List[str]
    ) -> Tuple[bool, str]:
        """
        데이터 구조 유효성 검증

        Args:
            data: 검증할 데이터
            required_fields: 필수 필드 목록

        Returns:
            Tuple[bool, message]: 유효성 여부와 메시지
        """
        if isinstance(data, pd.DataFrame):
            missing_fields = [f for f in required_fields if f not in data.columns]
            if missing_fields:
                return False, f"필수 컬럼 누락: {', '.join(missing_fields)}"
            return True, ""

        elif isinstance(data, dict):
            missing_fields = [f for f in required_fields if f not in data]
            if missing_fields:
                return False, f"필수 필드 누락: {', '.join(missing_fields)}"
            return True, ""

        else:
            return False, f"지원하지 않는 데이터 타입: {type(data)}"

    @staticmethod
    def filter_by_category(
        results: List[Dict],
        category: Optional[str] = None
    ) -> List[Dict]:
        """
        카테고리별 결과 필터링

        Args:
            results: 검수 결과 리스트
            category: 카테고리 (None이면 전체)

        Returns:
            List[Dict]: 필터링된 결과
        """
        if not category:
            return results

        return [r for r in results if r.get('category') == category]

    @staticmethod
    def filter_failed_only(results: List[Dict]) -> List[Dict]:
        """
        실패한 결과만 필터링

        Args:
            results: 검수 결과 리스트

        Returns:
            List[Dict]: 실패한 결과만
        """
        return [r for r in results if not r.get('is_valid', True)]
