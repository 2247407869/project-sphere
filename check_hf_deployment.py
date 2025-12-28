#!/usr/bin/env python3
# 检查 HF Spaces 部署状态

import requests
import time
import sys

def check_hf_space(space_url):
    """检查 HF Space 状态"""
    print(f"🔍 检查 HF Space: {space_url}")
    
    try:
        response = requests.get(space_url, timeout=10)
        if response.status_code == 200:
            print("✅ Space 可访问")
            
            # 检查是否包含我们的应用内容
            if "Project Sphere" in response.text:
                print("✅ 应用内容正常")
                return True
            else:
                print("⚠️  页面可访问但内容可能还在构建中")
                return False
        else:
            print(f"❌ Space 不可访问: HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 连接失败: {e}")
        return False

def check_health_endpoint(space_url):
    """检查健康检查端点"""
    health_url = f"{space_url}/health"
    print(f"🔍 检查健康端点: {health_url}")
    
    try:
        response = requests.get(health_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ 健康检查通过")
            print(f"   项目: {data.get('project', 'Unknown')}")
            print(f"   状态: {data.get('status', 'Unknown')}")
            return True
        else:
            print(f"❌ 健康检查失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False

def main():
    space_url = "https://huggingface.co/spaces/stormynight/project-sphere"
    
    print("🚀 检查 Project Sphere HF Spaces 部署状态")
    print("=" * 60)
    
    max_attempts = 10
    attempt = 1
    
    while attempt <= max_attempts:
        print(f"\n📋 第 {attempt}/{max_attempts} 次检查...")
        
        # 检查基本访问
        space_accessible = check_hf_space(space_url)
        
        if space_accessible:
            # 检查健康端点
            health_ok = check_health_endpoint(space_url)
            
            if health_ok:
                print("\n🎉 部署成功！应用正常运行。")
                print(f"🔗 访问地址: {space_url}")
                return 0
        
        if attempt < max_attempts:
            print(f"⏳ 等待 30 秒后重试... (HF Spaces 通常需要 2-5 分钟构建)")
            time.sleep(30)
        
        attempt += 1
    
    print(f"\n⚠️  经过 {max_attempts} 次检查，应用可能还在构建中。")
    print("请手动访问以下地址检查状态:")
    print(f"🔗 Space 地址: {space_url}")
    print(f"🔗 健康检查: {space_url}/health")
    print(f"🔗 Debug 页面: {space_url}/debug")
    
    return 1

if __name__ == "__main__":
    sys.exit(main())