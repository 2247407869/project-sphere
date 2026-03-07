# 长期记忆工具模块
# 提供 fetch_memory 和相关记忆管理工具

import logging
import re
from typing import Optional

from src.storage.sphere_storage import get_sphere_storage

logger = logging.getLogger(__name__)

# 常量定义
class MemoryConfig:
    MAX_PARAGRAPHS = 3
    MAX_LINES = 10
    CONTENT_PREVIEW_LENGTH = 2000


import time

async def fetch_memory(filename: str, keywords: Optional[str] = None) -> dict:
    """
    检索长期记忆 (M3)。
    
    Args:
        filename: 记忆文件名（如 职业规划.md）
        keywords: 可选搜索关键词
    
    Returns:
        dict: {"success": bool, "content": str, "error": str}
    
    性能优化：
    - 移除了实时更新 access_time（从 3 次网络请求减少到 1 次）
    - access_time 改为每日归档时批量更新
    """
    start_time = time.time()
    
    storage = get_sphere_storage()
    
    logger.info(f"[{time.strftime('%H:%M:%S')}] [fetch_memory] 开始检索: {filename}, 关键词: {keywords}")
    
    content = await storage.read_memory_file(filename)
    read_time = time.time() - start_time
    
    if content is None:
        logger.warning(f"[{time.strftime('%H:%M:%S')}] [fetch_memory] 文件不存在: {filename} (耗时 {read_time:.2f}s)")
        return {
            "success": False,
            "content": "",
            "error": f"文件不存在: {filename}"
        }
    
    # 如果有关键词，进行段落级搜索
    if keywords:
        paragraphs = re.split(r'\n(?=##)', content)  # 按二级标题分割
        matched = [p for p in paragraphs if keywords in p]
        
        if matched:
            result = "\n\n".join(matched[:MemoryConfig.MAX_PARAGRAPHS])  # 最多返回3段
        else:
            # 降级到全文匹配
            lines = [l for l in content.split("\n") if keywords in l]
            result = "\n".join(lines[:MemoryConfig.MAX_LINES]) if lines else content[:MemoryConfig.CONTENT_PREVIEW_LENGTH]
    else:
        # 无关键词，返回截断内容
        result = content[:MemoryConfig.CONTENT_PREVIEW_LENGTH]
    
    total_time = time.time() - start_time
    logger.info(f"[{time.strftime('%H:%M:%S')}] [fetch_memory] 完成: {filename}, 返回 {len(result)} 字符 (耗时 {total_time:.2f}s)")
    
    return {"success": True, "content": result}


async def read_memory_readonly(filename: str) -> dict:
    """只读获取记忆文件内容（不更新时间戳，用于 Debug 查看）"""
    storage = get_sphere_storage()
    content = await storage.read_memory_file(filename)
    if content:
        return {"success": True, "content": content, "error": ""}
    return {"success": False, "content": "", "error": f"文件 {filename} 不存在"}


async def list_available_memories() -> list[str]:
    """
    列出所有可用的记忆文件列表。
    现在记忆文件和会话文件存储在不同目录，不需要过滤。
    """
    storage = get_sphere_storage()
    return await storage.list_memory_files()


# ===== 工具定义 (供 LLM Function Calling 使用) =====

MEMORY_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "fetch_memory",
            "description": "检索长期记忆。当用户询问历史事件、个人偏好、过往决策等需要查阅记忆库的内容时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "记忆文件名（如 职业规划.md, 健康管理.md）"
                    },
                    "keywords": {
                        "type": "string",
                        "description": "可选搜索关键词"
                    }
                },
                "required": ["filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_daily_archive",
            "description": "手动触发每日归档任务（调试用）。执行会话摘要、M2更新、长期记忆更新等凌晨任务。"
        }
    }
]
