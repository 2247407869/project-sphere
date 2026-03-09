#!/usr/bin/env python3
# 简单测试工具调用

import requests
import json

def test_simple():
    url = "http://localhost:8000/chat"
    data = {
        "message": "请调用fetch_memory工具查询财务资产.md",
        "history": [],
        "summary": ""
    }
    
    print("发送明确的工具调用请求...")
    response = requests.post(url, json=data, stream=True)
    
    print("响应状态:", response.status_code)
    for line in response.iter_lines():
        if line:
            decoded = line.decode('utf-8')
            if 'event: content' in decoded or 'event: status' in decoded:
                print(decoded)

if __name__ == "__main__":
    test_simple()