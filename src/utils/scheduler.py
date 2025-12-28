import os
import json
import logging
from datetime import datetime, timedelta, date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.agents.daily_archive import trigger_daily_archive

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def auto_archive_job():
    """
    每日凌晨执行的自动归档任务。
    归档【昨天】的数据。
    """
    today = date.today()
    yesterday = today - timedelta(days=1)
    yesterday_str = yesterday.isoformat()
    
    logger.info(f"[Scheduler] ⏰ 触发自动归档任务，目标日期: {yesterday_str}")
    
    # 读取当前的 sessions.json（包含昨天的对话）
    session_file = os.path.join("data", "sessions.json")
    
    if not os.path.exists(session_file):
        logger.info(f"[Scheduler] sessions.json 不存在，跳过归档。")
        return

    try:
        with open(session_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            history = data.get("history", [])
            summary = data.get("summary", "")
            
        if not history:
            logger.info("[Scheduler] 历史为空，跳过。")
            return
            
        # 执行归档（会自动清理 M1 并更新 M2）
        result = await trigger_daily_archive(
            session_history=history,
            current_m2=summary,
            target_date=yesterday_str
        )
        
        logger.info(f"[Scheduler] ✅ 自动归档完成: {result.get('archive_file')}")
        
    except Exception as e:
        logger.error(f"[Scheduler] 自动归档失败: {e}", exc_info=True)

def start_scheduler():
    """启动调度器"""
    # 每天 04:00 执行
    scheduler.add_job(auto_archive_job, 'cron', hour=4, minute=0)
    scheduler.start()
    logger.info("[Scheduler] 🕒 定时任务调度器已启动 (每天 04:00 执行)")
