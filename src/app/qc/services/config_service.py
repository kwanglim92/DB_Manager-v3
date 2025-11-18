"""
Config Service - QC 설정 관리 서비스

기존 qc_custom_config.py 기능을 Services Layer로 통합
사용자 정의 QC 검수 설정 관리
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime


class ConfigService:
    """QC 설정 관리 서비스"""

    DEFAULT_CONFIG_PATH = 'config/custom_qc_specs.json'

    # 기본 Equipment Types
    DEFAULT_EQUIPMENT_TYPES = [
        "Standard Model",
        "Advanced Model",
        "Custom Model",
        "Test Configuration",
        "Production Line A",
        "Production Line B"
    ]

    def __init__(self, config_path: Optional[str] = None):
        """
        초기화

        Args:
            config_path: 설정 파일 경로 (None이면 기본 경로 사용)
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config = self.load_config()

    def load_config(self) -> Dict:
        """
        설정 파일 로드

        Returns:
            Dict: 설정 데이터
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"설정 파일 로드 오류: {e}")

        # 기본 설정 생성
        return self.create_default_config()

    def create_default_config(self) -> Dict:
        """
        기본 설정 생성

        Returns:
            Dict: 기본 설정
        """
        config = {
            'version': '2.0',
            'created': datetime.now().isoformat(),
            'equipment_types': self.DEFAULT_EQUIPMENT_TYPES,
            'specs': {}
        }

        # 각 Equipment Type에 대한 빈 스펙
        for eq_type in self.DEFAULT_EQUIPMENT_TYPES:
            config['specs'][eq_type] = []

        return config

    def save_config(self) -> bool:
        """
        설정 저장

        Returns:
            bool: 성공 여부
        """
        try:
            if self.config_path:
                dir_path = os.path.dirname(self.config_path)
                if dir_path:
                    os.makedirs(dir_path, exist_ok=True)

                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
                return True
            return False
        except Exception as e:
            print(f"설정 저장 오류: {e}")
            return False

    def get_equipment_types(self) -> List[str]:
        """
        Equipment Type 목록 반환

        Returns:
            List[str]: Equipment Type 목록
        """
        return self.config.get('equipment_types', self.DEFAULT_EQUIPMENT_TYPES)

    def add_equipment_type(self, type_name: str) -> bool:
        """
        Equipment Type 추가

        Args:
            type_name: Equipment Type 이름

        Returns:
            bool: 성공 여부
        """
        if type_name not in self.config['equipment_types']:
            self.config['equipment_types'].append(type_name)
            self.config['specs'][type_name] = []
            return self.save_config()
        return False

    def remove_equipment_type(self, type_name: str) -> bool:
        """
        Equipment Type 제거

        Args:
            type_name: Equipment Type 이름

        Returns:
            bool: 성공 여부
        """
        if type_name in self.config['equipment_types']:
            self.config['equipment_types'].remove(type_name)
            if type_name in self.config['specs']:
                del self.config['specs'][type_name]
            return self.save_config()
        return False

    def get_specs(self, equipment_type: str) -> List[Dict]:
        """
        특정 Equipment Type의 스펙 반환

        Args:
            equipment_type: Equipment Type 이름

        Returns:
            List[Dict]: 스펙 목록
        """
        return self.config.get('specs', {}).get(equipment_type, [])

    def update_specs(self, equipment_type: str, specs: List[Dict]) -> bool:
        """
        스펙 업데이트 (전체 교체)

        Args:
            equipment_type: Equipment Type 이름
            specs: 새로운 스펙 목록

        Returns:
            bool: 성공 여부
        """
        if 'specs' not in self.config:
            self.config['specs'] = {}
        self.config['specs'][equipment_type] = specs
        return self.save_config()

    def add_spec(self, equipment_type: str, spec: Dict) -> bool:
        """
        스펙 추가

        Args:
            equipment_type: Equipment Type 이름
            spec: 스펙 딕셔너리
                {
                    'item_name': str,
                    'min_spec': Optional[float],
                    'max_spec': Optional[float],
                    'unit': Optional[str],
                    'enabled': bool,
                    'description': Optional[str]
                }

        Returns:
            bool: 성공 여부
        """
        if equipment_type not in self.config.get('specs', {}):
            self.add_equipment_type(equipment_type)

        self.config['specs'][equipment_type].append(spec)
        return self.save_config()

    def add_specs(self, equipment_type: str, specs: List[Dict]) -> bool:
        """
        여러 스펙을 한 번에 추가

        Args:
            equipment_type: Equipment Type 이름
            specs: 스펙 딕셔너리 리스트

        Returns:
            bool: 성공 여부
        """
        if equipment_type not in self.config.get('specs', {}):
            self.add_equipment_type(equipment_type)

        for spec in specs:
            self.config['specs'][equipment_type].append(spec)

        return self.save_config()

    def remove_spec(self, equipment_type: str, item_name: str) -> bool:
        """
        스펙 제거

        Args:
            equipment_type: Equipment Type 이름
            item_name: 항목명

        Returns:
            bool: 성공 여부
        """
        if equipment_type in self.config.get('specs', {}):
            specs = self.config['specs'][equipment_type]
            self.config['specs'][equipment_type] = [
                s for s in specs if s.get('item_name') != item_name
            ]
            return self.save_config()
        return False

    def export_to_file(self, filepath: str) -> bool:
        """
        설정을 파일로 내보내기

        Args:
            filepath: 저장 경로

        Returns:
            bool: 성공 여부
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"내보내기 오류: {e}")
            return False

    def import_from_file(self, filepath: str) -> bool:
        """
        파일에서 설정 가져오기

        Args:
            filepath: 파일 경로

        Returns:
            bool: 성공 여부
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                imported = json.load(f)

            # 유효성 검사
            if 'equipment_types' in imported and 'specs' in imported:
                self.config = imported
                return self.save_config()

            return False
        except Exception as e:
            print(f"가져오기 오류: {e}")
            return False

    def reset_to_default(self) -> bool:
        """
        기본 설정으로 리셋

        Returns:
            bool: 성공 여부
        """
        self.config = self.create_default_config()
        return self.save_config()
