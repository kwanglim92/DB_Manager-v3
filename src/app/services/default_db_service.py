"""
Default DB 관리 서비스
장비 구성별 파라미터 관리를 단순화하고 체계화
"""

import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class DefaultDBService:
    """Default DB 관리 서비스"""
    
    # 장비 구성 요소 정의
    AE_TYPES = ['일체형', '분리형']
    CABINET_TYPES = ['T1', 'PB', None]  # None은 Cabinet 없음
    EFEM_TYPES = ['Single', 'Double', 'None']
    
    # 모듈 카테고리
    MODULES = [
        'Temperature',
        'Pressure', 
        'Motion',
        'Sensor',
        'Communication',
        'Safety',
        'Process',
        'Utility'
    ]
    
    def __init__(self, db_schema):
        self.db_schema = db_schema
        self.current_config = None
        self.cached_parameters = {}
        
    def get_or_create_configuration(self, model_id: int, ae_type: str, 
                                   cabinet_type: Optional[str], efem_type: str,
                                   options: Optional[Dict] = None) -> int:
        """
        장비 구성 조회 또는 생성
        
        Args:
            model_id: 장비 모델 ID
            ae_type: AE 타입 (일체형/분리형)
            cabinet_type: Cabinet 타입 (T1/PB/None)
            efem_type: EFEM 타입 (Single/Double/None)
            options: 추가 옵션 (JSON)
            
        Returns:
            configuration_id
        """
        # 구성 코드 생성
        config_code = self._generate_config_code(model_id, ae_type, cabinet_type, efem_type)
        
        # 기존 구성 조회
        query = """
        SELECT id FROM Equipment_Configurations 
        WHERE model_id = ? AND ae_type = ? 
        AND (cabinet_type = ? OR (cabinet_type IS NULL AND ? IS NULL))
        AND efem_type = ?
        """
        
        result = self.db_schema.execute_query(
            query, (model_id, ae_type, cabinet_type, cabinet_type, efem_type)
        )
        
        if result:
            return result[0][0]
        
        # 새 구성 생성
        insert_query = """
        INSERT INTO Equipment_Configurations 
        (model_id, ae_type, cabinet_type, efem_type, config_code, options)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        
        options_json = json.dumps(options) if options else None
        
        self.db_schema.execute_update(
            insert_query,
            (model_id, ae_type, cabinet_type, efem_type, config_code, options_json)
        )
        
        # 생성된 ID 조회
        return self.db_schema.execute_query("SELECT last_insert_rowid()")[0][0]
    
    def _generate_config_code(self, model_id: int, ae_type: str, 
                             cabinet_type: Optional[str], efem_type: str) -> str:
        """구성 코드 자동 생성"""
        ae_code = 'I' if ae_type == '일체형' else 'S'  # Integrated/Separated
        cabinet_code = cabinet_type or 'NC'  # No Cabinet
        efem_code = efem_type[0] if efem_type != 'None' else 'N'  # S/D/N
        
        return f"M{model_id}_{ae_code}_{cabinet_code}_{efem_code}"
    
    def get_configuration_display_name(self, config_id: int) -> str:
        """구성 표시 이름 생성"""
        config = self.get_configuration(config_id)
        if not config:
            return "Unknown"
        
        parts = []
        parts.append(config['ae_type'])
        
        if config['cabinet_type']:
            parts.append(f"Cabinet:{config['cabinet_type']}")
            
        if config['efem_type'] != 'None':
            parts.append(f"EFEM:{config['efem_type']}")
            
        return " / ".join(parts)
    
    def get_configuration(self, config_id: int) -> Optional[Dict]:
        """구성 정보 조회"""
        query = """
        SELECT c.*, m.model_name 
        FROM Equipment_Configurations c
        JOIN Equipment_Models m ON c.model_id = m.id
        WHERE c.id = ?
        """
        
        result = self.db_schema.execute_query(query, (config_id,))
        if not result:
            return None
            
        row = result[0]
        return {
            'id': row[0],
            'model_id': row[1],
            'ae_type': row[2],
            'cabinet_type': row[3],
            'efem_type': row[4],
            'config_code': row[5],
            'options': json.loads(row[6]) if row[6] else {},
            'model_name': row[7]
        }
    
    def get_parameters_grouped(self, config_id: int) -> Dict[str, List[Dict]]:
        """
        구성의 파라미터를 모듈별로 그룹화하여 조회
        
        Returns:
            {
                'Temperature': [params...],
                'Pressure': [params...],
                ...
            }
        """
        if config_id in self.cached_parameters:
            return self.cached_parameters[config_id]
            
        query = """
        SELECT parameter_name, default_value, module, sub_module, 
               data_type, unit
        FROM Default_DB_Values
        WHERE configuration_id = ?
        ORDER BY module, sub_module, parameter_name
        """
        
        results = self.db_schema.execute_query(query, (config_id,))
        
        grouped = {}
        for row in results:
            module = row[2] or 'General'
            if module not in grouped:
                grouped[module] = []
                
            grouped[module].append({
                'parameter_name': row[0],
                'default_value': row[1],
                'module': row[2],
                'sub_module': row[3],
                'data_type': row[4],
                'unit': row[5]
            })
        
        self.cached_parameters[config_id] = grouped
        return grouped
    
    def add_parameter(self, config_id: int, param_data: Dict) -> bool:
        """
        파라미터 추가
        
        Args:
            config_id: 구성 ID
            param_data: {
                'name': 파라미터명,
                'value': 기본값,
                'module': 모듈,
                'sub_module': 서브모듈,
                'data_type': 데이터 타입,
                'unit': 단위
            }
        """
        # 중복 확인
        check_query = """
        SELECT id FROM Default_DB_Values
        WHERE configuration_id = ? AND parameter_name = ?
        """
        
        existing = self.db_schema.execute_query(
            check_query, (config_id, param_data['name'])
        )
        
        if existing:
            raise ValueError(f"파라미터 '{param_data['name']}'이(가) 이미 존재합니다.")
        
        # 추가
        insert_query = """
        INSERT INTO Default_DB_Values
        (configuration_id, parameter_name, default_value, module, sub_module, data_type, unit)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        self.db_schema.execute_update(
            insert_query,
            (config_id, param_data['name'], param_data['value'],
             param_data['module'], param_data.get('sub_module'),
             param_data['data_type'], param_data.get('unit'))
        )
        
        # 캐시 무효화
        if config_id in self.cached_parameters:
            del self.cached_parameters[config_id]
            
        return True
    
    def update_parameter(self, config_id: int, param_name: str, 
                         new_data: Dict) -> bool:
        """파라미터 수정"""
        update_query = """
        UPDATE Default_DB_Values
        SET default_value = ?, module = ?, sub_module = ?, 
            data_type = ?, unit = ?
        WHERE configuration_id = ? AND parameter_name = ?
        """
        
        self.db_schema.execute_update(
            update_query,
            (new_data['value'], new_data['module'], new_data.get('sub_module'),
             new_data['data_type'], new_data.get('unit'),
             config_id, param_name)
        )
        
        # 캐시 무효화
        if config_id in self.cached_parameters:
            del self.cached_parameters[config_id]
            
        return True
    
    def delete_parameter(self, config_id: int, param_name: str) -> bool:
        """파라미터 삭제"""
        delete_query = """
        DELETE FROM Default_DB_Values
        WHERE configuration_id = ? AND parameter_name = ?
        """
        
        self.db_schema.execute_update(delete_query, (config_id, param_name))
        
        # 캐시 무효화
        if config_id in self.cached_parameters:
            del self.cached_parameters[config_id]
            
        return True
    
    def copy_configuration(self, source_config_id: int, 
                          target_model_id: int,
                          target_ae: str, 
                          target_cabinet: Optional[str],
                          target_efem: str) -> int:
        """
        구성 복사
        
        Returns:
            새로 생성된 configuration_id
        """
        # 타겟 구성 생성
        target_config_id = self.get_or_create_configuration(
            target_model_id, target_ae, target_cabinet, target_efem
        )
        
        # 기존 파라미터 삭제 (있다면)
        delete_query = "DELETE FROM Default_DB_Values WHERE configuration_id = ?"
        self.db_schema.execute_update(delete_query, (target_config_id,))
        
        # 소스 파라미터 복사
        copy_query = """
        INSERT INTO Default_DB_Values 
        (configuration_id, parameter_name, default_value, module, sub_module, data_type, unit)
        SELECT ?, parameter_name, default_value, module, sub_module, data_type, unit
        FROM Default_DB_Values
        WHERE configuration_id = ?
        """
        
        self.db_schema.execute_update(copy_query, (target_config_id, source_config_id))
        
        return target_config_id
    
    def import_parameters_from_file(self, config_id: int, file_path: str, 
                                   mode: str = 'append') -> Tuple[int, int]:
        """
        파일에서 파라미터 가져오기
        
        Args:
            config_id: 구성 ID
            file_path: 파일 경로
            mode: 'append' (추가) 또는 'replace' (교체)
            
        Returns:
            (성공 개수, 실패 개수)
        """
        success_count = 0
        fail_count = 0
        
        if mode == 'replace':
            # 기존 파라미터 삭제
            delete_query = "DELETE FROM Default_DB_Values WHERE configuration_id = ?"
            self.db_schema.execute_update(delete_query, (config_id,))
        
        # 파일 파싱 및 가져오기 로직
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if '=' in line:
                        parts = line.strip().split('=')
                        if len(parts) == 2:
                            param_name = parts[0].strip()
                            default_value = parts[1].strip()
                            
                            # 모듈 추론 (간단한 예시)
                            module = 'General'
                            if 'Temp' in param_name:
                                module = 'Temperature'
                            elif 'Pressure' in param_name:
                                module = 'Pressure'
                            elif 'Motion' in param_name:
                                module = 'Motion'
                            
                            try:
                                self.add_parameter(config_id, {
                                    'name': param_name,
                                    'value': default_value,
                                    'module': module,
                                    'data_type': 'string',
                                    'unit': None
                                })
                                success_count += 1
                            except ValueError:
                                # 이미 존재하는 파라미터
                                fail_count += 1
                            except Exception:
                                fail_count += 1
                                
        except Exception as e:
            print(f"파일 읽기 오류: {e}")
            
        return success_count, fail_count
    
    def export_parameters_to_file(self, config_id: int, file_path: str) -> bool:
        """파라미터를 파일로 내보내기"""
        try:
            params = self.get_parameters_grouped(config_id)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                for module, param_list in params.items():
                    f.write(f"# {module}\n")
                    for param in param_list:
                        f.write(f"{param['parameter_name']}={param['default_value']}\n")
                    f.write("\n")
                    
            return True
            
        except Exception as e:
            print(f"파일 쓰기 오류: {e}")
            return False