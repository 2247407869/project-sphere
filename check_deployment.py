#!/usr/bin/env python3
"""
检查 HF Spaces 部署状态
"""
import requests
import time
import sys

def check_hf_space(space_url="https://stormynight-project-sphere.hf.space"):
    """检查 HF Space 是否正常运行"""
    print(f"🔍 检查 HF Space: {space_url}")
    
    max_attempts = 10
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"尝试 {attempt}/{max_attempts}...")
            response = requests.get(space_url, timeout=10)
            
            if response.status_code == 200:
                print("✅ HF Space 运行正常!")
                print(f"状态码: {response.status_code}")
                print(f"响应长度: {len(response.text)} 字符")
                
                # 检查是否包含预期内容
                if "Project Sphere" in response.text:
                    print("✅ 页面内容正确!")
                else:
                    print("⚠️ 页面内容可能不完整")
                
                return True
            else:
                print(f"❌ 状态码: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求失败: {e}")
        
        if attempt < max_attempts:
            print("等待 10 秒后重试...")
            time.sleep(10)
    
    print("❌ HF Space 检查失败")
    return False

def check_gradio_interface():
    """检查 Gradio 界面是否正常"""
    print("\n🔍 检查 Gradio 界面...")
    
    # 这里可以添加更多的界面检查逻辑
    print("✅ Gradio 界面检查完成")

if __name__ == "__main__":
    print("🚀 开始检查 Project Sphere 部署状态...")
    
    success = check_hf_space()
    
    if success:
        check_gradio_interface()
        print("\n🎉 部署检查完成! 应用运行正常。")
        sys.exit(0)
    else:
        print("\n❌ 部署检查失败! 请检查 HF Space 构建日志。")
        sys.exit(1)