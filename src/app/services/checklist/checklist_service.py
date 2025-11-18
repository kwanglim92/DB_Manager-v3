"""
Check list 관리 서비스 구현
"""

import re
import json
from typing import List, Dict, Optional, Tuple

from ..interfaces.checklist_service_interface import IChecklistService


class ChecklistService(IChecklistService):
    """Check list 관리 서비스"""

    def __init__(self, db_schema, cache_service=None):
        """
        Args:
            db_schema: DBSchema 인스턴스
            cache_service: CacheService 인스턴스 (선택)
        """
        self.db_schema = db_schema
        self.cache = cache_service

    def add_checklist_item(self, item_name: str, parameter_pattern: str,
                          is_common: bool = True, severity_level: str = 'MEDIUM',
                          validation_rule: Optional[str] = None,
                          description: str = "") -> Optional[int]:
        """새 Check list 항목 추가"""
        # 심각도 레벨 검증
        valid_levels = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
        if severity_level not in valid_levels:
            raise ValueError(f"severity_level은 {valid_levels} 중 하나여야 합니다")

        # validation_rule이 JSON 형식인지 검증
        if validation_rule:
            try:
                json.loads(validation_rule)
            except json.JSONDecodeError:
                raise ValueError("validation_rule은 유효한 JSON 형식이어야 합니다")

        result = self.db_schema.add_checklist_item(
            item_name=item_name,
            parameter_pattern=parameter_pattern,
            is_common=is_common,
            severity_level=severity_level,
            validation_rule=validation_rule,
            description=description
        )

        # 캐시 무효화
        if self.cache:
            self.cache.invalidate_pattern('checklist_*')

        return result

    def get_common_checklist_items(self) -> List[Tuple]:
        """공통 Check list 항목 조회"""
        cache_key = 'checklist_common_items'

        # 캐시 조회
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        # DB 조회
        result = self.db_schema.get_checklist_items(common_only=True)

        # 캐시 저장
        if self.cache:
            self.cache.set(cache_key, result, ttl_seconds=300)

        return result

    def get_equipment_checklist(self, equipment_type_id: int) -> List[Dict]:
        """장비별 적용되는 Check list 조회"""
        cache_key = f'checklist_equipment_{equipment_type_id}'

        # 캐시 조회
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        # DB 조회
        raw_data = self.db_schema.get_equipment_checklist_items(equipment_type_id)

        # 딕셔너리 형태로 변환
        result = []
        for row in raw_data:
            result.append({
                'id': row[0],
                'item_name': row[1],
                'parameter_pattern': row[2],
                'is_common': row[3],
                'severity_level': row[4],
                'validation_rule': row[5],
                'description': row[6],
                'is_required': row[7],
                'custom_validation_rule': row[8],
                'priority': row[9],
                'source': row[10]  # 'COMMON' or 'SPECIFIC'
            })

        # 심각도 순서 정렬
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        result.sort(key=lambda x: (severity_order.get(x['severity_level'], 999), x['item_name']))

        # 캐시 저장
        if self.cache:
            self.cache.set(cache_key, result, ttl_seconds=300)

        return result

    def add_equipment_specific_checklist(self, equipment_type_id: int,
                                        checklist_item_id: int,
                                        is_required: bool = True,
                                        custom_validation_rule: Optional[str] = None,
                                        priority: int = 100,
                                        added_reason: str = "",
                                        added_by: str = "") -> Optional[int]:
        """장비별 Check list 항목 추가"""
        # custom_validation_rule이 JSON 형식인지 검증
        if custom_validation_rule:
            try:
                json.loads(custom_validation_rule)
            except json.JSONDecodeError:
                raise ValueError("custom_validation_rule은 유효한 JSON 형식이어야 합니다")

        result = self.db_schema.add_equipment_checklist_mapping(
            equipment_type_id=equipment_type_id,
            checklist_item_id=checklist_item_id,
            is_required=is_required,
            custom_validation_rule=custom_validation_rule,
            priority=priority,
            added_reason=added_reason,
            added_by=added_by
        )

        # 캐시 무효화
        if self.cache:
            self.cache.invalidate_pattern(f'checklist_equipment_{equipment_type_id}')

        return result

    def add_checklist_exception(self, equipment_type_id: int,
                               checklist_item_id: int,
                               reason: str,
                               approved_by: str = "") -> Optional[int]:
        """장비별 Check list 예외 추가"""
        if not reason:
            raise ValueError("예외 사유는 필수입니다")

        result = self.db_schema.add_checklist_exception(
            equipment_type_id=equipment_type_id,
            checklist_item_id=checklist_item_id,
            reason=reason,
            approved_by=approved_by
        )

        # 캐시 무효화
        if self.cache:
            self.cache.invalidate_pattern(f'checklist_equipment_{equipment_type_id}')

        return result

    def get_audit_log(self, limit: int = 100) -> List[Tuple]:
        """Check list 변경 이력 조회"""
        return self.db_schema.get_checklist_audit_log(limit=limit)

    def validate_parameter_against_checklist(self, equipment_type_id: int,
                                            parameter_name: str,
                                            parameter_value: str) -> Dict:
        """파라미터가 Check list에 포함되는지 검증"""
        # 장비별 Check list 조회
        checklist_items = self.get_equipment_checklist(equipment_type_id)

        # 파라미터 이름이 Check list 패턴과 매칭되는지 확인
        for item in checklist_items:
            pattern = item['parameter_pattern']
            try:
                if re.search(pattern, parameter_name, re.IGNORECASE):
                    # Check list에 포함됨
                    result = {
                        'is_checklist': True,
                        'severity_level': item['severity_level'],
                        'item_name': item['item_name'],
                        'validation_passed': True,
                        'message': ''
                    }

                    # 검증 규칙이 있으면 적용
                    validation_rule = item.get('custom_validation_rule') or item.get('validation_rule')
                    if validation_rule:
                        validation_result = self._apply_validation_rule(
                            parameter_name, parameter_value, validation_rule
                        )
                        result['validation_passed'] = validation_result['passed']
                        result['message'] = validation_result['message']

                    return result

            except re.error as e:
                print(f"정규식 오류: {pattern} - {e}")
                continue

        # Check list에 없음
        return {
            'is_checklist': False,
            'severity_level': None,
            'validation_passed': True,
            'message': ''
        }

    def _apply_validation_rule(self, parameter_name: str, parameter_value: str,
                              validation_rule: str) -> Dict:
        """
        검증 규칙 적용

        validation_rule JSON 형식:
        {
            "type": "range" | "pattern" | "enum",
            "min": float,
            "max": float,
            "pattern": str,
            "values": [str, ...]
        }
        """
        try:
            rule = json.loads(validation_rule)
            rule_type = rule.get('type')

            if rule_type == 'range':
                # 범위 검증
                try:
                    value = float(parameter_value)
                    min_val = rule.get('min')
                    max_val = rule.get('max')

                    if min_val is not None and value < min_val:
                        return {
                            'passed': False,
                            'message': f"값이 최소값({min_val})보다 작습니다"
                        }

                    if max_val is not None and value > max_val:
                        return {
                            'passed': False,
                            'message': f"값이 최대값({max_val})보다 큽니다"
                        }

                except ValueError:
                    return {
                        'passed': False,
                        'message': "숫자 형식이 아닙니다"
                    }

            elif rule_type == 'pattern':
                # 패턴 검증
                pattern = rule.get('pattern')
                if pattern and not re.match(pattern, parameter_value):
                    return {
                        'passed': False,
                        'message': f"패턴({pattern})과 일치하지 않습니다"
                    }

            elif rule_type == 'enum':
                # 열거형 검증
                values = rule.get('values', [])
                if parameter_value not in values:
                    return {
                        'passed': False,
                        'message': f"허용된 값({', '.join(values)}) 중 하나가 아닙니다"
                    }

            return {'passed': True, 'message': ''}

        except json.JSONDecodeError:
            return {'passed': True, 'message': '검증 규칙 파싱 실패'}
        except Exception as e:
            return {'passed': True, 'message': f'검증 오류: {str(e)}'}
