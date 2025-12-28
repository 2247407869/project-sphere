# Hugging Face Spaces 专用入口
import uvicorn
import os
import logging
import sys
from pathlib import Path

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

# 导入主应用
try:
    from main import app
    logger.info("✅ 主应用模块加载成功")
except Exception as e:
    logger.error(f"❌ 主应用模块加载失败: {e}")
    raise

if __name__ == "__main__":
    # Hugging Face Spaces 默认监听端口为 7860 或环境变量 PORT
    port = int(os.environ.get("PORT", 7860))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"🚀 Project Sphere 正在启动...")
    logger.info(f"📡 监听地址: {host}:{port}")
    logger.info(f"🌍 环境: {os.environ.get('ENV', 'production')}")
    
    try:
        uvicorn.run(
            "app:app", 
            host=host, 
            port=port, 
            reload=False,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"❌ 应用启动失败: {e}")
        raise
