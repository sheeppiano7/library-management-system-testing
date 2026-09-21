# -*- coding: utf-8 -*-
"""
跨数据库同步服务
支持实时同步和周期同步
"""
import os
# 在导入任何PostgreSQL相关模块之前设置环境变量
os.environ['PGCLIENTENCODING'] = 'UTF8'

from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
import config
from db_connector import db_connector
from models import Book, Reader, Borrow, User, SyncLog
import logging
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SyncService:
    """同步服务类"""
    
    def __init__(self):
        self.real_time_sync_enabled = config.SYNC_CONFIG["real_time_sync"]
    
    def log_sync(self, db_name, op_type, sync_status, is_conflict=False, conflict_desc=None):
        """记录同步日志"""
        session = None
        try:
            session = db_connector.get_session("mysql")  # 日志统一记录到MySQL
            
            # 截断冲突描述，确保不超过200个字符（数据库字段限制）
            if conflict_desc and len(conflict_desc) > 200:
                conflict_desc = conflict_desc[:197] + "..."
            
            log = SyncLog(
                db_name=db_name,
                op_type=op_type,
                sync_status=sync_status,
                is_conflict=is_conflict,
                conflict_desc=conflict_desc,
                sync_time=datetime.now()
            )
            session.add(log)
            session.commit()
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"记录同步日志失败: {str(e)}")
    
    def sync_data(self, target_db, op_type, model_class, data_dict, record_id=None, source_update_time=None):
        """同步数据到目标数据库"""
        try:
            session = db_connector.get_session(target_db)
            from sqlalchemy import text
            
            # PostgreSQL特殊处理：使用原始SQL避免编码问题
            if target_db == "postgresql":
                try:
                    # 设置编码
                    session.execute(text("SET client_encoding = 'UTF8'"))
                    session.commit()
                except Exception as e:
                    # 编码设置失败，记录警告但继续
                    error_msg = str(e).lower()
                    if "codec" not in error_msg and "utf" not in error_msg:
                        pass  # 静默忽略
            
                # PostgreSQL使用原始SQL
                if op_type == "增":
                    # 获取表名
                    table_name = model_class.__tablename__
                    # 构建INSERT SQL
                    columns = list(data_dict.keys())
                    placeholders = [f":{col}" for col in columns]
                    sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
                    
                    try:
                        session.execute(text(sql), data_dict)
                        session.commit()
                        self.log_sync(target_db, op_type, "成功")
                        logger.info(f"数据同步成功: {target_db} - {op_type} - {model_class.__name__} (使用原始SQL)")
                        return True
                    except Exception as e:
                        error_msg = str(e).lower()
                        if "codec" in error_msg or "utf" in error_msg:
                            logger.error(f"PostgreSQL同步失败（编码问题）: {str(e)}")
                        else:
                            logger.error(f"PostgreSQL同步失败: {str(e)}")
                        session.rollback()
                        self.log_sync(target_db, op_type, "失败")
                        return False
                
                elif op_type == "删":
                    if record_id:
                        table_name = model_class.__tablename__
                        pk_columns = list(model_class.__table__.primary_key.columns)
                        if pk_columns:
                            pk_column = pk_columns[0].name
                            sql = f"DELETE FROM {table_name} WHERE {pk_column} = :record_id"
                            try:
                                session.execute(text(sql), {"record_id": record_id})
                                session.commit()
                                self.log_sync(target_db, op_type, "成功")
                                logger.info(f"数据同步成功: {target_db} - {op_type} - {model_class.__name__} (使用原始SQL)")
                                return True
                            except Exception as e:
                                session.rollback()
                                self.log_sync(target_db, op_type, "失败")
                                logger.error(f"PostgreSQL同步失败: {str(e)}")
                                return False
                
                elif op_type == "改":
                    if record_id:
                        table_name = model_class.__tablename__
                        pk_columns = list(model_class.__table__.primary_key.columns)
                        if pk_columns:
                            pk_column = pk_columns[0].name
                            # 构建UPDATE SQL
                            set_clause = ", ".join([f"{k} = :{k}" for k in data_dict.keys()])
                            # 如果提供了源记录的 update_time，使用它；否则使用当前时间
                            if source_update_time:
                                sql = f"UPDATE {table_name} SET {set_clause}, update_time = :update_time WHERE {pk_column} = :record_id"
                                params = {**data_dict, "record_id": record_id, "update_time": source_update_time}
                            else:
                                sql = f"UPDATE {table_name} SET {set_clause}, update_time = CURRENT_TIMESTAMP WHERE {pk_column} = :record_id"
                                params = {**data_dict, "record_id": record_id}
                            try:
                                session.execute(text(sql), params)
                                session.commit()
                                self.log_sync(target_db, op_type, "成功")
                                logger.info(f"数据同步成功: {target_db} - {op_type} - {model_class.__name__} (使用原始SQL)")
                                return True
                            except Exception as e:
                                session.rollback()
                                self.log_sync(target_db, op_type, "失败")
                                logger.error(f"PostgreSQL同步失败: {str(e)}")
                                return False
                
                return False
            
            # MySQL和SQL Server使用ORM
            if op_type == "增":
                # 新增操作
                new_record = model_class(**data_dict)
                session.add(new_record)
                session.commit()
                self.log_sync(target_db, op_type, "成功")
                logger.info(f"数据同步成功: {target_db} - {op_type} - {model_class.__name__}")
                return True
                
            elif op_type == "删":
                # 删除操作
                if record_id:
                    # 获取主键字段名
                    pk_columns = list(model_class.__table__.primary_key.columns)
                    if pk_columns:
                        pk_column = pk_columns[0].name
                        record = session.query(model_class).filter_by(**{pk_column: record_id}).first()
                        if record:
                            session.delete(record)
                            session.commit()
                            self.log_sync(target_db, op_type, "成功")
                            logger.info(f"数据同步成功: {target_db} - {op_type} - {model_class.__name__}")
                            return True
                
            elif op_type == "改":
                # 修改操作
                if record_id:
                    # 获取主键字段名
                    pk_columns = list(model_class.__table__.primary_key.columns)
                    if pk_columns:
                        pk_column = pk_columns[0].name
                        record = session.query(model_class).filter_by(**{pk_column: record_id}).first()
                        if record:
                            for key, value in data_dict.items():
                                if hasattr(record, key):
                                    setattr(record, key, value)
                            # 如果提供了源记录的 update_time，使用它；否则使用当前时间
                            if source_update_time:
                                record.update_time = source_update_time
                            else:
                                record.update_time = datetime.now()
                            session.commit()
                            self.log_sync(target_db, op_type, "成功")
                            logger.info(f"数据同步成功: {target_db} - {op_type} - {model_class.__name__} - ID={record_id}")
                            return True
                        else:
                            logger.warning(f"记录不存在: {target_db} - {model_class.__name__} - ID={record_id}")
                            return False
            
        except SQLAlchemyError as e:
            session.rollback()
            self.log_sync(target_db, op_type, "失败")
            logger.error(f"数据同步失败: {target_db} - {op_type} - {str(e)}")
            return False
        except Exception as e:
            logger.error(f"数据同步异常: {target_db} - {op_type} - {str(e)}")
            return False
    
    def sync_to_other_dbs(self, source_db, op_type, model_class, data_dict, record_id=None):
        """同步数据到其他数据库"""
        if not self.real_time_sync_enabled:
            return
        
        other_dbs = [db for db in config.DB_CONFIG.keys() if db != source_db]
        for target_db in other_dbs:
            self.sync_data(target_db, op_type, model_class, data_dict, record_id)
    
    def get_all_conflicts(self):
        """获取所有当前存在的冲突列表（不记录日志）"""
        try:
            conflicts = []
            
            # 检查所有表的所有记录
            tables = [
                ("books", Book, "book_id"),
                ("readers", Reader, "reader_id"),
                ("borrows", Borrow, "borrow_id"),
                ("users", User, "user_id")
            ]
            
            for table_name, model_class, id_field in tables:
                # 获取 MySQL 中的所有记录ID
                session_mysql = db_connector.get_session("mysql")
                all_ids = {getattr(r, id_field) for r in session_mysql.query(model_class).all()}
                
                # 检查每个记录是否有冲突（不记录日志）
                for record_id in all_ids:
                    if self._check_conflict_silent(table_name, record_id):
                        # 获取冲突详情
                        success, records, times = self.get_conflict_details(table_name, record_id)
                        if success:
                            conflicts.append({
                                "table_name": table_name,
                                "record_id": record_id,
                                "records": records,
                                "times": times
                            })
            
            return True, conflicts
            
        except Exception as e:
            logger.error(f"获取所有冲突失败: {str(e)}")
            return False, []
    
    def _check_conflict_silent(self, table_name, record_id):
        """静默检查冲突（不记录日志和发送邮件）- 忽略update_time，只比较其他字段"""
        try:
            records = {}
            
            for db_type in config.DB_CONFIG.keys():
                session = db_connector.get_session(db_type)
                
                # 根据表名获取对应的模型类
                model_map = {
                    "books": Book,
                    "readers": Reader,
                    "borrows": Borrow,
                    "users": User
                }
                
                model_class = model_map.get(table_name)
                if not model_class:
                    continue
                
                # 获取主键字段名
                pk_columns = list(model_class.__table__.primary_key.columns)
                if pk_columns:
                    pk_column = pk_columns[0].name
                    record = session.query(model_class).filter_by(**{pk_column: record_id}).first()
                else:
                    continue
                
                if record:
                    records[db_type] = record
                else:
                    records[db_type] = None
            
            # 获取所有有记录的数据库
            valid_records = {k: v for k, v in records.items() if v is not None}
            
            if len(valid_records) < 2:
                return False  # 至少需要2个数据库有记录才能比较
            
            # 获取第一个记录作为基准
            first_db = list(valid_records.keys())[0]
            first_record = valid_records[first_db]
            
            # 获取主键字段名
            pk_columns = list(first_record.__table__.primary_key.columns)
            pk_column = pk_columns[0].name if pk_columns else None
            
            # 比较所有非主键、非时间字段
            for db_type, record in valid_records.items():
                if db_type == first_db:
                    continue
                
                # 比较每个字段（除了主键和update_time）
                for column in first_record.__table__.columns:
                    if column.name == pk_column or column.name == "update_time":
                        continue
                    
                    first_val = getattr(first_record, column.name, None)
                    other_val = getattr(record, column.name, None)
                    
                    # 如果字段值不同，认为有冲突
                    if first_val != other_val:
                        return True
            
            return False  # 所有字段都一致，无冲突
            
        except Exception as e:
            logger.error(f"静默冲突检测失败: {str(e)}")
            return False
    
    def get_conflict_details(self, table_name, record_id):
        """获取冲突的详细信息"""
        try:
            records = {}
            times = {}
            
            for db_type in config.DB_CONFIG.keys():
                session = db_connector.get_session(db_type)
                
                # 根据表名获取对应的模型类
                model_map = {
                    "books": Book,
                    "readers": Reader,
                    "borrows": Borrow,
                    "users": User
                }
                
                model_class = model_map.get(table_name)
                if not model_class:
                    continue
                
                # 获取主键字段名
                pk_columns = list(model_class.__table__.primary_key.columns)
                if pk_columns:
                    pk_column = pk_columns[0].name
                    record = session.query(model_class).filter_by(**{pk_column: record_id}).first()
                else:
                    continue
                
                if record:
                    records[db_type] = record
                    times[db_type] = record.update_time
                else:
                    records[db_type] = None
                    times[db_type] = None
            
            return True, records, times
            
        except Exception as e:
            logger.error(f"获取冲突详情失败: {str(e)}")
            return False, {}, {}
    
    def check_conflict(self, table_name, record_id):
        """检查数据冲突 - 忽略update_time，只比较其他字段"""
        try:
            records = {}
            
            for db_type in config.DB_CONFIG.keys():
                session = db_connector.get_session(db_type)
                
                # 根据表名获取对应的模型类
                model_map = {
                    "books": Book,
                    "readers": Reader,
                    "borrows": Borrow,
                    "users": User
                }
                
                model_class = model_map.get(table_name)
                if not model_class:
                    continue
                
                # 获取主键字段名
                pk_columns = list(model_class.__table__.primary_key.columns)
                if pk_columns:
                    pk_column = pk_columns[0].name
                    record = session.query(model_class).filter_by(**{pk_column: record_id}).first()
                else:
                    continue
                
                if record:
                    records[db_type] = record
                else:
                    records[db_type] = None
            
            # 获取所有有记录的数据库
            valid_records = {k: v for k, v in records.items() if v is not None}
            
            if len(valid_records) < 2:
                return False  # 至少需要2个数据库有记录才能比较
            
            # 获取第一个记录作为基准
            first_db = list(valid_records.keys())[0]
            first_record = valid_records[first_db]
            
            # 获取主键字段名
            pk_columns = list(first_record.__table__.primary_key.columns)
            pk_column = pk_columns[0].name if pk_columns else None
            
            # 找出不一致的字段
            conflict_fields = []
            
            # 比较所有非主键、非时间字段
            for db_type, record in valid_records.items():
                if db_type == first_db:
                    continue
                
                # 比较每个字段（除了主键和update_time）
                for column in first_record.__table__.columns:
                    if column.name == pk_column or column.name == "update_time":
                        continue
                    
                    first_val = getattr(first_record, column.name, None)
                    other_val = getattr(record, column.name, None)
                    
                    # 如果字段值不同，记录冲突字段（简化格式，只显示字段名）
                    if first_val != other_val:
                        # 简化格式，只显示字段名，避免描述过长
                        conflict_fields.append(column.name)
            
            # 如果有字段不一致，认为有冲突
            if conflict_fields:
                # 确保冲突描述不包含换行符，并限制长度
                # 只显示前3个不一致的字段，避免描述过长
                display_fields = conflict_fields[:3]
                if len(conflict_fields) > 3:
                    conflict_desc = f"表{table_name}，记录ID{record_id}字段不一致: {', '.join(display_fields)}等{len(conflict_fields)}个字段"
                else:
                    conflict_desc = f"表{table_name}，记录ID{record_id}字段不一致: {', '.join(display_fields)}"
                conflict_desc = conflict_desc.replace('\n', ' ').replace('\r', ' ')
                # 确保不超过200字符
                if len(conflict_desc) > 200:
                    conflict_desc = conflict_desc[:197] + "..."
                self.log_sync("system", "冲突", "失败", is_conflict=True, conflict_desc=conflict_desc)
                
                # 发送邮件提醒
                self.send_conflict_email(table_name, record_id, records)
                return True
            
            return False  # 所有字段都一致，无冲突
            
        except Exception as e:
            logger.error(f"冲突检测失败: {str(e)}")
            return False
    
    def resolve_conflict(self, table_name, record_id, source_db):
        """解决冲突：以指定数据库的数据为准，同步到其他数据库"""
        try:
            logger.info(f"开始解决冲突: {table_name} - ID={record_id} - 源数据库={source_db}")
            success, records, times = self.get_conflict_details(table_name, record_id)
            if not success or source_db not in records or records[source_db] is None:
                error_msg = "无法获取冲突详情或源数据库记录不存在"
                logger.error(f"解决冲突失败: {error_msg}")
                return False, error_msg
            
            source_record = records[source_db]
            logger.info(f"源记录: {source_record}")
            
            # 根据表名获取对应的模型类
            model_map = {
                "books": Book,
                "readers": Reader,
                "borrows": Borrow,
                "users": User
            }
            
            model_class = model_map.get(table_name)
            if not model_class:
                error_msg = "未知的表名"
                logger.error(f"解决冲突失败: {error_msg}")
                return False, error_msg
            
            # 同步到其他数据库
            data_dict = {}
            pk_columns = list(model_class.__table__.primary_key.columns)
            pk_column = pk_columns[0].name if pk_columns else None
            
            for column in model_class.__table__.columns:
                if column.name != pk_column and column.name != "update_time":
                    data_dict[column.name] = getattr(source_record, column.name)
            
            logger.info(f"准备同步的数据: {data_dict}")
            
            synced_count = 0
            failed_dbs = []
            
            for db_type in config.DB_CONFIG.keys():
                if db_type == source_db:
                    continue
                
                try:
                    # 检查目标数据库是否有该记录
                    session_target = db_connector.get_session(db_type)
                    target_record = records.get(db_type)
                    
                    # 对于 readers 表，需要特殊处理：优先更新原 ID 的记录
                    if table_name == "readers":
                        # 先检查原 ID 的记录是否存在
                        target_record_by_id = session_target.query(Reader).filter_by(reader_id=record_id).first()
                        
                        if target_record_by_id:
                            # 原 ID 的记录存在，直接更新
                            logger.info(f"更新原ID记录: {db_type} - ID={record_id}")
                            result = self.sync_data(db_type, "改", model_class, data_dict, record_id, source_record.update_time)
                            
                            # 如果通过 phone 找到了其他 ID 的记录，需要删除它（避免重复）
                            if source_record.phone:
                                existing_reader = session_target.query(Reader).filter_by(phone=source_record.phone).first()
                                if existing_reader and existing_reader.reader_id != record_id:
                                    logger.info(f"删除重复记录: {db_type} - phone={source_record.phone}, ID={existing_reader.reader_id}")
                                    try:
                                        session_target.delete(existing_reader)
                                        session_target.commit()
                                    except Exception as e:
                                        logger.warning(f"删除重复记录失败: {str(e)}")
                                        session_target.rollback()
                        else:
                            # 原 ID 不存在，检查是否有相同 phone 的记录
                            if source_record.phone:
                                existing_reader = session_target.query(Reader).filter_by(phone=source_record.phone).first()
                                if existing_reader:
                                    # 找到了相同 phone 但不同 ID 的记录，需要先删除它，然后插入新记录
                                    logger.info(f"删除phone重复记录: {db_type} - phone={source_record.phone}, ID={existing_reader.reader_id}")
                                    try:
                                        session_target.delete(existing_reader)
                                        session_target.commit()
                                    except Exception as e:
                                        logger.warning(f"删除phone重复记录失败: {str(e)}")
                                        session_target.rollback()
                            
                            # 插入新记录（使用原 ID，但需要手动设置 ID）
                            logger.info(f"插入新记录: {db_type} - ID={record_id}")
                            # 对于自增主键，我们需要先设置 ID，然后插入
                            try:
                                # 构建包含 ID 的完整数据
                                full_data_dict = {**data_dict}
                                # 对于 PostgreSQL，使用原始 SQL 插入并指定 ID
                                if db_type == "postgresql":
                                    from sqlalchemy import text
                                    columns = list(full_data_dict.keys()) + [pk_column]
                                    values = list(full_data_dict.values()) + [record_id]
                                    placeholders = [f":{col}" for col in columns]
                                    sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
                                    params = {**full_data_dict, pk_column: record_id}
                                    session_target.execute(text(sql), params)
                                    session_target.commit()
                                    result = True
                                    logger.info(f"PostgreSQL插入成功: {db_type} - {table_name} - ID={record_id}")
                                else:
                                    # MySQL 和 SQL Server：先设置 ID，然后插入
                                    new_record = model_class(**full_data_dict)
                                    setattr(new_record, pk_column, record_id)
                                    session_target.add(new_record)
                                    session_target.commit()
                                    result = True
                                    logger.info(f"插入成功: {db_type} - {table_name} - ID={record_id}")
                            except Exception as e:
                                logger.error(f"插入新记录失败: {db_type} - {table_name} - ID={record_id} - {str(e)}")
                                session_target.rollback()
                                result = False
                    elif target_record is None:
                        # 插入新记录
                        # 对于 borrows 表，检查外键约束
                        if table_name == "borrows":
                            book_exists = session_target.query(Book).filter_by(book_id=source_record.book_id).first()
                            reader_exists = session_target.query(Reader).filter_by(reader_id=source_record.reader_id).first()
                            if not book_exists or not reader_exists:
                                logger.warning(f"跳过同步：{db_type} 中缺少关联的 book_id={source_record.book_id} 或 reader_id={source_record.reader_id}")
                                failed_dbs.append(f"{db_type}(缺少外键关联)")
                                continue
                        result = self.sync_data(db_type, "增", model_class, data_dict, None, source_record.update_time)
                    else:
                        # 更新现有记录
                        result = self.sync_data(db_type, "改", model_class, data_dict, record_id, source_record.update_time)
                    
                    if result:
                        synced_count += 1
                        logger.info(f"冲突解决同步成功: {db_type} - {table_name} - ID={record_id}")
                    else:
                        failed_dbs.append(db_type)
                        logger.warning(f"冲突解决同步失败: {db_type} - {table_name} - ID={record_id}")
                        
                except Exception as e:
                    failed_dbs.append(f"{db_type}({str(e)})")
                    logger.error(f"冲突解决同步异常: {db_type} - {table_name} - ID={record_id} - {str(e)}")
            
            # 验证同步结果：重新检测是否还有冲突
            still_has_conflict = self._check_conflict_silent(table_name, record_id)
            
            if still_has_conflict:
                logger.warning(f"处理冲突后，记录 {table_name}-{record_id} 仍然存在冲突")
                # 记录冲突解决日志（使用允许的 op_type 值）
                self.log_sync("system", "冲突", "失败", is_conflict=True, 
                             conflict_desc=f"表{table_name}，记录ID{record_id}，以{source_db}数据库数据为准，已同步到{synced_count}个数据库，但仍存在冲突")
                
                if synced_count > 0:
                    return True, f"已同步到 {synced_count} 个数据库，但仍有冲突（失败: {', '.join(failed_dbs) if failed_dbs else '无'}）"
                else:
                    return False, f"同步失败，所有数据库同步都失败: {', '.join(failed_dbs)}"
            else:
                # 记录冲突解决日志（使用允许的 op_type 值）
                self.log_sync("system", "冲突", "成功", is_conflict=False, 
                             conflict_desc=f"表{table_name}，记录ID{record_id}，以{source_db}数据库数据为准，已同步到{synced_count}个数据库，冲突已完全解决")
                
                return True, f"冲突已完全解决，已同步到 {synced_count} 个数据库"
            
        except Exception as e:
            logger.error(f"解决冲突失败: {str(e)}")
            return False, f"解决冲突失败: {str(e)}"
    
    def send_conflict_email(self, table_name, record_id, records):
        """发送冲突邮件提醒"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.header import Header
            
            # 检查邮件配置是否完整
            if not all(key in config.EMAIL_CONFIG for key in ["sender_email", "admin_email", "smtp_server", "smtp_port", "sender_password"]):
                logger.warning("邮件配置不完整，跳过邮件发送")
                return
            
            conflict_info = f"检测到数据冲突：\n表名: {table_name}\n记录ID: {record_id}\n\n"
            for db_type, record in records.items():
                conflict_info += f"{db_type}数据库: {record}\n"
            conflict_info += "\n请及时处理！"
            
            msg = MIMEText(conflict_info, "plain", "utf-8")
            msg["From"] = config.EMAIL_CONFIG["sender_email"]
            msg["To"] = config.EMAIL_CONFIG["admin_email"]
            msg["Subject"] = Header("图书管理系统数据冲突提醒", "utf-8")
            
            smtp = smtplib.SMTP_SSL(config.EMAIL_CONFIG["smtp_server"], config.EMAIL_CONFIG["smtp_port"])
            smtp.login(config.EMAIL_CONFIG["sender_email"], config.EMAIL_CONFIG["sender_password"])
            smtp.sendmail(config.EMAIL_CONFIG["sender_email"], config.EMAIL_CONFIG["admin_email"], msg.as_string())
            smtp.quit()
            
            logger.info(f"冲突邮件发送成功: {table_name} - ID={record_id}")
            
        except smtplib.SMTPException as e:
            logger.warning(f"发送冲突邮件失败（SMTP错误）: {str(e)}")
        except Exception as e:
            logger.warning(f"发送冲突邮件失败: {str(e)}")
    
    def sync_all_dbs(self):
        """周期同步：对比所有数据库，同步差异数据"""
        try:
            logger.info("=" * 50)
            logger.info("开始周期同步...")
            
            # 同步所有表
            tables = [
                ("books", Book, "book_id"),
                ("readers", Reader, "reader_id"),
                ("borrows", Borrow, "borrow_id"),
                ("users", User, "user_id")
            ]
            
            total_synced = 0
            
            for table_name, model_class, id_field in tables:
                logger.info(f"处理表: {table_name}")
                # 获取所有数据库中的记录
                all_records = {}
                for db_type in config.DB_CONFIG.keys():
                    session = db_connector.get_session(db_type)
                    records = session.query(model_class).all()
                    all_records[db_type] = {getattr(r, id_field): r for r in records}
                    logger.info(f"  {db_type}: {len(records)} 条记录")
                
                # 找出差异并同步
                all_ids = set()
                for records in all_records.values():
                    all_ids.update(records.keys())
                
                for record_id in all_ids:
                    # 找出所有数据库中该记录的最新版本（update_time 最大的）
                    records_by_db = {}
                    for db_type in config.DB_CONFIG.keys():
                        if record_id in all_records[db_type]:
                            records_by_db[db_type] = all_records[db_type][record_id]
                    
                    if not records_by_db:
                        continue
                    
                    # 找出最新的记录（update_time 最大的）
                    latest_db = None
                    latest_record = None
                    latest_time = None
                    for db_type, record in records_by_db.items():
                        if record.update_time and (latest_time is None or record.update_time > latest_time):
                            latest_time = record.update_time
                            latest_db = db_type
                            latest_record = record
                    
                    # 如果没有 update_time，默认使用 MySQL 的记录
                    if latest_record is None:
                        if "mysql" in records_by_db:
                            latest_db = "mysql"
                            latest_record = records_by_db["mysql"]
                        else:
                            latest_db = list(records_by_db.keys())[0]
                            latest_record = records_by_db[latest_db]
                    
                    # 同步到所有其他数据库
                    for db_type in config.DB_CONFIG.keys():
                        if db_type == latest_db:
                            continue  # 跳过源数据库
                        
                        target_record = records_by_db.get(db_type)
                        
                        # 情况1：目标数据库没有该记录，需要插入
                        if target_record is None:
                            # 检查目标数据库是否已存在相同唯一约束的记录（避免重复插入）
                            session_target = db_connector.get_session(db_type)
                            should_insert = True
                            should_update_existing = False
                            existing_record_id = None
                            
                            # 对于 readers 表，检查 phone 是否已存在
                            if table_name == "readers" and latest_record.phone:
                                existing_reader = session_target.query(Reader).filter_by(phone=latest_record.phone).first()
                                if existing_reader:
                                    # 已存在相同 phone 的记录，更新该记录而不是插入
                                    logger.info(f"更新记录：{db_type} 中已存在 phone={latest_record.phone} 的记录（ID={existing_reader.reader_id}），将更新")
                                    should_insert = False
                                    should_update_existing = True
                                    existing_record_id = existing_reader.reader_id
                            
                            # 对于 borrows 表，检查外键约束（book_id 和 reader_id 必须存在）
                            if table_name == "borrows" and should_insert:
                                book_exists = session_target.query(Book).filter_by(book_id=latest_record.book_id).first()
                                reader_exists = session_target.query(Reader).filter_by(reader_id=latest_record.reader_id).first()
                                if not book_exists or not reader_exists:
                                    logger.warning(f"跳过同步：{db_type} 中缺少关联的 book_id={latest_record.book_id} 或 reader_id={latest_record.reader_id}")
                                    should_insert = False
                            
                            if should_insert:
                                # 插入数据
                                logger.info(f"同步插入：{db_type} - {table_name} - ID={record_id}")
                                data_dict = {}
                                pk_columns = list(model_class.__table__.primary_key.columns)
                                pk_column = pk_columns[0].name if pk_columns else None
                                for column in model_class.__table__.columns:
                                    if column.name != pk_column and column.name != "update_time":
                                        data_dict[column.name] = getattr(latest_record, column.name)
                                
                                result = self.sync_data(db_type, "增", model_class, data_dict, None, latest_record.update_time)
                                if result:
                                    total_synced += 1
                            
                            elif should_update_existing:
                                # 更新已存在的记录（通过唯一约束找到的）
                                logger.info(f"同步更新（唯一约束匹配）：{db_type} - {table_name} - ID={existing_record_id}")
                                data_dict = {}
                                pk_columns = list(model_class.__table__.primary_key.columns)
                                pk_column = pk_columns[0].name if pk_columns else None
                                for column in model_class.__table__.columns:
                                    if column.name != pk_column and column.name != "update_time":
                                        data_dict[column.name] = getattr(latest_record, column.name)
                                
                                result = self.sync_data(db_type, "改", model_class, data_dict, existing_record_id, latest_record.update_time)
                                if result:
                                    total_synced += 1
                        
                        # 情况2：目标数据库有该记录，但内容可能不同，需要更新
                        else:
                            # 检查是否需要更新（比较 update_time 或字段值）
                            need_update = False
                            
                            # 如果 update_time 不同，需要更新
                            if latest_record.update_time and target_record.update_time:
                                if latest_record.update_time > target_record.update_time:
                                    need_update = True
                                    logger.info(f"检测到时间差异：{db_type} - {table_name} - ID={record_id}，最新时间={latest_record.update_time}，目标时间={target_record.update_time}")
                            elif latest_record.update_time and not target_record.update_time:
                                need_update = True
                                logger.info(f"检测到时间差异：{db_type} - {table_name} - ID={record_id}，最新有时间，目标无时间")
                            
                            # 如果 update_time 相同，但其他字段可能不同，也更新（确保数据一致）
                            if not need_update:
                                # 比较所有非主键、非时间字段
                                pk_columns = list(model_class.__table__.primary_key.columns)
                                pk_column = pk_columns[0].name if pk_columns else None
                                for column in model_class.__table__.columns:
                                    if column.name != pk_column and column.name not in ["update_time", "reg_date", "borrow_date", "return_date"]:
                                        latest_val = getattr(latest_record, column.name, None)
                                        target_val = getattr(target_record, column.name, None)
                                        if latest_val != target_val:
                                            need_update = True
                                            logger.info(f"检测到字段差异：{db_type} - {table_name} - ID={record_id}，字段={column.name}，最新值={latest_val}，目标值={target_val}")
                                            break
                            
                            if need_update:
                                # 更新数据
                                logger.info(f"同步更新：{db_type} - {table_name} - ID={record_id}")
                                data_dict = {}
                                pk_columns = list(model_class.__table__.primary_key.columns)
                                pk_column = pk_columns[0].name if pk_columns else None
                                for column in model_class.__table__.columns:
                                    if column.name != pk_column and column.name != "update_time":
                                        data_dict[column.name] = getattr(latest_record, column.name)
                                
                                result = self.sync_data(db_type, "改", model_class, data_dict, record_id, latest_record.update_time)
                                if result:
                                    logger.info(f"更新成功：{db_type} - {table_name} - ID={record_id}")
                                    total_synced += 1
                                else:
                                    logger.error(f"更新失败：{db_type} - {table_name} - ID={record_id}")
                            else:
                                logger.debug(f"无需更新：{db_type} - {table_name} - ID={record_id}，数据已一致")
                
                logger.info(f"表 {table_name} 处理完成")
            
            logger.info(f"周期同步完成，共同步 {total_synced} 条记录")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"周期同步失败: {str(e)}")


# 同步装饰器
def sync_decorator(func):
    """同步装饰器：拦截增删改操作，同步至其他数据库"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 执行原操作
        result = func(*args, **kwargs)
        
        # 如果操作成功，进行同步
        if result and isinstance(result, tuple) and len(result) >= 3:
            success, op_type, model_class, data_dict, record_id = result[:5]
            source_db = kwargs.get("db_type", "mysql")
            
            if success:
                sync_service = SyncService()
                sync_service.sync_to_other_dbs(source_db, op_type, model_class, data_dict, record_id)
        
        return result
    return wrapper


# 全局同步服务实例
sync_service = SyncService()

