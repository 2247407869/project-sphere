# Hugging Face Spaces 专用入口 (独立产品版)
import uvicorn
import os
from main import app

if __name__ == "__main__":
    # Hugging Face Spaces 默认监听端口为 7860 或环境变量 PORT
    port = int(os.environ.get("PORT", 7860))
    logger.info(f"Sphere Backend Server is launching on port {port}...")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
