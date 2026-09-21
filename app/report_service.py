# -*- coding: utf-8 -*-
"""
报表生成服务
支持PC端和移动端报表
"""
import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import matplotlib.pyplot as plt
from matplotlib import font_manager
import pandas as pd
from datetime import datetime, timedelta
from db_connector import db_connector
from models import Book, Borrow, SyncLog
import config
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


def generate_stock_report(db_type="mysql"):
    """生成库存统计报表（饼图）"""
    try:
        session = db_connector.get_session(db_type)
        books = session.query(Book).all()
        
        # 统计各分类库存
        category_stock = {}
        for book in books:
            category = book.category if book.category else "未分类"
            category_stock[category] = category_stock.get(category, 0) + book.stock
        
        if not category_stock:
            return False, "暂无数据"
        
        # 生成饼图（适配页面显示，缩小尺寸）
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.pie(category_stock.values(), labels=category_stock.keys(), autopct='%1.1f%%', startangle=90)
        ax.set_title('图书库存分类统计', fontsize=16, fontweight='bold')
        
        # 保存图片（适中分辨率，避免过大文件）
        report_path = os.path.join(config.REPORT_DIR, f"stock_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        plt.savefig(report_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"库存统计报表生成成功: {report_path}")
        return True, report_path
        
    except Exception as e:
        logger.error(f"生成库存统计报表失败: {str(e)}")
        return False, f"生成报表失败: {str(e)}"


def generate_borrow_report(db_type="mysql", days=30):
    """生成借阅统计报表（柱状图）"""
    try:
        session = db_connector.get_session(db_type)
        
        # 获取近N天的借阅记录
        start_date = datetime.now() - timedelta(days=days)
        borrows = session.query(Borrow).filter(Borrow.borrow_date >= start_date).all()
        
        # 统计每日借阅次数
        daily_borrows = {}
        for borrow in borrows:
            date_str = borrow.borrow_date.strftime('%Y-%m-%d')
            daily_borrows[date_str] = daily_borrows.get(date_str, 0) + 1
        
        if not daily_borrows:
            return False, "暂无数据"
        
        # 生成柱状图
        dates = sorted(daily_borrows.keys())
        counts = [daily_borrows[d] for d in dates]
        
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.bar(dates, counts, color='steelblue', alpha=0.7)
        ax.set_xlabel('日期', fontsize=12)
        ax.set_ylabel('借阅次数', fontsize=12)
        ax.set_title(f'近{days}天借阅统计', fontsize=16, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        
        # 旋转x轴标签
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # 保存图片
        report_path = os.path.join(config.REPORT_DIR, f"borrow_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        plt.savefig(report_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"借阅统计报表生成成功: {report_path}")
        return True, report_path
        
    except Exception as e:
        logger.error(f"生成借阅统计报表失败: {str(e)}")
        return False, f"生成报表失败: {str(e)}"


def generate_sync_report(days=7):
    """生成同步状态报表（表格+折线图）"""
    try:
        session = db_connector.get_session("mysql")
        
        # 获取近N天的同步日志
        start_date = datetime.now() - timedelta(days=days)
        logs = session.query(SyncLog).filter(SyncLog.sync_time >= start_date).all()
        
        if not logs:
            return False, "暂无数据"
        
        # 统计每日同步情况
        daily_stats = {}
        for log in logs:
            date_str = log.sync_time.strftime('%Y-%m-%d')
            if date_str not in daily_stats:
                daily_stats[date_str] = {"成功": 0, "失败": 0, "冲突": 0}
            
            if log.sync_status == "成功":
                daily_stats[date_str]["成功"] += 1
            else:
                daily_stats[date_str]["失败"] += 1
            
            if log.is_conflict:
                daily_stats[date_str]["冲突"] += 1
        
        dates = sorted(daily_stats.keys())
        success_counts = [daily_stats[d]["成功"] for d in dates]
        fail_counts = [daily_stats[d]["失败"] for d in dates]
        conflict_counts = [daily_stats[d]["冲突"] for d in dates]
        
        # 生成折线图
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(dates, success_counts, marker='o', label='成功', color='green', linewidth=2)
        ax.plot(dates, fail_counts, marker='s', label='失败', color='red', linewidth=2)
        ax.plot(dates, conflict_counts, marker='^', label='冲突', color='orange', linewidth=2)
        ax.set_xlabel('日期', fontsize=12)
        ax.set_ylabel('次数', fontsize=12)
        ax.set_title(f'近{days}天同步状态统计', fontsize=16, fontweight='bold')
        ax.legend()
        ax.grid(alpha=0.3)
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # 保存图片
        report_path = os.path.join(config.REPORT_DIR, f"sync_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        plt.savefig(report_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"同步状态报表生成成功: {report_path}")
        return True, report_path
        
    except Exception as e:
        logger.error(f"生成同步状态报表失败: {str(e)}")
        return False, f"生成报表失败: {str(e)}"


def generate_mobile_sync_stats():
    """生成移动端同步统计（柱状图）"""
    try:
        session = db_connector.get_session("mysql")
        
        # 获取当日同步日志
        today = datetime.now().date()
        logs = session.query(SyncLog).filter(
            SyncLog.sync_time >= datetime.combine(today, datetime.min.time())
        ).all()
        
        stats = {"成功": 0, "失败": 0, "冲突": 0}
        for log in logs:
            if log.sync_status == "成功":
                stats["成功"] += 1
            else:
                stats["失败"] += 1
            if log.is_conflict:
                stats["冲突"] += 1
        
        # 生成柱状图
        fig, ax = plt.subplots(figsize=(8, 6))
        categories = list(stats.keys())
        values = list(stats.values())
        colors = ['green', 'red', 'orange']
        ax.bar(categories, values, color=colors, alpha=0.7)
        ax.set_ylabel('次数', fontsize=12)
        ax.set_title('当日同步统计', fontsize=16, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        
        # 保存图片
        report_path = os.path.join(config.REPORT_DIR, f"mobile_sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        plt.savefig(report_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"移动端同步统计生成成功: {report_path}")
        return True, report_path
        
    except Exception as e:
        logger.error(f"生成移动端同步统计失败: {str(e)}")
        return False, f"生成报表失败: {str(e)}"


def get_conflict_records():
    """获取冲突记录列表"""
    try:
        session = db_connector.get_session("mysql")
        conflicts = session.query(SyncLog).filter_by(is_conflict=True).order_by(SyncLog.sync_time.desc()).all()
        return True, conflicts
    except Exception as e:
        logger.error(f"获取冲突记录失败: {str(e)}")
        return False, f"获取冲突记录失败: {str(e)}"

