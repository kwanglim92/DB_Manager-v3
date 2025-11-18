#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 1 성능 테스트

대용량 데이터에 대한 Check list 검증 성능을 테스트합니다.
"""

import sys
import os
import io
import time
import pandas as pd

# Windows 콘솔 인코딩 문제 해결
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 프로젝트 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from app.schema import DBSchema
from app.services import ServiceFactory
from app.qc.checklist_validator import ChecklistValidator


class Phase1PerformanceTest:
    """Phase 1 성능 테스트"""

    def __init__(self):
        self.db_schema = DBSchema()
        self.service_factory = ServiceFactory(self.db_schema)
        self.checklist_service = self.service_factory.get_checklist_service()
        self.results = []

    def log(self, message):
        """로그 출력"""
        print(f">> {message}")

    def measure_time(self, func, *args, **kwargs):
        """함수 실행 시간 측정"""
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        return result, elapsed

    def test_checklist_service_performance(self):
        """Check list 서비스 성능 테스트"""
        self.log("\n[테스트 1] Check list 서비스 조회 성능")

        # 1. 공통 Check list 조회 (캐시 없이)
        self.checklist_service.cache.clear()
        _, elapsed1 = self.measure_time(self.checklist_service.get_common_checklist_items)
        self.log(f"  - 공통 Check list 조회 (캐시 없음): {elapsed1*1000:.2f} ms")

        # 2. 공통 Check list 조회 (캐시 있음)
        _, elapsed2 = self.measure_time(self.checklist_service.get_common_checklist_items)
        self.log(f"  - 공통 Check list 조회 (캐시 있음): {elapsed2*1000:.2f} ms")

        speedup = elapsed1 / elapsed2 if elapsed2 > 0 else 0
        self.log(f"  - 캐시 성능 향상: {speedup:.1f}배")

        self.results.append({
            'test': 'Checklist Service',
            'operation': '공통 Check list 조회',
            'without_cache_ms': elapsed1 * 1000,
            'with_cache_ms': elapsed2 * 1000,
            'speedup': speedup
        })

    def test_validator_performance_small(self):
        """Check list 검증 성능 - 소규모 (100개 파라미터)"""
        self.log("\n[테스트 2] Check list 검증 성능 - 소규모 (100개)")

        # 테스트용 데이터프레임 생성
        data = {
            'ItemName': [f'param_{i}' for i in range(100)],
            'Value1': [str(i * 10) for i in range(100)]
        }
        df = pd.DataFrame(data)

        # 장비 유형
        equipment_types = self.db_schema.get_equipment_types()
        if not equipment_types:
            self.log("  - SKIP: 장비 유형 없음")
            return

        equipment_type_id = equipment_types[0][0]

        # 검증 실행
        validator = ChecklistValidator(self.checklist_service, equipment_type_id)
        result, elapsed = self.measure_time(validator.validate_parameters, df)

        self.log(f"  - 검증 시간: {elapsed*1000:.2f} ms")
        self.log(f"  - 처리량: {len(df)/elapsed:.0f} 파라미터/초")
        self.log(f"  - Check list 매칭: {result['checklist_params']}개")

        self.results.append({
            'test': 'Validator - Small',
            'parameters': 100,
            'time_ms': elapsed * 1000,
            'throughput': len(df) / elapsed,
            'matched': result['checklist_params']
        })

    def test_validator_performance_medium(self):
        """Check list 검증 성능 - 중규모 (1000개 파라미터)"""
        self.log("\n[테스트 3] Check list 검증 성능 - 중규모 (1000개)")

        # 테스트용 데이터프레임 생성
        data = {
            'ItemName': [f'param_{i}' for i in range(1000)],
            'Value1': [str(i * 10) for i in range(1000)]
        }
        df = pd.DataFrame(data)

        # 장비 유형
        equipment_types = self.db_schema.get_equipment_types()
        equipment_type_id = equipment_types[0][0]

        # 검증 실행
        validator = ChecklistValidator(self.checklist_service, equipment_type_id)
        result, elapsed = self.measure_time(validator.validate_parameters, df)

        self.log(f"  - 검증 시간: {elapsed*1000:.2f} ms")
        self.log(f"  - 처리량: {len(df)/elapsed:.0f} 파라미터/초")
        self.log(f"  - Check list 매칭: {result['checklist_params']}개")

        self.results.append({
            'test': 'Validator - Medium',
            'parameters': 1000,
            'time_ms': elapsed * 1000,
            'throughput': len(df) / elapsed,
            'matched': result['checklist_params']
        })

    def test_validator_performance_large(self):
        """Check list 검증 성능 - 대규모 (실제 Default DB 크기)"""
        self.log("\n[테스트 4] Check list 검증 성능 - 대규모 (실제 데이터)")

        # 장비 유형
        equipment_types = self.db_schema.get_equipment_types()
        equipment_type_id = equipment_types[0][0]

        # 실제 Default DB 데이터 로드
        data = self.db_schema.get_default_values(equipment_type_id)
        if not data:
            self.log("  - SKIP: Default DB 데이터 없음")
            return

        df = pd.DataFrame(data, columns=[
            "id", "parameter_name", "default_value", "min_spec", "max_spec", "type_name",
            "occurrence_count", "total_files", "confidence_score", "source_files", "description",
            "module_name", "part_name", "item_type", "is_checklist"
        ])

        # ItemName 컬럼 생성
        df['ItemName'] = df['parameter_name']
        df['Value1'] = df['default_value']

        # 검증 실행
        validator = ChecklistValidator(self.checklist_service, equipment_type_id)
        result, elapsed = self.measure_time(validator.validate_parameters, df)

        self.log(f"  - 검증 시간: {elapsed*1000:.2f} ms ({elapsed:.2f}초)")
        self.log(f"  - 총 파라미터: {len(df)}개")
        self.log(f"  - 처리량: {len(df)/elapsed:.0f} 파라미터/초")
        self.log(f"  - Check list 매칭: {result['checklist_params']}개")
        self.log(f"  - 검증 통과: {result['validated_params']}개")
        self.log(f"  - 검증 실패: {result['failed_params']}개")

        self.results.append({
            'test': 'Validator - Large',
            'parameters': len(df),
            'time_ms': elapsed * 1000,
            'throughput': len(df) / elapsed,
            'matched': result['checklist_params'],
            'passed': result['validated_params'],
            'failed': result['failed_params']
        })

    def test_multiple_validations(self):
        """Check list 검증 성능 - 반복 실행 (10회)"""
        self.log("\n[테스트 5] Check list 검증 반복 실행 (10회)")

        # 장비 유형
        equipment_types = self.db_schema.get_equipment_types()
        equipment_type_id = equipment_types[0][0]

        # 실제 데이터 로드
        data = self.db_schema.get_default_values(equipment_type_id)
        if not data:
            self.log("  - SKIP: Default DB 데이터 없음")
            return

        df = pd.DataFrame(data, columns=[
            "id", "parameter_name", "default_value", "min_spec", "max_spec", "type_name",
            "occurrence_count", "total_files", "confidence_score", "source_files", "description",
            "module_name", "part_name", "item_type", "is_checklist"
        ])
        df['ItemName'] = df['parameter_name']
        df['Value1'] = df['default_value']

        # 10회 반복 실행
        times = []
        for i in range(10):
            validator = ChecklistValidator(self.checklist_service, equipment_type_id)
            _, elapsed = self.measure_time(validator.validate_parameters, df)
            times.append(elapsed)

        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        self.log(f"  - 평균 시간: {avg_time*1000:.2f} ms")
        self.log(f"  - 최소 시간: {min_time*1000:.2f} ms")
        self.log(f"  - 최대 시간: {max_time*1000:.2f} ms")
        self.log(f"  - 평균 처리량: {len(df)/avg_time:.0f} 파라미터/초")

        self.results.append({
            'test': 'Multiple Validations',
            'iterations': 10,
            'avg_time_ms': avg_time * 1000,
            'min_time_ms': min_time * 1000,
            'max_time_ms': max_time * 1000,
            'avg_throughput': len(df) / avg_time
        })

    def print_summary(self):
        """성능 테스트 결과 요약"""
        self.log("\n" + "=" * 70)
        self.log("성능 테스트 결과 요약")
        self.log("=" * 70)

        for result in self.results:
            test_name = result['test']
            self.log(f"\n[{test_name}]")

            for key, value in result.items():
                if key != 'test':
                    if isinstance(value, float):
                        self.log(f"  - {key}: {value:.2f}")
                    else:
                        self.log(f"  - {key}: {value}")

        self.log("\n" + "=" * 70)

        # 성능 기준 판정
        self.log("\n성능 기준 판정:")

        # Check list 조회는 10ms 이내 (캐시 있을 때)
        for result in self.results:
            if result['test'] == 'Checklist Service':
                if result['with_cache_ms'] < 10:
                    self.log("  ✅ Check list 조회: PASS (캐시 < 10ms)")
                else:
                    self.log(f"  ❌ Check list 조회: FAIL (캐시 {result['with_cache_ms']:.2f}ms > 10ms)")

        # 대규모 검증은 1초 이내
        for result in self.results:
            if result['test'] == 'Validator - Large':
                if result['time_ms'] < 1000:
                    self.log(f"  ✅ 대규모 검증: PASS ({result['time_ms']:.0f}ms < 1000ms)")
                else:
                    self.log(f"  ❌ 대규모 검증: FAIL ({result['time_ms']:.0f}ms > 1000ms)")

        # 처리량은 1000 파라미터/초 이상
        for result in self.results:
            if result['test'] == 'Multiple Validations':
                if result['avg_throughput'] > 1000:
                    self.log(f"  ✅ 평균 처리량: PASS ({result['avg_throughput']:.0f} > 1000 파라미터/초)")
                else:
                    self.log(f"  ❌ 평균 처리량: FAIL ({result['avg_throughput']:.0f} < 1000 파라미터/초)")

        self.log("\n" + "=" * 70)

    def run_all_tests(self):
        """모든 성능 테스트 실행"""
        self.log("=" * 70)
        self.log("Phase 1 성능 테스트 시작")
        self.log("=" * 70)

        try:
            self.test_checklist_service_performance()
            self.test_validator_performance_small()
            self.test_validator_performance_medium()
            self.test_validator_performance_large()
            self.test_multiple_validations()

            self.print_summary()

            return True

        except Exception as e:
            self.log(f"\n테스트 실행 중 예외 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """메인 실행 함수"""
    try:
        tester = Phase1PerformanceTest()
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n>> ERROR: 테스트 초기화 실패")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
