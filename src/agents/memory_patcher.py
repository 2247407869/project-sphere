import logging
import json
from datetime import datetime
from src.storage.sphere_storage import get_sphere_storage
from src.utils.config import settings
from src.agents.memory_tools import list_available_memories
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL,
    temperature=0.0  # 使用 0 温度以确保精确性
)

async def detect_memory_updates(session_history: list[dict]) -> list[dict]:
    """
    检测对话中是否包含针对 M3 记忆文件的状态更新。
    """
    # 获取现有记忆文件列表
    memory_files = await list_available_memories()
    
    # 即使没有现有文件，也应该检测是否需要创建新文件
    # if not memory_files:
    #     return []

    # 构造 Prompt
    history_text = "\n".join([
        f"{'User' if m['role'] == 'user' else 'AI'}: {m['content'][:300]}"
        for m in session_history
    ])

    detect_prompt = f"""
    作为记忆库管理员，请分析【对话历史】，判断用户是否提供了从属于 M3 记忆库的**状态变更**。
    
    现有文件列表: {json.dumps(memory_files, ensure_ascii=False) if memory_files else "[]"}
    
    规则：
    1. **修改/追加**: 如果信息属于现有文件，指定该文件名。
    2. **自动裂变 (Auto-Sharding)**: 如果信息属于**全新领域**且现有文件不适用，请提议一个**新文件名**（如 `法语学习.md`, `旅行计划_日本.md`）。文件命名需简洁、使用中文、领域导向。
    3. **严格过滤**: 忽略闲聊、询问、假设性讨论、测试对话。只有当用户明确提供了具体的个人信息、决策、计划或状态更新时才创建记忆。
    4. **命名规范**: 绝对不要使用包含"会话"、"归档"、"session"等词汇的文件名，这些是系统保留名称。
    
    对话历史：
    {history_text}
    
    返回 JSON 格式：
    [
      {{
        "filename": "目标文件名", 
        "reason": "变更原因", 
        "change_instruction": "详细指令。对于新增文件，请说明文件的用途和初始内容。"
      }}
    ]
    
    如果没有需要记录的状态变更，返回空数组 []。
    """

    try:
        response = await llm.ainvoke([
            SystemMessage(content="你是一个智能的知识库构建者。"),
            HumanMessage(content=detect_prompt)
        ])
        content = response.content.strip()
        if content.startswith("```json"):
            content = content.split("```json")[1].split("```")[0]
        elif content.startswith("```"):
            content = content.split("```")[1].split("```")[0]
            
        updates = json.loads(content)
        # 移除过滤逻辑，允许新文件
        return updates
    except Exception as e:
        logger.error(f"[MemoryPatch] Detection failed: {e}")
        return []

async def apply_memory_patch(filename: str, change_instruction: str) -> bool:
    """
    将变更应用到指定记忆文件（支持新建）。
    """
    storage = get_sphere_storage()
    try:
        # 1. 读取原始内容
        original_content = await storage.read_memory_file(filename)
        is_new_file = original_content is None
        
        if is_new_file:
            logger.info(f"[MemoryPatch] Creating NEW file: {filename}")
            original_content = "" # 空内容用于 Prompt

        # 2. 生成新内容
        if is_new_file:
            patch_prompt = f"""
            你正在创建一个名为【{filename}】的新记忆文件。
            请根据以下初始指令生成文件内容。
            
            初始指令：{change_instruction}
            
            要求：
            1. **标准结构**：必须包含 # 一级标题（文件名）和合理的 ## 二级标题结构。
            2. **内容填充**：将指令中的事实作为初始条目填入。
            3. **格式规范**：使用标准的 Markdown 列表或表格。
            4. 只输出文件全文。
            """
        else:
            patch_prompt = f"""
            请根据【修改指令】更新以下 Markdown 文档内容。
            
            修改指令：{change_instruction}
            
            原文内容：
            {original_content}
            
            要求：
            1. **保持文档结构**：严格保留原有的 Markdown 标题（# ##）、列表缩进和格式。
            2. **智能插入**：如果是新增条目，请找到语义最相关的章节/列表末尾追加。如果没有相关章节，可新建一个小节。
            3. **精准修改**：如果是数值变更，只修改对应数字。
            4. **去重合并**：如果同一日期下已存在相似的记录，请**合并**或**替换**，避免重复冗余。保持历史记录精简。
            5. 不要输出任何解释或 Markdown 代码块标记（如 ```markdown），直接输出完整的文档内容。
            """
        
        response = await llm.ainvoke([
            SystemMessage(content="你是一个文档维护专家。只输出修改后的文档全文。"),
            HumanMessage(content=patch_prompt)
        ])
        new_content = response.content.strip()
        if new_content.startswith("```markdown"):
            new_content = new_content.split("```markdown")[1].split("```")[0]
        elif new_content.startswith("```"):
            new_content = new_content.split("```")[1].split("```")[0]
        
        # 3. 写入新内容
        await storage.write_memory_file(filename, new_content)
        logger.info(f"[MemoryPatch] Successfully {'created' if is_new_file else 'patched'} {filename}")
        return True

    except Exception as e:
        logger.error(f"[MemoryPatch] Patching {filename} failed: {e}")
        return False
