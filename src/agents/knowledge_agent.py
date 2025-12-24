# Agent 编排层：定义基于 LangGraph 的逻辑状态机
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from src.utils.config import settings
from src.storage.qdrant_client import vector_store
import logging
import json

logger = logging.getLogger(__name__)

# 初始化大语言模型驱动 (DeepSeek 适配版)
llm = ChatOpenAI(
    model="deepseek-chat", 
    api_key=settings.DEEPSEEK_API_KEY, 
    base_url=settings.DEEPSEEK_BASE_URL,
    temperature=0
)

# 定义 Agent 的状态结构
class AgentState(TypedDict):
    content: str    # 原始文本内容
    metadata: dict   # 元数据（来源、标签等）
    summary: str     # AI 生成的简要摘要
    status: str      # 当前处理状态

def extraction_node(state: AgentState):
    """
    语义提取节点：使用 LLM 分析内容并生成结构化 JSON。
    1. 构造提示词，强制要求中文输出
    2. 调用 DeepSeek API
    3. 清洗并解析 JSON 响应
    """
    logger.info("正在使用 LLM 提取元数据与摘要...")
    
    prompt = f"""
    分析以下内容并提取结构化情报。
    请务必使用【中文】返回结果。
    结果必须是合法的 JSON 对象，不要包含任何 Markdown 格式。
    
    包含以下键：
    - 'summary': 用一句话概括核心内容。
    - 'keywords': 提取 3 个左右的核心关键词标签。
    
    内容：
    {state["content"]}
    """
    
    try:
        # 向 LLM 发起指令
        logger.info(f"--- [Extraction Start] ---")
        logger.info(f"Targeting content for extraction (length: {len(state['content'])})")
        response = llm.invoke([
            SystemMessage(content="你是一位严谨的知识架构师。你只输出纯 JSON，不输出任何解释或 Markdown 标记。"), 
            HumanMessage(content=prompt)
        ])
        
        # 兼容性清洗：移除可能存在的 Markdown 代码块标记 (如 ```json)
        raw_content = response.content.strip()
        logger.info(f"Raw LLM Extraction Output: {raw_content[:200]}...")
        
        if raw_content.startswith("```json"):
            raw_content = raw_content[7:-3].strip()
        elif raw_content.startswith("```"):
            raw_content = raw_content[3:-3].strip()
            
        # 将文本解析为 Python 字典
        data = json.loads(raw_content)
        
        state["summary"] = data.get("summary", "解析失败")
        state["metadata"] = {
            "keywords": data.get("keywords", []),
            "source": state["metadata"].get("source", "unknown"),
            "processed": True
        }
        state["status"] = "processed"
        logger.info(f"Successfully extracted summary: {state['summary']}")
        logger.info(f"Keywords identified: {state['metadata']['keywords']}")
        logger.info("--- [Extraction End] ---")
    except Exception as e:
        logger.error(f"LLM 提取失败: {e}", exc_info=True)
        state["status"] = "processed_with_error"
        state["summary"] = "AI 分析过程中出现异常。"
        
    return state

# 独立产品化：移除物理同步依赖

def storage_node(state: AgentState):
    """
    存储节点：独立产品化重构。
    将“灵感”持久化至云端 facts.json (Beta L3 事实云)。
    """
    import json
    import os
    from datetime import datetime
    
    logger.info("--- [Cloud Storage Process] ---")
    
    fact_entry = {
        "timestamp": datetime.now().isoformat(),
        "summary": state["summary"],
        "content": state["content"],
        "metadata": state["metadata"]
    }

    # 路径适配云端环境
    facts_file = os.path.join("data", "facts.json")
    os.makedirs("data", exist_ok=True)

    try:
        facts = []
        if os.path.exists(facts_file):
            with open(facts_file, "r", encoding="utf-8") as f:
                facts = json.load(f)
        
        facts.append(fact_entry)
        
        with open(facts_file, "w", encoding="utf-8") as f:
            json.dump(facts, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Fact accumulated. Total facts: {len(facts)}")
        state["status"] = "captured_in_cloud"
    except Exception as e:
        logger.error(f"Failed to save fact: {e}")
        state["status"] = "storage_failed"

    logger.info("--- [Storage Process End] ---")
    return state

# 构建 LangGraph 图拓扑
workflow = StateGraph(AgentState)

# 注册节点
workflow.add_node("extract", extraction_node)
workflow.add_node("store", storage_node)

# 编排执行流：入口 -> 提取 -> 存储 -> 结束
workflow.set_entry_point("extract")
workflow.add_edge("extract", "store")
workflow.add_edge("store", END)

# 编译生成可执行的 Agent 实例
knowledge_graph = workflow.compile()
