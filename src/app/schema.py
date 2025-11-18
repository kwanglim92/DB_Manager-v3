# 간소화된 DBSchema 클래스 - 핵심 기능만 유지

import os
import sqlite3
from datetime import datetime
from contextlib import contextmanager

class DBSchema:
    """
    DB Manager 애플리케이션의 로컬 데이터베이스 스키마를 관리하는 클래스
    장비 유형 및 Default DB 값 저장을 위한 테이블 구조를 생성하고 관리합니다.
    컨텍스트 매니저 패턴을 사용하여 데이터베이스 연결을 효율적으로 관리합니다.
    """
    def __init__(self, db_path=None):
        if db_path is None:
            # 기존 데이터베이스 위치 사용 (프로젝트 루트/data/)
            app_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data')
            if not os.path.exists(app_data_dir):
                os.makedirs(app_data_dir)
            self.db_path = os.path.join(app_data_dir, 'local_db.sqlite')
        else:
            self.db_path = db_path
        self.create_tables()

    @contextmanager
    def get_connection(self, conn_override=None):
        conn_provided = conn_override is not None
        conn = conn_override if conn_provided else sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            if not conn_provided and conn:
                conn.close()

    def create_tables(self):
        """핵심 테이블들만 생성"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 장비 유형 테이블
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS Equipment_Types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type_name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Default DB 값 테이블 (is_performance → is_checklist로 변경)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS Default_DB_Values (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_type_id INTEGER NOT NULL,
                parameter_name TEXT NOT NULL,
                default_value TEXT NOT NULL,
                min_spec TEXT,
                max_spec TEXT,
                occurrence_count INTEGER DEFAULT 1,
                total_files INTEGER DEFAULT 1,
                confidence_score REAL DEFAULT 1.0,
                source_files TEXT,
                description TEXT,
                module_name TEXT,
                part_name TEXT,
                item_type TEXT,
                is_checklist INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (equipment_type_id) REFERENCES Equipment_Types(id),
                UNIQUE(equipment_type_id, parameter_name)
            )
            ''')

            # Phase 1: QC Check list 마스터 테이블
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS QC_Checklist_Items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL UNIQUE,
                parameter_pattern TEXT NOT NULL,
                is_common INTEGER DEFAULT 1,
                severity_level TEXT CHECK(severity_level IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')) DEFAULT 'MEDIUM',
                validation_rule TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # Phase 1: 장비별 Check list 매핑 테이블
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS Equipment_Checklist_Mapping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_type_id INTEGER NOT NULL,
                checklist_item_id INTEGER NOT NULL,
                is_required INTEGER DEFAULT 1,
                custom_validation_rule TEXT,
                priority INTEGER DEFAULT 100,
                added_reason TEXT,
                added_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (equipment_type_id) REFERENCES Equipment_Types(id) ON DELETE CASCADE,
                FOREIGN KEY (checklist_item_id) REFERENCES QC_Checklist_Items(id) ON DELETE CASCADE,
                UNIQUE(equipment_type_id, checklist_item_id)
            )
            ''')

            # Phase 1: 장비별 Check list 예외 처리 테이블
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS Equipment_Checklist_Exceptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_type_id INTEGER NOT NULL,
                checklist_item_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                approved_by TEXT,
                approved_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (equipment_type_id) REFERENCES Equipment_Types(id) ON DELETE CASCADE,
                FOREIGN KEY (checklist_item_id) REFERENCES QC_Checklist_Items(id) ON DELETE CASCADE,
                UNIQUE(equipment_type_id, checklist_item_id)
            )
            ''')

            # Phase 1: Check list 변경 이력 테이블
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS Checklist_Audit_Log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT CHECK(action IN ('ADD', 'REMOVE', 'MODIFY', 'APPROVE', 'REJECT')) NOT NULL,
                target_table TEXT NOT NULL,
                target_id INTEGER,
                old_value TEXT,
                new_value TEXT,
                reason TEXT,
                user TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            conn.commit()
            
            # is_performance 컬럼이 있다면 is_checklist로 마이그레이션
            self._migrate_performance_to_checklist(cursor, conn)

    def _migrate_performance_to_checklist(self, cursor, conn):
        """is_performance 컬럼을 is_checklist로 마이그레이션"""
        try:
            # 기존 컬럼이 있는지 확인
            cursor.execute("PRAGMA table_info(Default_DB_Values)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'is_performance' in columns and 'is_checklist' not in columns:
                # is_checklist 컬럼 추가
                cursor.execute("ALTER TABLE Default_DB_Values ADD COLUMN is_checklist INTEGER DEFAULT 0")
                
                # 기존 is_performance 값을 is_checklist로 복사
                cursor.execute("UPDATE Default_DB_Values SET is_checklist = is_performance")
                
                conn.commit()
                print("✅ is_performance → is_checklist 마이그레이션 완료")
                
        except Exception as e:
            print(f"마이그레이션 중 오류 (무시 가능): {e}")

    # ==================== 장비 유형 관리 ====================
    
    def add_equipment_type(self, type_name, description="", conn_override=None):
        """
        새 장비 유형 추가 (Deprecated in Phase 1.5)

        ⚠️ Phase 1.5부터 Equipment_Types는 model_id (필수)가 필요합니다.
        CategoryService.create_type(model_id, type_name, description)를 사용하세요.
        """
        raise NotImplementedError(
            "add_equipment_type()는 Phase 1.5에서 더 이상 지원되지 않습니다.\n"
            "model_id가 필수입니다. CategoryService.create_type()를 사용하세요.\n\n"
            "예시:\n"
            "  from app.services import ServiceFactory\n"
            "  category_service = ServiceFactory.get_category_service()\n"
            "  type_id = category_service.create_type(model_id=1, type_name='AE', description='...')"
        )

    def get_equipment_types(self, conn_override=None):
        """모든 장비 유형 조회"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, type_name, description FROM Equipment_Types ORDER BY type_name')
            return cursor.fetchall()

    def get_equipment_type_by_name(self, type_name, conn_override=None):
        """이름으로 장비 유형 조회"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, type_name, description FROM Equipment_Types WHERE type_name = ?', (type_name,))
            return cursor.fetchone()

    def update_equipment_type(self, type_id, type_name=None, description=None, conn_override=None):
        """장비 유형 정보 업데이트"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            
            update_fields = []
            params = []
            
            if type_name is not None:
                update_fields.append("type_name = ?")
                params.append(type_name)
            
            if description is not None:
                update_fields.append("description = ?")
                params.append(description)
            
            if update_fields:
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                params.append(type_id)
                
                query = f"UPDATE Equipment_Types SET {', '.join(update_fields)} WHERE id = ?"
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount > 0
            
            return False

    def delete_equipment_type(self, type_id, conn_override=None):
        """장비 유형 삭제 (관련 Default DB 값들도 함께 삭제)"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            try:
                # 트랜잭션 시작
                cursor.execute('BEGIN TRANSACTION')
                
                # 먼저 관련된 Default DB 값들 삭제
                cursor.execute('DELETE FROM Default_DB_Values WHERE equipment_type_id = ?', (type_id,))
                deleted_params = cursor.rowcount
                
                # 장비 유형 삭제
                cursor.execute('DELETE FROM Equipment_Types WHERE id = ?', (type_id,))
                deleted_types = cursor.rowcount
                
                # 트랜잭션 커밋
                conn.commit()
                
                # 삭제된 항목이 있으면 성공
                return deleted_types > 0
                
            except Exception as e:
                # 오류 발생 시 롤백
                conn.rollback()
                raise e

    # ==================== Default DB 값 관리 ====================
    
    def add_default_value(self, equipment_type_id, parameter_name, default_value, 
                         min_spec=None, max_spec=None, occurrence_count=1, total_files=1,
                         confidence_score=1.0, source_files="", description="", 
                         module_name="", part_name="", item_type="", is_checklist=0, conn_override=None):
        """새 Default DB 값 추가"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                INSERT INTO Default_DB_Values 
                (equipment_type_id, parameter_name, default_value, min_spec, max_spec,
                 occurrence_count, total_files, confidence_score, source_files, description,
                 module_name, part_name, item_type, is_checklist)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (equipment_type_id, parameter_name, default_value, min_spec, max_spec,
                      occurrence_count, total_files, confidence_score, source_files, description,
                      module_name, part_name, item_type, is_checklist))
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return None

    def get_default_values(self, equipment_type_id, checklist_only=False, conn_override=None):
        """장비 유형별 Default DB 값 조회"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            
            if checklist_only:
                cursor.execute('''
                SELECT d.id, d.parameter_name, d.default_value, d.min_spec, d.max_spec, e.type_name,
                       d.occurrence_count, d.total_files, d.confidence_score, d.source_files, d.description,
                       d.module_name, d.part_name, d.item_type, d.is_checklist
                FROM Default_DB_Values d
                JOIN Equipment_Types e ON d.equipment_type_id = e.id
                WHERE d.equipment_type_id = ? AND d.is_checklist = 1
                ORDER BY d.parameter_name
                ''', (equipment_type_id,))
            else:
                cursor.execute('''
                SELECT d.id, d.parameter_name, d.default_value, d.min_spec, d.max_spec, e.type_name,
                       d.occurrence_count, d.total_files, d.confidence_score, d.source_files, d.description,
                       d.module_name, d.part_name, d.item_type, d.is_checklist
                FROM Default_DB_Values d
                JOIN Equipment_Types e ON d.equipment_type_id = e.id
                WHERE d.equipment_type_id = ?
                ORDER BY d.parameter_name
                ''', (equipment_type_id,))
            
            return cursor.fetchall()

    def update_default_value(self, value_id, **kwargs):
        """Default DB 값 업데이트"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 업데이트 가능한 필드들
            allowed_fields = [
                'parameter_name', 'default_value', 'min_spec', 'max_spec',
                'occurrence_count', 'total_files', 'confidence_score', 'source_files',
                'description', 'module_name', 'part_name', 'item_type', 'is_checklist'
            ]
            
            update_fields = []
            params = []
            
            for field, value in kwargs.items():
                if field in allowed_fields:
                    update_fields.append(f"{field} = ?")
                    params.append(value)
            
            if update_fields:
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                params.append(value_id)
                
                query = f"UPDATE Default_DB_Values SET {', '.join(update_fields)} WHERE id = ?"
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount > 0
            
            return False

    def delete_default_value(self, value_id, conn_override=None):
        """Default DB 값 삭제"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM Default_DB_Values WHERE id = ?', (value_id,))
            conn.commit()
            return cursor.rowcount > 0


    def get_parameter_by_id(self, parameter_id, conn_override=None):
        """특정 ID의 파라미터 정보를 반환합니다"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT d.id, d.equipment_type_id, d.parameter_name, d.default_value, 
                   d.min_spec, d.max_spec, e.type_name, d.description,
                   d.module_name, d.part_name, d.item_type, d.is_checklist,
                   d.occurrence_count, d.total_files, d.confidence_score, d.source_files
            FROM Default_DB_Values d
            JOIN Equipment_Types e ON d.equipment_type_id = e.id
            WHERE d.id = ?
            ''', (parameter_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'id': result[0],
                    'equipment_type_id': result[1],
                    'parameter_name': result[2],
                    'default_value': result[3],
                    'min_spec': result[4],
                    'max_spec': result[5],
                    'equipment_type': result[6],
                    'description': result[7],
                    'module_name': result[8],
                    'part_name': result[9],
                    'item_type': result[10],
                    'is_performance': result[11],  # is_checklist을 is_performance로 매핑 (호환성)
                    'occurrence_count': result[12],
                    'total_files': result[13],
                    'confidence_score': result[14],
                    'source_files': result[15]
                }
            return None

    def get_parameter_statistics(self, equipment_type_id, parameter_name, conn_override=None):
        """파라미터 통계 정보 조회"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT occurrence_count, total_files, confidence_score, source_files, default_value
            FROM Default_DB_Values 
            WHERE equipment_type_id = ? AND parameter_name = ?
            ''', (equipment_type_id, parameter_name))
            result = cursor.fetchone()
            
            if result:
                return {
                    'occurrence_count': result[0],
                    'total_files': result[1],
                    'confidence_score': result[2],
                    'source_files': result[3],
                    'default_value': result[4]
                }
            return None

    def set_performance_status(self, parameter_id, is_performance, conn_override=None):
        """파라미터의 Performance 상태 설정"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            UPDATE Default_DB_Values 
            SET is_checklist = ? 
            WHERE id = ?
            ''', (1 if is_performance else 0, parameter_id))
            conn.commit()
            return cursor.rowcount > 0

    # ==================== 유틸리티 메서드 ====================
    
    def get_checklist_parameter_count(self, equipment_type_id, conn_override=None):
        """Check list 파라미터 개수 조회"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT COUNT(*) FROM Default_DB_Values 
            WHERE equipment_type_id = ? AND is_checklist = 1
            ''', (equipment_type_id,))
            return cursor.fetchone()[0]

    def get_total_parameter_count(self, equipment_type_id, conn_override=None):
        """전체 파라미터 개수 조회"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT COUNT(*) FROM Default_DB_Values
            WHERE equipment_type_id = ?
            ''', (equipment_type_id,))
            return cursor.fetchone()[0]

    # ==================== Phase 1: Check list 관리 ====================

    def add_checklist_item(self, item_name, parameter_pattern, is_common=True,
                          severity_level='MEDIUM', validation_rule=None, description="", conn_override=None):
        """새 Check list 항목 추가"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                INSERT INTO QC_Checklist_Items
                (item_name, parameter_pattern, is_common, severity_level, validation_rule, description)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (item_name, parameter_pattern, 1 if is_common else 0, severity_level, validation_rule, description))
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return None

    def get_checklist_items(self, common_only=False, conn_override=None):
        """Check list 항목 조회"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            if common_only:
                cursor.execute('''
                SELECT id, item_name, parameter_pattern, is_common, severity_level,
                       validation_rule, description
                FROM QC_Checklist_Items
                WHERE is_common = 1
                ORDER BY severity_level, item_name
                ''')
            else:
                cursor.execute('''
                SELECT id, item_name, parameter_pattern, is_common, severity_level,
                       validation_rule, description
                FROM QC_Checklist_Items
                ORDER BY severity_level, item_name
                ''')
            return cursor.fetchall()

    def add_equipment_checklist_mapping(self, equipment_type_id, checklist_item_id,
                                       is_required=True, custom_validation_rule=None,
                                       priority=100, added_reason="", added_by="", conn_override=None):
        """장비별 Check list 매핑 추가"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                INSERT INTO Equipment_Checklist_Mapping
                (equipment_type_id, checklist_item_id, is_required, custom_validation_rule,
                 priority, added_reason, added_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (equipment_type_id, checklist_item_id, 1 if is_required else 0,
                      custom_validation_rule, priority, added_reason, added_by))
                conn.commit()

                # Audit Log 기록
                self._log_checklist_audit('ADD', 'Equipment_Checklist_Mapping', cursor.lastrowid,
                                         None, f"equipment_type_id={equipment_type_id}, checklist_item_id={checklist_item_id}",
                                         added_reason, added_by, conn)

                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return None

    def get_equipment_checklist_items(self, equipment_type_id, conn_override=None):
        """장비별 적용되는 Check list 항목 조회 (공통 + 장비 특화)"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()

            # 공통 Check list 항목
            cursor.execute('''
            SELECT c.id, c.item_name, c.parameter_pattern, c.is_common, c.severity_level,
                   c.validation_rule, c.description, NULL as is_required, NULL as custom_validation_rule,
                   NULL as priority, 'COMMON' as source
            FROM QC_Checklist_Items c
            WHERE c.is_common = 1
              AND c.id NOT IN (
                  SELECT checklist_item_id FROM Equipment_Checklist_Exceptions
                  WHERE equipment_type_id = ?
              )

            UNION

            SELECT c.id, c.item_name, c.parameter_pattern, c.is_common, c.severity_level,
                   COALESCE(m.custom_validation_rule, c.validation_rule) as validation_rule,
                   c.description, m.is_required, m.custom_validation_rule, m.priority, 'SPECIFIC' as source
            FROM QC_Checklist_Items c
            JOIN Equipment_Checklist_Mapping m ON c.id = m.checklist_item_id
            WHERE m.equipment_type_id = ?

            ORDER BY severity_level, item_name
            ''', (equipment_type_id, equipment_type_id))

            return cursor.fetchall()

    def add_checklist_exception(self, equipment_type_id, checklist_item_id, reason,
                               approved_by="", conn_override=None):
        """장비별 Check list 예외 추가 (특정 공통 Check list 제외)"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                INSERT INTO Equipment_Checklist_Exceptions
                (equipment_type_id, checklist_item_id, reason, approved_by, approved_date)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (equipment_type_id, checklist_item_id, reason, approved_by))
                conn.commit()

                # Audit Log 기록
                self._log_checklist_audit('ADD', 'Equipment_Checklist_Exceptions', cursor.lastrowid,
                                         None, f"Exception: equipment_type_id={equipment_type_id}, checklist_item_id={checklist_item_id}",
                                         reason, approved_by, conn)

                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return None

    def log_change_history(self, action, entity_type, entity_name, old_value, new_value, user, conn_override=None):
        """
        일반 변경 이력 기록 (레거시 호환용)

        Equipment Types, Default DB Parameters 등의 변경 이력을 기록합니다.
        내부적으로 Checklist_Audit_Log 테이블을 재사용합니다.

        Args:
            action (str): 작업 유형 ('add', 'update', 'delete', 'bulk_add')
            entity_type (str): 엔티티 종류 ('equipment_type', 'parameter' 등)
            entity_name (str): 엔티티 이름
            old_value (str): 이전 값 (삭제/수정 시)
            new_value (str): 새 값 (추가/수정 시)
            user (str): 작업 수행자
            conn_override: 외부 연결 객체 (선택사항)
        """
        # action 매핑 (소문자 → 대문자)
        action_map = {
            'add': 'ADD',
            'update': 'MODIFY',
            'delete': 'REMOVE',
            'bulk_add': 'ADD'
        }

        mapped_action = action_map.get(action, action.upper())

        # _log_checklist_audit 메서드 활용
        self._log_checklist_audit(
            action=mapped_action,
            target_table=entity_type,
            target_id=None,  # 일반 이력에서는 ID 불필요
            old_value=old_value if old_value else None,
            new_value=new_value if new_value else None,
            reason=f"{entity_name}",
            user=user,
            conn_override=conn_override
        )

    def _log_checklist_audit(self, action, target_table, target_id, old_value, new_value,
                            reason, user, conn_override=None):
        """Check list 변경 이력 기록 (내부 메서드)"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO Checklist_Audit_Log
            (action, target_table, target_id, old_value, new_value, reason, user)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (action, target_table, target_id, old_value, new_value, reason, user))
            conn.commit()

    def get_checklist_audit_log(self, limit=100, conn_override=None):
        """Check list 변경 이력 조회"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT id, action, target_table, target_id, old_value, new_value, reason, user, timestamp
            FROM Checklist_Audit_Log
            ORDER BY timestamp DESC
            LIMIT ?
            ''', (limit,))
            return cursor.fetchall()

    def get_checklist_audit_logs(self, limit=100, conn_override=None):
        """Check list 변경 이력 조회 (복수형 별칭)"""
        return self.get_checklist_audit_log(limit, conn_override)

    def update_checklist_item(self, item_id, item_name=None, parameter_pattern=None,
                             severity_level=None, validation_rule=None, description=None,
                             user="", conn_override=None):
        """Check list 항목 수정"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()

            # 기존 데이터 조회 (Audit Log용)
            cursor.execute('SELECT item_name, parameter_pattern, severity_level, validation_rule, description FROM QC_Checklist_Items WHERE id = ?', (item_id,))
            old_row = cursor.fetchone()
            if not old_row:
                return False

            # 업데이트할 필드만 변경
            updates = []
            params = []

            if item_name is not None:
                updates.append("item_name = ?")
                params.append(item_name)

            if parameter_pattern is not None:
                updates.append("parameter_pattern = ?")
                params.append(parameter_pattern)

            if severity_level is not None:
                updates.append("severity_level = ?")
                params.append(severity_level)

            if validation_rule is not None:
                updates.append("validation_rule = ?")
                params.append(validation_rule)

            if description is not None:
                updates.append("description = ?")
                params.append(description)

            if not updates:
                return False  # 변경사항 없음

            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(item_id)

            # 업데이트 실행
            cursor.execute(f'''
            UPDATE QC_Checklist_Items
            SET {', '.join(updates)}
            WHERE id = ?
            ''', params)
            conn.commit()

            # Audit Log 기록
            old_value = f"name={old_row[0]}, severity={old_row[2]}"
            new_value = f"name={item_name or old_row[0]}, severity={severity_level or old_row[2]}"
            self._log_checklist_audit('MODIFY', 'QC_Checklist_Items', item_id,
                                     old_value, new_value, 'Item updated', user, conn)

            return True

    def delete_checklist_item(self, item_id, user="", conn_override=None):
        """Check list 항목 삭제"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()

            # 기존 데이터 조회 (Audit Log용)
            cursor.execute('SELECT item_name FROM QC_Checklist_Items WHERE id = ?', (item_id,))
            row = cursor.fetchone()
            if not row:
                return False

            item_name = row[0]

            # 관련 매핑 먼저 삭제
            cursor.execute('DELETE FROM Equipment_Checklist_Mapping WHERE checklist_item_id = ?', (item_id,))

            # 관련 예외 삭제
            cursor.execute('DELETE FROM Equipment_Checklist_Exceptions WHERE checklist_item_id = ?', (item_id,))

            # 항목 삭제
            cursor.execute('DELETE FROM QC_Checklist_Items WHERE id = ?', (item_id,))
            conn.commit()

            # Audit Log 기록
            self._log_checklist_audit('REMOVE', 'QC_Checklist_Items', item_id,
                                     item_name, None, 'Item deleted', user, conn)

            return True

    def delete_equipment_checklist_mapping(self, mapping_id, user="", conn_override=None):
        """장비별 Check list 매핑 삭제"""
        with self.get_connection(conn_override) as conn:
            cursor = conn.cursor()

            # 기존 데이터 조회 (Audit Log용)
            cursor.execute('''
            SELECT equipment_type_id, checklist_item_id
            FROM Equipment_Checklist_Mapping
            WHERE id = ?
            ''', (mapping_id,))
            row = cursor.fetchone()
            if not row:
                return False

            # 매핑 삭제
            cursor.execute('DELETE FROM Equipment_Checklist_Mapping WHERE id = ?', (mapping_id,))
            conn.commit()

            # Audit Log 기록
            old_value = f"equipment_type_id={row[0]}, checklist_item_id={row[1]}"
            self._log_checklist_audit('REMOVE', 'Equipment_Checklist_Mapping', mapping_id,
                                     old_value, None, 'Mapping deleted', user, conn)

            return True