# 每日归档任务
# 凌晨定时执行或手动触发

import logging
import json
import os
from src.utils.date_helper import get_current_logical_date, format_logical_date
from typing import Optional
from src.storage.sphere_storage import get_sphere_storage
from src.utils.config import settings
from src.agents.memory_patcher import detect_memory_updates, apply_memory_patch
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

# LLM 实例
llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=settings.DEEPSEEK_API_KEY or "EMPTY",
    base_url=settings.DEEPSEEK_BASE_URL,
    temperature=0.3
)


async def trigger_daily_archive(
    session_history: list[dict],
    current_m2: str = "",
    target_date: Optional[str] = None
) -> dict:
    """
    手动触发每日归档任务。
    
    1. 生成当日会话摘要
    2. 更新 M2 前情提要
    3. 提取关键信息更新长期记忆
    4. 归档原始对话
    
    Args:
        session_history: 当日对话历史 [{"role": "user/assistant", "content": "..."}]
        current_m2: 当前的 M2 前情提要
        target_date: 归档日期 (ISO格式)，默认为今天
    
    Returns:
        dict: 归档结果
    """
    today = target_date if target_date else format_logical_date(get_current_logical_date())
    logger.info(f"[DailyArchive] 开始执行归档任务: {today}...")
    
    storage = get_sphere_storage()
    
    # ===== 1. 生成会话摘要 =====
    history_text = "\n".join([
        f"{'用户' if m['role'] == 'user' else 'AI'}: {m['content']}"
        for m in session_history  # 使用当天所有对话
    ])
    
    summary_prompt = f"""
请作为用户的“数字大脑”，对今天的对话进行深度消化与反思。

### 原始对话记录：
{history_text}

### 任务：
1. **凝结核心值**：今天最重要的 2-3 个讨论要点是什么？
2. **捕捉情感基调**：用户的状态如何？（如：富有成效、困惑、焦虑、充满动力）
3. **行动指南 (Next Actions)**：有哪些明确待办或未来的系统优化方向？
4. **认知沉淀**：今天学到了什么关于用户或系统的新知识？

请以第一人称（如“我们今天讨论了...”）生成一份具有反思感的精炼摘要。
"""
    
    try:
        response = llm.invoke([
            SystemMessage(content="你是一位精准的会话归档员。"),
            HumanMessage(content=summary_prompt)
        ])
        session_summary = response.content.strip()
    except Exception as e:
        logger.error(f"生成摘要失败: {e}")
        session_summary = f"[归档失败] {today} 的对话"
    
    logger.info(f"[DailyArchive] Step 1: 会话摘要已生成 ({len(session_summary)} chars)")
    
    m2_prompt = f"""
请将旧的背景记忆与今天的深度反思进行“生物学式”的巩固与融合。

### 旧的背景记忆：
{current_m2}

### 今天的深度反思：
{session_summary}

### 指令：
1. **去粗取精**：剔除已过时的细节，保留长期有效的核心价值。
2. **强化叙事**：将记忆编织成一段连贯、不断进化的“个人成长史”。
3. **线性时序**：确保旧脉络在前，新进化在后。
4. **类人反思**：不仅仅是陈述事实，要体现出认知的深化和系统的状态演进。

生成的更新版前情提要应简洁、有力且富有洞察力。
"""
    
    try:
        response = llm.invoke([
            SystemMessage(content="你是一位精准的叙事压缩专家。"),
            HumanMessage(content=m2_prompt)
        ])
        new_m2 = response.content.strip()
    except Exception as e:
        logger.error(f"更新M2失败: {e}")
        new_m2 = current_m2
    
    logger.info(f"[DailyArchive] Step 2: M2 前情提要已巩固 ({len(new_m2)} chars)")
    
    
    # ===== 3. 自动 Patch M3 =====
    patch_results = []
    try:
        updates = await detect_memory_updates(session_history)
        if updates:
            logger.info(f"[DailyArchive] 检测到 {len(updates)} 个 M3 变更，开始应用补丁...")
            for update in updates:
                success = await apply_memory_patch(update["filename"], update["change_instruction"])
                patch_results.append({
                    "filename": update["filename"],
                    "instruction": update["change_instruction"],
                    "success": success
                })
    except Exception as e:
        logger.error(f"[DailyArchive] M3 Patch 失败: {e}")

    if not patch_results:
        logger.info("[DailyArchive] Step 3: 未检测到值得存入 M3 的长期记忆变更。")
    else:
        logger.info(f"[DailyArchive] Step 3: 已成功应用 {len(patch_results)} 个 M3 补丁。")

    # ===== 4. 统一归档到会话目录 =====
    # 创建统一的会话归档文件，包含摘要、M2和完整对话
    archive_content = f"""# 会话归档 {today}

> session_date: {today}
> turns: {len(session_history)}

## 会话摘要
{session_summary}

## M2 前情提要
{new_m2}

## 对话记录
"""
    for m in session_history:
        role = "👤 用户" if m['role'] == 'user' else "🤖 AI"
        archive_content += f"\n### {role}\n{m['content']}\n"
    
    # 添加JSON格式的完整数据（便于程序化处理）
    archive_content += f"""

## 完整会话数据 (JSON)
```json
{{
  "session_date": "{today}",
  "turns": {len(session_history)},
  "session_summary": {json.dumps(session_summary, ensure_ascii=False)},
  "m2_summary": {json.dumps(new_m2, ensure_ascii=False)},
  "history": {json.dumps(session_history, ensure_ascii=False, indent=2)}
}}
```
"""
    
    archive_filename = f"会话归档_{today}.md"
    await storage.save_session_archive(archive_filename, archive_content)
    
    logger.info(f"[DailyArchive] 完成统一归档: {archive_filename}")
    
    # ===== 5. 更新当前session的摘要，但保持对话历史清空 =====
    # 将新的M2摘要保存到当前session，这样用户回到应用时能看到更新的摘要
    await storage.save_current_session([], new_m2)  # 空历史，但保留新摘要
    logger.info(f"[DailyArchive] 已更新当前session摘要: {len(new_m2)} 字符")
    
    return {
        "success": True,
        "session_summary": session_summary,
        "new_m2": new_m2,
        "archive_file": archive_filename,
        "patch_results": patch_results,
        "m1_cleared": True
    }

