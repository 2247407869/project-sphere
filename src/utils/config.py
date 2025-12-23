# 全局配置管理：基于 Pydantic 处理环境变量
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os

class Settings(BaseSettings):
    # 应用通用设置
    PROJECT_NAME: str = "Project Sphere"
    ENV: str = "development"
    DEBUG: bool = True

    # 大模型 API 密钥 (从 .env 文件自动注入)
    OPENAI_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"

    # Qdrant 存储路径配置
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    # 动态构造相对路径，确保在不同环境下存储位置一致
    QDRANT_PATH: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "qdrant_storage")

    # 指定环境变量加载策略
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# 实例化全局单例配置
settings = Settings()
