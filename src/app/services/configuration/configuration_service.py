"""
Configuration Service 구현 (Phase 1.5)

Equipment Configurations 및 Default DB Values 관리를 위한 서비스 구현
"""

import json
from contextlib import contextmanager
from typing import List, Optional, Dict, Any

from ..interfaces.configuration_service_interface import (
    IConfigurationService,
    EquipmentConfiguration,
    DefaultDBValue
)
from ..common.cache_service import CacheService
from ..common.logging_service import LoggingService


class ConfigurationService(IConfigurationService):
    """Configuration 관리 서비스 구현"""

    # 캐시 키 상수
    _CACHE_KEY_ALL_CONFIGS = "configurations:all"
    _CACHE_KEY_CONFIG_BY_ID = "configuration:id:{}"
    _CACHE_KEY_CONFIGS_BY_TYPE = "configurations:type:{}"
    _CACHE_KEY_DEFAULT_VALUES = "default_values:config:{}"
    _CACHE_KEY_CUSTOMERS = "configurations:customers"

    def __init__(self, db_schema, cache_service: Optional[CacheService] = None):
        """
        Args:
            db_schema: DBSchema 인스턴스
            cache_service: CacheService 인스턴스 (옵션)
        """
        self._db_schema = db_schema
        self._cache = cache_service or CacheService(max_size=1000, default_ttl=300)
        self._logging = LoggingService()
        self._logger = self._logging.get_logger(self.__class__.__name__)

    @contextmanager
    def _transaction(self):
        """트랜잭션 컨텍스트 매니저 (자동 캐시 무효화)"""
        try:
            yield
            self._invalidate_cache()
            self._logging.log_service_action(
                "ConfigurationService",
                "Transaction completed and cache invalidated"
            )
        except Exception as e:
            self._logging.log_error(
                "ConfigurationService",
                e,
                "Transaction failed"
            )
            raise

    def _invalidate_cache(self):
        """모든 캐시 무효화"""
        self._cache.clear()

    def _row_to_configuration(self, row) -> EquipmentConfiguration:
        """DB Row를 EquipmentConfiguration 객체로 변환"""
        custom_options = None
        if row['custom_options']:
            try:
                custom_options = json.loads(row['custom_options'])
            except (json.JSONDecodeError, TypeError):
                custom_options = None

        return EquipmentConfiguration(
            id=row['id'],
            type_id=row['type_id'],
            configuration_name=row['configuration_name'],
            port_count=row['port_count'],
            wafer_count=row['wafer_count'],
            custom_options=custom_options,
            is_customer_specific=bool(row['is_customer_specific']),
            customer_name=row.get('customer_name'),
            description=row.get('description'),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
            type_name=row.get('type_name'),
            model_name=row.get('model_name')
        )

    def _row_to_default_value(self, row) -> DefaultDBValue:
        """DB Row를 DefaultDBValue 객체로 변환"""
        return DefaultDBValue(
            id=row['id'],
            configuration_id=row['configuration_id'],
            parameter_name=row['parameter_name'],
            default_value=row['default_value'],
            is_type_common=bool(row.get('is_type_common', False)),
            notes=row.get('notes'),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
            configuration_name=row.get('configuration_name'),
            type_name=row.get('type_name'),
            model_name=row.get('model_name')
        )

    # ==================== Equipment Configurations ====================

    def get_all_configurations(self) -> List[EquipmentConfiguration]:
        """모든 장비 구성 조회 (관계 데이터 포함)"""
        cached_result = self._cache.get(self._CACHE_KEY_ALL_CONFIGS)
        if cached_result is not None:
            return cached_result

        with self._db_schema.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    c.id, c.type_id, c.configuration_name,
                    c.port_count, c.wafer_count, c.custom_options,
                    c.is_customer_specific, c.customer_name,
                    c.description, c.created_at, c.updated_at,
                    t.type_name,
                    m.model_name
                FROM Equipment_Configurations c
                LEFT JOIN Equipment_Types t ON c.type_id = t.id
                LEFT JOIN Equipment_Models m ON t.model_id = m.id
                ORDER BY m.display_order, m.model_name, t.type_name, c.configuration_name
            """)

            configurations = [self._row_to_configuration(row) for row in cursor.fetchall()]
            self._cache.set(self._CACHE_KEY_ALL_CONFIGS, configurations)
            return configurations

    def get_configurations_by_type(self, type_id: int) -> List[EquipmentConfiguration]:
        """특정 Equipment Type의 모든 Configurations 조회"""
        cache_key = self._CACHE_KEY_CONFIGS_BY_TYPE.format(type_id)
        cached_result = self._cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        with self._db_schema.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    c.id, c.type_id, c.configuration_name,
                    c.port_count, c.wafer_count, c.custom_options,
                    c.is_customer_specific, c.customer_name,
                    c.description, c.created_at, c.updated_at,
                    t.type_name,
                    m.model_name
                FROM Equipment_Configurations c
                LEFT JOIN Equipment_Types t ON c.type_id = t.id
                LEFT JOIN Equipment_Models m ON t.model_id = m.id
                WHERE c.type_id = ?
                ORDER BY c.configuration_name
            """, (type_id,))

            configurations = [self._row_to_configuration(row) for row in cursor.fetchall()]
            self._cache.set(cache_key, configurations)
            return configurations

    def get_configuration_by_id(self, config_id: int) -> Optional[EquipmentConfiguration]:
        """특정 Configuration 조회"""
        cache_key = self._CACHE_KEY_CONFIG_BY_ID.format(config_id)
        cached_result = self._cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        with self._db_schema.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    c.id, c.type_id, c.configuration_name,
                    c.port_count, c.wafer_count, c.custom_options,
                    c.is_customer_specific, c.customer_name,
                    c.description, c.created_at, c.updated_at,
                    t.type_name,
                    m.model_name
                FROM Equipment_Configurations c
                LEFT JOIN Equipment_Types t ON c.type_id = t.id
                LEFT JOIN Equipment_Models m ON t.model_id = m.id
                WHERE c.id = ?
            """, (config_id,))

            row = cursor.fetchone()
            if row:
                configuration = self._row_to_configuration(row)
                self._cache.set(cache_key, configuration)
                return configuration
            return None

    def get_configuration_by_name(
        self,
        type_id: int,
        configuration_name: str
    ) -> Optional[EquipmentConfiguration]:
        """Type + Configuration 이름으로 조회"""
        with self._db_schema.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    c.id, c.type_id, c.configuration_name,
                    c.port_count, c.wafer_count, c.custom_options,
                    c.is_customer_specific, c.customer_name,
                    c.description, c.created_at, c.updated_at,
                    t.type_name,
                    m.model_name
                FROM Equipment_Configurations c
                LEFT JOIN Equipment_Types t ON c.type_id = t.id
                LEFT JOIN Equipment_Models m ON t.model_id = m.id
                WHERE c.type_id = ? AND c.configuration_name = ?
            """, (type_id, configuration_name))

            row = cursor.fetchone()
            if row:
                return self._row_to_configuration(row)
            return None

    def create_configuration(
        self,
        type_id: int,
        configuration_name: str,
        port_count: int,
        wafer_count: int,
        custom_options: Optional[Dict[str, Any]] = None,
        is_customer_specific: bool = False,
        customer_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> int:
        """새 장비 구성 생성"""
        # Validation
        self.validate_port_wafer_counts(port_count, wafer_count)
        if not self.validate_configuration_name(type_id, configuration_name):
            raise ValueError(
                f"Configuration '{configuration_name}' already exists for type_id {type_id}"
            )

        # Prepare custom_options JSON
        custom_options_json = None
        if custom_options:
            custom_options_json = json.dumps(custom_options, ensure_ascii=False)

        with self._transaction():
            with self._db_schema.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO Equipment_Configurations (
                        type_id, configuration_name, port_count, wafer_count,
                        custom_options, is_customer_specific, customer_name, description
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    type_id, configuration_name, port_count, wafer_count,
                    custom_options_json, int(is_customer_specific), customer_name, description
                ))
                conn.commit()
                config_id = cursor.lastrowid

                self._logging.log_service_action(
                    "ConfigurationService",
                    f"Created configuration: {configuration_name} (ID: {config_id})"
                )
                return config_id

    def update_configuration(
        self,
        config_id: int,
        configuration_name: Optional[str] = None,
        port_count: Optional[int] = None,
        wafer_count: Optional[int] = None,
        custom_options: Optional[Dict[str, Any]] = None,
        is_customer_specific: Optional[bool] = None,
        customer_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> bool:
        """장비 구성 정보 수정"""
        # Validation
        if port_count is not None or wafer_count is not None:
            current_config = self.get_configuration_by_id(config_id)
            if not current_config:
                return False
            final_port = port_count if port_count is not None else current_config.port_count
            final_wafer = wafer_count if wafer_count is not None else current_config.wafer_count
            self.validate_port_wafer_counts(final_port, final_wafer)

        updates = []
        params = []

        if configuration_name is not None:
            updates.append("configuration_name = ?")
            params.append(configuration_name)
        if port_count is not None:
            updates.append("port_count = ?")
            params.append(port_count)
        if wafer_count is not None:
            updates.append("wafer_count = ?")
            params.append(wafer_count)
        if custom_options is not None:
            updates.append("custom_options = ?")
            params.append(json.dumps(custom_options, ensure_ascii=False))
        if is_customer_specific is not None:
            updates.append("is_customer_specific = ?")
            params.append(int(is_customer_specific))
        if customer_name is not None:
            updates.append("customer_name = ?")
            params.append(customer_name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)

        if not updates:
            return True

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(config_id)

        with self._transaction():
            with self._db_schema.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    UPDATE Equipment_Configurations
                    SET {', '.join(updates)}
                    WHERE id = ?
                """, params)
                conn.commit()

                self._logging.log_service_action(
                    "ConfigurationService",
                    f"Updated configuration ID: {config_id}"
                )
                return cursor.rowcount > 0

    def delete_configuration(self, config_id: int) -> bool:
        """장비 구성 삭제 (CASCADE: 관련 Default_DB_Values 삭제)"""
        with self._transaction():
            with self._db_schema.get_connection() as conn:
                cursor = conn.cursor()

                # Check Default DB Values count
                cursor.execute("""
                    SELECT COUNT(*) as count FROM Default_DB_Values
                    WHERE configuration_id = ?
                """, (config_id,))
                default_count = cursor.fetchone()['count']

                cursor.execute("""
                    DELETE FROM Equipment_Configurations WHERE id = ?
                """, (config_id,))
                conn.commit()

                if cursor.rowcount > 0:
                    self._logging.log_service_action(
                        "ConfigurationService",
                        f"Deleted configuration ID: {config_id} (CASCADE: {default_count} default values)"
                    )
                    return True
                return False

    # ==================== Custom Options Management ====================

    def update_custom_options(
        self,
        config_id: int,
        custom_options: Dict[str, Any]
    ) -> bool:
        """커스텀 옵션 JSON 업데이트"""
        with self._transaction():
            with self._db_schema.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE Equipment_Configurations
                    SET custom_options = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (json.dumps(custom_options, ensure_ascii=False), config_id))
                conn.commit()

                self._logging.log_service_action(
                    "ConfigurationService",
                    f"Updated custom options for configuration ID: {config_id}"
                )
                return cursor.rowcount > 0

    def get_custom_options(self, config_id: int) -> Optional[Dict[str, Any]]:
        """커스텀 옵션 조회"""
        config = self.get_configuration_by_id(config_id)
        return config.custom_options if config else None

    # ==================== Customer-Specific Configurations ====================

    def get_customer_configurations(self, customer_name: str) -> List[EquipmentConfiguration]:
        """특정 고객의 모든 특화 구성 조회"""
        with self._db_schema.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    c.id, c.type_id, c.configuration_name,
                    c.port_count, c.wafer_count, c.custom_options,
                    c.is_customer_specific, c.customer_name,
                    c.description, c.created_at, c.updated_at,
                    t.type_name,
                    m.model_name
                FROM Equipment_Configurations c
                LEFT JOIN Equipment_Types t ON c.type_id = t.id
                LEFT JOIN Equipment_Models m ON t.model_id = m.id
                WHERE c.is_customer_specific = 1 AND c.customer_name = ?
                ORDER BY m.display_order, t.type_name, c.configuration_name
            """, (customer_name,))

            return [self._row_to_configuration(row) for row in cursor.fetchall()]

    def get_all_customers(self) -> List[str]:
        """고객 특화 구성이 있는 모든 고객 목록"""
        cached_result = self._cache.get(self._CACHE_KEY_CUSTOMERS)
        if cached_result is not None:
            return cached_result

        with self._db_schema.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT customer_name
                FROM Equipment_Configurations
                WHERE is_customer_specific = 1 AND customer_name IS NOT NULL
                ORDER BY customer_name
            """)

            customers = [row['customer_name'] for row in cursor.fetchall()]
            self._cache.set(self._CACHE_KEY_CUSTOMERS, customers)
            return customers

    # ==================== Default DB Values ====================

    def get_default_values_by_configuration(
        self,
        config_id: int,
        include_type_common: bool = True
    ) -> List[DefaultDBValue]:
        """특정 Configuration의 모든 Default DB Values 조회"""
        cache_key = self._CACHE_KEY_DEFAULT_VALUES.format(config_id)
        cached_result = self._cache.get(cache_key)
        if cached_result is not None and include_type_common:
            return cached_result

        with self._db_schema.get_connection() as conn:
            cursor = conn.cursor()

            if include_type_common:
                query = """
                    SELECT
                        d.id, d.configuration_id, d.parameter_name,
                        d.default_value, d.is_type_common, d.notes,
                        d.created_at, d.updated_at,
                        c.configuration_name,
                        t.type_name,
                        m.model_name
                    FROM Default_DB_Values d
                    LEFT JOIN Equipment_Configurations c ON d.configuration_id = c.id
                    LEFT JOIN Equipment_Types t ON c.type_id = t.id
                    LEFT JOIN Equipment_Models m ON t.model_id = m.id
                    WHERE d.configuration_id = ?
                    ORDER BY d.parameter_name
                """
            else:
                query = """
                    SELECT
                        d.id, d.configuration_id, d.parameter_name,
                        d.default_value, d.is_type_common, d.notes,
                        d.created_at, d.updated_at,
                        c.configuration_name,
                        t.type_name,
                        m.model_name
                    FROM Default_DB_Values d
                    LEFT JOIN Equipment_Configurations c ON d.configuration_id = c.id
                    LEFT JOIN Equipment_Types t ON c.type_id = t.id
                    LEFT JOIN Equipment_Models m ON t.model_id = m.id
                    WHERE d.configuration_id = ? AND d.is_type_common = 0
                    ORDER BY d.parameter_name
                """

            cursor.execute(query, (config_id,))
            values = [self._row_to_default_value(row) for row in cursor.fetchall()]

            if include_type_common:
                self._cache.set(cache_key, values)
            return values

    def get_default_value_by_name(
        self,
        config_id: int,
        parameter_name: str
    ) -> Optional[DefaultDBValue]:
        """특정 파라미터의 Default DB Value 조회"""
        with self._db_schema.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    d.id, d.configuration_id, d.parameter_name,
                    d.default_value, d.is_type_common, d.notes,
                    d.created_at, d.updated_at,
                    c.configuration_name,
                    t.type_name,
                    m.model_name
                FROM Default_DB_Values d
                LEFT JOIN Equipment_Configurations c ON d.configuration_id = c.id
                LEFT JOIN Equipment_Types t ON c.type_id = t.id
                LEFT JOIN Equipment_Models m ON t.model_id = m.id
                WHERE d.configuration_id = ? AND d.parameter_name = ?
            """, (config_id, parameter_name))

            row = cursor.fetchone()
            if row:
                return self._row_to_default_value(row)
            return None

    def create_default_value(
        self,
        configuration_id: int,
        parameter_name: str,
        default_value: str,
        is_type_common: bool = False,
        notes: Optional[str] = None
    ) -> int:
        """새 Default DB Value 생성"""
        if not self.validate_parameter_name(configuration_id, parameter_name):
            raise ValueError(
                f"Parameter '{parameter_name}' already exists for configuration_id {configuration_id}"
            )

        with self._transaction():
            with self._db_schema.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO Default_DB_Values (
                        configuration_id, parameter_name, default_value,
                        is_type_common, notes
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    configuration_id, parameter_name, default_value,
                    int(is_type_common), notes
                ))
                conn.commit()
                value_id = cursor.lastrowid

                self._logging.log_service_action(
                    "ConfigurationService",
                    f"Created default value: {parameter_name} (ID: {value_id})"
                )
                return value_id

    def update_default_value(
        self,
        value_id: int,
        default_value: Optional[str] = None,
        is_type_common: Optional[bool] = None,
        notes: Optional[str] = None
    ) -> bool:
        """Default DB Value 정보 수정"""
        updates = []
        params = []

        if default_value is not None:
            updates.append("default_value = ?")
            params.append(default_value)
        if is_type_common is not None:
            updates.append("is_type_common = ?")
            params.append(int(is_type_common))
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)

        if not updates:
            return True

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(value_id)

        with self._transaction():
            with self._db_schema.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    UPDATE Default_DB_Values
                    SET {', '.join(updates)}
                    WHERE id = ?
                """, params)
                conn.commit()

                self._logging.log_service_action(
                    "ConfigurationService",
                    f"Updated default value ID: {value_id}"
                )
                return cursor.rowcount > 0

    def delete_default_value(self, value_id: int) -> bool:
        """Default DB Value 삭제"""
        with self._transaction():
            with self._db_schema.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Default_DB_Values WHERE id = ?", (value_id,))
                conn.commit()

                if cursor.rowcount > 0:
                    self._logging.log_service_action(
                        "ConfigurationService",
                        f"Deleted default value ID: {value_id}"
                    )
                    return True
                return False

    def bulk_create_default_values(
        self,
        configuration_id: int,
        values: List[Dict[str, Any]]
    ) -> int:
        """Default DB Values 대량 생성"""
        created_count = 0

        with self._transaction():
            with self._db_schema.get_connection() as conn:
                cursor = conn.cursor()

                for value_data in values:
                    parameter_name = value_data.get('parameter_name')
                    default_value = value_data.get('default_value')
                    is_type_common = value_data.get('is_type_common', False)
                    notes = value_data.get('notes')

                    # Skip if parameter already exists
                    if not self.validate_parameter_name(configuration_id, parameter_name):
                        continue

                    cursor.execute("""
                        INSERT INTO Default_DB_Values (
                            configuration_id, parameter_name, default_value,
                            is_type_common, notes
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (
                        configuration_id, parameter_name, default_value,
                        int(is_type_common), notes
                    ))
                    created_count += 1

                conn.commit()

                self._logging.log_service_action(
                    "ConfigurationService",
                    f"Bulk created {created_count} default values for configuration {configuration_id}"
                )
                return created_count

    # ==================== Hierarchy Operations ====================

    def get_configuration_hierarchy(self, type_id: int) -> Dict[str, Any]:
        """특정 Type의 Configuration 계층 구조 조회"""
        with self._db_schema.get_connection() as conn:
            cursor = conn.cursor()

            # Get Type info
            cursor.execute("""
                SELECT
                    t.id, t.model_id, t.type_name, t.description,
                    t.is_default, t.created_at, t.updated_at,
                    m.model_name
                FROM Equipment_Types t
                LEFT JOIN Equipment_Models m ON t.model_id = m.id
                WHERE t.id = ?
            """, (type_id,))
            type_row = cursor.fetchone()

            if not type_row:
                return {}

            from ..interfaces.category_service_interface import EquipmentTypeV2
            equipment_type = EquipmentTypeV2(
                id=type_row['id'],
                model_id=type_row['model_id'],
                type_name=type_row['type_name'],
                description=type_row.get('description'),
                is_default=bool(type_row.get('is_default', False)),
                created_at=type_row.get('created_at'),
                updated_at=type_row.get('updated_at'),
                model_name=type_row.get('model_name')
            )

            # Get Configurations
            configurations = self.get_configurations_by_type(type_id)
            config_details = []

            for config in configurations:
                # Get default value counts
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_count,
                        SUM(CASE WHEN is_type_common = 1 THEN 1 ELSE 0 END) as type_common_count
                    FROM Default_DB_Values
                    WHERE configuration_id = ?
                """, (config.id,))
                counts = cursor.fetchone()

                total_count = counts['total_count'] or 0
                type_common_count = counts['type_common_count'] or 0
                config_specific_count = total_count - type_common_count

                config_details.append({
                    'configuration': config,
                    'default_value_count': total_count,
                    'type_common_count': type_common_count,
                    'config_specific_count': config_specific_count
                })

            return {
                'type': equipment_type,
                'configurations': config_details
            }

    def get_full_hierarchy(self) -> List[Dict[str, Any]]:
        """전체 Equipment Hierarchy 조회 (Model → Type → Configuration)"""
        with self._db_schema.get_connection() as conn:
            cursor = conn.cursor()

            # Get all Models
            cursor.execute("""
                SELECT id, model_name, model_code, description, display_order,
                       created_at, updated_at
                FROM Equipment_Models
                ORDER BY display_order, model_name
            """)

            from ..interfaces.category_service_interface import EquipmentModel, EquipmentTypeV2

            hierarchy = []

            for model_row in cursor.fetchall():
                model = EquipmentModel(
                    id=model_row['id'],
                    model_name=model_row['model_name'],
                    model_code=model_row.get('model_code'),
                    description=model_row.get('description'),
                    display_order=model_row.get('display_order', 0),
                    created_at=model_row.get('created_at'),
                    updated_at=model_row.get('updated_at')
                )

                # Get Types for this Model
                cursor.execute("""
                    SELECT id, model_id, type_name, description, is_default,
                           created_at, updated_at
                    FROM Equipment_Types
                    WHERE model_id = ?
                    ORDER BY type_name
                """, (model.id,))

                type_details = []

                for type_row in cursor.fetchall():
                    equipment_type = EquipmentTypeV2(
                        id=type_row['id'],
                        model_id=type_row['model_id'],
                        type_name=type_row['type_name'],
                        description=type_row.get('description'),
                        is_default=bool(type_row.get('is_default', False)),
                        created_at=type_row.get('created_at'),
                        updated_at=type_row.get('updated_at'),
                        model_name=model.model_name
                    )

                    # Get Configurations for this Type
                    configurations = self.get_configurations_by_type(equipment_type.id)
                    config_details = []

                    for config in configurations:
                        # Get default value count
                        cursor.execute("""
                            SELECT COUNT(*) as count
                            FROM Default_DB_Values
                            WHERE configuration_id = ?
                        """, (config.id,))
                        count_row = cursor.fetchone()
                        default_value_count = count_row['count'] if count_row else 0

                        config_details.append({
                            'configuration': config,
                            'default_value_count': default_value_count
                        })

                    type_details.append({
                        'type': equipment_type,
                        'configurations': config_details
                    })

                hierarchy.append({
                    'model': model,
                    'types': type_details
                })

            return hierarchy

    # ==================== Validation ====================

    def validate_port_wafer_counts(self, port_count: int, wafer_count: int) -> bool:
        """Port/Wafer 수 유효성 검사 (> 0)"""
        if port_count <= 0:
            raise ValueError(f"Port count must be greater than 0 (got {port_count})")
        if wafer_count <= 0:
            raise ValueError(f"Wafer count must be greater than 0 (got {wafer_count})")
        return True

    def validate_configuration_name(self, type_id: int, configuration_name: str) -> bool:
        """Configuration 이름 유효성 검사 (Unique 제약)"""
        existing = self.get_configuration_by_name(type_id, configuration_name)
        return existing is None

    def validate_parameter_name(self, config_id: int, parameter_name: str) -> bool:
        """파라미터 이름 유효성 검사 (Unique 제약)"""
        existing = self.get_default_value_by_name(config_id, parameter_name)
        return existing is None

    # ==================== Search ====================

    def search_configurations(self, query: str) -> List[EquipmentConfiguration]:
        """Configuration 검색 (이름, 고객명, 설명)"""
        with self._db_schema.get_connection() as conn:
            cursor = conn.cursor()
            search_pattern = f"%{query}%"

            cursor.execute("""
                SELECT
                    c.id, c.type_id, c.configuration_name,
                    c.port_count, c.wafer_count, c.custom_options,
                    c.is_customer_specific, c.customer_name,
                    c.description, c.created_at, c.updated_at,
                    t.type_name,
                    m.model_name
                FROM Equipment_Configurations c
                LEFT JOIN Equipment_Types t ON c.type_id = t.id
                LEFT JOIN Equipment_Models m ON t.model_id = m.id
                WHERE c.configuration_name LIKE ?
                   OR c.customer_name LIKE ?
                   OR c.description LIKE ?
                ORDER BY m.display_order, t.type_name, c.configuration_name
            """, (search_pattern, search_pattern, search_pattern))

            return [self._row_to_configuration(row) for row in cursor.fetchall()]

    def search_default_values(self, query: str) -> List[DefaultDBValue]:
        """Default DB Value 검색 (파라미터 이름, 값, 비고)"""
        with self._db_schema.get_connection() as conn:
            cursor = conn.cursor()
            search_pattern = f"%{query}%"

            cursor.execute("""
                SELECT
                    d.id, d.configuration_id, d.parameter_name,
                    d.default_value, d.is_type_common, d.notes,
                    d.created_at, d.updated_at,
                    c.configuration_name,
                    t.type_name,
                    m.model_name
                FROM Default_DB_Values d
                LEFT JOIN Equipment_Configurations c ON d.configuration_id = c.id
                LEFT JOIN Equipment_Types t ON c.type_id = t.id
                LEFT JOIN Equipment_Models m ON t.model_id = m.id
                WHERE d.parameter_name LIKE ?
                   OR d.default_value LIKE ?
                   OR d.notes LIKE ?
                ORDER BY m.display_order, t.type_name, c.configuration_name, d.parameter_name
            """, (search_pattern, search_pattern, search_pattern))

            return [self._row_to_default_value(row) for row in cursor.fetchall()]
