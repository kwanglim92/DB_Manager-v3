"""
QC Inspection v2 - Module.Part.ItemName 복합 키 기반 자동 매칭 검수 시스템

Phase 2 구현:
- Module.Part.ItemName 복합 키 기반 자동 매칭
- Equipment_Checklist_Exceptions 적용
- Pass/Fail 판정 (심각도 없음, 모든 항목 동일 중요도)

Phase 1.5 Week 3 구현:
- ItemName 기반 자동 매칭 (Configuration별 매핑 제거)
- Equipment_Checklist_Exceptions 적용
- Pass/Fail 판정 (심각도 없음, 모든 항목 동일 중요도)

Author: Phase 2
Date: 2025-11-18
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class ChecklistItem:
    """Check list 항목 데이터 클래스"""
    id: int
    item_name: str
    module: Optional[str]
    part: Optional[str]
    spec_min: Optional[str]
    spec_max: Optional[str]
    expected_value: Optional[str]
    category: Optional[str]
    description: Optional[str]
    is_active: bool


def get_active_checklist_items() -> List[ChecklistItem]:
    """
    활성화된 QC Checklist 항목 조회

    Returns:
        List[ChecklistItem]: 활성화된 Check list 항목 목록
    """
    from db_schema import DBSchema

    db_schema = DBSchema()

    with db_schema.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, item_name, module, part, spec_min, spec_max, expected_value,
                   category, description, is_active
            FROM QC_Checklist_Items
            WHERE is_active = 1
            ORDER BY module, part, item_name
        """)

        rows = cursor.fetchall()

        return [
            ChecklistItem(
                id=row[0],
                item_name=row[1],
                module=row[2],
                part=row[3],
                spec_min=row[4],
                spec_max=row[5],
                expected_value=row[6],
                category=row[7],
                description=row[8],
                is_active=bool(row[9])
            )
            for row in rows
        ]


def get_exception_item_ids(configuration_id: Optional[int]) -> List[int]:
    """
    Configuration별 예외 항목 ID 목록 조회

    Args:
        configuration_id: Configuration ID (None이면 빈 목록 반환)

    Returns:
        List[int]: 예외 항목 ID 목록
    """
    if configuration_id is None:
        return []

    from db_schema import DBSchema

    db_schema = DBSchema()

    with db_schema.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT checklist_item_id
            FROM Equipment_Checklist_Exceptions
            WHERE configuration_id = ?
        """, (configuration_id,))

        rows = cursor.fetchall()
        return [row[0] for row in rows]


def validate_item(item: ChecklistItem, file_value: Any) -> bool:
    """
    단일 Check list 항목 검증

    Args:
        item: Check list 항목
        file_value: 파일의 실제 값

    Returns:
        bool: 검증 성공 여부
    """
    # Spec 범위 검증
    if item.spec_min and item.spec_max:
        try:
            val = float(file_value)
            return float(item.spec_min) <= val <= float(item.spec_max)
        except (ValueError, TypeError):
            return False

    # Expected Value 검증 (Pass/Fail, Enum 등)
    elif item.expected_value:
        # JSON 파싱 시도 (Enum: ["Pass", "Fail"] 등)
        try:
            allowed_values = json.loads(item.expected_value)
            if isinstance(allowed_values, list):
                return str(file_value) in [str(v) for v in allowed_values]
        except (json.JSONDecodeError, TypeError):
            pass

        # 단순 문자열 비교 (대소문자 무시)
        return str(file_value).upper() == str(item.expected_value).upper()

    # Spec 없음 (항목 존재만 확인)
    else:
        return True


def get_spec_display(item: ChecklistItem) -> str:
    """
    Spec 표시 문자열 생성

    Args:
        item: Check list 항목

    Returns:
        str: Spec 표시 문자열 ("0.5 ~ 2.0", "Pass", "N/A" 등)
    """
    if item.spec_min and item.spec_max:
        return f"{item.spec_min} ~ {item.spec_max}"
    elif item.expected_value:
        # JSON인 경우 파싱하여 보기 좋게 표시
        try:
            allowed_values = json.loads(item.expected_value)
            if isinstance(allowed_values, list):
                return " / ".join(str(v) for v in allowed_values)
        except (json.JSONDecodeError, TypeError):
            pass
        return item.expected_value
    else:
        return "N/A"


def qc_inspection_v2(file_data: Dict[str, Any], configuration_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Module.Part.ItemName 복합 키 기반 자동 매칭 QC 검수 (Phase 2)

    특징:
    - Module.Part.ItemName 복합 키 기반 자동 매칭
    - 레거시 호환성: ItemName만으로도 매칭 가능 (module, part가 NULL인 Type Common 항목)
    - Equipment_Checklist_Exceptions 적용
    - Pass/Fail 판정 (심각도 없음, 모든 항목 동일 중요도)

    Args:
        file_data: 파일 데이터
            - 옵션 1: ItemName → Value 매핑 (레거시)
            - 옵션 2: (Module, Part, ItemName) → Value 매핑 (신규)
        configuration_id: Configuration ID (None이면 Type Common)

    Returns:
        Dict[str, Any]: 검수 결과
            {
                'is_pass': bool,           # 전체 합격 여부 (모든 항목 Pass)
                'total_count': int,        # 검증된 항목 수
                'failed_count': int,       # 실패한 항목 수
                'results': List[Dict]      # 각 항목 검증 결과
            }
    """
    # 1. 파일 데이터 파싱 (복합 키 또는 단순 키)
    file_keys = set()
    file_values_map = {}

    for key, value in file_data.items():
        if isinstance(key, tuple) and len(key) == 3:
            # (Module, Part, ItemName) 복합 키
            file_keys.add(key)
            file_values_map[key] = value
        else:
            # ItemName 단순 키 (레거시)
            simple_key = (None, None, str(key))
            file_keys.add(simple_key)
            file_values_map[simple_key] = value

    # 2. QC_Checklist_Items 마스터에서 활성 항목 조회
    all_checklist_items = get_active_checklist_items()

    # 3. 복합 키 매칭 (우선순위: Module.Part.ItemName > ItemName)
    matched_items = []
    for item in all_checklist_items:
        item_key = (item.module, item.part, item.item_name)

        # 우선순위 1: 정확한 복합 키 매칭
        if item_key in file_keys:
            matched_items.append((item, item_key))
            continue

        # 우선순위 2: module, part가 NULL이면 ItemName만 매칭 (Type Common)
        if item.module is None and item.part is None:
            for fkey in file_keys:
                if fkey[2] == item.item_name:  # ItemName만 비교
                    matched_items.append((item, fkey))
                    break

    # 4. Configuration 예외 제거
    exception_item_ids = get_exception_item_ids(configuration_id)
    checklist_items = [
        (item, fkey) for item, fkey in matched_items
        if item.id not in exception_item_ids
    ]

    # 5. 각 항목 검증 (Pass/Fail만)
    results = []
    for item, fkey in checklist_items:
        file_value = file_values_map[fkey]
        is_valid = validate_item(item, file_value)

        # Module/Part 표시 (있으면)
        display_name = item.item_name
        if item.module or item.part:
            parts = []
            if item.module:
                parts.append(item.module)
            if item.part:
                parts.append(item.part)
            display_name = f"{'.'.join(parts)}.{item.item_name}"

        results.append({
            'item_name': item.item_name,
            'module': item.module,
            'part': item.part,
            'display_name': display_name,
            'file_value': file_value,
            'is_valid': is_valid,
            'spec': get_spec_display(item),
            'category': item.category or 'Uncategorized',
            'description': item.description or ''
        })

    # 6. 전체 Pass/Fail 판정 (심각도 없음, 모든 항목 동일 중요도)
    # 모든 항목이 Pass일 때만 전체 Pass
    failed_items = [r for r in results if not r['is_valid']]
    is_pass = len(failed_items) == 0

    return {
        'is_pass': is_pass,
        'total_count': len(results),
        'failed_count': len(failed_items),
        'results': results,
        'matched_count': len(matched_items),  # 매칭된 항목 수 (예외 포함)
        'exception_count': len(exception_item_ids)  # 예외 처리된 항목 수
    }


def get_inspection_summary(result: Dict[str, Any]) -> str:
    """
    검수 결과 요약 문자열 생성

    Args:
        result: qc_inspection_v2() 결과

    Returns:
        str: 요약 문자열
    """
    is_pass = result['is_pass']
    total = result['total_count']
    failed = result['failed_count']
    passed = total - failed

    status = "PASS" if is_pass else "FAIL"

    summary = f"QC Inspection Result: {status}\n"
    summary += f"Total Items: {total}\n"
    summary += f"Passed: {passed} ({passed/total*100:.1f}%)\n" if total > 0 else "Passed: 0\n"
    summary += f"Failed: {failed} ({failed/total*100:.1f}%)\n" if total > 0 else "Failed: 0\n"

    if result.get('exception_count', 0) > 0:
        summary += f"Exceptions Applied: {result['exception_count']}\n"

    return summary


# 레거시 호환성을 위한 Alias (향후 제거 예정)
def perform_qc_inspection_v2(file_data: Dict[str, Any], configuration_id: Optional[int] = None) -> Dict[str, Any]:
    """
    qc_inspection_v2() 별칭 (레거시 호환성)
    """
    return qc_inspection_v2(file_data, configuration_id)
