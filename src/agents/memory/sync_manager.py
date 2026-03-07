import os
import json
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class SyncManager:
    """
    同步管理器：负责协调 LobeChat 状态与 MCP 记忆服务器。
    目前的主要职责是捕获对话结束信号并触发记忆提取。
    """
    
    def __init__(self):
        self.mcp_endpoint = os.getenv("MCP_SERVER_URL", "http://cognition-mcp:8000/sse")

    async def on_conversation_turn_end(self, history: List[Dict]):
        """
        每回合结束后调用。
        分析最近的对话，如果包含有价值的信息，则同步到 MCP 服务器。
        """
        if not history:
            return
            
        last_exchange = history[-2:] # 获取最后两轮对话
        # 这里未来可以接入 LLM 进行“价值判断”
        # 暂时简化为：如果最后一条消息较长，则认为是“有价值的情节”
        content_to_save = "\n".join([f"{h['role']}: {h['content']}" for h in last_exchange])
        
        if len(content_to_save) > 50:
            logger.info("[SyncManager] 发现潜在记忆点，正在同步到 MCP...")
            # 实际调用 MCP 服务的工具逻辑
            # 在全架构视角下，LobeChat 会自动通过 MCP 插件完成这一步
            # 此 Manager 更多是作为“兜底”或“主动同步”逻辑
            pass

sync_manager = SyncManager()
