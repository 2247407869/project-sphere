import os
import json
import logging
from datetime import datetime, timedelta, date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.agents.daily_archive import trigger_daily_archive
from src.utils.date_helper import get_current_logical_date, format_logical_date, get_beijing_time

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def auto_archive_job():
    """
    每日凌晨执行的自动归档任务。
    归档【前一个逻辑日期】的数据。
    """
    # 获取当前逻辑日期的前一天作为归档目标
    current_logical = get_current_logical_date()
    target_logical = current_logical - timedelta(days=1)
    target_date_str = format_logical_date(target_logical)
    
    logger.info(f"[Scheduler] ⏰ 触发自动归档任务，目标逻辑日期: {target_date_str}")
    
    # 从云端加载目标日期的session
    from src.storage.sphere_storage import get_sphere_storage
    storage = get_sphere_storage()
    
    # 尝试加载目标日期的session文件
    filename = f"current_session_{target_date_str}.json"
    content = await storage.current_storage.read_file(filename)
    
    if not content:
        logger.info(f"[Scheduler] 目标日期 {target_date_str} 的session文件不存在，跳过归档。")
        return

    try:
        data = json.loads(content)
        history = data.get("history", [])
        summary = data.get("summary", "")
            
        if not history:
            logger.info(f"[Scheduler] 目标日期 {target_date_str} 的历史为空，跳过。")
            return
            
        # 执行归档（会自动清理 M1 并更新 M2）
        result = await trigger_daily_archive(
            session_history=history,
            current_m2=summary,
            target_date=target_date_str
        )
        
        logger.info(f"[Scheduler] ✅ 自动归档完成: {result.get('archive_file')}")
        
    except Exception as e:
        logger.error(f"[Scheduler] 自动归档失败: {e}", exc_info=True)

def start_scheduler():
    """启动调度器"""
    # 每天北京时间 03:59 执行（在逻辑日期切换前）
    # 使用 Asia/Shanghai 时区确保使用北京时间
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    import pytz
    
    beijing_tz = pytz.timezone('Asia/Shanghai')
    scheduler.add_job(
        auto_archive_job, 
        'cron', 
        hour=3, 
        minute=59, 
        timezone=beijing_tz
    )
    scheduler.start()
    logger.info("[Scheduler] 🕒 定时任务调度器已启动 (每天北京时间 03:59 执行)")
