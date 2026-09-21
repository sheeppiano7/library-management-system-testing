# -*- coding: utf-8 -*-
"""
定时任务服务
使用APScheduler实现周期同步
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sync_service import sync_service
import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = None


def periodic_sync():
    """周期同步任务"""
    try:
        logger.info("开始执行周期同步...")
        sync_service.sync_all_dbs()
        logger.info("周期同步执行完成")
    except Exception as e:
        logger.error(f"周期同步执行失败: {str(e)}")


def start_scheduler():
    """启动定时任务调度器"""
    global scheduler
    
    if not config.SYNC_CONFIG["periodic_sync"]:
        logger.info("周期同步未启用")
        return
    
    try:
        scheduler = BackgroundScheduler()
        
        # 添加定时任务（每日指定时间执行）
        hour = config.SYNC_CONFIG["sync_hour"]
        minute = config.SYNC_CONFIG["sync_minute"]
        
        scheduler.add_job(
            periodic_sync,
            trigger=CronTrigger(hour=hour, minute=minute),
            id='periodic_sync',
            name='周期同步任务',
            replace_existing=True
        )
        
        scheduler.start()
        logger.info(f"定时任务调度器启动成功，同步时间: {hour:02d}:{minute:02d}")
        
    except Exception as e:
        logger.error(f"启动定时任务调度器失败: {str(e)}")


def stop_scheduler():
    """停止定时任务调度器"""
    global scheduler
    if scheduler:
        scheduler.shutdown()
        logger.info("定时任务调度器已停止")

