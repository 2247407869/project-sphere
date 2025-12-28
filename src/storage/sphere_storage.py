# Sphere 分层存储管理器
# 管理记忆文件、会话归档和当前对话的分层存储

import json
import logging
import os
from datetime import datetime, date, timedelta
from typing import Optional

from src.storage.infinicloud import InfiniCloudStorage
from src.utils.date_helper import get_current_logical_date, format_logical_date
from src.utils.config import settings

logger = logging.getLogger(__name__)


class SphereStorage:
    """
    Sphere 分层存储管理器
    
    存储结构：
    - /obsidian/mem/           - 长期记忆文件 (M3)
    - /obsidian/sessions/      - 会话归档文件
    - /obsidian/sessions/current/ - 当前对话文件
    """
    
    def __init__(self):
        self.base_url = settings.INFINICLOUD_URL or "https://mori.teracloud.jp/dav"
        self.username = settings.INFINICLOUD_USER or ""
        self.password = settings.INFINICLOUD_PASS or ""
        
        # 创建不同用途的存储实例
        self.memory_storage = InfiniCloudStorage(
            self.base_url, self.username, self.password, 
            settings.INFINICLOUD_MEMORY_DIR
        )
        self.sessions_storage = InfiniCloudStorage(
            self.base_url, self.username, self.password,
            settings.INFINICLOUD_SESSIONS_DIR
        )
        self.current_storage = InfiniCloudStorage(
            self.base_url, self.username, self.password,
            settings.INFINICLOUD_CURRENT_DIR
        )
    
    # ===== 记忆文件管理 (M3) =====
    
    async def list_memory_files(self) -> list[str]:
        """列出所有长期记忆文件"""
        return await self.memory_storage.list_files()
    
    async def read_memory_file(self, filename: str) -> Optional[str]:
        """读取记忆文件内容"""
        return await self.memory_storage.read_file(filename)
    
    async def write_memory_file(self, filename: str, content: str) -> bool:
        """写入记忆文件"""
        return await self.memory_storage.write_file(filename, content)
    
    async def update_memory_timestamp(self, filename: str) -> bool:
        """更新记忆文件的访问时间戳"""
        return await self.memory_storage.update_timestamp(filename)
    
    async def delete_memory_file(self, filename: str) -> bool:
        """删除记忆文件"""
        return await self.memory_storage.delete_file(filename)
    
    # ===== 会话归档管理 =====
    
    async def save_session_archive(self, filename: str, content: str) -> bool:
        """保存统一的会话归档文件"""
        return await self.sessions_storage.write_file(filename, content)
    
    async def list_session_files(self) -> list[str]:
        """列出所有会话文件"""
        return await self.sessions_storage.list_files()
    
    # ===== 当前对话管理 =====
    
    async def save_current_session(self, history: list, summary: str) -> bool:
        """保存当前对话到云端"""
        logical_date = get_current_logical_date()
        session_data = {
            "history": history,
            "summary": summary,
            "last_updated": datetime.now().isoformat(),
            "date": format_logical_date(logical_date),
            "logical_date": format_logical_date(logical_date)  # 明确标记逻辑日期
        }
        
        content = json.dumps(session_data, ensure_ascii=False, indent=2)
        filename = f"current_session_{format_logical_date(logical_date)}.json"
        
        success = await self.current_storage.write_file(filename, content)
        if success:
            logger.info(f"[SphereStorage] 当前对话已保存到云端: {filename} (逻辑日期)")
        return success
    
    async def load_current_session(self) -> dict:
        """从云端加载当前对话"""
        logical_date = get_current_logical_date()
        
        # 首先尝试加载当前逻辑日期的session
        filename = f"current_session_{format_logical_date(logical_date)}.json"
        content = await self.current_storage.read_file(filename)
        
        if content:
            try:
                data = json.loads(content)
                logger.info(f"[SphereStorage] 从云端加载当前对话: {filename} (逻辑日期)")
                return {
                    "history": data.get("history", []),
                    "summary": data.get("summary", "")
                }
            except json.JSONDecodeError as e:
                logger.error(f"[SphereStorage] 解析当前对话失败: {e}")
        
        # 如果当前逻辑日期没有session，尝试加载最近几天的session
        logger.info("[SphereStorage] 当前逻辑日期没有对话记录，尝试加载最近的session...")
        for days_back in range(1, 8):  # 尝试最近7天
            past_logical_date = logical_date - timedelta(days=days_back)
            past_filename = f"current_session_{format_logical_date(past_logical_date)}.json"
            past_content = await self.current_storage.read_file(past_filename)
            
            if past_content:
                try:
                    data = json.loads(past_content)
                    logger.info(f"[SphereStorage] 从云端加载历史对话: {past_filename} (逻辑日期)")
                    return {
                        "history": data.get("history", []),
                        "summary": data.get("summary", "")
                    }
                except json.JSONDecodeError as e:
                    logger.error(f"[SphereStorage] 解析历史对话失败: {e}")
                    continue
        
        # 如果云端都没有，尝试从本地加载
        logger.info("[SphereStorage] 云端没有找到任何session，尝试本地加载...")
        return self._load_local_session()
    
    async def clear_current_session(self) -> bool:
        """清空当前对话（仅云端）"""
        logical_date = get_current_logical_date()
        filename = f"current_session_{format_logical_date(logical_date)}.json"
        empty_data = {
            "history": [],
            "summary": "",
            "last_updated": datetime.now().isoformat(),
            "date": format_logical_date(logical_date),
            "logical_date": format_logical_date(logical_date)
        }
        content = json.dumps(empty_data, ensure_ascii=False, indent=2)
        return await self.current_storage.write_file(filename, content)
    
    def _load_local_session(self) -> dict:
        """从本地加载会话（备用）"""
        session_file = os.path.join("data", "sessions.json")
        if os.path.exists(session_file):
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return {
                        "history": data.get("history", []),
                        "summary": data.get("summary", "")
                    }
            except Exception as e:
                logger.error(f"[SphereStorage] 加载本地会话失败: {e}")
        
        return {"history": [], "summary": ""}


# 全局单例
_sphere_storage: Optional[SphereStorage] = None

def get_sphere_storage() -> SphereStorage:
    """获取 Sphere 存储管理器单例"""
    global _sphere_storage
    if _sphere_storage is None:
        _sphere_storage = SphereStorage()
    return _sphere_storage