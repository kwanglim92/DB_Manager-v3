"""
QC Spec 관리 서비스
모든 QC 검사 기준을 중앙에서 관리
"""

import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class QCSpecService:
    """QC Spec 중앙 관리 서비스"""
    
    def __init__(self, db_schema):
        self.db_schema = db_schema
        self.spec_cache = {}
        
    def add_spec(self, item_name: str, min_spec: Optional[str] = None,
                 max_spec: Optional[str] = None, expected_value: Optional[str] = None,
                 category: str = 'General', severity: str = 'MEDIUM') -> bool:
        """
        QC 스펙 추가
        
        Args:
            item_name: 파라미터명 (ItemName)
            min_spec: 최소 스펙
            max_spec: 최대 스펙
            expected_value: 기대값 (Pass/Fail 항목용)
            category: 카테고리
            severity: 심각도 (CRITICAL/HIGH/MEDIUM/LOW)
        """
        # check_type 자동 결정
        if min_spec and max_spec:
            check_type = 'range'
        elif expected_value:
            check_type = 'exact' if expected_value in ['PASS', 'FAIL', 'ON', 'OFF'] else 'boolean'
        else:
            check_type = 'exists'
            
        query = """
        INSERT OR REPLACE INTO QC_Spec_Master
        (item_name, min_spec, max_spec, expected_value, check_type, category, severity)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        try:
            self.db_schema.execute_update(
                query, 
                (item_name, min_spec, max_spec, expected_value, check_type, category, severity)
            )
            # 캐시 무효화
            self.spec_cache.clear()
            return True
        except Exception as e:
            print(f"QC Spec 추가 오류: {e}")
            return False
    
    def get_all_specs(self, category: Optional[str] = None, 
                      is_active: bool = True) -> List[Dict]:
        """
        모든 QC 스펙 조회
        
        Args:
            category: 카테고리 필터
            is_active: 활성화된 항목만
        """
        query = """
        SELECT id, item_name, min_spec, max_spec, expected_value,
               check_type, category, severity, is_active, description
        FROM QC_Spec_Master
        WHERE is_active = ?
        """
        params = [1 if is_active else 0]
        
        if category:
            query += " AND category = ?"
            params.append(category)
            
        query += " ORDER BY category, severity DESC, item_name"
        
        results = self.db_schema.execute_query(query, params)
        
        specs = []
        for row in results:
            specs.append({
                'id': row[0],
                'item_name': row[1],
                'min_spec': row[2],
                'max_spec': row[3],
                'expected_value': row[4],
                'check_type': row[5],
                'category': row[6],
                'severity': row[7],
                'is_active': bool(row[8]),
                'description': row[9]
            })
            
        return specs
    
    def get_spec_by_item_name(self, item_name: str) -> Optional[Dict]:
        """ItemName으로 스펙 조회"""
        
        # 캐시 확인
        if item_name in self.spec_cache:
            return self.spec_cache[item_name]
            
        query = """
        SELECT id, min_spec, max_spec, expected_value, check_type, 
               category, severity, description
        FROM QC_Spec_Master
        WHERE item_name = ? AND is_active = 1
        """
        
        result = self.db_schema.execute_query(query, (item_name,))
        
        if result:
            row = result[0]
            spec = {
                'id': row[0],
                'item_name': item_name,
                'min_spec': row[1],
                'max_spec': row[2],
                'expected_value': row[3],
                'check_type': row[4],
                'category': row[5],
                'severity': row[6],
                'description': row[7]
            }
            # 캐시 저장
            self.spec_cache[item_name] = spec
            return spec
            
        return None
    
    def update_spec(self, item_name: str, **kwargs) -> bool:
        """스펙 업데이트"""
        allowed_fields = ['min_spec', 'max_spec', 'expected_value', 
                         'category', 'severity', 'description']
        
        updates = []
        values = []
        for field, value in kwargs.items():
            if field in allowed_fields:
                updates.append(f"{field} = ?")
                values.append(value)
                
        if not updates:
            return False
            
        query = f"""
        UPDATE QC_Spec_Master
        SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
        WHERE item_name = ?
        """
        
        values.append(item_name)
        
        try:
            self.db_schema.execute_update(query, values)
            # 캐시 무효화
            if item_name in self.spec_cache:
                del self.spec_cache[item_name]
            return True
        except Exception as e:
            print(f"스펙 업데이트 오류: {e}")
            return False
    
    def delete_spec(self, item_name: str) -> bool:
        """스펙 삭제 (비활성화)"""
        query = """
        UPDATE QC_Spec_Master
        SET is_active = 0, updated_at = CURRENT_TIMESTAMP
        WHERE item_name = ?
        """
        
        try:
            self.db_schema.execute_update(query, (item_name,))
            # 캐시 무효화
            if item_name in self.spec_cache:
                del self.spec_cache[item_name]
            return True
        except Exception as e:
            print(f"스펙 삭제 오류: {e}")
            return False
    
    def add_exception(self, configuration_id: Optional[int], 
                     model_id: Optional[int], 
                     item_name: str, 
                     reason: str, 
                     approved_by: str = 'System') -> bool:
        """
        특정 구성/모델에서 QC 항목 제외
        
        Args:
            configuration_id: 구성 ID (None이면 모델 전체)
            model_id: 모델 ID (None이면 구성만)
            item_name: 제외할 항목명
            reason: 제외 사유
            approved_by: 승인자
        """
        # spec_master_id 조회
        spec = self.get_spec_by_item_name(item_name)
        if not spec:
            print(f"QC Spec을 찾을 수 없습니다: {item_name}")
            return False
            
        query = """
        INSERT OR REPLACE INTO QC_Equipment_Exceptions
        (configuration_id, model_id, spec_master_id, reason, approved_by)
        VALUES (?, ?, ?, ?, ?)
        """
        
        try:
            self.db_schema.execute_update(
                query,
                (configuration_id, model_id, spec['id'], reason, approved_by)
            )
            return True
        except Exception as e:
            print(f"예외 추가 오류: {e}")
            return False
    
    def get_exceptions(self, configuration_id: Optional[int] = None,
                      model_id: Optional[int] = None) -> List[Dict]:
        """예외 항목 조회"""
        query = """
        SELECT e.id, e.spec_master_id, s.item_name, e.reason, e.approved_by
        FROM QC_Equipment_Exceptions e
        JOIN QC_Spec_Master s ON e.spec_master_id = s.id
        WHERE 1=1
        """
        params = []
        
        if configuration_id:
            query += " AND e.configuration_id = ?"
            params.append(configuration_id)
            
        if model_id:
            query += " AND e.model_id = ?"
            params.append(model_id)
            
        results = self.db_schema.execute_query(query, params)
        
        exceptions = []
        for row in results:
            exceptions.append({
                'id': row[0],
                'spec_master_id': row[1],
                'item_name': row[2],
                'reason': row[3],
                'approved_by': row[4]
            })
            
        return exceptions
    
    def check_value(self, item_name: str, value: str, 
                   configuration_id: Optional[int] = None) -> Dict:
        """
        값 검증
        
        Returns:
            {
                'pass': bool,
                'spec': str,
                'message': str,
                'severity': str
            }
        """
        spec = self.get_spec_by_item_name(item_name)
        if not spec:
            return {
                'pass': True,
                'spec': 'N/A',
                'message': 'No spec defined',
                'severity': 'INFO'
            }
        
        # 예외 확인
        if configuration_id:
            exceptions = self.get_exceptions(configuration_id=configuration_id)
            if any(e['spec_master_id'] == spec['id'] for e in exceptions):
                return {
                    'pass': True,
                    'spec': 'Excepted',
                    'message': 'This item is excepted for this configuration',
                    'severity': 'INFO'
                }
        
        # 오버라이드 확인 (TODO: 구현 필요)
        
        # 값 검증
        passed = False
        message = ''
        
        if spec['check_type'] == 'range':
            try:
                val = float(value)
                min_val = float(spec['min_spec']) if spec['min_spec'] else float('-inf')
                max_val = float(spec['max_spec']) if spec['max_spec'] else float('inf')
                passed = min_val <= val <= max_val
                spec_str = f"{spec['min_spec'] or '-∞'} ~ {spec['max_spec'] or '+∞'}"
                if not passed:
                    message = f"Value {value} is out of range {spec_str}"
            except ValueError:
                message = f"Cannot convert '{value}' to number"
                spec_str = f"{spec['min_spec']} ~ {spec['max_spec']}"
                
        elif spec['check_type'] == 'exact':
            expected = spec['expected_value']
            passed = str(value).upper() == str(expected).upper()
            spec_str = expected
            if not passed:
                message = f"Expected '{expected}', got '{value}'"
                
        elif spec['check_type'] == 'boolean':
            expected = spec['expected_value']
            passed = str(value) in ['1', 'true', 'True', 'TRUE', 'ON', 'on']
            spec_str = 'Boolean'
            if not passed:
                message = f"Expected boolean true, got '{value}'"
                
        else:  # exists
            passed = value is not None and str(value).strip() != ''
            spec_str = 'Exists'
            if not passed:
                message = "Value is missing or empty"
        
        return {
            'pass': passed,
            'spec': spec_str,
            'message': message or 'OK',
            'severity': spec['severity']
        }
    
    def perform_qc_inspection(self, file_data: Dict, 
                             configuration_id: Optional[int] = None) -> Dict:
        """
        파일 데이터에 대한 QC 검수 실행
        
        Args:
            file_data: {item_name: value} 형태의 파일 데이터
            configuration_id: 구성 ID (예외 처리용)
            
        Returns:
            {
                'total': 전체 항목 수,
                'matched': QC 스펙 매칭 수,
                'passed': 통과 수,
                'failed': 실패 수,
                'results': [검사 결과 리스트],
                'summary': 요약 정보
            }
        """
        results = []
        matched_count = 0
        passed_count = 0
        failed_count = 0
        
        severity_counts = {
            'CRITICAL': {'passed': 0, 'failed': 0},
            'HIGH': {'passed': 0, 'failed': 0},
            'MEDIUM': {'passed': 0, 'failed': 0},
            'LOW': {'passed': 0, 'failed': 0}
        }
        
        for item_name, value in file_data.items():
            # QC 스펙 확인
            spec = self.get_spec_by_item_name(item_name)
            if not spec:
                continue
                
            matched_count += 1
            
            # 값 검증
            check_result = self.check_value(item_name, value, configuration_id)
            
            if check_result['pass']:
                passed_count += 1
                severity_counts[check_result['severity']]['passed'] += 1
            else:
                failed_count += 1
                severity_counts[check_result['severity']]['failed'] += 1
                
            results.append({
                'item_name': item_name,
                'value': value,
                'spec': check_result['spec'],
                'pass': check_result['pass'],
                'message': check_result['message'],
                'severity': check_result['severity']
            })
        
        # 전체 판정
        overall_pass = True
        fail_reasons = []
        
        # CRITICAL 실패가 하나라도 있으면 불합격
        if severity_counts['CRITICAL']['failed'] > 0:
            overall_pass = False
            fail_reasons.append(f"CRITICAL 항목 {severity_counts['CRITICAL']['failed']}개 실패")
            
        # HIGH 실패가 3개 이상이면 불합격
        if severity_counts['HIGH']['failed'] >= 3:
            overall_pass = False
            fail_reasons.append(f"HIGH 항목 {severity_counts['HIGH']['failed']}개 실패 (기준: 3개 미만)")
            
        # 전체 통과율 95% 미만이면 불합격
        if matched_count > 0:
            pass_rate = (passed_count / matched_count) * 100
            if pass_rate < 95:
                overall_pass = False
                fail_reasons.append(f"통과율 {pass_rate:.1f}% (기준: 95% 이상)")
        
        return {
            'total': len(file_data),
            'matched': matched_count,
            'passed': passed_count,
            'failed': failed_count,
            'overall_pass': overall_pass,
            'fail_reasons': fail_reasons,
            'pass_rate': (passed_count / matched_count * 100) if matched_count > 0 else 0,
            'severity_summary': severity_counts,
            'results': results
        }