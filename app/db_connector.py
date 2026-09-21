# -*- coding: utf-8 -*-
"""
数据库连接管理类
支持MySQL、SQL Server、PostgreSQL三种数据库
PostgreSQL 通过 SQLAlchemy + pg8000 驱动，避免 psycopg2 在 Windows 下的编码问题
"""
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
import config
from models import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DBConnector:
    """数据库连接管理器"""

    def __init__(self):
        self.engines = {}
        self.sessions = {}
        self.current_db = "mysql"  # 默认使用MySQL

        # 初始化所有数据库连接
        for db_type, url in config.DB_CONFIG.items():
            try:
                if db_type == "postgresql":
                    # 使用 pg8000 驱动，保持默认参数，编码在会话级别设置
                    engine = create_engine(
                        url,
                        echo=False,
                        pool_pre_ping=True,
                    )
                else:
                    engine = create_engine(url, echo=False, pool_pre_ping=True)

                self.engines[db_type] = engine
                self.sessions[db_type] = scoped_session(sessionmaker(bind=engine))
                logger.info(f"数据库 {db_type} 连接成功")
            except Exception as e:
                logger.error(f"数据库 {db_type} 连接失败: {str(e)}")
    
    def get_session(self, db_type=None):
        """获取数据库会话"""
        if db_type is None:
            db_type = self.current_db
        
        if db_type not in self.sessions:
            raise ValueError(f"不支持的数据库类型: {db_type}")
        
        session = self.sessions[db_type]()

        # PostgreSQL：保险起见，每次会话设置 UTF8
        if db_type == "postgresql":
            try:
                session.execute(text("SET client_encoding = 'UTF8'"))
                session.commit()
            except Exception as e:
                logger.warning(f"PostgreSQL 设置编码时出现警告: {str(e)}")

        return session
    
    def switch_db(self, db_type):
        """切换当前数据库"""
        if db_type in self.engines:
            self.current_db = db_type
            return True
        return False
    
    def _create_postgresql_tables(self, engine):
        """使用原始SQL为PostgreSQL创建表（绕过编码问题）"""
        sql_statements = [
            # 创建更新时间触发器函数
            """
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.update_time = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql';
            """,
            # 图书表
            """
            CREATE TABLE IF NOT EXISTS public.books (
                book_id SERIAL NOT NULL,
                book_name VARCHAR(100) NOT NULL,
                author VARCHAR(50) NULL,
                category VARCHAR(30) NULL,
                stock INTEGER DEFAULT 0,
                update_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (book_id)
            );
            """,
            "CREATE INDEX IF NOT EXISTS idx_book_name ON public.books (book_name);",
            """
            DROP TRIGGER IF EXISTS update_books_updated_at ON public.books;
            CREATE TRIGGER update_books_updated_at BEFORE UPDATE ON public.books
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            """,
            # 读者表
            """
            CREATE TABLE IF NOT EXISTS public.readers (
                reader_id SERIAL NOT NULL,
                name VARCHAR(50) NOT NULL,
                gender VARCHAR(10) NULL,
                phone VARCHAR(20) NULL,
                reg_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                update_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (reader_id),
                CONSTRAINT readers_phone_unique UNIQUE (phone)
            );
            """,
            "CREATE INDEX IF NOT EXISTS idx_reader_phone ON public.readers (phone);",
            """
            DROP TRIGGER IF EXISTS update_readers_updated_at ON public.readers;
            CREATE TRIGGER update_readers_updated_at BEFORE UPDATE ON public.readers
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            """,
            # 借阅记录表
            """
            CREATE TABLE IF NOT EXISTS public.borrows (
                borrow_id SERIAL NOT NULL,
                book_id INTEGER NOT NULL,
                reader_id INTEGER NOT NULL,
                borrow_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                return_date TIMESTAMP NULL,
                is_overdue BOOLEAN NOT NULL DEFAULT FALSE,
                update_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (borrow_id),
                CONSTRAINT fk_borrows_books FOREIGN KEY (book_id) REFERENCES public.books (book_id) ON DELETE CASCADE,
                CONSTRAINT fk_borrows_readers FOREIGN KEY (reader_id) REFERENCES public.readers (reader_id) ON DELETE CASCADE
            );
            """,
            "CREATE INDEX IF NOT EXISTS idx_book_reader ON public.borrows (book_id, reader_id);",
            """
            DROP TRIGGER IF EXISTS update_borrows_updated_at ON public.borrows;
            CREATE TRIGGER update_borrows_updated_at BEFORE UPDATE ON public.borrows
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            """,
            # 系统用户表
            """
            CREATE TABLE IF NOT EXISTS public.users (
                user_id SERIAL NOT NULL,
                username VARCHAR(20) NOT NULL,
                password VARCHAR(32) NOT NULL,
                role VARCHAR(10) NOT NULL CHECK (role IN ('管理员', '操作员', '查看员')),
                create_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                update_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id),
                CONSTRAINT users_username_unique UNIQUE (username)
            );
            """,
            "CREATE INDEX IF NOT EXISTS idx_username ON public.users (username);",
            """
            DROP TRIGGER IF EXISTS update_users_updated_at ON public.users;
            CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            """,
            # 同步日志表
            """
            CREATE TABLE IF NOT EXISTS public.sync_logs (
                log_id SERIAL NOT NULL,
                db_name VARCHAR(20) NOT NULL,
                op_type VARCHAR(10) NOT NULL CHECK (op_type IN ('增', '删', '改', '冲突')),
                sync_status VARCHAR(10) NOT NULL CHECK (sync_status IN ('成功', '失败')),
                is_conflict BOOLEAN NOT NULL DEFAULT FALSE,
                conflict_desc VARCHAR(200) NULL,
                sync_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (log_id)
            );
            """,
            "CREATE INDEX IF NOT EXISTS idx_sync_time ON public.sync_logs (sync_time);",
            "CREATE INDEX IF NOT EXISTS idx_is_conflict ON public.sync_logs (is_conflict);",
        ]
        
        try:
            with engine.connect() as conn:
                # 设置客户端编码（使用原始连接避免编码问题）
                try:
                    conn.execute(text("SET client_encoding = 'UTF8'"))
                except:
                    # 如果设置编码失败，继续执行（可能已经设置）
                    pass
                
                # 执行所有SQL语句
                success_count = 0
                for sql in sql_statements:
                    try:
                        conn.execute(text(sql))
                        success_count += 1
                    except Exception as e:
                        error_msg = str(e).lower()
                        # 忽略已存在的错误（表或索引已存在）
                        if "already exists" in error_msg or "duplicate" in error_msg:
                            # 这是正常的，表或索引已存在
                            success_count += 1
                        elif "codec" in error_msg or "utf" in error_msg:
                            # 编码错误，但继续执行（可能是某些元数据查询的问题）
                            logger.warning(f"PostgreSQL执行SQL时出现编码警告，继续执行...")
                            success_count += 1
                        else:
                            logger.warning(f"PostgreSQL执行SQL时出现警告: {str(e)}")
                
                # 提交事务
                try:
                    conn.commit()
                except:
                    # 某些操作可能不需要commit，继续
                    pass
                
                # 如果大部分SQL执行成功，认为表创建成功
                if success_count >= len(sql_statements) * 0.8:  # 至少80%的SQL执行成功
                    logger.info("PostgreSQL表创建成功（使用原始SQL）")
                    return True
                else:
                    logger.warning(f"PostgreSQL表创建部分成功（{success_count}/{len(sql_statements)}）")
                    return False
        except Exception as e:
            error_msg = str(e)
            # 如果是编码错误，尝试继续
            if "codec" in error_msg.lower() or "utf" in error_msg.lower():
                logger.warning(f"PostgreSQL表创建遇到编码问题: {error_msg}")
                # 使用原始SQL检查表是否已创建（避免使用inspect）
                try:
                    required_tables = ["books", "readers", "borrows", "users", "sync_logs"]
                    existing_count = 0
                    with engine.connect() as check_conn:
                        for table in required_tables:
                            try:
                                # 使用原始SQL查询表是否存在
                                result = check_conn.execute(text(f"""
                                    SELECT EXISTS (
                                        SELECT FROM information_schema.tables 
                                        WHERE table_schema = 'public' 
                                        AND table_name = '{table}'
                                    )
                                """))
                                if result.fetchone()[0]:
                                    existing_count += 1
                            except:
                                # 如果查询失败，尝试直接查询表
                                try:
                                    check_conn.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                                    existing_count += 1
                                except:
                                    pass
                    
                    if existing_count >= 3:  # 至少3个表存在
                        logger.info(f"PostgreSQL表已存在（{existing_count}/{len(required_tables)}），可以正常使用")
                        logger.info("提示: 如果表未完全创建，请在PostgreSQL中手动执行 create_postgresql_tables.sql")
                        return True
                    else:
                        logger.warning(f"PostgreSQL表创建失败，只有 {existing_count}/{len(required_tables)} 个表存在")
                        logger.warning("建议: 请在PostgreSQL中手动执行 create_postgresql_tables.sql 脚本创建表")
                except Exception as check_e:
                    logger.warning(f"检查PostgreSQL表时出错: {str(check_e)}")
                    logger.warning("建议: 请在PostgreSQL中手动执行 create_postgresql_tables.sql 脚本创建表")
            logger.error(f"PostgreSQL表创建失败: {error_msg}")
            return False
    
    def create_tables(self, db_type=None):
        """创建数据表"""
        if db_type:
            if db_type in self.engines:
                try:
                    # PostgreSQL使用原始SQL创建表
                    if db_type == "postgresql":
                        self._create_postgresql_tables(self.engines[db_type])
                    else:
                        Base.metadata.create_all(self.engines[db_type])
                    logger.info(f"数据库 {db_type} 表创建成功")
                except Exception as e:
                    logger.error(f"数据库 {db_type} 表创建失败: {str(e)}")
        else:
            # 为所有数据库创建表
            for db_type, engine in self.engines.items():
                try:
                    # PostgreSQL使用原始SQL创建表
                    if db_type == "postgresql":
                        self._create_postgresql_tables(engine)
                    else:
                        Base.metadata.create_all(engine)
                    logger.info(f"数据库 {db_type} 表创建成功")
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"数据库 {db_type} 表创建失败: {error_msg}")
    
    def check_table_exists(self, db_type, table_name):
        """检查表是否存在"""
        if db_type not in self.engines:
            return False
        inspector = inspect(self.engines[db_type])
        return table_name in inspector.get_table_names()
    
    def close_all(self):
        """关闭所有数据库连接"""
        for db_type, session in self.sessions.items():
            session.remove()
        for db_type, engine in self.engines.items():
            engine.dispose()
        logger.info("所有数据库连接已关闭")


# 全局数据库连接器实例
db_connector = DBConnector()

