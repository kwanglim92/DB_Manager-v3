"""
QC 검증 서비스
파일의 파라미터를 Master Spec과 비교하여 검증
"""

import re
from typing import Dict, List, Optional, Any
from datetime import datetime

class QCValidator:
    """QC 검증 서비스"""
    
    def __init__(self, db_schema, spec_service):
        """
        Args:
            db_schema: 데이터베이스 스키마
            spec_service: QCSpecService 인스턴스
        """
        self.db_schema = db_schema
        self.spec_service = spec_service
        
    def validate_file(self, file_path: str, 
                     equipment_type_id: int = None,
                     configuration_id: int = None) -> Dict:
        """
        파일 검증
        
        Args:
            file_path: 검증할 파일 경로
            equipment_type_id: 장비 타입 ID (옵션)
            configuration_id: 구성 ID (옵션)
            
        Returns:
            검증 결과 딕셔너리
        """
        # 파일 파싱
        parameters = self.parse_file(file_path)
        
        # 검증 수행
        return self.validate_parameters(parameters, equipment_type_id, configuration_id)
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        파일 파싱
        
        Returns:
            {ItemName: Value} 딕셔너리
        """
        parameters = {}
        
        # 파일 확장자 확인
        if file_path.endswith('.csv'):
            import pandas as pd
            df = pd.read_csv(file_path)
            
            # ItemName, Value 컬럼 찾기
            if 'ItemName' in df.columns and 'Value' in df.columns:
                for _, row in df.iterrows():
                    parameters[row['ItemName']] = row['Value']
            elif 'Parameter' in df.columns and 'Value' in df.columns:
                for _, row in df.iterrows():
                    parameters[row['Parameter']] = row['Value']
                    
        elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            import pandas as pd
            df = pd.read_excel(file_path)
            
            if 'ItemName' in df.columns and 'Value' in df.columns:
                for _, row in df.iterrows():
                    parameters[row['ItemName']] = row['Value']
                    
        else:
            # 텍스트 파일 (key=value 형식)
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if '=' in line:
                        parts = line.strip().split('=')
                        if len(parts) == 2:
                            item_name = parts[0].strip()
                            value = parts[1].strip()
                            parameters[item_name] = value
        
        return parameters
    
    def validate_parameters(self, parameters: Dict[str, Any],
                          equipment_type_id: int = None,
                          configuration_id: int = None) -> Dict:
        """
        파라미터 검증
        
        Args:
            parameters: {ItemName: Value} 딕셔너리
            equipment_type_id: 장비 타입 ID (옵션)
            configuration_id: 구성 ID (옵션)
            
        Returns:
            검증 결과
        """
        results = {
            'passed': [],
            'failed': [],
            'skipped': [],
            'summary': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Master Spec 조회
        master_specs = self.spec_service.get_master_specs()
        
        # Override 조회
        overrides = {}
        if equipment_type_id or configuration_id:
            overrides = self.spec_service.get_overrides(
                equipment_type_id, configuration_id
            )
        
        # 카테고리별 결과 집계
        category_results = {}
        
        # 각 파라미터 검증
        for item_name, value in parameters.items():
            # Spec 찾기
            spec = self.find_spec(item_name, master_specs, overrides)
            
            if not spec:
                results['skipped'].append({
                    'item_name': item_name,
                    'value': value,
                    'reason': 'No spec defined'
                })
                continue
            
            # 제외 항목 확인
            if spec.get('is_excluded'):
                results['skipped'].append({
                    'item_name': item_name,
                    'value': value,
                    'reason': spec.get('reason', 'Excluded for this configuration')
                })
                continue
            
            # 검증 수행
            is_valid, message = self.check_value(value, spec)
            
            # 카테고리별 집계
            category = spec.get('category', 'General')
            if category not in category_results:
                category_results[category] = {'passed': 0, 'failed': 0}
            
            result_entry = {
                'item_name': item_name,
                'value': value,
                'spec': self.format_spec_display(spec),
                'category': category,
                'is_valid': is_valid,
                'message': message
            }
            
            if is_valid:
                results['passed'].append(result_entry)
                category_results[category]['passed'] += 1
            else:
                results['failed'].append(result_entry)
                category_results[category]['failed'] += 1
        
        # 요약 생성
        total = len(parameters)
        passed = len(results['passed'])
        failed = len(results['failed'])
        skipped = len(results['skipped'])
        
        results['summary'] = {
            'total': total,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'pass_rate': (passed / total * 100) if total > 0 else 0,
            'status': 'PASS' if failed == 0 else 'FAIL',
            'by_category': category_results
        }
        
        # Critical 항목 체크 (Safety 카테고리)
        if 'Safety' in category_results and category_results['Safety']['failed'] > 0:
            results['summary']['status'] = 'CRITICAL_FAIL'
            results['summary']['critical_message'] = 'Safety 항목 실패'
        
        return results
    
    def find_spec(self, item_name: str, master_specs: Dict, overrides: Dict) -> Optional[Dict]:
        """
        ItemName에 해당하는 Spec 찾기
        
        Args:
            item_name: 파라미터명
            master_specs: Master Spec 딕셔너리
            overrides: Override 딕셔너리
            
        Returns:
            Spec 정보 또는 None
        """
        # 1. Override 확인
        if item_name in overrides:
            override = overrides[item_name]
            if override.get('is_excluded'):
                return override
            
            # Master spec과 병합
            if item_name in master_specs:
                spec = master_specs[item_name].copy()
                # Override 값으로 덮어쓰기
                if override.get('override_min_spec') is not None:
                    spec['min_spec'] = override['override_min_spec']
                if override.get('override_max_spec') is not None:
                    spec['max_spec'] = override['override_max_spec']
                if override.get('override_expected_value') is not None:
                    spec['expected_value'] = override['override_expected_value']
                spec['is_override'] = True
                return spec
        
        # 2. Master Spec 정확한 매칭
        if item_name in master_specs:
            return master_specs[item_name].copy()
        
        # 3. 패턴 매칭 (와일드카드)
        # 예: "Temp.*" 패턴이 "Temp.Chamber.Set"과 매칭
        for spec_name, spec in master_specs.items():
            if '*' in spec_name or '?' in spec_name:
                pattern = spec_name.replace('.', r'\.')
                pattern = pattern.replace('*', '.*')
                pattern = pattern.replace('?', '.')
                pattern = f'^{pattern}$'
                
                if re.match(pattern, item_name):
                    spec_copy = spec.copy()
                    spec_copy['matched_by_pattern'] = True
                    return spec_copy
        
        return None
    
    def check_value(self, value: Any, spec: Dict) -> Tuple[bool, str]:
        """
        값 검증
        
        Args:
            value: 검증할 값
            spec: Spec 정보
            
        Returns:
            (검증 결과, 메시지)
        """
        check_type = spec.get('check_type', 'range')
        
        try:
            if check_type == 'range':
                # 범위 검증
                val = float(value)
                min_spec = float(spec['min_spec']) if spec.get('min_spec') else None
                max_spec = float(spec['max_spec']) if spec.get('max_spec') else None
                
                if min_spec is not None and val < min_spec:
                    return False, f"값 {val}이(가) 최소값 {min_spec}보다 작음"
                if max_spec is not None and val > max_spec:
                    return False, f"값 {val}이(가) 최대값 {max_spec}보다 큼"
                return True, "OK"
                
            elif check_type == 'exact':
                # 정확한 값 비교
                expected = str(spec.get('expected_value', '')).upper()
                actual = str(value).upper()
                
                if actual == expected:
                    return True, "OK"
                else:
                    return False, f"기대값 {expected}, 실제값 {actual}"
                    
            elif check_type == 'boolean':
                # Boolean 검증
                value_str = str(value).upper()
                expected = str(spec.get('expected_value', '1')).upper()
                
                true_values = ['1', 'ON', 'TRUE', 'ENABLE', 'ENABLED', 'YES']
                false_values = ['0', 'OFF', 'FALSE', 'DISABLE', 'DISABLED', 'NO']
                
                if expected in true_values:
                    if value_str in true_values:
                        return True, "OK"
                    else:
                        return False, f"기대값 ON, 실제값 {value}"
                        
                elif expected in false_values:
                    if value_str in false_values:
                        return True, "OK"
                    else:
                        return False, f"기대값 OFF, 실제값 {value}"
                        
                else:
                    if value_str == expected:
                        return True, "OK"
                    else:
                        return False, f"기대값 {expected}, 실제값 {value}"
                        
            elif check_type == 'pattern':
                # 정규식 패턴 매칭
                pattern = spec.get('expected_value', '')
                if re.match(pattern, str(value)):
                    return True, "OK"
                else:
                    return False, f"패턴 {pattern}과 불일치"
                    
            else:
                # 알 수 없는 타입
                return True, "검증 타입 미지정"
                
        except Exception as e:
            return False, f"검증 오류: {str(e)}"
    
    def format_spec_display(self, spec: Dict) -> str:
        """Spec을 표시용 문자열로 포맷"""
        check_type = spec.get('check_type', 'range')
        
        if check_type == 'range':
            min_spec = spec.get('min_spec', '')
            max_spec = spec.get('max_spec', '')
            
            if min_spec and max_spec:
                return f"{min_spec} ~ {max_spec}"
            elif min_spec:
                return f">= {min_spec}"
            elif max_spec:
                return f"<= {max_spec}"
            else:
                return "No limit"
                
        elif check_type in ['exact', 'boolean']:
            return str(spec.get('expected_value', ''))
            
        elif check_type == 'pattern':
            return f"Pattern: {spec.get('expected_value', '')}"
            
        else:
            return "Unknown"