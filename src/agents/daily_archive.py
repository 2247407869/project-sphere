# 每日归档任务
# 凌晨定时执行或手动触发

import logging
import json
import os
from datetime import datetime, date
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
    api_key=settings.DEEPSEEK_API_KEY,
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
    today = target_date if target_date else date.today().isoformat()
    logger.info(f"[DailyArchive] 开始执行归档任务: {today}...")
    
    storage = get_sphere_storage()
    
    # ===== 1. 生成会话摘要 =====
    history_text = "\n".join([
        f"{'用户' if m['role'] == 'user' else 'AI'}: {m['content']}"
        for m in session_history  # 使用当天所有对话
    ])
    
    summary_prompt = f"""
请总结今天的对话内容。

对话记录：
{history_text}
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
    
    logger.info(f"[DailyArchive] 会话摘要: {session_summary[:100]}...")
    
    # ===== 2. 更新 M2 =====
    m2_prompt = f"""
请基于现有的前情提要和今天的会话摘要，生成新的前情提要。

现有前情提要：
{current_m2}

今天的会话摘要：
{session_summary}
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

