"""
Category Service 구현 (Phase 1.5)

Equipment Models 및 Equipment Types (V2) 관리 서비스
- Equipment_Models: 장비 모델명 관리
- Equipment_Types: AE 형태 관리 (model_id FK)
"""

from typing import List, Optional, Dict, Any
import logging
from contextlib import contextmanager

from ..interfaces.category_service_interface import (
    ICategoryService,
    EquipmentModel,
    EquipmentTypeV2
)
from ..common.cache_service import CacheService
from ..common.logging_service import LoggingService


class CategoryService(ICategoryService):
    """Category 관리 서비스 구현"""

    def __init__(self, db_schema, cache_service: Optional[CacheService] = None):
        """
        서비스 초기화

        Args:
            db_schema: 데이터베이스 스키마 인스턴스
            cache_service: 캐시 서비스 (선택사항)
        """
        self._db_schema = db_schema
        self._cache = cache_service or CacheService(max_size=500, default_ttl=300)
        self._logging = LoggingService()
        self._logger = self._logging.get_logger(self.__class__.__name__)

        # 캐시 키 상수
        self._CACHE_KEY_ALL_MODELS = "equipment_models_all"
        self._CACHE_KEY_MODEL_PREFIX = "equipment_model_"
        self._CACHE_KEY_ALL_TYPES = "equipment_types_all"
        self._CACHE_KEY_TYPE_PREFIX = "equipment_type_"
        self._CACHE_KEY_TYPES_BY_MODEL_PREFIX = "equipment_types_by_model_"
        self._CACHE_KEY_HIERARCHY = "equipment_hierarchy_tree"

    @contextmanager
    def _transaction(self):
        """트랜잭션 컨텍스트 매니저"""
        try:
            yield
            self._invalidate_cache()
            self._logging.log_service_action("CategoryService", "Transaction completed")
        except Exception as e:
            self._logging.log_error("CategoryService", e, "Transaction failed")
            raise

    def _invalidate_cache(self, model_id: Optional[int] = None, type_id: Optional[int] = None):
        """캐시 무효화"""
        if model_id:
            self._cache.delete(f"{self._CACHE_KEY_MODEL_PREFIX}{model_id}")
            self._cache.delete(f"{self._CACHE_KEY_TYPES_BY_MODEL_PREFIX}{model_id}")
        if type_id:
            self._cache.delete(f"{self._CACHE_KEY_TYPE_PREFIX}{type_id}")
        # 전체 목록 캐시도 무효화
        self._cache.delete(self._CACHE_KEY_ALL_MODELS)
        self._cache.delete(self._CACHE_KEY_ALL_TYPES)
        self._cache.delete(self._CACHE_KEY_HIERARCHY)

    # ==================== Equipment Models ====================

    def get_all_models(self) -> List[EquipmentModel]:
        """모든 장비 모델 조회 (display_order 순)"""
        cached_result = self._cache.get(self._CACHE_KEY_ALL_MODELS)
        if cached_result is not None:
            self._logger.debug("캐시에서 장비 모델 목록 조회")
            return cached_result

        try:
            with self._db_schema.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, model_name, model_code, description, display_order, created_at, updated_at
                    FROM Equipment_Models
                    ORDER BY display_order, model_name
                """)
                rows = cursor.fetchall()

                models = [
                    EquipmentModel(
                        id=row[0],
                        model_name=row[1],
                        model_code=row[2],
                        description=row[3],
                        display_order=row[4] or 0,
                        created_at=row[5],
                        updated_at=row[6]
                    )
                    for row in rows
                ]

                self._cache.set(self._CACHE_KEY_ALL_MODELS, models)
                self._logger.info(f"장비 모델 {len(models)}개 조회")
                return models

        except Exception as e:
            self._logger.error(f"장비 모델 조회 실패: {e}")
            raise

    def get_model_by_id(self, model_id: int) -> Optional[EquipmentModel]:
        """특정 장비 모델 조회"""
        cache_key = f"{self._CACHE_KEY_MODEL_PREFIX}{model_id}"
        cached_result = self._cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        try:
            with self._db_schema.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, model_name, model_code, description, display_order, created_at, updated_at
                    FROM Equipment_Models
                    WHERE id = ?
                """, (model_id,))
                row = cursor.fetchone()

                if row:
                    model = EquipmentModel(
                        id=row[0],
                        model_name=row[1],
                        model_code=row[2],
                        description=row[3],
                        display_order=row[4] or 0,
                        created_at=row[5],
                        updated_at=row[6]
                    )
                    self._cache.set(cache_key, model)
                    return model
                return None

        except Exception as e:
            self._logger.error(f"장비 모델 조회 실패 (ID: {model_id}): {e}")
            raise

    def get_model_by_name(self, model_name: str) -> Optional[EquipmentModel]:
        """모델명으로 조회"""
        # 전체 목록에서 검색 (캐시 활용)
        all_models = self.get_all_models()
        for model in all_models:
            if model.model_name == model_name:
                return model
        return None

    def create_model(
        self,
        model_name: str,
        model_code: Optional[str] = None,
        description: Optional[str] = None,
        display_order: Optional[int] = None
    ) -> int:
        """새 장비 모델 생성"""
        try:
            with self._transaction():
                with self._db_schema.get_connection() as conn:
                    cursor = conn.cursor()

                    # display_order 자동 할당
                    if display_order is None:
                        cursor.execute("SELECT MAX(display_order) FROM Equipment_Models")
                        max_order = cursor.fetchone()[0]
                        display_order = (max_order or 0) + 1

                    cursor.execute("""
                        INSERT INTO Equipment_Models (model_name, model_code, description, display_order)
                        VALUES (?, ?, ?, ?)
                    """, (model_name, model_code, description, display_order))

                    model_id = cursor.lastrowid
                    conn.commit()

                    self._logger.info(f"장비 모델 생성: {model_name} (ID: {model_id})")
                    return model_id

        except Exception as e:
            self._logger.error(f"장비 모델 생성 실패 ({model_name}): {e}")
            raise

    def update_model(
        self,
        model_id: int,
        model_name: Optional[str] = None,
        model_code: Optional[str] = None,
        description: Optional[str] = None,
        display_order: Optional[int] = None
    ) -> bool:
        """장비 모델 정보 수정"""
        try:
            with self._transaction():
                with self._db_schema.get_connection() as conn:
                    cursor = conn.cursor()

                    update_fields = []
                    params = []

                    if model_name is not None:
                        update_fields.append("model_name = ?")
                        params.append(model_name)

                    if model_code is not None:
                        update_fields.append("model_code = ?")
                        params.append(model_code)

                    if description is not None:
                        update_fields.append("description = ?")
                        params.append(description)

                    if display_order is not None:
                        update_fields.append("display_order = ?")
                        params.append(display_order)

                    if not update_fields:
                        return False

                    update_fields.append("updated_at = CURRENT_TIMESTAMP")
                    params.append(model_id)

                    query = f"UPDATE Equipment_Models SET {', '.join(update_fields)} WHERE id = ?"
                    cursor.execute(query, params)
                    conn.commit()

                    self._invalidate_cache(model_id=model_id)
                    self._logger.info(f"장비 모델 수정: ID {model_id}")
                    return cursor.rowcount > 0

        except Exception as e:
            self._logger.error(f"장비 모델 수정 실패 (ID: {model_id}): {e}")
            raise

    def delete_model(self, model_id: int) -> bool:
        """장비 모델 삭제 (CASCADE: 관련 Equipment_Types도 삭제)"""
        try:
            with self._transaction():
                with self._db_schema.get_connection() as conn:
                    cursor = conn.cursor()

                    # 연결된 Types 개수 확인 (경고용)
                    cursor.execute("SELECT COUNT(*) FROM Equipment_Types WHERE model_id = ?", (model_id,))
                    type_count = cursor.fetchone()[0]

                    if type_count > 0:
                        self._logger.warning(f"장비 모델 삭제 시 {type_count}개 Types도 함께 삭제됩니다.")

                    cursor.execute("DELETE FROM Equipment_Models WHERE id = ?", (model_id,))
                    conn.commit()

                    self._invalidate_cache(model_id=model_id)
                    self._logger.info(f"장비 모델 삭제: ID {model_id} ({type_count}개 Types 포함)")
                    return cursor.rowcount > 0

        except Exception as e:
            self._logger.error(f"장비 모델 삭제 실패 (ID: {model_id}): {e}")
            raise

    def reorder_models(self, model_id_order: List[int]) -> bool:
        """모델 정렬 순서 변경"""
        try:
            with self._transaction():
                with self._db_schema.get_connection() as conn:
                    cursor = conn.cursor()

                    for order, model_id in enumerate(model_id_order):
                        cursor.execute("""
                            UPDATE Equipment_Models
                            SET display_order = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (order, model_id))

                    conn.commit()
                    self._invalidate_cache()
                    self._logger.info(f"{len(model_id_order)}개 모델 순서 변경")
                    return True

        except Exception as e:
            self._logger.error(f"모델 순서 변경 실패: {e}")
            raise

    # ==================== Equipment Types ====================

    def get_types_by_model(self, model_id: int) -> List[EquipmentTypeV2]:
        """특정 모델의 모든 Types 조회"""
        cache_key = f"{self._CACHE_KEY_TYPES_BY_MODEL_PREFIX}{model_id}"
        cached_result = self._cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        try:
            with self._db_schema.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT et.id, et.model_id, et.type_name, et.description, et.is_default,
                           et.created_at, et.updated_at, em.model_name
                    FROM Equipment_Types et
                    JOIN Equipment_Models em ON et.model_id = em.id
                    WHERE et.model_id = ?
                    ORDER BY et.is_default DESC, et.type_name
                """, (model_id,))
                rows = cursor.fetchall()

                types = [
                    EquipmentTypeV2(
                        id=row[0],
                        model_id=row[1],
                        type_name=row[2],
                        description=row[3],
                        is_default=bool(row[4]),
                        created_at=row[5],
                        updated_at=row[6],
                        model_name=row[7]
                    )
                    for row in rows
                ]

                self._cache.set(cache_key, types)
                return types

        except Exception as e:
            self._logger.error(f"모델별 Types 조회 실패 (model_id: {model_id}): {e}")
            raise

    def get_all_types(self) -> List[EquipmentTypeV2]:
        """모든 Equipment Types 조회 (모델 정보 포함)"""
        cached_result = self._cache.get(self._CACHE_KEY_ALL_TYPES)
        if cached_result is not None:
            return cached_result

        try:
            with self._db_schema.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT et.id, et.model_id, et.type_name, et.description, et.is_default,
                           et.created_at, et.updated_at, em.model_name
                    FROM Equipment_Types et
                    JOIN Equipment_Models em ON et.model_id = em.id
                    ORDER BY em.display_order, et.is_default DESC, et.type_name
                """)
                rows = cursor.fetchall()

                types = [
                    EquipmentTypeV2(
                        id=row[0],
                        model_id=row[1],
                        type_name=row[2],
                        description=row[3],
                        is_default=bool(row[4]),
                        created_at=row[5],
                        updated_at=row[6],
                        model_name=row[7]
                    )
                    for row in rows
                ]

                self._cache.set(self._CACHE_KEY_ALL_TYPES, types)
                return types

        except Exception as e:
            self._logger.error(f"모든 Types 조회 실패: {e}")
            raise

    def get_type_by_id(self, type_id: int) -> Optional[EquipmentTypeV2]:
        """특정 Equipment Type 조회"""
        cache_key = f"{self._CACHE_KEY_TYPE_PREFIX}{type_id}"
        cached_result = self._cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        try:
            with self._db_schema.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT et.id, et.model_id, et.type_name, et.description, et.is_default,
                           et.created_at, et.updated_at, em.model_name
                    FROM Equipment_Types et
                    JOIN Equipment_Models em ON et.model_id = em.id
                    WHERE et.id = ?
                """, (type_id,))
                row = cursor.fetchone()

                if row:
                    type_obj = EquipmentTypeV2(
                        id=row[0],
                        model_id=row[1],
                        type_name=row[2],
                        description=row[3],
                        is_default=bool(row[4]),
                        created_at=row[5],
                        updated_at=row[6],
                        model_name=row[7]
                    )
                    self._cache.set(cache_key, type_obj)
                    return type_obj
                return None

        except Exception as e:
            self._logger.error(f"Equipment Type 조회 실패 (ID: {type_id}): {e}")
            raise

    def create_type(
        self,
        model_id: int,
        type_name: str,
        description: Optional[str] = None,
        is_default: bool = False
    ) -> int:
        """새 Equipment Type 생성"""
        try:
            with self._transaction():
                with self._db_schema.get_connection() as conn:
                    cursor = conn.cursor()

                    # Unique 제약 확인: (model_id, type_name)
                    if not self.validate_model_type_combination(model_id, type_name):
                        raise ValueError(f"이미 존재하는 조합: model_id={model_id}, type_name={type_name}")

                    cursor.execute("""
                        INSERT INTO Equipment_Types (model_id, type_name, description, is_default)
                        VALUES (?, ?, ?, ?)
                    """, (model_id, type_name, description, int(is_default)))

                    type_id = cursor.lastrowid
                    conn.commit()

                    self._invalidate_cache(model_id=model_id)
                    self._logger.info(f"Equipment Type 생성: {type_name} (model_id: {model_id}, ID: {type_id})")
                    return type_id

        except Exception as e:
            self._logger.error(f"Equipment Type 생성 실패 ({type_name}): {e}")
            raise

    def update_type(
        self,
        type_id: int,
        type_name: Optional[str] = None,
        description: Optional[str] = None,
        is_default: Optional[bool] = None
    ) -> bool:
        """Equipment Type 정보 수정"""
        try:
            with self._transaction():
                with self._db_schema.get_connection() as conn:
                    cursor = conn.cursor()

                    update_fields = []
                    params = []

                    if type_name is not None:
                        update_fields.append("type_name = ?")
                        params.append(type_name)

                    if description is not None:
                        update_fields.append("description = ?")
                        params.append(description)

                    if is_default is not None:
                        update_fields.append("is_default = ?")
                        params.append(int(is_default))

                    if not update_fields:
                        return False

                    update_fields.append("updated_at = CURRENT_TIMESTAMP")
                    params.append(type_id)

                    query = f"UPDATE Equipment_Types SET {', '.join(update_fields)} WHERE id = ?"
                    cursor.execute(query, params)
                    conn.commit()

                    self._invalidate_cache(type_id=type_id)
                    self._logger.info(f"Equipment Type 수정: ID {type_id}")
                    return cursor.rowcount > 0

        except Exception as e:
            self._logger.error(f"Equipment Type 수정 실패 (ID: {type_id}): {e}")
            raise

    def delete_type(self, type_id: int) -> bool:
        """Equipment Type 삭제 (CASCADE: 관련 Configurations 삭제)"""
        try:
            with self._transaction():
                with self._db_schema.get_connection() as conn:
                    cursor = conn.cursor()

                    # 연결된 Configurations 개수 확인
                    cursor.execute("SELECT COUNT(*) FROM Equipment_Configurations WHERE equipment_type_id = ?", (type_id,))
                    config_count = cursor.fetchone()[0]

                    if config_count > 0:
                        self._logger.warning(f"Equipment Type 삭제 시 {config_count}개 Configurations도 함께 삭제됩니다.")

                    cursor.execute("DELETE FROM Equipment_Types WHERE id = ?", (type_id,))
                    conn.commit()

                    self._invalidate_cache(type_id=type_id)
                    self._logger.info(f"Equipment Type 삭제: ID {type_id} ({config_count}개 Configurations 포함)")
                    return cursor.rowcount > 0

        except Exception as e:
            self._logger.error(f"Equipment Type 삭제 실패 (ID: {type_id}): {e}")
            raise

    # ==================== Hierarchy Operations ====================

    def get_hierarchy_tree(self) -> List[Dict[str, Any]]:
        """전체 Equipment Hierarchy Tree 조회"""
        cached_result = self._cache.get(self._CACHE_KEY_HIERARCHY)
        if cached_result is not None:
            return cached_result

        try:
            with self._db_schema.get_connection() as conn:
                cursor = conn.cursor()

                # Models 조회
                cursor.execute("""
                    SELECT id, model_name, model_code, description, display_order
                    FROM Equipment_Models
                    ORDER BY display_order, model_name
                """)
                models = cursor.fetchall()

                hierarchy = []

                for model_row in models:
                    model_id = model_row[0]

                    # 각 Model의 Types 조회
                    cursor.execute("""
                        SELECT id, type_name, description, is_default
                        FROM Equipment_Types
                        WHERE model_id = ?
                        ORDER BY is_default DESC, type_name
                    """, (model_id,))
                    types_rows = cursor.fetchall()

                    types_data = []
                    for type_row in types_rows:
                        type_id = type_row[0]

                        # 각 Type의 Configuration 개수 조회
                        cursor.execute("""
                            SELECT COUNT(*)
                            FROM Equipment_Configurations
                            WHERE equipment_type_id = ?
                        """, (type_id,))
                        config_count = cursor.fetchone()[0]

                        types_data.append({
                            'type': EquipmentTypeV2(
                                id=type_id,
                                model_id=model_id,
                                type_name=type_row[1],
                                description=type_row[2],
                                is_default=bool(type_row[3]),
                                model_name=model_row[1]
                            ),
                            'configuration_count': config_count
                        })

                    hierarchy.append({
                        'model': EquipmentModel(
                            id=model_id,
                            model_name=model_row[1],
                            model_code=model_row[2],
                            description=model_row[3],
                            display_order=model_row[4]
                        ),
                        'types': types_data
                    })

                self._cache.set(self._CACHE_KEY_HIERARCHY, hierarchy)
                return hierarchy

        except Exception as e:
            self._logger.error(f"Hierarchy Tree 조회 실패: {e}")
            raise

    def validate_model_type_combination(self, model_id: int, type_name: str) -> bool:
        """Model + Type 조합 유효성 검사 (Unique 제약)"""
        try:
            with self._db_schema.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM Equipment_Types
                    WHERE model_id = ? AND type_name = ?
                """, (model_id, type_name))
                count = cursor.fetchone()[0]
                return count == 0

        except Exception as e:
            self._logger.error(f"Model-Type 조합 검증 실패: {e}")
            raise

    def search_models(self, query: str) -> List[EquipmentModel]:
        """모델명, 코드로 검색"""
        all_models = self.get_all_models()
        query_lower = query.lower()
        return [
            model for model in all_models
            if query_lower in model.model_name.lower()
            or (model.model_code and query_lower in model.model_code.lower())
        ]

    def search_types(self, query: str) -> List[EquipmentTypeV2]:
        """Type 검색 (모델 정보 포함)"""
        all_types = self.get_all_types()
        query_lower = query.lower()
        return [
            type_obj for type_obj in all_types
            if query_lower in type_obj.type_name.lower()
            or (type_obj.description and query_lower in type_obj.description.lower())
            or (type_obj.model_name and query_lower in type_obj.model_name.lower())
        ]
