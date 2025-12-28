import logging
import json
from src.agents.life_agent import LifeAgent
from src.utils.config import settings
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

# 分发器使用 LLM 进行语义分类
llm = ChatOpenAI(
    model="deepseek-chat", 
    api_key=settings.DEEPSEEK_API_KEY, 
    base_url=settings.DEEPSEEK_BASE_URL,
    temperature=0
)

class Dispatcher:
    """
    大脑分发器：后台异步处理逻辑的核心。
    负责将对话日志分类为不同的档案领域，并触发对应的子代理。
    """
    
    def __init__(self, obsidian_dir: str):
        self.obsidian_dir = obsidian_dir
        self.life_agent = LifeAgent(obsidian_dir)
        # 未来可扩展其他领域代理
        # self.asset_agent = AssetAgent(obsidian_dir)

    def dispatch(self, conversation_log: str):
        """
        分析对话日志并分发任务。
        """
        prompt = f"""
        分析以下对话内容，判断其中涉及的【档案库领域】。
        对话内容："{conversation_log}"
        
        可选领域：
        - 'vitality': 生活、物资、鸡蛋、面包、健康、情感。
        - 'asset': 财务、账户、金额。
        - 'kernel': 决策规则、人生游戏、生命积分。
        - 'nav': 职业规划、方舟计划进度。
        - 'tactical': 技术笔记、Debug、管理SOP。
        - 'none': 无需归档的闲聊。
        
        仅返回一个合法的 JSON，包含 'domain' 键。
        """
        
        try:
            response = llm.invoke([
                SystemMessage(content="你只输出纯 JSON。"),
                HumanMessage(content=prompt)
            ])
            res = json.loads(response.content.strip().replace("```json", "").replace("```", ""))
            domain = res.get("domain", "none").lower()
            
            logger.info(f"意图分发：领域为 [{domain}]")
            
            if domain == "vitality":
                return self.life_agent.process_vitality(conversation_log)
            elif domain == "none":
                return "无需归档。"
            else:
                return f"该领域 [{domain}] 的处理逻辑尚在开发中。"
                
        except Exception as e:
            logger.error(f"Dispatcher 分发失败: {e}", exc_info=True)
            return f"分发失败: {e}"

if __name__ == "__main__":
    import os
    logging.basicConfig(level=logging.INFO)
    obs_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    dispatcher = Dispatcher(obs_dir)
    
    # 模拟一个复杂的对话
    test_log = "今天心情不错，中午吃了自己蒸的鸡蛋。买了20个蛋一共15块，记一下物资。"
    print(dispatcher.dispatch(test_log))
