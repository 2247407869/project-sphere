#!/usr/bin/env python3
# Gradio 包装器 - 用于 HF Spaces 部署

import gradio as gr
import threading
import time
import requests
import uvicorn
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def create_iframe_interface():
    """创建一个包含 iframe 的界面"""
    
    # 启动 FastAPI 服务器的函数
    def start_server():
        try:
            from main import app as fastapi_app
            uvicorn.run(
                fastapi_app,
                host="0.0.0.0",
                port=8000,
                log_level="info"
            )
        except Exception as e:
            print(f"服务器启动失败: {e}")
    
    # 在后台启动服务器
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # 等待服务器启动
    time.sleep(3)
    
    # 创建 HTML 内容
    html_content = """
    <div style="width: 100%; height: 800px;">
        <h2>🧠 Project Sphere - AI Memory Assistant</h2>
        <p>正在加载应用...</p>
        <iframe 
            src="/proxy/8000/" 
            width="100%" 
            height="750px" 
            frameborder="0"
            style="border: 1px solid #ddd; border-radius: 8px;">
        </iframe>
        <p><small>如果应用未加载，请等待几秒钟后刷新页面</small></p>
    </div>
    """
    
    return gr.HTML(html_content)

# 创建 Gradio 应用
with gr.Blocks(title="Project Sphere", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🧠 Project Sphere - AI Memory Assistant")
    gr.Markdown("一个具有三层记忆架构的AI助手")
    
    # 添加 iframe
    create_iframe_interface()

# 启动应用
if __name__ == "__main__":
    # 设置环境变量
    os.environ.setdefault("ENV", "production")
    os.environ.setdefault("DEBUG", "false")
    
    print("🚀 启动 Project Sphere (Gradio 包装器)")
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )