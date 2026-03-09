#!/usr/bin/env python3
# 部署验证测试脚本

import requests
import json
import time
import sys

def test_health_check(base_url):
    """测试健康检查接口"""
    print("🔍 测试健康检查...")
    
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ 健康检查通过")
            print(f"   项目: {data.get('project')}")
            print(f"   状态: {data.get('status')}")
            print(f"   环境: {data.get('config', {}).get('environment')}")
            return True
        else:
            print(f"❌ 健康检查失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False

def test_static_files(base_url):
    """测试静态文件访问"""
    print("🔍 测试静态文件...")
    
    try:
        response = requests.get(base_url, timeout=10)
        if response.status_code == 200:
            print("✅ 主页访问正常")
            return True
        else:
            print(f"❌ 主页访问失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 主页访问异常: {e}")
        return False

def test_debug_page(base_url):
    """测试Debug页面"""
    print("🔍 测试Debug页面...")
    
    try:
        response = requests.get(f"{base_url}/debug", timeout=10)
        if response.status_code == 200:
            print("✅ Debug页面访问正常")
            return True
        else:
            print(f"❌ Debug页面访问失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Debug页面访问异常: {e}")
        return False

def test_session_api(base_url):
    """测试会话API"""
    print("🔍 测试会话API...")
    
    try:
        response = requests.get(f"{base_url}/session/load", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ 会话API正常")
            print(f"   历史消息数: {len(data.get('history', []))}")
            return True
        else:
            print(f"❌ 会话API失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 会话API异常: {e}")
        return False

def main():
    """主测试函数"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1].rstrip('/')
    else:
        base_url = "http://localhost:7860"
    
    print(f"🧪 开始测试部署: {base_url}")
    print("=" * 50)
    
    tests = [
        ("健康检查", test_health_check),
        ("静态文件", test_static_files),
        ("Debug页面", test_debug_page),
        ("会话API", test_session_api)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        success = test_func(base_url)
        results.append((test_name, success))
        time.sleep(1)  # 避免请求过快
    
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    print("=" * 50)
    
    passed = 0
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print("=" * 50)
    print(f"总计: {passed}/{len(results)} 个测试通过")
    
    if passed == len(results):
        print("🎉 所有测试通过！部署成功。")
        return 0
    else:
        print("⚠️  部分测试失败，请检查配置。")
        return 1

if __name__ == "__main__":
    sys.exit(main())