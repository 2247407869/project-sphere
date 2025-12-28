# InfiniCloud 存储适配器
# 用于读写长期记忆文件

import os
import re
import logging
import time
from datetime import datetime
from typing import Optional, Tuple
import httpx

logger = logging.getLogger(__name__)

# ===== 内存缓存 =====
# 缓存格式: {key: (content, timestamp)}
_MEMORY_CACHE: dict[str, Tuple[str, float]] = {}
_FILE_LIST_CACHE: Tuple[list[str], float] = ([], 0)

# 缓存有效期（秒）
CACHE_TTL_FILE = 300      # 文件内容缓存 5 分钟
CACHE_TTL_LIST = 60       # 文件列表缓存 1 分钟


def get_cached(key: str, ttl: int) -> Optional[str]:
    """获取缓存内容，过期返回 None"""
    if key in _MEMORY_CACHE:
        content, ts = _MEMORY_CACHE[key]
        if time.time() - ts < ttl:
            logger.info(f"[{time.strftime('%H:%M:%S')}] [Cache HIT] {key}")
            return content
    return None


def set_cache(key: str, content: str):
    """设置缓存"""
    _MEMORY_CACHE[key] = (content, time.time())
    logger.info(f"[{time.strftime('%H:%M:%S')}] [Cache SET] {key} ({len(content)} chars)")


def clear_cache(key: str = None):
    """清除缓存（单个或全部）"""
    global _MEMORY_CACHE, _FILE_LIST_CACHE
    if key:
        _MEMORY_CACHE.pop(key, None)
    else:
        _MEMORY_CACHE.clear()
        _FILE_LIST_CACHE = ([], 0)
    logger.info(f"[Cache CLEAR] {key or 'ALL'}")


class InfiniCloudStorage:
    """
    InfiniCloud WebDAV 存储适配器。
    使用 httpx 进行 HTTP 请求，支持中文文件名。
    """
    
    def __init__(self, base_url: str, username: str, password: str, memory_dir: str = "/obsidian/mem"):
        self.base_url = base_url.rstrip("/")
        self.auth = (username, password)
        self.memory_dir = memory_dir  # 从配置传入
    
    def _get_url(self, filename: str) -> str:
        return f"{self.base_url}{self.memory_dir}/{filename}"
    
    async def list_files(self) -> list[str]:
        """列出所有记忆文件（带缓存）"""
        global _FILE_LIST_CACHE
        
        # 检查缓存
        cached_files, cached_ts = _FILE_LIST_CACHE
        if cached_files and time.time() - cached_ts < CACHE_TTL_LIST:
            logger.info(f"[{time.strftime('%H:%M:%S')}] [Cache HIT] file_list ({len(cached_files)} files)")
            return cached_files
        
        from urllib.parse import unquote
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    "PROPFIND",
                    f"{self.base_url}{self.memory_dir}/",
                    auth=self.auth,
                    headers={"Depth": "1"}
                )
                # 解析 WebDAV XML 响应，大小写不敏感，解码 URL
                matches = re.findall(r'<D:href>.*?/([^/]+\.md)</D:href>', response.text, re.IGNORECASE)
                files = [unquote(f) for f in matches]
                
                # 更新缓存
                _FILE_LIST_CACHE = (files, time.time())
                logger.info(f"[{time.strftime('%H:%M:%S')}] [Cache SET] file_list ({len(files)} files)")
                return files
        except Exception as e:
            logger.error(f"列出文件失败: {e}")
            return cached_files if cached_files else []  # 失败时返回旧缓存
    
    async def read_file(self, filename: str) -> Optional[str]:
        """读取记忆文件内容（带缓存）"""
        cache_key = f"file:{filename}"
        
        # 检查缓存
        cached = get_cached(cache_key, CACHE_TTL_FILE)
        if cached is not None:
            return cached
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self._get_url(filename),
                    auth=self.auth
                )
                if response.status_code == 200:
                    content = response.text
                    # 更新缓存
                    set_cache(cache_key, content)
                    return content
                else:
                    logger.warning(f"文件不存在: {filename}")
                    return None
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            return None
    
    async def write_file(self, filename: str, content: str) -> bool:
        """写入记忆文件"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    self._get_url(filename),
                    auth=self.auth,
                    content=content.encode("utf-8"),
                    headers={"Content-Type": "text/markdown; charset=utf-8"}
                )
                success = response.status_code in (200, 201, 204)
                if success:
                    logger.info(f"文件写入成功: {filename}")
                    # 更新缓存
                    cache_key = f"file:{filename}"
                    set_cache(cache_key, content)
                return success
        except Exception as e:
            logger.error(f"写入文件失败: {e}")
            return False
    
    async def update_timestamp(self, filename: str) -> bool:
        """更新文件的 last_accessed 时间戳"""
        content = await self.read_file(filename)
        if content is None:
            return False
        
        now = datetime.now().strftime("%Y-%m-%d")
        # 更新或插入时间戳
        if "> last_accessed:" in content:
            content = re.sub(
                r"> last_accessed: \d{4}-\d{2}-\d{2}",
                f"> last_accessed: {now}",
                content
            )
        else:
            # 在标题后插入
            content = re.sub(
                r"(# .+\n)",
                f"\\1> last_accessed: {now}\n",
                content,
                count=1
            )
        return await self.write_file(filename, content)
    
    async def delete_file(self, filename: str) -> bool:
        """删除记忆文件"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    self._get_url(filename),
                    auth=self.auth
                )
                success = response.status_code in (200, 204, 404)  # 404也算成功（文件已不存在）
                if success:
                    logger.info(f"文件删除成功: {filename}")
                    # 清除相关缓存
                    clear_cache(f"file:{filename}")
                    global _FILE_LIST_CACHE
                    _FILE_LIST_CACHE = ([], 0)  # 清除文件列表缓存
                return success
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return False


# 从配置初始化单例
def get_infinicloud_storage() -> InfiniCloudStorage:
    from src.utils.config import settings
    return InfiniCloudStorage(
        base_url=settings.INFINICLOUD_URL or "https://mori.teracloud.jp/dav",
        username=settings.INFINICLOUD_USER or "",
        password=settings.INFINICLOUD_PASS or "",
        memory_dir=settings.INFINICLOUD_MEMORY_DIR
    )

