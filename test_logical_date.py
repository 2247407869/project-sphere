#!/usr/bin/env python3
"""
测试逻辑日期功能
"""
from datetime import datetime, date, timezone, timedelta
from src.utils.date_helper import get_logical_date, get_current_logical_date, format_logical_date, get_beijing_time

def test_logical_date():
    """测试逻辑日期计算"""
    print("=== 逻辑日期测试 (固定北京时间) ===")
    
    # 北京时区
    beijing_tz = timezone(timedelta(hours=8))
    
    # 测试不同时间点的逻辑日期（北京时间）
    test_cases = [
        datetime(2025, 12, 29, 1, 30, tzinfo=beijing_tz),   # 凌晨1:30 -> 应该是12-28
        datetime(2025, 12, 29, 3, 59, tzinfo=beijing_tz),   # 凌晨3:59 -> 应该是12-28
        datetime(2025, 12, 29, 4, 0, tzinfo=beijing_tz),    # 凌晨4:00 -> 应该是12-29
        datetime(2025, 12, 29, 4, 1, tzinfo=beijing_tz),    # 凌晨4:01 -> 应该是12-29
        datetime(2025, 12, 29, 12, 0, tzinfo=beijing_tz),   # 中午12:00 -> 应该是12-29
        datetime(2025, 12, 29, 23, 59, tzinfo=beijing_tz),  # 晚上23:59 -> 应该是12-29
    ]
    
    for dt in test_cases:
        logical_date = get_logical_date(dt)
        print(f"北京时间: {dt.strftime('%Y-%m-%d %H:%M')} -> 逻辑日期: {format_logical_date(logical_date)}")
    
    # 测试当前逻辑日期
    current_logical = get_current_logical_date()
    current_beijing = get_beijing_time()
    print(f"\n当前北京时间: {current_beijing.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"当前逻辑日期: {format_logical_date(current_logical)}")
    
    # 判断当前是否在"深夜模式"
    if current_beijing.hour < 4:
        print("🌙 当前处于深夜模式，对话将记录到前一天的session中")
    else:
        print("☀️ 当前处于正常模式，对话将记录到今天的session中")
    
    # 测试UTC时间转换
    print(f"\n=== 时区转换测试 ===")
    utc_now = datetime.now(timezone.utc)
    beijing_now = get_beijing_time()
    print(f"UTC时间: {utc_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"北京时间: {beijing_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"UTC逻辑日期: {format_logical_date(get_logical_date(utc_now))}")
    print(f"北京逻辑日期: {format_logical_date(get_logical_date(beijing_now))}")

if __name__ == "__main__":
    test_logical_date()