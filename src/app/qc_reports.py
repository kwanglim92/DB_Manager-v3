# 간소화된 QC 검수 보고서 생성 모듈

import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd


def export_qc_results_to_excel(qc_results: List[Dict], equipment_name: str, 
                              equipment_type: str, file_path: str) -> bool:
    """QC 검수 결과를 Excel 파일로 내보내기"""
    try:
        # 검수 결과 데이터프레임 생성
        results_data = []
        for result in qc_results:
            results_data.append({
                '파라미터': result.get('parameter', ''),
                '문제 유형': result.get('issue_type', ''),
                '상세 설명': result.get('description', ''),
                '심각도': result.get('severity', ''),
                '카테고리': result.get('category', ''),
                '권장사항': result.get('recommendation', '')
            })
        
        results_df = pd.DataFrame(results_data)
        
        # 검수 요약 정보
        summary_data = {
            '항목': [
                '검수 일시',
                '장비명', 
                '장비 유형',
                '총 이슈 수',
                '높은 심각도',
                '중간 심각도', 
                '낮은 심각도'
            ],
            '값': [
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                equipment_name,
                equipment_type,
                len(qc_results),
                len([r for r in qc_results if r.get('severity') == '높음']),
                len([r for r in qc_results if r.get('severity') == '중간']),
                len([r for r in qc_results if r.get('severity') == '낮음'])
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        
        # Excel 파일 생성
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # 검수 요약 시트
            summary_df.to_excel(writer, sheet_name='검수 요약', index=False)
            
            # 검수 결과 시트
            if results_df.empty:
                # 이슈가 없는 경우
                no_issues_df = pd.DataFrame({
                    '결과': ['✅ 검수 완료 - 발견된 이슈가 없습니다.']
                })
                no_issues_df.to_excel(writer, sheet_name='검수 결과', index=False)
            else:
                results_df.to_excel(writer, sheet_name='검수 결과', index=False)
        
        return True
        
    except Exception as e:
        print(f"Excel 보고서 생성 오류: {e}")
        return False


def export_qc_results_to_csv(qc_results: List[Dict], equipment_name: str,
                            equipment_type: str, file_path: str) -> bool:
    """QC 검수 결과를 CSV 파일로 내보내기"""
    try:
        # 검수 결과 데이터프레임 생성
        results_data = []
        for result in qc_results:
            results_data.append({
                '파라미터': result.get('parameter', ''),
                '문제 유형': result.get('issue_type', ''),
                '상세 설명': result.get('description', ''),
                '심각도': result.get('severity', ''),
                '카테고리': result.get('category', ''),
                '권장사항': result.get('recommendation', '')
            })

        results_df = pd.DataFrame(results_data)

        # CSV 파일 생성
        results_df.to_csv(file_path, index=False, encoding='utf-8-sig')

        return True

    except Exception as e:
        print(f"CSV 보고서 생성 오류: {e}")
        return False


def export_full_qc_report_to_excel(qc_result: Dict[str, Any], equipment_name: str,
                                   equipment_type: str, file_path: str) -> bool:
    """
    Phase 1.5: 전체 QC 검수 결과를 Excel 파일로 내보내기
    (기본 QC 검사 + Check list 검증 결과 포함)

    Args:
        qc_result: perform_qc_check() 결과 전체
        equipment_name: 장비명
        equipment_type: 장비 유형
        file_path: 저장 경로

    Returns:
        bool: 성공 여부
    """
    try:
        # 1. 검수 요약 정보
        summary = qc_result.get('summary', {})
        summary_data = {
            '항목': [
                '검수 일시',
                '장비명',
                '장비 유형',
                '검수 모드',
                '전체 상태',
                '',
                '[기본 QC 검사]',
                '총 이슈 수',
                '높은 심각도',
                '중간 심각도',
                '낮은 심각도'
            ],
            '값': [
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                equipment_name,
                equipment_type,
                qc_result.get('mode', 'comprehensive'),
                summary.get('overall_status', 'UNKNOWN'),
                '',
                '',
                summary.get('total_issues', 0),
                summary.get('high_severity', 0),
                summary.get('medium_severity', 0),
                summary.get('low_severity', 0)
            ]
        }

        # Check list 검증 결과가 있으면 추가
        checklist_validation = qc_result.get('checklist_validation')
        if checklist_validation:
            summary_data['항목'].extend([
                '',
                '[Check list 검증]',
                '검증 상태',
                '검증 항목',
                '통과 항목',
                '실패 항목'
            ])
            summary_data['값'].extend([
                '',
                '',
                '✅ 통과' if checklist_validation.get('qc_passed', True) else '❌ 실패',
                checklist_validation.get('checklist_params', 0),
                checklist_validation.get('passed', 0),
                checklist_validation.get('failed', 0)
            ])

            # 예외 적용 정보
            exception_count = checklist_validation.get('exception_count', 0)
            if exception_count > 0:
                summary_data['항목'].append('예외 적용')
                summary_data['값'].append(exception_count)

        summary_df = pd.DataFrame(summary_data)

        # 2. 기본 QC 검사 결과
        qc_results = qc_result.get('detailed_results', [])
        qc_results_data = []
        for result in qc_results:
            qc_results_data.append({
                '파라미터': result.get('parameter', ''),
                '문제 유형': result.get('issue_type', ''),
                '상세 설명': result.get('description', ''),
                '심각도': result.get('severity', ''),
                '카테고리': result.get('category', ''),
                '권장사항': result.get('recommendation', '')
            })

        qc_results_df = pd.DataFrame(qc_results_data) if qc_results_data else pd.DataFrame({
            '결과': ['✅ 발견된 이슈가 없습니다.']
        })

        # 3. Check list 검증 결과 (Phase 1.5: Pass/Fail만, 심각도 없음)
        checklist_df = None
        if checklist_validation:
            checklist_results = checklist_validation.get('results', [])
            checklist_data = []
            for result in checklist_results:
                checklist_data.append({
                    'Result': '✅ Pass' if result.get('is_valid', False) else '❌ Fail',
                    'ItemName': result.get('item_name', ''),
                    'Value': result.get('value', ''),
                    'Expected': result.get('expected', ''),
                    'Category': result.get('category', ''),
                    'Reason': result.get('reason', '')
                })

            checklist_df = pd.DataFrame(checklist_data) if checklist_data else pd.DataFrame({
                '결과': ['✅ 검증된 Check list 항목이 없습니다.']
            })

        # 4. 권장사항
        recommendations = qc_result.get('recommendations', [])
        recommendations_df = pd.DataFrame({
            '권장사항': recommendations
        }) if recommendations else pd.DataFrame({
            '권장사항': ['권장사항이 없습니다.']
        })

        # Excel 파일 생성
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # 검수 요약 시트
            summary_df.to_excel(writer, sheet_name='검수 요약', index=False)

            # 기본 QC 검사 결과 시트
            qc_results_df.to_excel(writer, sheet_name='기본 QC 검사', index=False)

            # Check list 검증 결과 시트 (Phase 1.5)
            if checklist_df is not None:
                checklist_df.to_excel(writer, sheet_name='Check list 검증', index=False)

            # 권장사항 시트
            recommendations_df.to_excel(writer, sheet_name='권장사항', index=False)

        return True

    except Exception as e:
        print(f"전체 QC 보고서 생성 오류: {e}")
        import traceback
        traceback.print_exc()
        return False