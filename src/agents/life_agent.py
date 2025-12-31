import os
import json
import logging
from src.storage.markdown_table import MarkdownTableEngine
from src.utils.config import settings
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

# 使用 LLM 进行字段决策
llm = ChatOpenAI(
    model="deepseek-chat", 
    api_key=settings.DEEPSEEK_API_KEY or "EMPTY", 
    base_url=settings.DEEPSEEK_BASE_URL,
    temperature=0
)

class LifeAgent:
    """
    生存领域代理：负责生活物资、健康、SOP 等表格的维护。
    核心逻辑：执行 ParentAgent 路由过来的具体数据。
    """
    
    def __init__(self, obsidian_dir: str):
        self.engine = MarkdownTableEngine(obsidian_dir)
        self.file_map = {
            "vitality": "生活/物资状态.md",
            "asset": "财务/金融账单.md",
            "kernel": "哲学/生命积分.md",
            "nav": "职业/航向追踪.md",
            "tactical": "技术/战术日志.md"
        }

    def process_vitality(self, text_context: str):
        """
        处理生存领域的请求。
        1. 调用 LLM 提取字段数据。
        2. 自动对齐表格 Schema。
        3. 执行追加。
        """
        prompt = f"""
        你是一位资产审计员。从以下对话上下文中提取【生存领域】的结构化数据。
        内容："{text_context}"
        
        如果涉及物资变动，请生成包含字段的 JSON：
        - 必须包含：'日期' (YYYY-MM-DD), '物品', '变动量', '单位'
        - 你可以根据上下文逻辑【自主生成】额外字段（例如：'来源', '保质期', '备注' 等）
        - 仅返回 JSON。
        """
        
        try:
            response = llm.invoke([
                SystemMessage(content="你只输出纯 JSON，不含 Markdown。"),
                HumanMessage(content=prompt)
            ])
            data = json.loads(response.content.strip().replace("```json", "").replace("```", ""))
            
            target_file = self.file_map["vitality"]
            
            # 获取现有表格结构
            table = self.engine.read_table(target_file)
            if table:
                # 检查是否有新字段
                new_fields = [k for k in data.keys() if k not in table["headers"]]
                for field in new_fields:
                    logger.info(f"检测到新字段: {field}，正在执行动态扩容...")
                    # 简单回填，旧数据留空
                    self.engine.add_column(target_file, field)
            
            # 追加行
            self.engine.append_row(target_file, data)
            logger.info(f"成功更新生活档案: {data.get('物品', '未知项目')}")
            return f"已在存档中记录：{data}"
            
        except Exception as e:
            logger.error(f"LifeAgent 处理失败: {e}", exc_info=True)
            return f"归档失败: {str(e)}"

# 单测执行流
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # 模拟 Obsidian 目录
    obs_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    agent = LifeAgent(obs_dir)
    
    # 第一次运行：初始化并建表
    print(agent.process_vitality("我刚才在盒马下单了 20 枚鸡蛋，花了 15 块钱，感觉品质不错。"))
    
    # 第二次运行：检测并动态增加“品质”字段
    print(agent.process_vitality("又买了 2 袋面包，日期很新鲜。"))
