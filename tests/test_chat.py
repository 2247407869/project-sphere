#!/usr/bin/env python3
# 测试聊天API的工具调用功能

import requests
import json

def test_chat():
    url = "http://localhost:8000/chat"
    data = {
        "message": "我的财务资产详情是什么？",
        "history": [],
        "summary": ""
    }
    
    print("发送请求...")
    response = requests.post(url, json=data, stream=True)
    
    print("响应状态:", response.status_code)
    for line in response.iter_lines():
        if line:
            print(line.decode('utf-8'))

if __name__ == "__main__":
    test_chat()