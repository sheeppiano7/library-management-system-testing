# -*- coding: utf-8 -*-
"""
数据库模型定义
使用SQLAlchemy ORM，支持MySQL、SQL Server、PostgreSQL
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Book(Base):
    """图书表"""
    __tablename__ = "books"
    
    book_id = Column(Integer, primary_key=True, autoincrement=True)
    book_name = Column(String(100), nullable=False, comment="图书名称")
    author = Column(String(50), comment="图书作者")
    category = Column(String(30), comment="图书分类")
    stock = Column(Integer, default=0, comment="库存数量")
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="更新时间")
    
    # 关系
    borrows = relationship("Borrow", back_populates="book", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Book(book_id={self.book_id}, book_name='{self.book_name}')>"


class Reader(Base):
    """读者表"""
    __tablename__ = "readers"
    
    reader_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment="读者姓名")
    gender = Column(String(10), comment="读者性别")
    phone = Column(String(20), unique=True, comment="联系方式")
    reg_date = Column(DateTime, default=datetime.now, nullable=False, comment="注册日期")
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="更新时间")
    
    # 关系
    borrows = relationship("Borrow", back_populates="reader", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Reader(reader_id={self.reader_id}, name='{self.name}')>"


class Borrow(Base):
    """借阅记录表"""
    __tablename__ = "borrows"
    
    borrow_id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.book_id", ondelete="CASCADE"), nullable=False, comment="图书ID")
    reader_id = Column(Integer, ForeignKey("readers.reader_id", ondelete="CASCADE"), nullable=False, comment="读者ID")
    borrow_date = Column(DateTime, default=datetime.now, nullable=False, comment="借阅日期")
    return_date = Column(DateTime, comment="归还日期")
    is_overdue = Column(Boolean, default=False, nullable=False, comment="是否逾期")
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="更新时间")
    
    # 关系
    book = relationship("Book", back_populates="borrows")
    reader = relationship("Reader", back_populates="borrows")
    
    def __repr__(self):
        return f"<Borrow(borrow_id={self.borrow_id}, book_id={self.book_id}, reader_id={self.reader_id})>"


class User(Base):
    """系统用户表"""
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(20), nullable=False, unique=True, comment="用户名")
    password = Column(String(32), nullable=False, comment="密码（MD5加密）")
    role = Column(String(10), nullable=False, comment="角色")
    create_time = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="更新时间")
    
    # 添加检查约束（在创建表时）
    __table_args__ = (
        CheckConstraint("role IN ('管理员', '操作员', '查看员')", name="check_role"),
    )
    
    def __repr__(self):
        return f"<User(user_id={self.user_id}, username='{self.username}', role='{self.role}')>"


class SyncLog(Base):
    """同步日志表"""
    __tablename__ = "sync_logs"
    
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    db_name = Column(String(20), nullable=False, comment="数据库名称")
    op_type = Column(String(10), nullable=False, comment="操作类型")
    sync_status = Column(String(10), nullable=False, comment="同步状态")
    is_conflict = Column(Boolean, default=False, nullable=False, comment="是否冲突")
    conflict_desc = Column(String(200), comment="冲突描述")
    sync_time = Column(DateTime, default=datetime.now, nullable=False, comment="同步时间")
    
    # 添加检查约束
    __table_args__ = (
        CheckConstraint("op_type IN ('增', '删', '改', '冲突')", name="check_op_type"),
        CheckConstraint("sync_status IN ('成功', '失败')", name="check_sync_status"),
    )
    
    def __repr__(self):
        return f"<SyncLog(log_id={self.log_id}, db_name='{self.db_name}', op_type='{self.op_type}')>"

