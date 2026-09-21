# -*- coding: utf-8 -*-
"""
业务逻辑服务整合模块
整合了认证、图书、读者、借阅等所有业务逻辑
"""
import hashlib
from contextvars import ContextVar
from sqlalchemy import update
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
import re
import logging

from db_connector import db_connector
from models import User, Book, Reader, Borrow, SyncLog
from sync_service import sync_service
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== 认证服务 ====================
# 全局当前用户信息
current_user = None
_user_context = ContextVar('library_current_user', default=None)

def set_current_user(user):
    global current_user
    current_user = user  # legacy sequential service caller compatibility
    _user_context.set(user)



def md5_hash(password):
    """MD5加密"""
    return hashlib.md5(password.encode('utf-8')).hexdigest()


def login(username, password):
    """用户登录"""
    global current_user
    
    try:
        session = db_connector.get_session()
        user = session.query(User).filter_by(username=username).first()
        
        if not user:
            return False, "用户名不存在"
        
        # 密码校验（MD5）
        if md5_hash(password) != user.password:
            return False, "密码错误"
        
        # 记录当前用户
        set_current_user({"user_id": user.user_id, "username": user.username, "role": user.role})
        
        logger.info(f"用户 {username} 登录成功，角色: {user.role}")
        return True, "登录成功"
        
    except Exception as e:
        logger.error(f"登录失败: {str(e)}")
        return False, f"登录失败: {str(e)}"


def logout():
    """用户登出"""
    global current_user
    set_current_user(None)
    logger.info("用户已登出")


def get_current_user():
    """获取当前用户信息"""
    return _user_context.get()


def has_permission(required_role):
    """检查用户权限"""
    if not get_current_user():
        return False
    
    role_hierarchy = {
        "查看员": 1,
        "操作员": 2,
        "管理员": 3
    }
    
    current_role_level = role_hierarchy.get(get_current_user()["role"], 0)
    required_role_level = role_hierarchy.get(required_role, 0)
    
    return current_role_level >= required_role_level


def permission_required(required_role):
    """权限装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not get_current_user():
                return False, "请先登录"
            
            if not has_permission(required_role):
                return False, f"无操作权限，需要{required_role}及以上权限"
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ==================== 图书服务 ====================

@permission_required("查看员")
def get_all_books(db_type="mysql"):
    """获取所有图书"""
    try:
        session = db_connector.get_session(db_type)
        books = session.query(Book).all()
        return True, books
    except Exception as e:
        logger.error(f"获取图书列表失败: {str(e)}")
        return False, f"获取图书列表失败: {str(e)}"


@permission_required("查看员")
def get_book_by_id(book_id, db_type="mysql"):
    """根据ID获取图书"""
    try:
        session = db_connector.get_session(db_type)
        book = session.query(Book).filter_by(book_id=book_id).first()
        if book:
            return True, book
        return False, "图书不存在"
    except Exception as e:
        logger.error(f"获取图书失败: {str(e)}")
        return False, f"获取图书失败: {str(e)}"


@permission_required("操作员")
def add_book(book_name, author=None, category=None, stock=0, db_type="mysql"):
    """新增图书"""
    try:
        if not book_name or not book_name.strip():
            return False, "图书名称不能为空"
        
        if not isinstance(stock, int) or isinstance(stock, bool) or not 0 <= stock <= 2147483647:
            return False, "库存必须为0到2147483647之间的整数"
        session = db_connector.get_session(db_type)
        new_book = Book(
            book_name=book_name.strip(),
            author=author.strip() if author else None,
            category=category.strip() if category else None,
            stock=stock if stock >= 0 else 0
        )
        session.add(new_book)
        session.commit()
        
        data_dict = {
            "book_name": new_book.book_name,
            "author": new_book.author,
            "category": new_book.category,
            "stock": new_book.stock
        }
        sync_service.sync_to_other_dbs(db_type, "增", Book, data_dict, None)
        
        logger.info(f"新增图书成功: {book_name}")
        return True, "新增图书成功", new_book.book_id
        
    except Exception as e:
        session.rollback()
        logger.error(f"新增图书失败: {str(e)}")
        return False, f"新增图书失败: {str(e)}"


@permission_required("操作员")
def update_book(book_id, book_name=None, author=None, category=None, stock=None, db_type="mysql"):
    """修改图书"""
    if stock is not None and (not isinstance(stock, int) or isinstance(stock, bool) or not 0 <= stock <= 2147483647):
        return False, "库存必须为0到2147483647之间的整数"
    try:
        session = db_connector.get_session(db_type)
        book = session.query(Book).filter_by(book_id=book_id).first()
        
        if not book:
            return False, "图书不存在"
        
        if book_name:
            book.book_name = book_name.strip()
        if author is not None:
            book.author = author.strip() if author else None
        if category is not None:
            book.category = category.strip() if category else None
        if stock is not None:
            book.stock = stock if stock >= 0 else book.stock
        
        book.update_time = datetime.now()
        session.commit()
        
        data_dict = {
            "book_name": book.book_name,
            "author": book.author,
            "category": book.category,
            "stock": book.stock
        }
        sync_service.sync_to_other_dbs(db_type, "改", Book, data_dict, book_id)
        
        logger.info(f"修改图书成功: book_id={book_id}")
        return True, "修改图书成功"
        
    except Exception as e:
        session.rollback()
        logger.error(f"修改图书失败: {str(e)}")
        return False, f"修改图书失败: {str(e)}"


@permission_required("操作员")
def delete_book(book_id, db_type="mysql"):
    """删除图书"""
    try:
        session = db_connector.get_session(db_type)
        book = session.query(Book).filter_by(book_id=book_id).first()
        
        if not book:
            return False, "图书不存在"
        
        borrows = session.query(Borrow).filter_by(book_id=book_id, return_date=None).all()
        if borrows:
            return False, "该图书正在被借阅，无法删除"
        
        session.delete(book)
        session.commit()
        
        sync_service.sync_to_other_dbs(db_type, "删", Book, {}, book_id)
        
        logger.info(f"删除图书成功: book_id={book_id}")
        return True, "删除图书成功"
        
    except Exception as e:
        session.rollback()
        logger.error(f"删除图书失败: {str(e)}")
        return False, f"删除图书失败: {str(e)}"


@permission_required("查看员")
def search_books(keyword, db_type="mysql"):
    """搜索图书"""
    try:
        session = db_connector.get_session(db_type)
        books = session.query(Book).filter(
            Book.book_name.like(f"%{keyword}%") |
            Book.author.like(f"%{keyword}%") |
            Book.category.like(f"%{keyword}%")
        ).all()
        return True, books
    except Exception as e:
        logger.error(f"搜索图书失败: {str(e)}")
        return False, f"搜索图书失败: {str(e)}"


# ==================== 读者服务 ====================

def validate_phone(phone):
    """验证手机号格式"""
    if not phone:
        return True
    pattern = r'^1[3-9]\d{9}$'
    return bool(re.match(pattern, phone))


@permission_required("查看员")
def get_all_readers(db_type="mysql"):
    """获取所有读者"""
    try:
        session = db_connector.get_session(db_type)
        readers = session.query(Reader).all()
        return True, readers
    except Exception as e:
        logger.error(f"获取读者列表失败: {str(e)}")
        return False, f"获取读者列表失败: {str(e)}"


@permission_required("查看员")
def get_reader_by_id(reader_id, db_type="mysql"):
    """根据ID获取读者"""
    try:
        session = db_connector.get_session(db_type)
        reader = session.query(Reader).filter_by(reader_id=reader_id).first()
        if reader:
            return True, reader
        return False, "读者不存在"
    except Exception as e:
        logger.error(f"获取读者失败: {str(e)}")
        return False, f"获取读者失败: {str(e)}"


@permission_required("操作员")
def add_reader(name, gender=None, phone=None, db_type="mysql"):
    """新增读者"""
    try:
        if not name or not name.strip():
            return False, "读者姓名不能为空"
        
        if phone and not validate_phone(phone):
            return False, "手机号格式不正确"
        
        session = db_connector.get_session(db_type)
        
        if phone:
            existing_reader = session.query(Reader).filter_by(phone=phone).first()
            if existing_reader:
                return False, "手机号已存在"
        
        new_reader = Reader(
            name=name.strip(),
            gender=gender.strip() if gender else None,
            phone=phone.strip() if phone else None
        )
        session.add(new_reader)
        session.commit()
        
        data_dict = {
            "name": new_reader.name,
            "gender": new_reader.gender,
            "phone": new_reader.phone
        }
        sync_service.sync_to_other_dbs(db_type, "增", Reader, data_dict, None)
        
        logger.info(f"新增读者成功: {name}")
        return True, "新增读者成功", new_reader.reader_id
        
    except Exception as e:
        session.rollback()
        logger.error(f"新增读者失败: {str(e)}")
        return False, f"新增读者失败: {str(e)}"


@permission_required("操作员")
def update_reader(reader_id, name=None, gender=None, phone=None, db_type="mysql"):
    """修改读者"""
    try:
        session = db_connector.get_session(db_type)
        reader = session.query(Reader).filter_by(reader_id=reader_id).first()
        
        if not reader:
            return False, "读者不存在"
        
        if phone and not validate_phone(phone):
            return False, "手机号格式不正确"
        
        if phone:
            existing_reader = session.query(Reader).filter_by(phone=phone).first()
            if existing_reader and existing_reader.reader_id != reader_id:
                return False, "手机号已被其他读者使用"
        
        if name:
            reader.name = name.strip()
        if gender is not None:
            reader.gender = gender.strip() if gender else None
        if phone is not None:
            reader.phone = phone.strip() if phone else None
        
        reader.update_time = datetime.now()
        session.commit()
        
        data_dict = {
            "name": reader.name,
            "gender": reader.gender,
            "phone": reader.phone
        }
        sync_service.sync_to_other_dbs(db_type, "改", Reader, data_dict, reader_id)
        
        logger.info(f"修改读者成功: reader_id={reader_id}")
        return True, "修改读者成功"
        
    except Exception as e:
        session.rollback()
        logger.error(f"修改读者失败: {str(e)}")
        return False, f"修改读者失败: {str(e)}"


@permission_required("操作员")
def delete_reader(reader_id, db_type="mysql"):
    """删除读者"""
    try:
        session = db_connector.get_session(db_type)
        reader = session.query(Reader).filter_by(reader_id=reader_id).first()
        
        if not reader:
            return False, "读者不存在"
        
        borrows = session.query(Borrow).filter_by(reader_id=reader_id, return_date=None).all()
        if borrows:
            return False, "该读者有未归还的图书，无法删除"
        
        session.delete(reader)
        session.commit()
        
        sync_service.sync_to_other_dbs(db_type, "删", Reader, {}, reader_id)
        
        logger.info(f"删除读者成功: reader_id={reader_id}")
        return True, "删除读者成功"
        
    except Exception as e:
        session.rollback()
        logger.error(f"删除读者失败: {str(e)}")
        return False, f"删除读者失败: {str(e)}"


@permission_required("查看员")
def search_readers(keyword, db_type="mysql"):
    """搜索读者"""
    try:
        session = db_connector.get_session(db_type)
        readers = session.query(Reader).filter(
            Reader.name.like(f"%{keyword}%") |
            Reader.phone.like(f"%{keyword}%")
        ).all()
        return True, readers
    except Exception as e:
        logger.error(f"搜索读者失败: {str(e)}")
        return False, f"搜索读者失败: {str(e)}"


# ==================== 借阅服务 ====================

def check_overdue(borrow_date):
    """检查是否逾期"""
    max_days = config.BORROW_CONFIG["max_borrow_days"]
    return datetime.now() > borrow_date + timedelta(days=max_days)


@permission_required("查看员")
def get_all_borrows(db_type="mysql"):
    """获取所有借阅记录"""
    try:
        session = db_connector.get_session(db_type)
        borrows = session.query(Borrow).order_by(Borrow.borrow_date.desc()).all()
        return True, borrows
    except Exception as e:
        logger.error(f"获取借阅记录失败: {str(e)}")
        return False, f"获取借阅记录失败: {str(e)}"


@permission_required("查看员")
def get_borrow_by_id(borrow_id, db_type="mysql"):
    """根据ID获取借阅记录"""
    try:
        session = db_connector.get_session(db_type)
        borrow = session.query(Borrow).filter_by(borrow_id=borrow_id).first()
        if borrow:
            return True, borrow
        return False, "借阅记录不存在"
    except Exception as e:
        logger.error(f"获取借阅记录失败: {str(e)}")
        return False, f"获取借阅记录失败: {str(e)}"


@permission_required("操作员")
def borrow_book(book_id, reader_id, db_type="mysql"):
    """借阅图书"""
    try:
        session = db_connector.get_session(db_type)
        
        book = session.query(Book).filter_by(book_id=book_id).first()
        if not book:
            return False, "图书不存在"
        
        if book.stock <= 0:
            return False, "图书库存不足"
        
        reader = session.query(Reader).filter_by(reader_id=reader_id).first()
        if not reader:
            return False, "读者不存在"
        
        changed = session.execute(update(Book).where(Book.book_id == book_id, Book.stock > 0)
            .values(stock=Book.stock - 1, update_time=datetime.now()),
            execution_options={"synchronize_session": False}).rowcount
        if changed != 1:
            session.rollback()
            return False, "图书库存不足"

        existing_borrow = session.query(Borrow).filter_by(
            book_id=book_id,
            reader_id=reader_id,
            return_date=None
        ).with_for_update().first()
        if existing_borrow:
            session.rollback()
            return False, "该读者已借阅此图书且未归还"
        
        new_borrow = Borrow(
            book_id=book_id,
            reader_id=reader_id,
            borrow_date=datetime.now()
        )
        session.add(new_borrow)
        
        session.expire(book)
        
        session.commit()
        
        data_dict = {
            "book_id": new_borrow.book_id,
            "reader_id": new_borrow.reader_id,
            "borrow_date": new_borrow.borrow_date,
            "is_overdue": new_borrow.is_overdue
        }
        sync_service.sync_to_other_dbs(db_type, "增", Borrow, data_dict, None)
        
        book_data = {
            "book_name": book.book_name,
            "author": book.author,
            "category": book.category,
            "stock": book.stock
        }
        sync_service.sync_to_other_dbs(db_type, "改", Book, book_data, book_id)
        
        logger.info(f"借阅成功: book_id={book_id}, reader_id={reader_id}")
        return True, "借阅成功", new_borrow.borrow_id
        
    except Exception as e:
        session.rollback()
        logger.error(f"借阅失败: {str(e)}")
        return False, f"借阅失败: {str(e)}"


@permission_required("操作员")
def return_book(borrow_id, db_type="mysql"):
    """归还图书"""
    try:
        session = db_connector.get_session(db_type)
        borrow = session.query(Borrow).filter_by(borrow_id=borrow_id).first()
        
        if not borrow:
            return False, "借阅记录不存在"
        
        if borrow.return_date:
            return False, "该图书已归还"
        
        changed = session.execute(update(Borrow).where(Borrow.borrow_id == borrow_id, Borrow.return_date.is_(None))
            .values(return_date=datetime.now(), is_overdue=check_overdue(borrow.borrow_date), update_time=datetime.now()),
            execution_options={"synchronize_session": False}).rowcount
        if changed != 1:
            session.rollback()
            return False, "该图书已归还"
        session.execute(update(Book).where(Book.book_id == borrow.book_id)
            .values(stock=Book.stock + 1, update_time=datetime.now()),
            execution_options={"synchronize_session": False})
        session.expire_all()
        book = session.query(Book).filter_by(book_id=borrow.book_id).first()
        
        session.commit()
        
        data_dict = {
            "book_id": borrow.book_id,
            "reader_id": borrow.reader_id,
            "borrow_date": borrow.borrow_date,
            "return_date": borrow.return_date,
            "is_overdue": borrow.is_overdue
        }
        sync_service.sync_to_other_dbs(db_type, "改", Borrow, data_dict, borrow_id)
        
        if book:
            book_data = {
                "book_name": book.book_name,
                "author": book.author,
                "category": book.category,
                "stock": book.stock
            }
            sync_service.sync_to_other_dbs(db_type, "改", Book, book_data, book.book_id)
        
        logger.info(f"归还成功: borrow_id={borrow_id}")
        return True, "归还成功"
        
    except Exception as e:
        session.rollback()
        logger.error(f"归还失败: {str(e)}")
        return False, f"归还失败: {str(e)}"


@permission_required("查看员")
def get_overdue_borrows(db_type="mysql"):
    """获取逾期借阅记录"""
    try:
        session = db_connector.get_session(db_type)
        cutoff = datetime.now() - timedelta(days=config.BORROW_CONFIG["max_borrow_days"])
        borrows = session.query(Borrow).filter(Borrow.return_date.is_(None), Borrow.borrow_date < cutoff).all()
        # Query by actual due date; reading the overdue list does not modify rows.
        return True, borrows
    except Exception as e:
        logger.error(f"获取逾期记录失败: {str(e)}")
        return False, f"获取逾期记录失败: {str(e)}"


@permission_required("查看员")
def get_reader_borrows(reader_id, db_type="mysql"):
    """获取读者的借阅记录"""
    try:
        session = db_connector.get_session(db_type)
        borrows = session.query(Borrow).filter_by(reader_id=reader_id).order_by(Borrow.borrow_date.desc()).all()
        return True, borrows
    except Exception as e:
        logger.error(f"获取读者借阅记录失败: {str(e)}")
        return False, f"获取读者借阅记录失败: {str(e)}"

