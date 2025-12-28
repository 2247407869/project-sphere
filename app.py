# Hugging Face Spaces 专用入口 - Gradio 包装器
import gradio as gr
import threading
import time
import uvicorn
import os
import logging
import sys
from pathlib import Path
import requests

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def pre_startup_check():
    """启动前检查"""
    logger.info("🔍 执行启动前检查...")
    
    # 检查关键环境变量
    required_vars = ["DEEPSEEK_API_KEY"]
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        logger.warning(f"⚠️  缺少关键环境变量: {', '.join(missing)}")
        logger.warning("应用可能无法正常工作")
    
    # 创建必要目录
    for dir_name in ["data", "logs"]:
        Path(dir_name).mkdir(exist_ok=True)
    
    logger.info("✅ 启动前检查完成")

# 执行启动前检查
pre_startup_check()

# 全局变量存储 FastAPI 应用
fastapi_app = None
server_thread = None

def start_fastapi_server():
    """在后台启动 FastAPI 服务器"""
    global fastapi_app
    try:
        from main import app as main_app
        fastapi_app = main_app
        logger.info("✅ FastAPI 应用加载成功")
        
        uvicorn.run(
            fastapi_app,
            host="127.0.0.1",
            port=8000,
            log_level="warning"  # 减少日志输出
        )
    except Exception as e:
        logger.error(f"❌ FastAPI 服务器启动失败: {e}")

def wait_for_server():
    """等待服务器启动"""
    max_attempts = 30
    for i in range(max_attempts):
        try:
            response = requests.get("http://127.0.0.1:8000/health", timeout=1)
            if response.status_code == 200:
                logger.info("✅ FastAPI 服务器已就绪")
                return True
        except:
            pass
        time.sleep(1)
    logger.warning("⚠️ FastAPI 服务器启动超时")
    return False

def create_gradio_interface():
    """创建 Gradio 界面"""
    
    # 启动 FastAPI 服务器
    global server_thread
    server_thread = threading.Thread(target=start_fastapi_server, daemon=True)
    server_thread.start()
    
    # 等待服务器启动
    wait_for_server()
    
    # 创建 HTML 内容
    html_content = """
    <div style="width: 100%; height: 800px;">
        <iframe 
            src="http://127.0.0.1:8000/" 
            width="100%" 
            height="800px" 
            frameborder="0"
            style="border: 1px solid #ddd; border-radius: 8px;">
        </iframe>
    </div>
    <script>
    // 定期检查 iframe 是否加载成功
    setInterval(function() {
        const iframe = document.querySelector('iframe');
        if (iframe && !iframe.contentDocument) {
            iframe.src = iframe.src; // 重新加载
        }
    }, 5000);
    </script>
    """
    
    return gr.HTML(html_content)

# 创建 Gradio 应用
with gr.Blocks(
    title="Project Sphere - AI Memory Assistant",
    theme=gr.themes.Soft(),
    css="""
    .gradio-container {
        max-width: 100% !important;
        padding: 0 !important;
    }
    """
) as demo:
    gr.Markdown("# 🧠 Project Sphere - AI Memory Assistant")
    gr.Markdown("一个具有三层记忆架构的AI助手")
    
    # 添加 iframe
    create_gradio_interface()
    
    gr.Markdown("""
    ### 使用说明
    1. 在上方的聊天界面中开始对话
    2. 告诉AI你的个人信息，它会自动记住
    3. 访问 `/debug` 页面查看记忆状态
    4. 支持自动归档和长期记忆管理
    
    **注意**: 这是演示版本，请不要输入敏感信息。
    """)

if __name__ == "__main__":
    # 设置环境变量
    os.environ.setdefault("ENV", "production")
    os.environ.setdefault("DEBUG", "false")
    
    # Hugging Face Spaces 默认监听端口为 7860
    port = int(os.environ.get("PORT", 7860))
    
    logger.info(f"🚀 Project Sphere 正在启动 (Gradio 模式)...")
    logger.info(f"📡 监听端口: {port}")
    
    try:
        demo.launch(
            server_name="0.0.0.0",
            server_port=port,
            share=False,
            show_error=True,
            quiet=False
        )
    except Exception as e:
        logger.error(f"❌ 应用启动失败: {e}")
        raise
