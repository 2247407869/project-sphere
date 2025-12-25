# 存储持久化层：对接 Qdrant 向量数据库
from qdrant_client import QdrantClient
from qdrant_client.http import models
from src.utils.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        # 初始化 Qdrant 客户端，使用本地持久化路径
        try:
            self.client = QdrantClient(path=settings.QDRANT_PATH)
            logger.info(f"Qdrant 存储已在路径初始化: {settings.QDRANT_PATH}")
        except RuntimeError as e:
            if "already accessed" in str(e):
                logger.warning("⚠️ Qdrant 数据库已被其他进程占（可能是同步脚本）。正在切换至内存模式 (Ephemeral Mode)...")
                self.client = QdrantClient(":memory:")
            else:
                raise e

    def init_collection(self, collection_name: str, vector_size: int = 1536):
        """
        初始化集合 (Collection)
        """
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == collection_name for c in collections)
            
            if not exists:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
                )
                logger.info(f"成功创建向量集合: {collection_name}")
            else:
                logger.info(f"向量集合 {collection_name} 已存在，跳过创建")
        except Exception as e:
            logger.error(f"Failed to initialize collection: {e}")

# 导出单例对象，供全局使用
vector_store = VectorStore()
