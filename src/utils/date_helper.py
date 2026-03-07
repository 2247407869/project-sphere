# 日期辅助工具
# 处理以凌晨4点为分界线的"逻辑日期"
# 固定使用北京时间 (UTC+8)

from datetime import datetime, date, timedelta, timezone

# 北京时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))

def get_logical_date(dt: datetime = None) -> date:
    """
    获取逻辑日期：以凌晨4点为分界线
    - 凌晨4点前算作前一天
    - 凌晨4点后算作当天
    - 固定使用北京时间 (UTC+8)
    
    Args:
        dt: 指定时间，默认为当前北京时间
    
    Returns:
        逻辑日期
    """
    if dt is None:
        # 获取当前北京时间
        dt = datetime.now(BEIJING_TZ)
    elif dt.tzinfo is None:
        # 如果传入的时间没有时区信息，假设为北京时间
        dt = dt.replace(tzinfo=BEIJING_TZ)
    else:
        # 转换为北京时间
        dt = dt.astimezone(BEIJING_TZ)
    
    # 如果是凌晨4点前，算作前一天
    if dt.hour < 4:
        return (dt.date() - timedelta(days=1))
    else:
        return dt.date()

def get_current_logical_date() -> date:
    """获取当前逻辑日期（基于北京时间）"""
    return get_logical_date()

def format_logical_date(logical_date: date) -> str:
    """格式化逻辑日期为字符串"""
    return logical_date.isoformat()

def get_beijing_time() -> datetime:
    """获取当前北京时间"""
    return datetime.now(BEIJING_TZ)