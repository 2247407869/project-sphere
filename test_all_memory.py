#!/usr/bin/env python3
# 测试一轮对话读取所有记忆文件

import requests
import json
import time

def test_all_memory():
    url = "http://localhost:8000/chat"
    data = {
        "message": "请帮我总结一下我的所有个人信息，包括财务资产、职业规划、健康管理、情感记录、技能学习等各个方面的详细情况",
        "history": [],
        "summary": ""
    }
    
    print("测试读取所有记忆文件...")
    print("发送时间:", time.strftime('%H:%M:%S'))
    
    try:
        response = requests.post(url, json=data, stream=True, timeout=60)
        print("响应状态:", response.status_code)
        
        start_time = time.time()
        content_count = 0
        
        for line in response.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if 'event: content' in decoded:
                    content_count += 1
                    if content_count % 10 == 0:
                        elapsed = time.time() - start_time
                        print(f"[{elapsed:.1f}s] 已接收 {content_count} 个内容块")
                elif 'event: status' in decoded:
                    status = decoded.split('data: ', 1)[1] if 'data: ' in decoded else ''
                    elapsed = time.time() - start_time
                    print(f"[{elapsed:.1f}s] 状态: {status}")
                elif 'event: done' in decoded:
                    elapsed = time.time() - start_time
                    print(f"[{elapsed:.1f}s] 完成！总共接收 {content_count} 个内容块")
                    break
        
        total_time = time.time() - start_time
        print(f"总耗时: {total_time:.1f}秒")
        
    except requests.exceptions.Timeout:
        print("❌ 请求超时（60秒）")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

if __name__ == "__main__":
    test_all_memory()