# 日期辅助工具
# 处理以凌晨4点为分界线的"逻辑日期"

from datetime import datetime, date, timedelta

def get_logical_date(dt: datetime = None) -> date:
    """
    获取逻辑日期：以凌晨4点为分界线
    - 凌晨4点前算作前一天
    - 凌晨4点后算作当天
    
    Args:
        dt: 指定时间，默认为当前时间
    
    Returns:
        逻辑日期
    """
    if dt is None:
        dt = datetime.now()
    
    # 如果是凌晨4点前，算作前一天
    if dt.hour < 4:
        return (dt.date() - timedelta(days=1))
    else:
        return dt.date()

def get_current_logical_date() -> date:
    """获取当前逻辑日期"""
    return get_logical_date()

def format_logical_date(logical_date: date) -> str:
    """格式化逻辑日期为字符串"""
    return logical_date.isoformat()