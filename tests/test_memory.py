#!/usr/bin/env python3
# 测试M3记忆系统

import requests
import json

def test_memory():
    url = "http://localhost:8000/chat"
    data = {
        "message": "我的净资产是多少？",
        "history": [],
        "summary": ""
    }
    
    print("测试M3记忆系统...")
    response = requests.post(url, json=data, stream=True)
    
    print("响应状态:", response.status_code)
    content = ""
    for line in response.iter_lines():
        if line:
            decoded = line.decode('utf-8')
            if 'event: content' in decoded:
                content_part = decoded.split('data: ', 1)[1] if 'data: ' in decoded else ''
                content += content_part
                print(content_part, end='', flush=True)
            elif 'event: status' in decoded:
                status = decoded.split('data: ', 1)[1] if 'data: ' in decoded else ''
                print(f"\n[状态] {status}")
    
    print(f"\n\n完整回答: {content}")

if __name__ == "__main__":
    test_memory()