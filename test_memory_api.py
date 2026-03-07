#!/usr/bin/env python3
"""
测试记忆API
"""
import requests
import json

def test_memory_apis():
    base_url = "http://localhost:8000"
    
    print("=== 测试记忆API ===")
    
    # 测试记忆列表
    print("\n1. 测试 /memory/list")
    try:
        response = requests.get(f"{base_url}/memory/list")
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"返回数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"错误: {e}")
    
    # 测试记忆读取
    print("\n2. 测试 /memory/read")
    try:
        payload = {"filename": "用户基本信息.md"}
        response = requests.post(f"{base_url}/memory/read", json=payload)
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"返回数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    test_memory_apis()