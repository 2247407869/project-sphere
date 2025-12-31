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
    作为用户的“外挂记忆体”，请从【对话历史】中提取出人类大脑最容易遗忘但又极具价值的信息，沉淀到 M3 长期记忆库中。

    现有文件列表: {json.dumps(memory_files, ensure_ascii=False) if memory_files else "[]"}

    ### 提取准则（防遗忘维度）：
    1. **决策背后的逻辑 (Rationale)**：不仅记录“做了什么”，还要记录“为什么这么做”（这最容易忘）。
    2. **细微偏好与禁忌**：用户对特定事物的小癖好、审美偏好或明确的反感点。
    3. **高熵参考信息**：具体的链接、复杂的 ID、特殊的参数配置、提及的人名或书名。
    4. **战略性转向**：职业规划、生活战略或项目方向的微妙调整。
    5. **未竟之志**：用户提到的“以后想做”或“还没想清楚但很重要”的碎片灵感。

    ### 处理规则：
    1. **智能裂变**: 文件名应领域化（如 `系统架构哲学.md`, `个人财务战略.md`）。
    2. **过滤噪音**: 绝对不记录日常琐事（如“今天吃了什么”），只记录能在 3 个月后产生价值的“干货”。
    3. **命名禁忌**: 禁止使用包含 "session", "archive", "会话" 的名称。

    对话历史：
    {history_text}

    返回 JSON 格式：
    [
      {{
        "filename": "目标文件名", 
        "reason": "为何该条信息值得被人类记录（防遗忘价值）", 
        "change_instruction": "请详细描述要添加/修改的笔记内容，并附带对话发生的背景简述。"
      }}
    ]
    
    如果没有需要“凝结”成长期记忆的信息，返回空数组 []。
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

            要求（笔记规范）：
            1. **结构化录入**：确保信息被归类到合适的 ## 章节下。
            2. **时间戳溯源**：每条新记录或重大修改，请在末尾标注日期，如 `[2025-12-31]`。
            3. **逻辑保留**：如果指令中包含“因为...所以...”，请务必完整保留其逻辑脉络。
            4. **精简干练**：使用清单（-）或表格，避免长篇累牍。
            5. **历史版本感**：如果是修改旧条目，不要直接删除，可以在后面括号注明“（原为xxx，已于2025-12-31更新为yyy）”，除非用户要求彻底重写。
            
            只输出修改后的文档全文。
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
