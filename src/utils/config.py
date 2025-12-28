# 全局配置管理：基于 Pydantic 处理环境变量
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os

class Settings(BaseSettings):
    # 应用通用设置
    PROJECT_NAME: str = "Project Sphere"
    ENV: str = "production"  # HF环境默认为生产环境
    DEBUG: bool = False      # HF环境关闭调试模式

    # 大模型 API 密钥 (从环境变量自动注入)
    OPENAI_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"

    # InfiniCloud 存储目录配置
    INFINICLOUD_MEMORY_DIR: str = "/obsidian/mem"          # 长期记忆文件
    INFINICLOUD_SESSIONS_DIR: str = "/obsidian/sessions"   # 会话归档文件
    INFINICLOUD_CURRENT_DIR: str = "/obsidian/sessions/current"  # 当前对话文件

    # InfiniCloud 长期记忆存储 (WebDAV)
    INFINICLOUD_URL: Optional[str] = None
    INFINICLOUD_USER: Optional[str] = None
    INFINICLOUD_PASS: Optional[str] = None

    # 指定环境变量加载策略 - HF环境优先使用环境变量
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True
    )

# 实例化全局单例配置
settings = Settings()
