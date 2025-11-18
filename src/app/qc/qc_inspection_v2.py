"""
QC Inspection v2 - ItemName 기반 자동 매칭 검수 시스템

Phase 1.5 Week 3 구현:
- ItemName 기반 자동 매칭 (Configuration별 매핑 제거)
- Equipment_Checklist_Exceptions 적용
- Pass/Fail 판정 (심각도 없음, 모든 항목 동일 중요도)

Author: Phase 1.5 Week 3
Date: 2025-11-13
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class ChecklistItem:
    """Check list 항목 데이터 클래스"""
    id: int
    item_name: str
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
            SELECT id, item_name, spec_min, spec_max, expected_value,
                   category, description, is_active
            FROM QC_Checklist_Items
            WHERE is_active = 1
            ORDER BY item_name
        """)

        rows = cursor.fetchall()

        return [
            ChecklistItem(
                id=row[0],
                item_name=row[1],
                spec_min=row[2],
                spec_max=row[3],
                expected_value=row[4],
                category=row[5],
                description=row[6],
                is_active=bool(row[7])
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
    ItemName 기반 자동 매칭 QC 검수 (Phase 1.5 신규 시스템)

    특징:
    - ItemName 기반 자동 매칭 (Configuration별 매핑 제거)
    - Equipment_Checklist_Exceptions 적용
    - Pass/Fail 판정 (심각도 없음, 모든 항목 동일 중요도)

    Args:
        file_data: 파일 데이터 (ItemName → Value 매핑)
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
    # 1. 파일에서 ItemName 추출
    file_item_names = set(file_data.keys())

    # 2. QC_Checklist_Items 마스터에서 활성 항목 조회
    all_checklist_items = get_active_checklist_items()

    # 3. ItemName 매칭 (파일에 있는 항목만)
    matched_items = [
        item for item in all_checklist_items
        if item.item_name in file_item_names
    ]

    # 4. Configuration 예외 제거
    exception_item_ids = get_exception_item_ids(configuration_id)
    checklist_items = [
        item for item in matched_items
        if item.id not in exception_item_ids
    ]

    # 5. 각 항목 검증 (Pass/Fail만)
    results = []
    for item in checklist_items:
        file_value = file_data[item.item_name]
        is_valid = validate_item(item, file_value)

        results.append({
            'item_name': item.item_name,
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
