"""
Shipped Equipment Service 구현 (Phase 2)

출고 장비 Raw Data 관리 서비스
"""

import os
import re
from typing import List, Optional, Dict, Any, Tuple
from datetime import date, datetime
from pathlib import Path

from app.services.interfaces.shipped_equipment_service_interface import (
    IShippedEquipmentService,
    ShippedEquipment,
    ShippedEquipmentParameter,
    FileParseResult,
    ParameterHistory
)


class ShippedEquipmentService(IShippedEquipmentService):
    """출고 장비 관리 서비스 구현"""

    def __init__(self, db_schema):
        """
        Args:
            db_schema (DBSchema): 데이터베이스 스키마 인스턴스
        """
        self.db_schema = db_schema

    # ==================== Shipped Equipment CRUD ====================

    def get_all_shipped_equipment(
        self,
        configuration_id: Optional[int] = None,
        customer_name: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[ShippedEquipment]:
        """모든 출고 장비 조회 (필터링 지원)"""
        with self.db_schema.get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT
                    se.id, se.equipment_type_id, se.configuration_id,
                    se.serial_number, se.customer_name, se.ship_date,
                    se.is_refit, se.original_serial_number, se.notes, se.created_at,
                    et.type_name,
                    ec.configuration_name,
                    em.model_name
                FROM Shipped_Equipment se
                LEFT JOIN Equipment_Types et ON se.equipment_type_id = et.id
                LEFT JOIN Equipment_Configurations ec ON se.configuration_id = ec.id
                LEFT JOIN Equipment_Models em ON et.model_id = em.id
                WHERE 1=1
            """
            params = []

            if configuration_id:
                query += " AND se.configuration_id = ?"
                params.append(configuration_id)

            if customer_name:
                query += " AND se.customer_name LIKE ?"
                params.append(f"%{customer_name}%")

            if start_date:
                query += " AND se.ship_date >= ?"
                params.append(start_date.isoformat())

            if end_date:
                query += " AND se.ship_date <= ?"
                params.append(end_date.isoformat())

            query += " ORDER BY se.ship_date DESC, se.created_at DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_shipped_equipment(row) for row in rows]

    def get_shipped_equipment_by_id(self, equipment_id: int) -> Optional[ShippedEquipment]:
        """특정 출고 장비 조회"""
        with self.db_schema.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    se.id, se.equipment_type_id, se.configuration_id,
                    se.serial_number, se.customer_name, se.ship_date,
                    se.is_refit, se.original_serial_number, se.notes, se.created_at,
                    et.type_name,
                    ec.configuration_name,
                    em.model_name
                FROM Shipped_Equipment se
                LEFT JOIN Equipment_Types et ON se.equipment_type_id = et.id
                LEFT JOIN Equipment_Configurations ec ON se.configuration_id = ec.id
                LEFT JOIN Equipment_Models em ON et.model_id = em.id
                WHERE se.id = ?
            """, (equipment_id,))

            row = cursor.fetchone()
            return self._row_to_shipped_equipment(row) if row else None

    def get_shipped_equipment_by_serial(self, serial_number: str) -> Optional[ShippedEquipment]:
        """시리얼 번호로 출고 장비 조회"""
        with self.db_schema.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    se.id, se.equipment_type_id, se.configuration_id,
                    se.serial_number, se.customer_name, se.ship_date,
                    se.is_refit, se.original_serial_number, se.notes, se.created_at,
                    et.type_name,
                    ec.configuration_name,
                    em.model_name
                FROM Shipped_Equipment se
                LEFT JOIN Equipment_Types et ON se.equipment_type_id = et.id
                LEFT JOIN Equipment_Configurations ec ON se.configuration_id = ec.id
                LEFT JOIN Equipment_Models em ON et.model_id = em.id
                WHERE se.serial_number = ?
            """, (serial_number,))

            row = cursor.fetchone()
            return self._row_to_shipped_equipment(row) if row else None

    def create_shipped_equipment(
        self,
        equipment_type_id: int,
        configuration_id: int,
        serial_number: str,
        customer_name: str,
        ship_date: Optional[date] = None,
        is_refit: bool = False,
        original_serial_number: Optional[str] = None,
        notes: Optional[str] = None
    ) -> int:
        """출고 장비 생성"""
        with self.db_schema.get_connection() as conn:
            cursor = conn.cursor()

            # 시리얼 번호 중복 확인
            cursor.execute(
                "SELECT id FROM Shipped_Equipment WHERE serial_number = ?",
                (serial_number,)
            )
            if cursor.fetchone():
                raise ValueError(f"Duplicate serial number: {serial_number}")

            # Configuration 유효성 확인
            cursor.execute(
                "SELECT id FROM Equipment_Configurations WHERE id = ?",
                (configuration_id,)
            )
            if not cursor.fetchone():
                raise ValueError(f"Invalid configuration_id: {configuration_id}")

            # 삽입
            ship_date_str = ship_date.isoformat() if ship_date else None
            cursor.execute("""
                INSERT INTO Shipped_Equipment (
                    equipment_type_id, configuration_id, serial_number,
                    customer_name, ship_date, is_refit, original_serial_number, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                equipment_type_id, configuration_id, serial_number,
                customer_name, ship_date_str, 1 if is_refit else 0,
                original_serial_number, notes
            ))

            conn.commit()
            return cursor.lastrowid

    def update_shipped_equipment(
        self,
        equipment_id: int,
        customer_name: Optional[str] = None,
        ship_date: Optional[date] = None,
        notes: Optional[str] = None
    ) -> bool:
        """출고 장비 정보 수정"""
        with self.db_schema.get_connection() as conn:
            cursor = conn.cursor()

            # 존재 확인
            cursor.execute("SELECT id FROM Shipped_Equipment WHERE id = ?", (equipment_id,))
            if not cursor.fetchone():
                return False

            # 수정할 필드만 업데이트
            updates = []
            params = []

            if customer_name is not None:
                updates.append("customer_name = ?")
                params.append(customer_name)

            if ship_date is not None:
                updates.append("ship_date = ?")
                params.append(ship_date.isoformat())

            if notes is not None:
                updates.append("notes = ?")
                params.append(notes)

            if not updates:
                return True  # 수정할 것이 없음

            params.append(equipment_id)
            query = f"UPDATE Shipped_Equipment SET {', '.join(updates)} WHERE id = ?"

            cursor.execute(query, params)
            conn.commit()

            return cursor.rowcount > 0

    def delete_shipped_equipment(self, equipment_id: int) -> bool:
        """출고 장비 삭제 (CASCADE: 파라미터도 함께 삭제)"""
        with self.db_schema.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM Shipped_Equipment WHERE id = ?", (equipment_id,))
            conn.commit()

            return cursor.rowcount > 0

    # ==================== Shipped Equipment Parameters ====================

    def get_parameters_by_equipment(
        self, equipment_id: int
    ) -> List[ShippedEquipmentParameter]:
        """특정 출고 장비의 모든 파라미터 조회"""
        with self.db_schema.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, shipped_equipment_id, parameter_name, parameter_value,
                       module, part, data_type
                FROM Shipped_Equipment_Parameters
                WHERE shipped_equipment_id = ?
                ORDER BY parameter_name
            """, (equipment_id,))

            rows = cursor.fetchall()

            return [
                ShippedEquipmentParameter(
                    id=row[0],
                    shipped_equipment_id=row[1],
                    parameter_name=row[2],
                    parameter_value=row[3],
                    module=row[4],
                    part=row[5],
                    data_type=row[6]
                )
                for row in rows
            ]

    def add_parameters_bulk(
        self,
        equipment_id: int,
        parameters: List[Dict[str, str]]
    ) -> int:
        """파라미터 일괄 추가 (2000+ 파라미터 지원)"""
        with self.db_schema.get_connection() as conn:
            cursor = conn.cursor()

            # equipment_id 유효성 확인
            cursor.execute("SELECT id FROM Shipped_Equipment WHERE id = ?", (equipment_id,))
            if not cursor.fetchone():
                raise ValueError(f"Invalid equipment_id: {equipment_id}")

            # Batch insert (1000개씩)
            batch_size = 1000
            total_inserted = 0

            for i in range(0, len(parameters), batch_size):
                batch = parameters[i:i + batch_size]

                cursor.executemany("""
                    INSERT INTO Shipped_Equipment_Parameters (
                        shipped_equipment_id, parameter_name, parameter_value,
                        module, part, data_type
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, [
                    (
                        equipment_id,
                        p.get('parameter_name'),
                        p.get('parameter_value'),
                        p.get('module'),
                        p.get('part'),
                        p.get('data_type')
                    )
                    for p in batch
                ])

                total_inserted += cursor.rowcount

            conn.commit()
            return total_inserted

    # ==================== File Import ====================

    def parse_equipment_file(self, file_path: str) -> FileParseResult:
        """
        장비 데이터 파일 파싱 ({Serial}_{Customer}_{Model}.txt)

        파일명 형식: U27005-100225_Intel Hillsboro #4_NX-Hybrid WLI.txt
                    D27004-211124_Samsung_NX-Mask.txt

        파일 형식: TSV (Tab-separated values)
                  헤더: Module\tPart\tItemName\tItemType\tItemValue\tItemDescription
        """
        try:
            # 1. 파일명 파싱
            filename = Path(file_path).stem  # 확장자 제거
            parts = filename.split('_')

            if len(parts) < 3:
                return FileParseResult(
                    serial_number="",
                    customer_name="",
                    model_name="",
                    parameters=[],
                    total_count=0,
                    success=False,
                    error_message=f"Invalid filename format. Expected: {{Serial}}_{{Customer}}_{{Model}}.txt"
                )

            serial_number = parts[0]
            customer_name = parts[1]
            model_name = '_'.join(parts[2:])  # 나머지는 모델명 (언더스코어 포함 가능)

            # 2. 파일 내용 파싱
            parameters = []

            with open(file_path, 'r', encoding='utf-8') as f:
                # 첫 줄(헤더) 읽기
                header_line = f.readline().strip()

                # TSV 형식 확인 (탭으로 구분된 헤더)
                is_tsv = '\t' in header_line

                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    if is_tsv:
                        # TSV 형식: Module\tPart\tItemName\tItemType\tItemValue\tItemDescription
                        columns = line.split('\t')

                        if len(columns) < 5:
                            continue  # 필수 컬럼 부족

                        module = columns[0]
                        part = columns[1]
                        item_name = columns[2]
                        item_type = columns[3]
                        item_value = columns[4]

                        # Module.Part.ItemName 형식으로 parameter_name 생성
                        parameter_name = f"{module}.{part}.{item_name}"

                        param = {
                            'parameter_name': parameter_name,
                            'parameter_value': item_value,
                            'module': module,
                            'part': part,
                            'data_type': item_type if item_type else self._infer_data_type(item_value)
                        }
                    else:
                        # 기존 Key=Value 형식
                        if '=' not in line:
                            continue

                        key, value = line.split('=', 1)
                        key_parts = key.split('.')

                        param = {
                            'parameter_name': key,
                            'parameter_value': value,
                            'module': None,
                            'part': None,
                            'data_type': self._infer_data_type(value)
                        }

                        # Module.Part.ItemName 구조 파싱
                        if len(key_parts) >= 3:
                            param['module'] = key_parts[0]
                            param['part'] = key_parts[1]

                    parameters.append(param)

            return FileParseResult(
                serial_number=serial_number,
                customer_name=customer_name,
                model_name=model_name,
                parameters=parameters,
                total_count=len(parameters),
                success=True
            )

        except Exception as e:
            return FileParseResult(
                serial_number="",
                customer_name="",
                model_name="",
                parameters=[],
                total_count=0,
                success=False,
                error_message=str(e)
            )

    def import_from_file(
        self,
        file_path: str,
        configuration_id: Optional[int] = None,
        auto_match: bool = True
    ) -> Tuple[bool, str, Optional[int]]:
        """파일에서 출고 장비 데이터 임포트"""
        try:
            # 1. 파일 파싱
            parse_result = self.parse_equipment_file(file_path)

            if not parse_result.success:
                return False, f"File parsing failed: {parse_result.error_message}", None

            # 2. Configuration 매칭
            if configuration_id is None and auto_match:
                configuration_id = self.match_configuration(
                    parse_result.model_name,
                    parse_result.serial_number
                )

                if configuration_id is None:
                    return False, f"Configuration auto-matching failed for model: {parse_result.model_name}", None

            if configuration_id is None:
                return False, "Configuration ID required (auto-match failed)", None

            # 3. equipment_type_id 조회
            with self.db_schema.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT type_id FROM Equipment_Configurations WHERE id = ?",
                    (configuration_id,)
                )
                row = cursor.fetchone()
                if not row:
                    return False, f"Invalid configuration_id: {configuration_id}", None

                equipment_type_id = row[0]

            # 4. Shipped_Equipment 생성
            equipment_id = self.create_shipped_equipment(
                equipment_type_id=equipment_type_id,
                configuration_id=configuration_id,
                serial_number=parse_result.serial_number,
                customer_name=parse_result.customer_name,
                ship_date=date.today(),  # 기본값: 오늘
                notes=f"Imported from {Path(file_path).name}"
            )

            # 5. Parameters 일괄 삽입
            param_count = self.add_parameters_bulk(equipment_id, parse_result.parameters)

            return True, f"Imported {param_count} parameters for {parse_result.serial_number}", equipment_id

        except Exception as e:
            return False, f"Import failed: {str(e)}", None

    # ==================== Parameter History & Statistics ====================

    def get_parameter_history(
        self,
        parameter_name: str,
        configuration_id: Optional[int] = None,
        limit: int = 100
    ) -> ParameterHistory:
        """특정 파라미터의 출고 이력 및 통계 조회"""
        with self.db_schema.get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT
                    se.serial_number,
                    sep.parameter_value,
                    se.ship_date
                FROM Shipped_Equipment_Parameters sep
                JOIN Shipped_Equipment se ON sep.shipped_equipment_id = se.id
                WHERE sep.parameter_name = ?
            """
            params = [parameter_name]

            if configuration_id:
                query += " AND se.configuration_id = ?"
                params.append(configuration_id)

            query += " ORDER BY se.ship_date DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            values = [(row[0], row[1], row[2]) for row in rows]

            # 통계 계산 (숫자형인 경우)
            numeric_values = []
            for _, val, _ in values:
                try:
                    numeric_values.append(float(val))
                except ValueError:
                    pass

            if numeric_values:
                import statistics
                return ParameterHistory(
                    parameter_name=parameter_name,
                    value_count=len(values),
                    min_value=min(numeric_values),
                    max_value=max(numeric_values),
                    avg_value=statistics.mean(numeric_values),
                    std_dev=statistics.stdev(numeric_values) if len(numeric_values) > 1 else 0.0,
                    values=values
                )
            else:
                return ParameterHistory(
                    parameter_name=parameter_name,
                    value_count=len(values),
                    values=values
                )

    # ==================== Auto Matching ====================

    def match_configuration(
        self,
        model_name: str,
        serial_number: Optional[str] = None
    ) -> Optional[int]:
        """Model 이름 기반 Configuration 자동 매칭"""
        with self.db_schema.get_connection() as conn:
            cursor = conn.cursor()

            # 1. model_name → Equipment_Models 조회
            cursor.execute(
                "SELECT id FROM Equipment_Models WHERE model_name = ?",
                (model_name,)
            )
            model_row = cursor.fetchone()

            if not model_row:
                return None  # 모델 찾기 실패

            model_id = model_row[0]

            # 2. 해당 Model의 기본 Type 조회 (첫 번째 Type)
            cursor.execute(
                "SELECT id FROM Equipment_Types WHERE model_id = ? ORDER BY display_order LIMIT 1",
                (model_id,)
            )
            type_row = cursor.fetchone()

            if not type_row:
                return None  # Type 찾기 실패

            type_id = type_row[0]

            # 3. 해당 Type의 기본 Configuration 조회 (customer_specific=0, 첫 번째)
            cursor.execute("""
                SELECT id FROM Equipment_Configurations
                WHERE type_id = ? AND is_customer_specific = 0
                ORDER BY id
                LIMIT 1
            """, (type_id,))
            config_row = cursor.fetchone()

            if not config_row:
                return None  # Configuration 찾기 실패

            return config_row[0]

    # ==================== Helper Methods ====================

    def _row_to_shipped_equipment(self, row) -> ShippedEquipment:
        """DB row → ShippedEquipment 변환"""
        ship_date_obj = None
        if row[5]:  # ship_date
            try:
                ship_date_obj = datetime.fromisoformat(row[5]).date()
            except:
                pass

        return ShippedEquipment(
            id=row[0],
            equipment_type_id=row[1],
            configuration_id=row[2],
            serial_number=row[3],
            customer_name=row[4],
            ship_date=ship_date_obj,
            is_refit=bool(row[6]),
            original_serial_number=row[7],
            notes=row[8],
            created_at=row[9],
            type_name=row[10],
            configuration_name=row[11],
            model_name=row[12]
        )

    def _infer_data_type(self, value: str) -> str:
        """값에서 데이터 타입 추론"""
        # 정수
        if re.match(r'^-?\d+$', value):
            return 'int'

        # 실수
        if re.match(r'^-?\d+\.\d+([eE][+-]?\d+)?$', value):
            return 'float'

        # 불리언
        if value.lower() in ('true', 'false', 'on', 'off', 'yes', 'no'):
            return 'bool'

        # 기본값: 문자열
        return 'str'
