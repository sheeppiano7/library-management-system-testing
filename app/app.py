# -*- coding: utf-8 -*-
"""
图书管理系统 - Web服务主程序
提供完整的图书管理功能（图书、读者、借阅、同步、报表）
"""
from flask import Flask, render_template_string, jsonify, request, redirect, url_for, session, flash
from report_service import generate_mobile_sync_stats, get_conflict_records, generate_stock_report, generate_borrow_report, generate_sync_report
from db_connector import db_connector
from scheduler_service import start_scheduler
from models import SyncLog, Book, Reader, Borrow
from datetime import datetime
from urllib.parse import quote
from services import (
    login as auth_login, logout as auth_logout, get_current_user,
    get_all_books, get_book_by_id, add_book, update_book, delete_book, search_books,
    get_all_readers, get_reader_by_id, add_reader, update_reader, delete_reader, search_readers,
    get_all_borrows, borrow_book, return_book, get_overdue_borrows
)
# 临时设置当前用户（Web环境）
import services
from sync_service import sync_service
from functools import wraps
import logging
import sys
import config
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('BOOK_SECRET_KEY', 'change-this-key-for-local-testing')

@app.teardown_request
def release_request_sessions(error=None):
    for factory in db_connector.sessions.values():
        factory.remove()
    services.set_current_user(None)

def nonnegative_int(value, label):
    if value is None or not str(value).strip().isascii() or not str(value).strip().isdecimal():
        raise ValueError(label + "必须为非负整数")
    value = int(value)
    if value > 2147483647:
        raise ValueError(label + "超出整数范围")
    return value


# 初始化数据库和定时任务
try:
    logger.info("初始化数据库连接...")
    db_connector.create_tables()
    logger.info("数据库初始化完成")
except Exception as e:
    logger.error(f"数据库初始化失败: {str(e)}")

try:
    logger.info("启动定时任务...")
    start_scheduler()
    logger.info("定时任务启动成功")
except Exception as e:
    logger.warning(f"定时任务启动失败: {str(e)}")


# 登录检查装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        # 设置当前用户到services模块（用于权限检查）
        if 'user_id' in session:
            services.set_current_user({
                "user_id": session.get('user_id'),
                "username": session.get('username'),
                "role": session.get('role')
            })
        return f(*args, **kwargs)
    return decorated_function


# 登录页面模板
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>图书管理系统 - 登录</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: "Microsoft YaHei", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .login-container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            width: 100%;
            max-width: 500px;
            overflow: hidden;
        }
        .login-header {
            background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
            padding: 40px 30px;
            text-align: center;
            color: white;
        }
        .login-header h1 {
            font-size: 32px;
            margin-bottom: 10px;
        }
        .login-header p {
            font-size: 14px;
            opacity: 0.9;
        }
        .login-body {
            padding: 40px 30px;
        }
        .form-group {
            margin-bottom: 25px;
        }
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: bold;
            font-size: 14px;
        }
        .form-group input {
            width: 100%;
            padding: 14px 18px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
            transition: all 0.3s;
        }
        .form-group input:focus {
            outline: none;
            border-color: #2196F3;
            box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.1);
        }
        .login-btn {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            margin-top: 10px;
        }
        .login-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(33, 150, 243, 0.4);
        }
        .login-btn:active {
            transform: translateY(0);
        }
        .alert {
            padding: 12px 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
        }
        .alert-error {
            background: #ffebee;
            color: #c62828;
            border: 1px solid #ef5350;
        }
        .alert-success {
            background: #e8f5e9;
            color: #2e7d32;
            border: 1px solid #66bb6a;
        }
        .tip {
            text-align: center;
            color: #666;
            font-size: 13px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <h1>图书管理系统</h1>
            <p>Library Management System</p>
        </div>
        <div class="login-body">
            {% if error %}
            <div class="alert alert-error">{{ error }}</div>
            {% endif %}
            {% if success %}
            <div class="alert alert-success">{{ success }}</div>
            {% endif %}
            <form method="POST" action="/login">
                <div class="form-group">
                    <label>👤 用户名</label>
                    <input type="text" name="username" placeholder="请输入用户名" required autofocus>
                </div>
                <div class="form-group">
                    <label>🔒 密码</label>
                    <input type="password" name="password" placeholder="请输入密码" required>
                </div>
                <button type="submit" class="login-btn">🚀 登录</button>
            </form>
            <div class="tip">默认账户: admin / admin123</div>
        </div>
    </div>
</body>
</html>
"""


# 主界面模板（左侧导航栏）
MAIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - 图书管理系统</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: "Microsoft YaHei", Arial, sans-serif;
            background: #f5f7fa;
            min-height: 100vh;
            display: flex;
        }
        .sidebar {
            width: 250px;
            background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
            color: white;
            min-height: 100vh;
            position: fixed;
            left: 0;
            top: 0;
            box-shadow: 2px 0 10px rgba(0,0,0,0.1);
        }
        .sidebar-header {
            padding: 25px 20px;
            background: rgba(0,0,0,0.2);
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .sidebar-header h2 {
            font-size: 22px;
            margin-bottom: 5px;
        }
        .sidebar-header p {
            font-size: 12px;
            opacity: 0.8;
        }
        .user-info {
            padding: 15px 20px;
            background: rgba(0,0,0,0.15);
            border-bottom: 1px solid rgba(255,255,255,0.1);
            font-size: 13px;
        }
        .user-info strong {
            display: block;
            margin-bottom: 5px;
        }
        .nav-menu {
            padding: 20px 0;
        }
        .nav-item {
            display: block;
            padding: 15px 25px;
            color: rgba(255,255,255,0.8);
            text-decoration: none;
            transition: all 0.3s;
            border-left: 3px solid transparent;
        }
        .nav-item:hover {
            background: rgba(255,255,255,0.1);
            color: white;
            border-left-color: #2196F3;
        }
        .nav-item.active {
            background: rgba(33, 150, 243, 0.2);
            color: white;
            border-left-color: #2196F3;
        }
        .nav-item i {
            margin-right: 10px;
            font-size: 18px;
        }
        .logout-btn {
            position: absolute;
            bottom: 20px;
            left: 20px;
            right: 20px;
            padding: 12px;
            background: rgba(244, 67, 54, 0.8);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            text-align: center;
            transition: all 0.3s;
        }
        .logout-btn:hover {
            background: rgba(244, 67, 54, 1);
        }
        .main-content {
            margin-left: 250px;
            flex: 1;
            padding: 30px;
        }
        .content-header {
            background: white;
            padding: 25px 30px;
            border-radius: 10px;
            margin-bottom: 25px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        .content-header h1 {
            color: #2c3e50;
            font-size: 28px;
            margin-bottom: 5px;
        }
        .content-header p {
            color: #7f8c8d;
            font-size: 14px;
        }
        .card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        .card h2 {
            color: #2c3e50;
            font-size: 20px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #2196F3;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .stat-item {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-value {
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 8px;
        }
        .stat-label {
            font-size: 14px;
            opacity: 0.9;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        table th, table td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }
        table th {
            background: #f8f9fa;
            color: #2c3e50;
            font-weight: bold;
            font-size: 14px;
        }
        table tr:hover {
            background: #f8f9fa;
        }
        .btn {
            display: inline-block;
            padding: 10px 20px;
            background: #2196F3;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            margin: 5px;
            border: none;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
        }
        .btn:hover {
            background: #1976D2;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        .btn-success {
            background: #4CAF50;
        }
        .btn-success:hover {
            background: #45a049;
        }
        .btn-danger {
            background: #f44336;
        }
        .btn-danger:hover {
            background: #da190b;
        }
        .btn-primary {
            background: #2196F3;
        }
        .btn-primary:hover {
            background: #1976D2;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #2c3e50;
            font-weight: bold;
            font-size: 14px;
        }
        .form-group input, .form-group select {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: all 0.3s;
        }
        .form-group input:focus, .form-group select:focus {
            outline: none;
            border-color: #2196F3;
            box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.1);
        }
        .search-box {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .search-box input {
            flex: 1;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
        }
        .search-box button {
            padding: 12px 25px;
            background: #2196F3;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
        }
        .alert {
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
        }
        .alert-success {
            background: #e8f5e9;
            color: #2e7d32;
            border: 1px solid #66bb6a;
        }
        .alert-error {
            background: #ffebee;
            color: #c62828;
            border: 1px solid #ef5350;
        }
        .conflict-item {
            padding: 15px;
            margin: 10px 0;
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            border-radius: 6px;
        }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header">
            <h2>图书管理系统</h2>
            <p>Library Management</p>
        </div>
        <div class="user-info">
            <strong>当前用户: {{ session.username }}</strong>
            <span>角色: {{ session.role }}</span>
        </div>
        <nav class="nav-menu">
            <a href="/" class="nav-item {{ 'active' if current_page == 'index' else '' }}">
                首页
            </a>
            <a href="/books" class="nav-item {{ 'active' if current_page == 'books' else '' }}">
                图书管理
            </a>
            <a href="/readers" class="nav-item {{ 'active' if current_page == 'readers' else '' }}">
                读者管理
            </a>
            <a href="/borrows" class="nav-item {{ 'active' if current_page == 'borrows' else '' }}">
                借阅管理
            </a>
            <a href="/sync" class="nav-item {{ 'active' if current_page == 'sync' else '' }}">
                同步管理
            </a>
            <a href="/reports" class="nav-item {{ 'active' if current_page == 'reports' else '' }}">
                报表统计
            </a>
        </nav>
        <a href="/logout" class="logout-btn">退出登录</a>
    </div>
    <div class="main-content">
        <div class="content-header">
            <h1>{{ title }}</h1>
            <p>{{ subtitle }}</p>
        </div>
        {% for message in get_flashed_messages() %}<div class="alert" role="status">{{ message }}</div>{% endfor %}{{ content|safe }}
    </div>
</body>
</html>
"""


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    """登录页面"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return render_template_string(LOGIN_TEMPLATE, error="请输入用户名和密码")
        
        success, message = auth_login(username, password)
        
        if success:
            # 保存用户信息到session
            user = get_current_user()
            if user:
                session['user_id'] = user['user_id']
                session['username'] = user['username']
                session['role'] = user['role']
                # 设置services模块的当前用户（用于权限检查）
                services.set_current_user(user)
            return redirect(url_for('index'))
        else:
            return render_template_string(LOGIN_TEMPLATE, error=message)
    
    # 如果已登录，重定向到首页
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    return render_template_string(LOGIN_TEMPLATE)


@app.route('/logout')
def logout_page():
    """退出登录"""
    auth_logout()
    session.clear()
    # 清除services模块的当前用户
    services.set_current_user(None)
    return redirect(url_for('login_page'))


@app.route('/')
@login_required
def index():
    """首页"""
    try:
        session_db = db_connector.get_session("mysql")
        
        # 获取统计信息
        book_count = session_db.query(Book).count()
        reader_count = session_db.query(Reader).count()
        borrow_count = session_db.query(Borrow).filter_by(return_date=None).count()
        overdue_count = session_db.query(Borrow).filter_by(return_date=None, is_overdue=True).count()
        
        # 获取当日同步统计
        from datetime import datetime
        today = datetime.now().date()
        logs = session_db.query(SyncLog).filter(
            SyncLog.sync_time >= datetime.combine(today, datetime.min.time())
        ).all()
        
        sync_stats = {"成功": 0, "失败": 0, "冲突": 0}
        for log in logs:
            if log.sync_status == "成功":
                sync_stats["成功"] += 1
            else:
                sync_stats["失败"] += 1
            if log.is_conflict:
                sync_stats["冲突"] += 1
        
        content = f"""
        <div class="card">
            <h2>系统概览</h2>
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-value">{book_count}</div>
                    <div class="stat-label">图书总数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{reader_count}</div>
                    <div class="stat-label">读者总数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{borrow_count}</div>
                    <div class="stat-label">在借图书</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{overdue_count}</div>
                    <div class="stat-label">逾期图书</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>今日同步统计</h2>
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-value">{sync_stats['成功']}</div>
                    <div class="stat-label">成功</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{sync_stats['失败']}</div>
                    <div class="stat-label">失败</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{sync_stats['冲突']}</div>
                    <div class="stat-label">冲突</div>
                </div>
            </div>
        </div>
        """
        
        return render_template_string(
            MAIN_TEMPLATE,
            title="首页",
            subtitle="系统概览和统计信息",
            current_page="index",
            content=content
        )
    except Exception as e:
        logger.error(f"首页加载失败: {str(e)}")
        return f"<h1>错误</h1><p>{str(e)}</p>", 500


@app.route('/books')
@login_required
def books_page():
    """图书管理页面"""
    try:
        # 确保设置当前用户
        if 'user_id' in session:
            services.set_current_user({
                "user_id": session.get('user_id'),
                "username": session.get('username'),
                "role": session.get('role')
            })
        
        success, result = get_all_books()
        if success:
            books = result
        else:
            books = []
            logger.warning(f"获取图书列表失败: {result}")
        
        user_role = session.get('role', '查看员')
        can_operate = user_role in ['管理员', '操作员']
        
        logger.info(f"图书管理页面: 成功={success}, 图书数量={len(books) if success else 0}, 用户角色={user_role}")
        
        content = """
        <div class="card">
            <h2>图书管理</h2>
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="搜索图书（名称/作者/分类）">
                <button onclick="searchBooks()">搜索</button>
        """
        
        if can_operate:
            content += '<a href="/books/add" class="btn btn-success">新增图书</a>'
        
        content += """
            </div>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>图书名称</th>
                        <th>作者</th>
                        <th>分类</th>
                        <th>库存</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        if books:
            for book in books:
                content += f"""
                        <tr>
                            <td>{book.book_id}</td>
                            <td>{book.book_name}</td>
                            <td>{book.author or '-'}</td>
                            <td>{book.category or '-'}</td>
                            <td>{book.stock}</td>
                            <td>
                """
                
                if can_operate:
                    content += f'<a href="/books/edit/{book.book_id}" class="btn btn-primary">编辑</a>'
                    content += f'<a href="/books/delete/{book.book_id}" class="btn btn-danger" onclick="return confirm(\'确定删除吗？\')">删除</a>'
                else:
                    content += '<span style="color:#999;">仅查看</span>'
                
                content += """
                            </td>
                        </tr>
                """
        else:
            content += """
                    <tr>
                        <td colspan="6" style="text-align: center; padding: 40px; color: #999;">
                            <p style="font-size: 16px;">暂无图书数据</p>
                            <p style="font-size: 14px; margin-top: 10px;">请点击"新增图书"按钮添加图书</p>
                        </td>
                    </tr>
            """
        
        content += """
                </tbody>
            </table>
        </div>
        <script>
            function searchBooks() {
                const keyword = document.getElementById('searchInput').value;
                if (keyword) {
                    window.location.href = '/books/search?q=' + encodeURIComponent(keyword);
                } else {
                    window.location.href = '/books';
                }
            }
            document.getElementById('searchInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    searchBooks();
                }
            });
        </script>
        """
        
        return render_template_string(
            MAIN_TEMPLATE,
            title="图书管理",
            subtitle="管理图书信息",
            current_page="books",
            content=content
        )
    except Exception as e:
        logger.error(f"图书管理页面加载失败: {str(e)}")
        return f"<h1>错误</h1><p>{str(e)}</p>", 500


@app.route('/books/add', methods=['GET', 'POST'])
@login_required
def add_book_page():
    """新增图书"""
    error = None
    if request.method == 'POST':
        book_name = request.form.get('book_name')
        author = request.form.get('author')
        category = request.form.get('category')
        try:
            stock = nonnegative_int(request.form.get('stock', 0), "库存")
        except ValueError as exc:
            return str(exc), 400
        
        success, message, *_ = add_book(book_name, author, category, stock)
        if success:
            return redirect('/books')
        else:
            error = message
    
    content = f"""
    <div class="card">
        <h2>新增图书</h2>
        {f'<div class="alert alert-error">{error}</div>' if error else ''}
        <form method="POST">
            <div class="form-group">
                <label>图书名称 *</label>
                <input type="text" name="book_name" required>
            </div>
            <div class="form-group">
                <label>作者</label>
                <input type="text" name="author">
            </div>
            <div class="form-group">
                <label>分类</label>
                <input type="text" name="category">
            </div>
            <div class="form-group">
                <label>库存</label>
                <input type="number" name="stock" value="0" min="0">
            </div>
            <button type="submit" class="btn btn-success">提交</button>
            <a href="/books" class="btn btn-danger">取消</a>
        </form>
    </div>
    """
    
    return render_template_string(
        MAIN_TEMPLATE,
        title="新增图书",
        subtitle="添加新图书到系统",
        current_page="books",
        content=content
    )


@app.route('/books/edit/<int:book_id>', methods=['GET', 'POST'])
@login_required
def edit_book_page(book_id):
    """编辑图书"""
    error = None
    success, book = get_book_by_id(book_id)
    
    if not success:
        return redirect('/books')
    
    if request.method == 'POST':
        book_name = request.form.get('book_name')
        author = request.form.get('author')
        category = request.form.get('category')
        try:
            stock = nonnegative_int(request.form.get('stock', 0), "库存")
        except ValueError as exc:
            return str(exc), 400
        
        success, message = update_book(book_id, book_name, author, category, stock)
        if success:
            return redirect('/books')
        else:
            error = message
    
    content = f"""
    <div class="card">
        <h2>编辑图书</h2>
        {f'<div class="alert alert-error">{error}</div>' if error else ''}
        <form method="POST">
            <div class="form-group">
                <label>图书名称 *</label>
                <input type="text" name="book_name" value="{book.book_name}" required>
            </div>
            <div class="form-group">
                <label>作者</label>
                <input type="text" name="author" value="{book.author or ''}">
            </div>
            <div class="form-group">
                <label>分类</label>
                <input type="text" name="category" value="{book.category or ''}">
            </div>
            <div class="form-group">
                <label>库存</label>
                <input type="number" name="stock" value="{book.stock}" min="0">
            </div>
            <button type="submit" class="btn btn-success">保存</button>
            <a href="/books" class="btn btn-danger">取消</a>
        </form>
    </div>
    """
    
    return render_template_string(
        MAIN_TEMPLATE,
        title="编辑图书",
        subtitle="修改图书信息",
        current_page="books",
        content=content
    )


@app.route('/books/delete/<int:book_id>')
@login_required
def delete_book_page(book_id):
    """删除图书"""
    success, message = delete_book(book_id)
    flash(message)
    return redirect('/books')


@app.route('/books/search')
@login_required
def search_books_page():
    """搜索图书"""
    keyword = request.args.get('q', '')
    if not keyword:
        return redirect('/books')
    
    success, books = search_books(keyword)
    if not success:
        books = []
    
    user_role = session.get('role', '查看员')
    can_operate = user_role in ['管理员', '操作员']
    
    content = f"""
    <div class="card">
        <h2>搜索结果："{keyword}"</h2>
        <div class="search-box">
            <input type="text" id="searchInput" value="{keyword}" placeholder="搜索图书（名称/作者/分类）">
            <button onclick="searchBooks()">搜索</button>
            <a href="/books" class="btn">返回列表</a>
    """
    
    if can_operate:
        content += '<a href="/books/add" class="btn btn-success">新增图书</a>'
    
    content += """
        </div>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>图书名称</th>
                    <th>作者</th>
                    <th>分类</th>
                    <th>库存</th>
                    <th>操作</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for book in books:
        content += f"""
                <tr>
                    <td>{book.book_id}</td>
                    <td>{book.book_name}</td>
                    <td>{book.author or '-'}</td>
                    <td>{book.category or '-'}</td>
                    <td>{book.stock}</td>
                    <td>
        """
        
        if can_operate:
            content += f'<a href="/books/edit/{book.book_id}" class="btn btn-primary">编辑</a>'
            content += f'<a href="/books/delete/{book.book_id}" class="btn btn-danger" onclick="return confirm(\'确定删除吗？\')">删除</a>'
        else:
            content += '<span style="color:#999;">仅查看</span>'
        
        content += """
                    </td>
                </tr>
        """
    
    content += """
            </tbody>
        </table>
    </div>
    <script>
        function searchBooks() {
            const keyword = document.getElementById('searchInput').value;
            if (keyword) {
                window.location.href = '/books/search?q=' + encodeURIComponent(keyword);
            } else {
                window.location.href = '/books';
            }
        }
        document.getElementById('searchInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchBooks();
            }
        });
    </script>
    """
    
    return render_template_string(
        MAIN_TEMPLATE,
        title="搜索图书",
        subtitle=f'搜索结果："{keyword}"',
        current_page="books",
        content=content
    )


@app.route('/readers')
@login_required
def readers_page():
    """读者管理页面"""
    try:
        # 确保设置当前用户
        if 'user_id' in session:
            services.set_current_user({
                "user_id": session.get('user_id'),
                "username": session.get('username'),
                "role": session.get('role')
            })
        
        success, result = get_all_readers()
        if success:
            readers = result
        else:
            readers = []
            logger.warning(f"获取读者列表失败: {result}")
        
        user_role = session.get('role', '查看员')
        can_operate = user_role in ['管理员', '操作员']
        
        logger.info(f"读者管理页面: 成功={success}, 读者数量={len(readers) if success else 0}, 用户角色={user_role}")
        
        content = """
        <div class="card">
            <h2>读者管理</h2>
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="搜索读者（姓名/手机号）">
                <button onclick="searchReaders()">搜索</button>
        """
        
        if can_operate:
            content += '<a href="/readers/add" class="btn btn-success">新增读者</a>'
        
        content += """
            </div>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>姓名</th>
                        <th>性别</th>
                        <th>联系方式</th>
                        <th>注册日期</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for reader in readers:
            content += f"""
                    <tr>
                        <td>{reader.reader_id}</td>
                        <td>{reader.name}</td>
                        <td>{reader.gender or '-'}</td>
                        <td>{reader.phone or '-'}</td>
                        <td>{reader.reg_date.strftime('%Y-%m-%d') if reader.reg_date else '-'}</td>
                        <td>
            """
            
            if can_operate:
                content += f'<a href="/readers/edit/{reader.reader_id}" class="btn btn-primary">编辑</a>'
                content += f'<a href="/readers/delete/{reader.reader_id}" class="btn btn-danger" onclick="return confirm(\'确定删除吗？\')">删除</a>'
            else:
                content += '<span style="color:#999;">仅查看</span>'
            
            content += """
                        </td>
                    </tr>
            """
        
        content += """
                </tbody>
            </table>
        </div>
        <script>
            function searchReaders() {
                const keyword = document.getElementById('searchInput').value;
                if (keyword) {
                    window.location.href = '/readers/search?q=' + encodeURIComponent(keyword);
                } else {
                    window.location.href = '/readers';
                }
            }
            document.getElementById('searchInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    searchReaders();
                }
            });
        </script>
        """
        
        return render_template_string(
            MAIN_TEMPLATE,
            title="读者管理",
            subtitle="管理读者信息",
            current_page="readers",
            content=content
        )
    except Exception as e:
        logger.error(f"读者管理页面加载失败: {str(e)}")
        return f"<h1>错误</h1><p>{str(e)}</p>", 500


@app.route('/readers/add', methods=['GET', 'POST'])
@login_required
def add_reader_page():
    """新增读者"""
    error = None
    if request.method == 'POST':
        name = request.form.get('name')
        gender = request.form.get('gender')
        phone = request.form.get('phone')
        
        success, message, *_ = add_reader(name, gender, phone)
        if success:
            return redirect('/readers')
        else:
            error = message
    
    content = f"""
    <div class="card">
        <h2>新增读者</h2>
        {f'<div class="alert alert-error">{error}</div>' if error else ''}
        <form method="POST">
            <div class="form-group">
                <label>姓名 *</label>
                <input type="text" name="name" required>
            </div>
            <div class="form-group">
                <label>性别</label>
                <select name="gender">
                    <option value="">请选择</option>
                    <option value="男">男</option>
                    <option value="女">女</option>
                    <option value="其他">其他</option>
                </select>
            </div>
            <div class="form-group">
                <label>联系方式</label>
                <input type="text" name="phone" placeholder="手机号">
            </div>
            <button type="submit" class="btn btn-success">提交</button>
            <a href="/readers" class="btn btn-danger">取消</a>
        </form>
    </div>
    """
    
    return render_template_string(
        MAIN_TEMPLATE,
        title="新增读者",
        subtitle="添加新读者到系统",
        current_page="readers",
        content=content
    )


@app.route('/readers/edit/<int:reader_id>', methods=['GET', 'POST'])
@login_required
def edit_reader_page(reader_id):
    """编辑读者"""
    error = None
    success, reader = get_reader_by_id(reader_id)
    
    if not success:
        return redirect('/readers')
    
    if request.method == 'POST':
        name = request.form.get('name')
        gender = request.form.get('gender')
        phone = request.form.get('phone')
        
        success, message = update_reader(reader_id, name, gender, phone)
        if success:
            return redirect('/readers')
        else:
            error = message
    
    gender_selected = {'': '', '男': 'selected', '女': 'selected', '其他': 'selected'}
    if reader.gender:
        gender_selected = {k: 'selected' if k == reader.gender else '' for k in gender_selected.keys()}
    
    content = f"""
    <div class="card">
        <h2>编辑读者</h2>
        {f'<div class="alert alert-error">{error}</div>' if error else ''}
        <form method="POST">
            <div class="form-group">
                <label>姓名 *</label>
                <input type="text" name="name" value="{reader.name}" required>
            </div>
            <div class="form-group">
                <label>性别</label>
                <select name="gender">
                    <option value="" {gender_selected.get('', '')}>请选择</option>
                    <option value="男" {gender_selected.get('男', '')}>男</option>
                    <option value="女" {gender_selected.get('女', '')}>女</option>
                    <option value="其他" {gender_selected.get('其他', '')}>其他</option>
                </select>
            </div>
            <div class="form-group">
                <label>联系方式</label>
                <input type="text" name="phone" value="{reader.phone or ''}" placeholder="手机号">
            </div>
            <button type="submit" class="btn btn-success">保存</button>
            <a href="/readers" class="btn btn-danger">取消</a>
        </form>
    </div>
    """
    
    return render_template_string(
        MAIN_TEMPLATE,
        title="编辑读者",
        subtitle="修改读者信息",
        current_page="readers",
        content=content
    )


@app.route('/readers/delete/<int:reader_id>')
@login_required
def delete_reader_page(reader_id):
    """删除读者"""
    success, message = delete_reader(reader_id)
    flash(message)
    return redirect('/readers')


@app.route('/readers/search')
@login_required
def search_readers_page():
    """搜索读者"""
    keyword = request.args.get('q', '')
    if not keyword:
        return redirect('/readers')
    
    success, readers = search_readers(keyword)
    if not success:
        readers = []
    
    user_role = session.get('role', '查看员')
    can_operate = user_role in ['管理员', '操作员']
    
    content = f"""
    <div class="card">
        <h2>搜索结果："{keyword}"</h2>
        <div class="search-box">
            <input type="text" id="searchInput" value="{keyword}" placeholder="搜索读者（姓名/手机号）">
            <button onclick="searchReaders()">搜索</button>
            <a href="/readers" class="btn">返回列表</a>
        """
    
    if can_operate:
        content += '<a href="/readers/add" class="btn btn-success">新增读者</a>'
    
    content += """
        </div>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>姓名</th>
                    <th>性别</th>
                    <th>联系方式</th>
                    <th>注册日期</th>
                    <th>操作</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for reader in readers:
        content += f"""
                <tr>
                    <td>{reader.reader_id}</td>
                    <td>{reader.name}</td>
                    <td>{reader.gender or '-'}</td>
                    <td>{reader.phone or '-'}</td>
                    <td>{reader.reg_date.strftime('%Y-%m-%d') if reader.reg_date else '-'}</td>
                    <td>
        """
        
        if can_operate:
            content += f'<a href="/readers/edit/{reader.reader_id}" class="btn btn-primary">编辑</a>'
            content += f'<a href="/readers/delete/{reader.reader_id}" class="btn btn-danger" onclick="return confirm(\'确定删除吗？\')">删除</a>'
        else:
            content += '<span style="color:#999;">仅查看</span>'
        
        content += """
                    </td>
                </tr>
        """
    
    content += """
            </tbody>
        </table>
    </div>
    <script>
        function searchReaders() {
            const keyword = document.getElementById('searchInput').value;
            if (keyword) {
                window.location.href = '/readers/search?q=' + encodeURIComponent(keyword);
            } else {
                window.location.href = '/readers';
            }
        }
        document.getElementById('searchInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchReaders();
            }
        });
    </script>
    """
    
    return render_template_string(
        MAIN_TEMPLATE,
        title="搜索读者",
        subtitle=f'搜索结果："{keyword}"',
        current_page="readers",
        content=content
    )


@app.route('/borrows')
@login_required
def borrows_page():
    """借阅管理页面"""
    try:
        # 确保设置当前用户
        if 'user_id' in session:
            services.set_current_user({
                "user_id": session.get('user_id'),
                "username": session.get('username'),
                "role": session.get('role')
            })
        
        success, result = get_all_borrows()
        if success:
            borrows = result
        else:
            borrows = []
            logger.warning(f"获取借阅列表失败: {result}")
        
        # 获取图书和读者信息用于显示
        session_db = db_connector.get_session("mysql")
        books_dict = {b.book_id: b for b in session_db.query(Book).all()}
        readers_dict = {r.reader_id: r for r in session_db.query(Reader).all()}
        
        user_role = session.get('role', '查看员')
        can_operate = user_role in ['管理员', '操作员']
        
        logger.info(f"借阅管理页面: 成功={success}, 借阅数量={len(borrows) if success else 0}, 用户角色={user_role}")
        
        content = """
        <div class="card">
            <h2>借阅管理</h2>
            <div style="margin-bottom: 20px;">
        """
        
        if can_operate:
            content += """
                <a href="/borrows/add" class="btn btn-success">借阅图书</a>
            """
        
        content += """
                <a href="/borrows/overdue" class="btn btn-danger">查看逾期</a>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>图书名称</th>
                        <th>读者姓名</th>
                        <th>借阅日期</th>
                        <th>归还日期</th>
                        <th>是否逾期</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for borrow in borrows:
            book = books_dict.get(borrow.book_id)
            reader = readers_dict.get(borrow.reader_id)
            book_name = book.book_name if book else f"图书ID:{borrow.book_id}"
            reader_name = reader.name if reader else f"读者ID:{borrow.reader_id}"
            
            content += f"""
                    <tr>
                        <td>{borrow.borrow_id}</td>
                        <td>{book_name}</td>
                        <td>{reader_name}</td>
                        <td>{borrow.borrow_date.strftime('%Y-%m-%d') if borrow.borrow_date else '-'}</td>
                        <td>{borrow.return_date.strftime('%Y-%m-%d') if borrow.return_date else '<span style="color:red;">未归还</span>'}</td>
                        <td>{'<span style="color:red;">是</span>' if borrow.is_overdue else '否'}</td>
                        <td>
            """
            
            if can_operate and not borrow.return_date:
                content += f'<a href="/borrows/return/{borrow.borrow_id}" class="btn btn-success">归还</a>'
            
            content += """
                        </td>
                    </tr>
            """
        
        content += """
                </tbody>
            </table>
        </div>
        """
        
        return render_template_string(
            MAIN_TEMPLATE,
            title="借阅管理",
            subtitle="管理图书借阅记录",
            current_page="borrows",
            content=content
        )
    except Exception as e:
        logger.error(f"借阅管理页面加载失败: {str(e)}")
        return f"<h1>错误</h1><p>{str(e)}</p>", 500


@app.route('/borrows/add', methods=['GET', 'POST'])
@login_required
def borrow_add():
    """借阅图书"""
    error = None
    if request.method == 'POST':
        try:
            book_id = nonnegative_int(request.form.get('book_id'), "图书编号")
            reader_id = nonnegative_int(request.form.get('reader_id'), "读者编号")
            if book_id == 0 or reader_id == 0:
                raise ValueError("请选择有效的图书和读者")
        except ValueError as exc:
            return str(exc), 400
        success, message, *_ = borrow_book(book_id, reader_id)
        if success:
            return redirect('/borrows')
        else:
            error = message
    
    # 获取可借阅的图书（库存>0）和所有读者
    session_db = db_connector.get_session("mysql")
    available_books = session_db.query(Book).filter(Book.stock > 0).all()
    readers = session_db.query(Reader).all()
    
    book_options = ""
    for book in available_books:
        book_options += f'<option value="{book.book_id}">{book.book_name} (库存:{book.stock})</option>'
    
    reader_options = ""
    for reader in readers:
        reader_options += f'<option value="{reader.reader_id}">{reader.name} ({reader.phone or "无手机号"})</option>'
    
    content = f"""
    <div class="card">
        <h2>借阅图书</h2>
        {f'<div class="alert alert-error">{error}</div>' if error else ''}
        <form method="POST">
            <div class="form-group">
                <label>选择图书 *</label>
                <select name="book_id" required>
                    <option value="">请选择图书</option>
                    {book_options}
                </select>
            </div>
            <div class="form-group">
                <label>选择读者 *</label>
                <select name="reader_id" required>
                    <option value="">请选择读者</option>
                    {reader_options}
                </select>
            </div>
            <button type="submit" class="btn btn-success">提交</button>
            <a href="/borrows" class="btn btn-danger">取消</a>
        </form>
    </div>
    """
    return render_template_string(
        MAIN_TEMPLATE,
        title="借阅图书",
        subtitle="登记图书借阅",
        current_page="borrows",
        content=content
    )


@app.route('/borrows/return/<int:borrow_id>')
@login_required
def borrow_return(borrow_id):
    """归还图书"""
    success, message = return_book(borrow_id)
    flash(message)
    return redirect('/borrows')


@app.route('/borrows/overdue')
@login_required
def overdue_borrows():
    """逾期借阅"""
    try:
        success, borrows = get_overdue_borrows()
        if not success:
            borrows = []
        
        # 获取图书和读者信息
        session_db = db_connector.get_session("mysql")
        books_dict = {b.book_id: b for b in session_db.query(Book).all()}
        readers_dict = {r.reader_id: r for r in session_db.query(Reader).all()}
        
        user_role = session.get('role', '查看员')
        can_operate = user_role in ['管理员', '操作员']
        
        content = """
        <div class="card">
            <h2>逾期借阅记录</h2>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>图书名称</th>
                        <th>读者姓名</th>
                        <th>借阅日期</th>
                        <th>逾期天数</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        from datetime import datetime, timedelta
        today = datetime.now().date()
        
        for borrow in borrows:
            book = books_dict.get(borrow.book_id)
            reader = readers_dict.get(borrow.reader_id)
            book_name = book.book_name if book else f"图书ID:{borrow.book_id}"
            reader_name = reader.name if reader else f"读者ID:{borrow.reader_id}"
            
            # 计算逾期天数
            borrow_date = borrow.borrow_date.date() if borrow.borrow_date else today
            overdue_days = (today - borrow_date).days - config.BORROW_CONFIG["max_borrow_days"]
            overdue_days = max(0, overdue_days)
            
            content += f"""
                    <tr>
                        <td>{borrow.borrow_id}</td>
                        <td>{book_name}</td>
                        <td>{reader_name}</td>
                        <td>{borrow.borrow_date.strftime('%Y-%m-%d') if borrow.borrow_date else '-'}</td>
                        <td><span style="color:red;font-weight:bold;">{overdue_days}天</span></td>
                        <td>
            """
            
            if can_operate:
                content += f'<a href="/borrows/return/{borrow.borrow_id}" class="btn btn-success">归还</a>'
            
            content += """
                        </td>
                    </tr>
            """
        
        content += """
                </tbody>
            </table>
        </div>
        """
        
        return render_template_string(
            MAIN_TEMPLATE,
            title="逾期借阅",
            subtitle="查看逾期未归还的图书",
            current_page="borrows",
            content=content
        )
    except Exception as e:
        logger.error(f"逾期借阅页面加载失败: {str(e)}")
        return f"<h1>错误</h1><p>{str(e)}</p>", 500


@app.route('/sync')
@login_required
def sync_page():
    """同步管理页面"""
    try:
        session_db = db_connector.get_session("mysql")
        logs = session_db.query(SyncLog).order_by(SyncLog.sync_time.desc()).limit(50).all()
        
        success, conflicts = get_conflict_records()
        if not success:
            conflicts = []
        
        # 获取当前所有冲突
        from sync_service import sync_service
        success_all, all_conflicts = sync_service.get_all_conflicts()
        if not success_all:
            all_conflicts = []
        
        # 获取提示消息
        message = request.args.get('message', '')
        message_html = ''
        if message:
            message_html = f'<div class="alert alert-info" style="padding: 10px; margin-bottom: 20px; background-color: #d1ecf1; border: 1px solid #bee5eb; border-radius: 4px; color: #0c5460;">{message}</div>'
        
        content = f"""
        <div class="card">
            <h2>同步管理</h2>
            {message_html}
            <div style="margin-bottom: 20px;">
                <a href="/sync/manual" class="btn btn-primary">手动同步</a>
                <a href="/sync/check_conflicts" class="btn btn-danger" style="margin-left: 10px;">检测冲突</a>
            </div>
            <h3>同步日志（最近50条）</h3>
            <table>
                <thead>
                    <tr>
                        <th>时间</th>
                        <th>数据库</th>
                        <th>操作类型</th>
                        <th>状态</th>
                        <th>冲突</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for log in logs:
            content += f"""
                    <tr>
                        <td>{log.sync_time.strftime('%Y-%m-%d %H:%M:%S')}</td>
                        <td>{log.db_name}</td>
                        <td>{log.op_type}</td>
                        <td>{log.sync_status}</td>
                        <td>{'是' if log.is_conflict else '否'}</td>
                    </tr>
            """
        
        content += """
                </tbody>
            </table>
        </div>
        
        <div class="card">
            <h2>当前冲突列表（{len(all_conflicts)} 个）</h2>
        """
        
        if all_conflicts:
            content += """
            <table>
                <thead>
                    <tr>
                        <th>表名</th>
                        <th>记录ID</th>
                        <th>数据库状态</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for conflict in all_conflicts:
                table_name = conflict["table_name"]
                record_id = conflict["record_id"]
                records = conflict["records"]
                times = conflict["times"]
                
                # 显示每个数据库的状态
                db_status = []
                for db_type in ["mysql", "sqlserver", "postgresql"]:
                    if db_type in records and records[db_type] is not None:
                        update_time = times.get(db_type, "未知")
                        if isinstance(update_time, datetime):
                            update_time_str = update_time.strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            update_time_str = str(update_time)
                        db_status.append(f"{db_type}: {update_time_str}")
                    else:
                        db_status.append(f"{db_type}: 无记录")
                
                content += f"""
                    <tr>
                        <td>{table_name}</td>
                        <td>{record_id}</td>
                        <td>{'<br>'.join(db_status)}</td>
                        <td><a href="/sync/resolve/{table_name}/{record_id}" class="btn btn-primary">处理冲突</a></td>
                    </tr>
                """
            
            content += """
                </tbody>
            </table>
            """
        else:
            content += "<p>暂无冲突记录</p>"
        
        content += """
        </div>
        
        <div class="card">
            <h2>冲突历史记录</h2>
        """
        
        if conflicts:
            for conflict in conflicts[:10]:
                content += f"""
                <div class="conflict-item">
                    <strong>数据库:</strong> {conflict.db_name}<br>
                    <strong>时间:</strong> {conflict.sync_time}<br>
                    <strong>描述:</strong> {conflict.conflict_desc or '无'}
                </div>
                """
        else:
            content += "<p>暂无冲突历史记录</p>"
        
        content += "</div>"
        
        return render_template_string(
            MAIN_TEMPLATE,
            title="同步管理",
            subtitle="查看同步日志和冲突记录",
            current_page="sync",
            content=content
        )
    except Exception as e:
        logger.error(f"同步管理页面加载失败: {str(e)}")
        return f"<h1>错误</h1><p>{str(e)}</p>", 500


@app.route('/sync/manual')
@login_required
def manual_sync():
    """手动同步"""
    try:
        sync_service.sync_all_dbs()
        return redirect('/sync?message=手动同步完成')
    except Exception as e:
        logger.error(f"手动同步失败: {str(e)}")
        error_msg = str(e).replace('\n', ' ').replace('\r', ' ')
        return redirect('/sync?message=' + quote(f'手动同步失败: {error_msg}'))


@app.route('/sync/check_conflicts')
@login_required
def check_conflicts():
    """检测冲突"""
    try:
        from sync_service import SyncService
        sync = SyncService()
        
        # 检查所有表的所有记录
        tables = [
            ("books", "book_id"),
            ("readers", "reader_id"),
            ("borrows", "borrow_id"),
            ("users", "user_id")
        ]
        
        conflict_count = 0
        
        for table_name, id_field in tables:
            # 获取每个数据库中该表的所有记录ID
            session_mysql = db_connector.get_session("mysql")
            if table_name == "books":
                all_ids = {b.book_id for b in session_mysql.query(Book).all()}
            elif table_name == "readers":
                all_ids = {r.reader_id for r in session_mysql.query(Reader).all()}
            elif table_name == "borrows":
                all_ids = {b.borrow_id for b in session_mysql.query(Borrow).all()}
            elif table_name == "users":
                from models import User
                all_ids = {u.user_id for u in session_mysql.query(User).all()}
            else:
                continue
            
            # 对每个记录ID进行冲突检测
            for record_id in all_ids:
                if sync.check_conflict(table_name, record_id):
                    conflict_count += 1
        
        if conflict_count > 0:
            return redirect('/sync?message=检测到' + str(conflict_count) + '个冲突，邮件已发送')
        else:
            return redirect('/sync?message=未检测到冲突')
            
    except Exception as e:
        logger.error(f"冲突检测失败: {str(e)}")
        error_msg = str(e).replace('\n', ' ').replace('\r', ' ')
        return redirect('/sync?message=' + quote(f'冲突检测失败: {error_msg}'))


@app.route('/sync/resolve/<table_name>/<int:record_id>')
@login_required
def resolve_conflict_page(table_name, record_id):
    """冲突处理页面"""
    try:
        from sync_service import sync_service
        success, records, times = sync_service.get_conflict_details(table_name, record_id)
        
        if not success:
            return redirect('/sync?message=无法获取冲突详情')
        
        # 构建冲突详情显示
        conflict_details = []
        for db_type in ["mysql", "sqlserver", "postgresql"]:
            record = records.get(db_type)
            update_time = times.get(db_type)
            
            if record:
                # 根据表名获取字段
                if table_name == "books":
                    detail = {
                        "db_type": db_type,
                        "book_name": record.book_name,
                        "author": record.author or "-",
                        "category": record.category or "-",
                        "stock": record.stock,
                        "update_time": update_time.strftime('%Y-%m-%d %H:%M:%S') if isinstance(update_time, datetime) else str(update_time)
                    }
                elif table_name == "readers":
                    detail = {
                        "db_type": db_type,
                        "name": record.name,
                        "gender": record.gender or "-",
                        "phone": record.phone or "-",
                        "update_time": update_time.strftime('%Y-%m-%d %H:%M:%S') if isinstance(update_time, datetime) else str(update_time)
                    }
                elif table_name == "borrows":
                    detail = {
                        "db_type": db_type,
                        "book_id": record.book_id,
                        "reader_id": record.reader_id,
                        "borrow_date": record.borrow_date.strftime('%Y-%m-%d') if record.borrow_date else "-",
                        "return_date": record.return_date.strftime('%Y-%m-%d') if record.return_date else "未归还",
                        "is_overdue": "是" if record.is_overdue else "否",
                        "update_time": update_time.strftime('%Y-%m-%d %H:%M:%S') if isinstance(update_time, datetime) else str(update_time)
                    }
                else:
                    detail = {
                        "db_type": db_type,
                        "data": str(record),
                        "update_time": update_time.strftime('%Y-%m-%d %H:%M:%S') if isinstance(update_time, datetime) else str(update_time)
                    }
            else:
                detail = {
                    "db_type": db_type,
                    "status": "无记录"
                }
            
            conflict_details.append(detail)
        
        # 构建表格显示
        if table_name == "books":
            table_headers = ["数据库", "图书名称", "作者", "分类", "库存", "更新时间"]
            table_rows = []
            for detail in conflict_details:
                if "status" in detail:
                    table_rows.append([detail["db_type"], "无记录", "-", "-", "-", "-"])
                else:
                    table_rows.append([
                        detail["db_type"],
                        detail["book_name"],
                        detail["author"],
                        detail["category"],
                        detail["stock"],
                        detail["update_time"]
                    ])
        elif table_name == "readers":
            table_headers = ["数据库", "姓名", "性别", "联系方式", "更新时间"]
            table_rows = []
            for detail in conflict_details:
                if "status" in detail:
                    table_rows.append([detail["db_type"], "无记录", "-", "-", "-"])
                else:
                    table_rows.append([
                        detail["db_type"],
                        detail["name"],
                        detail["gender"],
                        detail["phone"],
                        detail["update_time"]
                    ])
        elif table_name == "borrows":
            table_headers = ["数据库", "图书ID", "读者ID", "借阅日期", "归还日期", "是否逾期", "更新时间"]
            table_rows = []
            for detail in conflict_details:
                if "status" in detail:
                    table_rows.append([detail["db_type"], "无记录", "-", "-", "-", "-", "-"])
                else:
                    table_rows.append([
                        detail["db_type"],
                        detail["book_id"],
                        detail["reader_id"],
                        detail["borrow_date"],
                        detail["return_date"],
                        detail["is_overdue"],
                        detail["update_time"]
                    ])
        else:
            table_headers = ["数据库", "数据", "更新时间"]
            table_rows = []
            for detail in conflict_details:
                if "status" in detail:
                    table_rows.append([detail["db_type"], "无记录", "-"])
                else:
                    table_rows.append([
                        detail["db_type"],
                        detail.get("data", "-"),
                        detail.get("update_time", "-")
                    ])
        
        # 构建表格HTML
        table_html = "<table><thead><tr>"
        for header in table_headers:
            table_html += f"<th>{header}</th>"
        table_html += "</tr></thead><tbody>"
        
        for row in table_rows:
            table_html += "<tr>"
            for cell in row:
                table_html += f"<td>{cell}</td>"
            table_html += "</tr>"
        
        table_html += "</tbody></table>"
        
        # 构建选择数据库的按钮
        db_buttons = ""
        for db_type in ["mysql", "sqlserver", "postgresql"]:
            if db_type in records and records[db_type] is not None:
                db_buttons += f'<a href="/sync/resolve_action/{table_name}/{record_id}/{db_type}" class="btn btn-primary" style="margin: 5px;" onclick="return confirm(\'确定以{db_type}数据库的数据为准，同步到其他数据库吗？\')">以{db_type}为准</a>'
        
        content = f"""
        <div class="card">
            <h2>处理冲突：{table_name} 表，记录ID {record_id}</h2>
            <p style="color: #666; margin-bottom: 20px;">请选择以哪个数据库的数据为准，系统将自动同步到其他数据库</p>
            
            {table_html}
            
            <div style="margin-top: 30px; padding: 20px; background-color: #f8f9fa; border-radius: 8px;">
                <h3>选择数据源</h3>
                <p style="color: #666; margin-bottom: 15px;">选择一个数据库作为数据源，系统将把该数据库的数据同步到其他数据库：</p>
                {db_buttons}
            </div>
            
            <div style="margin-top: 20px;">
                <a href="/sync" class="btn">返回同步管理</a>
            </div>
        </div>
        """
        
        return render_template_string(
            MAIN_TEMPLATE,
            title="处理冲突",
            subtitle=f"处理 {table_name} 表记录ID {record_id} 的冲突",
            current_page="sync",
            content=content
        )
    except Exception as e:
        logger.error(f"冲突处理页面加载失败: {str(e)}")
        error_msg = str(e).replace('\n', ' ').replace('\r', ' ')
        return redirect('/sync?message=' + quote(f'冲突处理页面加载失败: {error_msg}'))


@app.route('/sync/resolve_action/<table_name>/<int:record_id>/<source_db>')
@login_required
def resolve_conflict_action(table_name, record_id, source_db):
    """执行冲突处理"""
    try:
        from sync_service import sync_service
        success, message = sync_service.resolve_conflict(table_name, record_id, source_db)
        
        if success:
            safe_msg = message.replace('\n', ' ').replace('\r', ' ')
            return redirect('/sync?message=' + quote(f'冲突处理成功: {safe_msg}'))
        else:
            safe_msg = message.replace('\n', ' ').replace('\r', ' ')
            return redirect('/sync?message=' + quote(f'冲突处理失败: {safe_msg}'))
            
    except Exception as e:
        logger.error(f"冲突处理失败: {str(e)}")
        error_msg = str(e).replace('\n', ' ').replace('\r', ' ')
        return redirect('/sync?message=' + quote(f'冲突处理失败: {error_msg}'))


@app.route('/reports')
@login_required
def reports_page():
    """报表统计页面"""
    content = """
    <div class="card">
        <h2>报表统计</h2>
        <div style="margin: 20px 0;">
            <a href="/reports/stock" class="btn btn-primary">生成库存统计</a>
            <a href="/reports/borrow" class="btn btn-primary">生成借阅统计</a>
            <a href="/reports/sync" class="btn btn-primary">生成同步统计</a>
        </div>
    </div>
    """
    return render_template_string(
        MAIN_TEMPLATE,
        title="报表统计",
        subtitle="生成各种统计报表",
        current_page="reports",
        content=content
    )


@app.route('/reports/stock')
@login_required
def report_stock():
    """生成库存统计"""
    success, result = generate_stock_report()
    if success:
        import os
        filename = os.path.basename(result)
        content = f"""
        <div class="card">
            <h2>库存统计报表</h2>
            <div class="alert alert-success">报表已生成成功！</div>
            <div style="text-align: center; margin: 20px 0;">
                <img src="/static/reports/{filename}" alt="库存统计报表" style="max-width: 100%; border: 1px solid #ddd; border-radius: 8px;">
            </div>
            <p><strong>文件路径:</strong> {result}</p>
            <a href="/reports" class="btn">返回</a>
        </div>
        """
    else:
        content = f"""
        <div class="card">
            <h2>错误</h2>
            <div class="alert alert-error">{result}</div>
            <a href="/reports" class="btn">返回</a>
        </div>
        """
    return render_template_string(
        MAIN_TEMPLATE,
        title="库存统计报表",
        subtitle="图书库存分类统计",
        current_page="reports",
        content=content
    )


@app.route('/reports/borrow')
@login_required
def report_borrow():
    """生成借阅统计"""
    success, result = generate_borrow_report()
    if success:
        import os
        filename = os.path.basename(result)
        content = f"""
        <div class="card">
            <h2>借阅统计报表</h2>
            <div class="alert alert-success">报表已生成成功！</div>
            <div style="text-align: center; margin: 20px 0;">
                <img src="/static/reports/{filename}" alt="借阅统计报表" style="max-width: 100%; border: 1px solid #ddd; border-radius: 8px;">
            </div>
            <p><strong>文件路径:</strong> {result}</p>
            <a href="/reports" class="btn">返回</a>
        </div>
        """
    else:
        content = f"""
        <div class="card">
            <h2>错误</h2>
            <div class="alert alert-error">{result}</div>
            <a href="/reports" class="btn">返回</a>
        </div>
        """
    return render_template_string(
        MAIN_TEMPLATE,
        title="借阅统计报表",
        subtitle="近30天借阅统计",
        current_page="reports",
        content=content
    )


@app.route('/reports/sync')
@login_required
def report_sync():
    """生成同步统计"""
    success, result = generate_sync_report()
    if success:
        import os
        filename = os.path.basename(result)
        content = f"""
        <div class="card">
            <h2>同步统计报表</h2>
            <div class="alert alert-success">报表已生成成功！</div>
            <div style="text-align: center; margin: 20px 0;">
                <img src="/static/reports/{filename}" alt="同步统计报表" style="max-width: 100%; border: 1px solid #ddd; border-radius: 8px;">
            </div>
            <p><strong>文件路径:</strong> {result}</p>
            <a href="/reports" class="btn">返回</a>
        </div>
        """
    else:
        content = f"""
        <div class="card">
            <h2>错误</h2>
            <div class="alert alert-error">{result}</div>
            <a href="/reports" class="btn">返回</a>
        </div>
        """
    return render_template_string(
        MAIN_TEMPLATE,
        title="同步统计报表",
        subtitle="近7天同步状态统计",
        current_page="reports",
        content=content
    )




# 添加静态文件路由用于显示报表图片
@app.route('/static/reports/<filename>')
def report_image(filename):
    """返回报表图片"""
    import os
    from flask import send_from_directory
    report_dir = os.path.join(os.path.dirname(__file__), 'reports')
    return send_from_directory(report_dir, filename)


# 调试路由：测试数据查询
@app.route('/debug/books')
@login_required
def debug_books():
    """调试：测试图书查询"""
    try:
        # 确保设置当前用户
        if 'user_id' in session:
            services.set_current_user({
                "user_id": session.get('user_id'),
                "username": session.get('username'),
                "role": session.get('role')
            })
        
        # 直接查询数据库
        session_db = db_connector.get_session("mysql")
        books_direct = session_db.query(Book).all()
        
        # 通过服务查询
        success, result = get_all_books()
        
        debug_info = f"""
        <h1>调试信息</h1>
        <h2>Session信息</h2>
        <pre>user_id: {session.get('user_id')}
username: {session.get('username')}
role: {session.get('role')}</pre>
        
        <h2>Current User (services模块)</h2>
        <pre>{services.current_user}</pre>
        
        <h2>直接查询数据库</h2>
        <p>图书数量: {len(books_direct)}</p>
        <pre>{[(b.book_id, b.book_name) for b in books_direct[:5]]}</pre>
        
        <h2>通过服务查询</h2>
        <p>成功: {success}</p>
        <p>结果类型: {type(result)}</p>
        <p>结果: {result if not success else f'图书数量: {len(result)}'}</p>
        
        <h2>权限检查</h2>
        <p>has_permission('查看员'): {services.has_permission('查看员')}</p>
        <p>has_permission('操作员'): {services.has_permission('操作员')}</p>
        <p>has_permission('管理员'): {services.has_permission('管理员')}</p>
        
        <a href="/books">返回图书管理</a>
        """
        return debug_info
    except Exception as e:
        import traceback
        return f"<h1>错误</h1><pre>{traceback.format_exc()}</pre>"


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("图书管理系统 Web 服务启动")
    logger.info("访问地址: http://localhost:5000")
    logger.info("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)
