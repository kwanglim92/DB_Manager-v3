#!/usr/bin/env python3
"""
Custom Configuration 기능 테스트
DB 독립적인 Equipment Type 및 QC 스펙 관리 테스트
"""

import json
import os
from src.app.qc_custom_config import CustomQCConfig

def test_custom_config():
    """Custom Configuration 테스트"""
    
    print("=" * 60)
    print("Custom QC Configuration 테스트")
    print("=" * 60)
    
    # 1. 새 설정 생성
    config = CustomQCConfig(config_path="test_custom_config.json")
    print("\n1. 설정 생성 완료")
    print(f"   - 기본 Equipment Types: {len(config.get_equipment_types())}개")
    
    # 2. 사용자 정의 Equipment Types 추가
    custom_types = [
        "고객맞춤형 모델 A",
        "특수 장비 Type B",
        "실험용 Configuration"
    ]
    
    for eq_type in custom_types:
        success = config.add_equipment_type(eq_type)
        if success:
            print(f"   ✓ Equipment Type 추가: {eq_type}")
    
    print(f"\n2. 현재 Equipment Types ({len(config.get_equipment_types())}개):")
    for i, eq_type in enumerate(config.get_equipment_types(), 1):
        print(f"   {i}. {eq_type}")
    
    # 3. 각 Type별 사용자 정의 스펙 설정
    # 고객맞춤형 모델 A - 온도와 압력 스펙
    specs_a = [
        {
            'item_name': '온도_센서_1',
            'min_spec': 20.0,
            'max_spec': 25.0,
            'unit': '°C',
            'enabled': True
        },
        {
            'item_name': '압력_게이지',
            'min_spec': 100.0,
            'max_spec': 200.0,
            'unit': 'kPa',
            'enabled': True
        },
        {
            'item_name': '유량계',
            'min_spec': 10.0,
            'max_spec': 20.0,
            'unit': 'L/min',
            'enabled': True
        }
    ]
    config.update_specs("고객맞춤형 모델 A", specs_a)
    
    # 특수 장비 Type B - 전기 스펙
    specs_b = [
        {
            'item_name': '전압_체크',
            'min_spec': 3.2,
            'max_spec': 3.4,
            'unit': 'V',
            'enabled': True
        },
        {
            'item_name': '전류_측정',
            'min_spec': 0.8,
            'max_spec': 1.2,
            'unit': 'A',
            'enabled': True
        },
        {
            'item_name': '주파수',
            'min_spec': 50.0,
            'max_spec': 60.0,
            'unit': 'Hz',
            'enabled': True
        }
    ]
    config.update_specs("특수 장비 Type B", specs_b)
    
    # 실험용 Configuration - 테스트 스펙
    specs_test = [
        {
            'item_name': '테스트_항목_1',
            'min_spec': 0,
            'max_spec': 100,
            'unit': '%',
            'enabled': True
        },
        {
            'item_name': '테스트_항목_2',
            'min_spec': -50,
            'max_spec': 50,
            'unit': 'unit',
            'enabled': True
        }
    ]
    config.update_specs("실험용 Configuration", specs_test)
    
    print("\n3. 각 Equipment Type별 검수 항목 설정:")
    for eq_type in ["고객맞춤형 모델 A", "특수 장비 Type B", "실험용 Configuration"]:
        specs = config.get_specs(eq_type)
        if specs:
            print(f"\n   [{eq_type}]")
            for spec in specs:
                print(f"      • {spec['item_name']}: "
                      f"Min={spec['min_spec']}, Max={spec['max_spec']} {spec.get('unit', '')}")
    
    # 4. 설정 저장 확인
    config.save_config()
    print(f"\n4. 설정 파일 저장 완료: test_custom_config.json")
    
    # 5. 저장된 파일 내용 확인
    with open("test_custom_config.json", 'r', encoding='utf-8') as f:
        saved_data = json.load(f)
    
    print("\n5. 저장된 설정 구조:")
    print(f"   - Equipment Types 개수: {len(saved_data.get('equipment_types', []))}")
    print(f"   - 설정된 스펙 타입 개수: {len(saved_data.get('specs', {}))}")
    
    # 6. 설정 다시 로드
    new_config = CustomQCConfig(config_path="test_custom_config.json")
    
    print("\n6. 설정 재로드 검증:")
    print(f"   - Equipment Types 일치: {new_config.get_equipment_types() == config.get_equipment_types()}")
    print(f"   - 로드된 Equipment Types: {len(new_config.get_equipment_types())}개")
    
    # 7. QC 검수 시뮬레이션
    print("\n7. QC 검수 시뮬레이션:")
    
    # 테스트 데이터
    test_data = {
        "고객맞춤형 모델 A": [
            ("온도_센서_1", 22.5),  # Pass
            ("압력_게이지", 150.0),  # Pass  
            ("유량계", 25.0)  # Fail (Max=20)
        ],
        "특수 장비 Type B": [
            ("전압_체크", 3.3),  # Pass
            ("전류_측정", 1.5),  # Fail (Max=1.2)
            ("주파수", 55.0)  # Pass
        ]
    }
    
    for eq_type, measurements in test_data.items():
        print(f"\n   [{eq_type}]")
        specs = config.get_specs(eq_type)
        
        for item_name, measured_value in measurements:
            # 스펙에서 해당 항목 찾기
            spec_item = next((s for s in specs if s['item_name'] == item_name), None)
            if spec_item:
                min_val = spec_item['min_spec']
                max_val = spec_item['max_spec']
                unit = spec_item.get('unit', '')
                pass_fail = "✅ Pass" if min_val <= measured_value <= max_val else "❌ Fail"
                print(f"      • {item_name}: {measured_value}{unit} "
                      f"(Spec: {min_val}-{max_val}{unit}) → {pass_fail}")
    
    # 8. 스펙 항목 추가 테스트
    new_item = {
        'item_name': '습도_센서',
        'min_spec': 40,
        'max_spec': 60,
        'unit': '%RH',
        'enabled': True
    }
    config.add_spec_item("고객맞춤형 모델 A", new_item)
    print(f"\n8. 스펙 항목 추가: '고객맞춤형 모델 A'에 '습도_센서' 추가")
    
    # 9. Equipment Type 삭제 테스트
    config.remove_equipment_type("Test Configuration")
    remaining = len(config.get_equipment_types())
    print(f"\n9. Equipment Type 삭제 후: {remaining}개 남음")
    
    # 10. 스펙 항목 제거 테스트
    config.remove_spec_item("고객맞춤형 모델 A", "습도_센서")
    print("\n10. 스펙 항목 제거: '습도_센서' 제거 완료")
    
    print("\n" + "=" * 60)
    print("✅ 모든 테스트 완료!")
    print("\n핵심 기능:")
    print("• Equipment Types을 사용자가 자유롭게 정의")
    print("• 각 Type별 검수 항목과 스펙을 독립적으로 관리")
    print("• JSON 파일로 설정 저장/로드")
    print("• Default DB와 완전히 독립적으로 작동")
    print("=" * 60)
    
    # 테스트 파일 정리
    if os.path.exists("test_custom_config.json"):
        os.remove("test_custom_config.json")
        print(f"\n테스트 파일 삭제: test_custom_config.json")

if __name__ == "__main__":
    test_custom_config()