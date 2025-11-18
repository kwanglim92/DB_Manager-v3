"""
Report Service - QC 검수 보고서 생성 서비스

기존 qc_reports.py 기능을 Services Layer로 통합
"""

import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd


class ReportService:
    """QC 검수 보고서 생성 서비스"""

    def __init__(self):
        """초기화"""
        pass

    def export_to_excel(
        self,
        inspection_result: Dict[str, Any],
        file_path: str,
        equipment_name: str = '',
        equipment_type: str = '',
        configuration_name: str = ''
    ) -> bool:
        """
        QC 검수 결과를 Excel 파일로 내보내기

        Args:
            inspection_result: QCService.run_inspection() 결과
            file_path: 저장 경로
            equipment_name: 장비명
            equipment_type: 장비 유형
            configuration_name: Configuration 명

        Returns:
            bool: 성공 여부
        """
        try:
            # 1. 검수 요약 정보
            summary_data = {
                '항목': [
                    '검수 일시',
                    '장비명',
                    '장비 유형',
                    'Configuration',
                    '검수 상태',
                    '',
                    '전체 항목',
                    '통과 항목',
                    '실패 항목',
                    '통과율',
                    '매칭된 항목',
                    '예외 처리'
                ],
                '값': [
                    inspection_result.get('timestamp', datetime.now().isoformat()),
                    equipment_name,
                    equipment_type,
                    configuration_name or 'Type Common',
                    '✅ PASS' if inspection_result.get('is_pass') else '❌ FAIL',
                    '',
                    inspection_result.get('total_count', 0),
                    inspection_result.get('passed_count', 0),
                    inspection_result.get('failed_count', 0),
                    f"{(inspection_result.get('passed_count', 0) / inspection_result.get('total_count', 1) * 100):.1f}%",
                    inspection_result.get('matched_count', 0),
                    inspection_result.get('exception_count', 0)
                ]
            }
            summary_df = pd.DataFrame(summary_data)

            # 2. 검수 결과 상세
            results = inspection_result.get('results', [])
            results_data = []

            for result in results:
                results_data.append({
                    'Result': '✅ Pass' if result.get('is_valid') else '❌ Fail',
                    'Display Name': result.get('display_name', ''),
                    'Item Name': result.get('item_name', ''),
                    'Module': result.get('module', ''),
                    'Part': result.get('part', ''),
                    'Value': result.get('file_value', ''),
                    'Spec': result.get('spec', ''),
                    'Category': result.get('category', ''),
                    'Description': result.get('description', '')
                })

            if results_data:
                results_df = pd.DataFrame(results_data)
            else:
                results_df = pd.DataFrame({
                    '결과': ['검수된 항목이 없습니다.']
                })

            # 3. 실패 항목만 필터링
            failed_results = [r for r in results if not r.get('is_valid')]
            if failed_results:
                failed_data = []
                for result in failed_results:
                    failed_data.append({
                        'Display Name': result.get('display_name', ''),
                        'Value': result.get('file_value', ''),
                        'Spec': result.get('spec', ''),
                        'Category': result.get('category', ''),
                        'Description': result.get('description', '')
                    })
                failed_df = pd.DataFrame(failed_data)
            else:
                failed_df = pd.DataFrame({
                    '결과': ['✅ 실패 항목이 없습니다.']
                })

            # 4. 카테고리별 통계
            category_stats = {}
            for result in results:
                category = result.get('category', 'Uncategorized')
                if category not in category_stats:
                    category_stats[category] = {'passed': 0, 'failed': 0, 'total': 0}

                category_stats[category]['total'] += 1
                if result.get('is_valid'):
                    category_stats[category]['passed'] += 1
                else:
                    category_stats[category]['failed'] += 1

            category_data = []
            for category, stats in category_stats.items():
                pass_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
                category_data.append({
                    'Category': category,
                    'Total': stats['total'],
                    'Passed': stats['passed'],
                    'Failed': stats['failed'],
                    'Pass Rate': f"{pass_rate:.1f}%"
                })

            if category_data:
                category_df = pd.DataFrame(category_data)
            else:
                category_df = pd.DataFrame({'결과': ['카테고리 정보가 없습니다.']})

            # Excel 파일 생성
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                summary_df.to_excel(writer, sheet_name='검수 요약', index=False)
                results_df.to_excel(writer, sheet_name='검수 결과', index=False)
                failed_df.to_excel(writer, sheet_name='실패 항목', index=False)
                category_df.to_excel(writer, sheet_name='카테고리별 통계', index=False)

            return True

        except Exception as e:
            print(f"Excel 보고서 생성 오류: {e}")
            import traceback
            traceback.print_exc()
            return False

    def export_to_csv(
        self,
        inspection_result: Dict[str, Any],
        file_path: str
    ) -> bool:
        """
        QC 검수 결과를 CSV 파일로 내보내기

        Args:
            inspection_result: QCService.run_inspection() 결과
            file_path: 저장 경로

        Returns:
            bool: 성공 여부
        """
        try:
            results = inspection_result.get('results', [])
            results_data = []

            for result in results:
                results_data.append({
                    'Result': 'Pass' if result.get('is_valid') else 'Fail',
                    'Display Name': result.get('display_name', ''),
                    'Item Name': result.get('item_name', ''),
                    'Module': result.get('module', ''),
                    'Part': result.get('part', ''),
                    'Value': result.get('file_value', ''),
                    'Spec': result.get('spec', ''),
                    'Category': result.get('category', ''),
                    'Description': result.get('description', '')
                })

            if results_data:
                results_df = pd.DataFrame(results_data)
                results_df.to_csv(file_path, index=False, encoding='utf-8-sig')
                return True
            else:
                # 빈 결과
                pd.DataFrame({'결과': ['검수된 항목이 없습니다.']}).to_csv(
                    file_path, index=False, encoding='utf-8-sig'
                )
                return True

        except Exception as e:
            print(f"CSV 보고서 생성 오류: {e}")
            return False

    def generate_summary_report(
        self,
        inspection_result: Dict[str, Any]
    ) -> str:
        """
        검수 결과 요약 텍스트 생성

        Args:
            inspection_result: QCService.run_inspection() 결과

        Returns:
            str: 요약 보고서 텍스트
        """
        is_pass = inspection_result.get('is_pass', False)
        total = inspection_result.get('total_count', 0)
        passed = inspection_result.get('passed_count', 0)
        failed = inspection_result.get('failed_count', 0)
        matched = inspection_result.get('matched_count', 0)
        exception_count = inspection_result.get('exception_count', 0)

        status = "✅ PASS" if is_pass else "❌ FAIL"
        pass_rate = (passed / total * 100) if total > 0 else 0

        report = f"""
QC Inspection Summary Report
{'=' * 50}

Status: {status}

검수 결과:
  - 전체 항목: {total}
  - 통과: {passed} ({pass_rate:.1f}%)
  - 실패: {failed}
  - 매칭: {matched}
  - 예외 처리: {exception_count}

"""

        # 실패 항목이 있으면 나열
        if failed > 0:
            report += "실패 항목:\n"
            for i, result in enumerate(inspection_result.get('results', []), 1):
                if not result.get('is_valid'):
                    report += f"  {i}. {result.get('display_name', 'N/A')}\n"
                    report += f"     Value: {result.get('file_value', 'N/A')}, Spec: {result.get('spec', 'N/A')}\n"

        report += f"\n{'=' * 50}\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

        return report
