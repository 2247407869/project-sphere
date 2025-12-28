# 主程序入口：负责 Web 应用的启动与 API 路由调度
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Optional

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel

from src.agents.knowledge_agent import llm
from src.utils.config import settings
from src.utils.scheduler import start_scheduler

# 配置日志系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("Sphere-Core")
logger.propagate = True

# 常量定义
class Config:
    SESSION_FILE = os.path.join("data", "sessions.json")
    DEBUG_PROMPT_FILE = "debug_prompt.txt"
    DEBUG_STREAM_LOG = "debug_stream.log"
    FRONTEND_PATH = os.path.join(os.path.dirname(__file__), "frontend")
    
    # 超时设置
    CHAT_TIMEOUT = 45.0
    TOOL_TIMEOUT = 30.0
    
    # 限制设置
    MAX_TOOLS_PER_ROUND = 5
    MAX_TOOL_ROUNDS = 10
    CONTENT_PREVIEW_LENGTH = 2000

app = FastAPI(title=settings.PROJECT_NAME)

# 定义 API 请求模型
class CollectRequest(BaseModel):
    content: str
    source: str = "mobile"

class ChatRequest(BaseModel):
    message: str
    history: list = []
    summary: str = ""  # 当前对话的滚动摘要
    auto_save: bool = True  # 是否自动保存会话（测试时可设为 False）

# 配置 CORS 跨域支持 (允许移动端 Web 访问)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    start_scheduler()

@app.get("/health")
async def health_check():
    """健康检查接口：用于验证服务是否在线"""
    try:
        # 检查基本配置
        config_status = {
            "deepseek_api_configured": bool(settings.DEEPSEEK_API_KEY),
            "webdav_configured": bool(settings.INFINICLOUD_URL and settings.INFINICLOUD_USER),
            "environment": settings.ENV,
            "debug_mode": settings.DEBUG
        }
        
        # 检查存储连接（简单测试）
        storage_status = "unknown"
        try:
            from src.storage.sphere_storage import get_sphere_storage
            storage = get_sphere_storage()
            # 简单的连接测试
            storage_status = "connected"
        except Exception as e:
            storage_status = f"error: {str(e)[:100]}"
        
        return {
            "status": "healthy",
            "project": settings.PROJECT_NAME,
            "version": "1.0.0",
            "config": config_status,
            "storage": storage_status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# ===== 会话管理 =====
class SessionSyncRequest(BaseModel):
    history: list
    summary: str

@app.get("/session/load")
async def load_session():
    """从云端恢复会话状态"""
    from src.storage.sphere_storage import get_sphere_storage
    storage = get_sphere_storage()
    return await storage.load_current_session()

@app.post("/session/sync")
async def sync_session(req: SessionSyncRequest):
    """同步会话状态至云端"""
    from src.storage.sphere_storage import get_sphere_storage
    storage = get_sphere_storage()
    success = await storage.save_current_session(req.history, req.summary)
    if success:
        return {"status": "synced"}
    else:
        return {"status": "error", "message": "同步失败"}

@app.delete("/session/clear")
async def clear_session():
    """清空会话历史和摘要（云端+本地）"""
    from src.storage.sphere_storage import get_sphere_storage
    storage = get_sphere_storage()
    
    # 清空云端
    cloud_success = await storage.clear_current_session()
    
    # 清空本地文件
    local_success = True
    try:
        if os.path.exists(Config.SESSION_FILE):
            with open(Config.SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump({"history": [], "summary": ""}, f, ensure_ascii=False, indent=2)
            logger.info("[Session] Cleared local session file")
    except Exception as e:
        logger.error(f"[Session] Failed to clear local file: {e}")
        local_success = False
    
    if cloud_success and local_success:
        logger.info("[Session] Cleared current session (cloud + local)")
        return {"status": "cleared"}
    else:
        return {"status": "partial", "message": f"云端: {'成功' if cloud_success else '失败'}, 本地: {'成功' if local_success else '失败'}"}

class SummaryUpdateRequest(BaseModel):
    summary: str

@app.put("/session/summary")
async def update_summary(req: SummaryUpdateRequest):
    """更新摘要内容（保留对话历史）"""
    try:
        existing = {"history": [], "summary": ""}
        if os.path.exists(Config.SESSION_FILE):
            with open(Config.SESSION_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        existing["summary"] = req.summary
        with open(Config.SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        logger.info(f"[Session] Summary updated, length: {len(req.summary)}")
        return {"status": "updated", "summary": req.summary}
    except Exception as e:
        logger.error(f"Failed to update summary: {e}")
        return {"status": "error", "message": str(e)}

@app.delete("/session/message/{index}")
async def delete_message(index: int):
    """删除指定索引的对话消息（同时删除对应的 AI 回复）"""
    try:
        if not os.path.exists(Config.SESSION_FILE):
            return {"status": "error", "message": "Session file not found"}
        
        with open(Config.SESSION_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        history = data.get("history", [])
        if index < 0 or index >= len(history):
            return {"status": "error", "message": "Invalid index"}
        
        # 计算要删除的消息数量（用户消息 + 后续的 AI/system 消息）
        deleted = [history[index]]
        
        # 如果删除的是用户消息，同时删除后续的 AI 回复和可能的 system 消息
        i = index + 1
        while i < len(history) and history[i]["role"] != "user":
            deleted.append(history[i])
            i += 1
        
        # 从 history 中移除
        for _ in range(len(deleted)):
            if index < len(history):
                history.pop(index)
        
        data["history"] = history
        with open(Config.SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"[Session] Deleted {len(deleted)} messages starting at index {index}")
        return {"status": "deleted", "count": len(deleted), "history": history}
    except Exception as e:
        logger.error(f"Failed to delete message: {e}")
        return {"status": "error", "message": str(e)}

# [REMOVED] TodoItem 和 todos API 已移除 (V3.0 简化)

# ===== 认知球 V2.3 新增接口 =====
from src.agents.memory_tools import fetch_memory, list_available_memories, MEMORY_TOOLS, read_memory_readonly
from src.agents.daily_archive import trigger_daily_archive as do_daily_archive

class MemoryRequest(BaseModel):
    filename: str
    keywords: str = None

@app.post("/memory/fetch")
async def api_fetch_memory(req: MemoryRequest):
    """获取长期记忆 (M3) - 会更新访问时间"""
    result = await fetch_memory(req.filename, req.keywords)
    return result

@app.post("/memory/read")
async def api_read_memory(req: MemoryRequest):
    """只读获取记忆文件（不更新时间戳，Debug 用）"""
    result = await read_memory_readonly(req.filename)
    return result

class DeleteMemoryRequest(BaseModel):
    filename: str

@app.delete("/memory/delete")
async def api_delete_memory(req: DeleteMemoryRequest):
    """删除记忆文件"""
    from src.storage.sphere_storage import get_sphere_storage
    storage = get_sphere_storage()
    success = await storage.delete_memory_file(req.filename)
    if success:
        logger.info(f"[API] 记忆文件已删除: {req.filename}")
        return {"success": True, "message": f"文件 {req.filename} 已删除"}
    else:
        return {"success": False, "error": f"删除文件 {req.filename} 失败"}

@app.get("/memory/list")
async def api_list_memories():
    """列出可用的记忆文件"""
    files = await list_available_memories()
    return {"files": files}

@app.get("/debug/status")
async def debug_status():
    """Debug: 获取系统状态"""
    from src.utils.date_helper import get_current_logical_date, format_logical_date
    from src.storage.sphere_storage import get_sphere_storage
    
    storage = get_sphere_storage()
    session_data = await storage.load_current_session()
    
    # 获取记忆文件数量
    try:
        memories_response = await list_available_memories()
        memory_count = len(memories_response.get("memories", []))
    except:
        memory_count = 0
    
    return {
        "logical_date": format_logical_date(get_current_logical_date()),
        "session_count": len(session_data.get("history", [])),
        "summary_length": len(session_data.get("summary", "")),
        "memory_count": memory_count,
        "system_time": datetime.now().isoformat()
    }

@app.post("/debug/archive")
async def debug_archive():
    """Debug: 手动触发归档"""
    try:
        from src.storage.sphere_storage import get_sphere_storage
        storage = get_sphere_storage()
        session_data = await storage.load_current_session()
        
        if not session_data.get("history"):
            return {"status": "skipped", "message": "没有对话记录需要归档"}
        
        result = await do_daily_archive(
            session_history=session_data["history"],
            current_m2=session_data.get("summary", "")
        )
        
        return {"status": "success", "message": f"归档完成: {result.get('archive_file', 'N/A')}"}
    except Exception as e:
        logger.error(f"Debug归档失败: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/memory/tools")
async def api_get_memory_tools():
    """获取记忆工具定义 (供前端 Function Calling 使用)"""
    return {"tools": MEMORY_TOOLS}

class ArchiveRequest(BaseModel):
    history: list
    summary: str

@app.post("/archive/trigger")
async def api_trigger_archive(req: ArchiveRequest):
    """手动触发每日归档任务"""
    result = await do_daily_archive(req.history, req.summary)
    return result


# 静态文件服务
if os.path.exists(Config.FRONTEND_PATH):
    app.mount("/static", StaticFiles(directory=Config.FRONTEND_PATH), name="static")

@app.get("/")
async def read_index():
    """入口重定向：访问根路径时直接返回聊天界面"""
    index_file = os.path.join(Config.FRONTEND_PATH, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Frontend index.html not found. Please check 'frontend' folder."}

@app.get("/debug")
async def read_debug():
    """调试面板入口"""
    debug_file = os.path.join(Config.FRONTEND_PATH, "debug.html")
    if os.path.exists(debug_file):
        return FileResponse(debug_file)
    return {"message": "debug.html not found"}

@app.get("/debug/prompt")
async def get_debug_prompt():
    """获取最近的 Prompt 日志"""
    try:
        with open(Config.DEBUG_PROMPT_FILE, "r", encoding="utf-8") as f:
            return {"content": f.read()}
    except FileNotFoundError:
        return {"content": "暂无 Prompt 日志。先进行一次对话后再刷新。"}


# 辅助函数
def write_debug_prompt(messages: list) -> None:
    """写入调试 Prompt 到文件"""
    try:
        debug_info = f"\n{'='*50}\nTIMESTAMP: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}\n"
        for i, m in enumerate(messages):
            role = "SYSTEM" if isinstance(m, SystemMessage) else "USER" if isinstance(m, HumanMessage) else "ASSISTANT"
            debug_info += f"\n[{i}] {role}:\n{m.content}\n"
        debug_info += f"{'='*50}\n"
        with open(Config.DEBUG_PROMPT_FILE, "w", encoding="utf-8") as df:
            df.write(debug_info)
    except Exception as e:
        logger.error(f"Failed to write debug prompt: {e}")

def build_system_prompt(summary: str, memory_files: list) -> str:
    """构建系统提示词"""
    system_content = ""
    
    if summary:
        system_content += f"\n\n【前情提要（动态记忆）】：\n{summary}"
        
    if memory_files:
        system_content += f"\n\n【可用长期记忆文件】：{', '.join(memory_files)}\n\n**重要提醒**：\n1. 在调用 fetch_memory 工具前，请**务必先仔细检查对话历史**中是否已经包含相关的记忆内容\n2. 如果历史中有 [已检索的长期记忆] 标记的内容，说明相关记忆已经获取过，**不要重复调用工具**\n3. 只有当历史中确实没有相关信息时，才调用 fetch_memory 工具\n4. 优先使用历史中已有的记忆内容来回答问题"
    
    # 调试：输出系统提示词
    logger.info(f"[DEBUG] System prompt built: {system_content[:200]}...")
    return system_content

def build_messages(system_content: str, history: list, current_message: str) -> list:
    """构建消息列表"""
    messages = [SystemMessage(content=system_content)]
    for h in history:
        if h["role"] == "user":
            messages.append(HumanMessage(content=h["content"]))
        else:
            messages.append(AIMessage(content=h["content"]))
    messages.append(HumanMessage(content=current_message))
    return messages

def save_session_if_needed(auto_save: bool, history: list, summary: str) -> None:
    """根据需要保存会话"""
    if auto_save:
        os.makedirs("data", exist_ok=True)
        with open(Config.SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump({"history": history, "summary": summary}, f, ensure_ascii=False, indent=2)
        logger.info(f"[Session] Auto-saved to file, history length: {len(history)}")
    else:
        logger.info("[Session] auto_save=False, skipped saving")


@app.post("/chat")
async def chat_with_agent(req: ChatRequest):
    """
    三层记忆架构对话接口 (TMA Stage 1) - 流式版本:
    1. 动态注入 L2 摘要作为“长期背景”
    2. 使用 StreamingResponse 实现打字机效果
    3. 在流结束时回传 metadata (summary & history)
    """
    import sys, time
    from datetime import datetime
    start_time = time.time()
    # 强制在函数入口打桩，不依赖 generator 开始执行
    entry_msg = f"\n[{datetime.now().strftime('%H:%M:%S')}] 🚀 [BACKEND HIT] /chat endpoint reached.\n"
    sys.stderr.write(entry_msg)
    sys.stderr.flush()
    
    logger.info("--- [Stream Chat Session Start] ---")
    
    async def chat_generator():
        banner = f"\n{'='*30}\n🟢 NEW STREAMING REQUEST AT {datetime.now().strftime('%H:%M:%S.%f')[:-3]}\n{'='*30}\n"
        sys.stderr.write(banner)
        sys.stderr.write(f"RAW USER TEXT: {req.message}\n")
        sys.stderr.flush()
        
        # 构建系统提示词和消息
        from src.agents.memory_tools import list_available_memories
        memory_files = await list_available_memories()
        system_content = build_system_prompt(req.summary, memory_files)
        messages = build_messages(system_content, req.history, req.message)
        
        # 日志追踪
        logger.info(f">>> [System Prompt Context]:\n{system_content}")
        logger.info(f">>> [Chat History Window]: {len(req.history)} messages")

        # 写入调试日志
        write_debug_prompt(messages)
        sys.stderr.write(f"\n[{datetime.now().strftime('%H:%M:%S')}] 📝 Raw prompt synced to debug file\n")
        sys.stderr.flush()
        
        full_content = ""
        m3_context = ""  # 存储检索到的长期记忆
        use_thinking_mode = True  # 必须使用thinking mode
        
        # --- 定义工具 ---
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "fetch_memory",
                    "description": "检索长期记忆。当用户询问历史事件、个人偏好、过往决策、职业规划、财务资产等需要查阅记忆库的内容时调用。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string", "description": "记忆文件名，如：职业规划.md, 财务资产.md, 健康管理.md, 情感记录.md"},
                            "keywords": {"type": "string", "description": "可选搜索关键词，用于精确匹配段落"}
                        },
                        "required": ["filename"]
                    }
                }
            }
        ] if memory_files else []
        
        # 调试：输出工具定义
        logger.info(f"[Tools Debug] 可用工具数量: {len(tools)}")
        logger.info(f"[Tools Debug] 记忆文件数量: {len(memory_files) if memory_files else 0}")
        if tools:
            logger.info(f"[Tools Debug] 工具定义: {json.dumps(tools[0], ensure_ascii=False, indent=2)}")
        
        # --- 工具执行器 ---
        async def execute_tool(name: str, args: dict) -> str:
            """执行工具并返回结果"""
            nonlocal m3_context, system_content
            if name == "fetch_memory":
                filename = args.get("filename", "")
                keywords = args.get("keywords")
                sys.stderr.write(f"[{datetime.now().strftime('%H:%M:%S')}] 🔧 Executing fetch_memory({filename})\n")
                sys.stderr.flush()
                result = await fetch_memory(filename, keywords)
                if result["success"]:
                    content = result["content"]
                    m3_context += f"\n\n【来自 {filename} 的长期记忆】：\n{content}"
                    logger.info(f"[M3 Success] 获取到 {len(content)} 字符")
                    return content
                else:
                    return f"未找到文件: {filename}"
            return f"未知工具: {name}"
        
        try:
            # --- Thinking Mode + Tool Calls (V3.2 新特性) ---
            if use_thinking_mode and tools:
                yield "event: status\ndata: 💭 正在思考并查阅记忆...\n\n"
                sys.stderr.write(f"[{datetime.now().strftime('%H:%M:%S')}] 🧠 Using Thinking Mode + Tool Calls\n")
                sys.stderr.flush()
                
                from src.agents.thinking_tool_stream import stream_with_thinking_tools, ChunkType
                
                # 转换 LangChain messages 为 OpenAI 格式
                openai_messages = []
                for m in messages:
                    if isinstance(m, SystemMessage):
                        openai_messages.append({"role": "system", "content": m.content})
                    elif isinstance(m, HumanMessage):
                        openai_messages.append({"role": "user", "content": m.content})
                    elif isinstance(m, AIMessage):
                        openai_messages.append({"role": "assistant", "content": m.content})
                
                thinking_start = time.time()
                try:
                    async for chunk in stream_with_thinking_tools(
                        messages=openai_messages,
                        tools=tools,
                        tool_executor=execute_tool,
                        max_tool_rounds=10  # 增加到10轮，支持读取所有记忆文件
                    ):
                        if chunk.type == ChunkType.TOOL_CALL:
                            # 显示具体的工具参数，让用户知道在查阅哪个文件
                            tool_info = chunk.tool_call or {}
                            tool_name = tool_info.get("name", "unknown")
                            tool_args = tool_info.get("args", {})
                            if tool_name == "fetch_memory":
                                filename = tool_args.get("filename", "")
                                yield f"event: status\ndata: 📂 正在查阅记忆：{filename}\n\n"
                            else:
                                yield f"event: status\ndata: 🔧 {chunk.content}\n\n"
                        elif chunk.type == ChunkType.CONTENT:
                            full_content += chunk.content
                            # 修复换行符问题：将内容中的换行符转换为SSE格式
                            content_lines = chunk.content.split('\n')
                            if len(content_lines) == 1:
                                # 单行内容
                                yield f"event: content\ndata: {chunk.content}\n\n"
                            else:
                                # 多行内容，每行都要加data:前缀
                                sse_content = "event: content\n"
                                for line in content_lines:
                                    sse_content += f"data: {line}\n"
                                sse_content += "\n"
                                yield sse_content
                        elif chunk.type == ChunkType.ERROR:
                            # Thinking Mode 失败，回退到普通模式
                            logger.warning(f"[Thinking Mode] Error: {chunk.content}, falling back...")
                            sys.stderr.write(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Thinking Mode failed, fallback\n")
                            use_thinking_mode = False
                            break
                    else:
                        # 正常完成
                        thinking_time = time.time() - thinking_start
                        sys.stderr.write(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Thinking Mode done ({thinking_time:.2f}s)\n")
                        logger.info(f"[Thinking Mode] 完成，耗时 {thinking_time:.2f}s")
                        
                except Exception as e:
                    logger.error(f"[Thinking Mode] Exception: {e}")
                    sys.stderr.write(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Thinking Mode exception: {e}\n")
                    use_thinking_mode = False
            
            # --- Fallback: 普通流式调用 (不使用 Thinking Mode) ---
            if not use_thinking_mode or not full_content:
                if not full_content:  # 只有在没有生成内容时才回退
                    yield "event: status\ndata: ✨ 正在生成回复...\n\n"
                    sys.stderr.write(f"[{datetime.now().strftime('%H:%M:%S')}] 📝 Fallback to standard streaming\n")
                    
                    # 如果已经获取了记忆内容，注入到 system prompt
                    if m3_context:
                        system_content += m3_context
                        messages[0] = SystemMessage(content=system_content)
                    
                    async for chunk in llm.astream(messages):
                        token = chunk.content
                        full_content += token
                        yield f"event: content\ndata: {token}\n\n"
            
            chat_done_time = time.time()
            logger.info(f"LLM First Response Latency: {chat_done_time - start_time:.2f}s")

            # 2. 对话结束后，处理记忆逻辑 (L2 压缩)
            new_summary = req.summary
            
            # 构建新历史：如果本次获取了记忆，把记忆内容也加入历史
            # 这样后续对话模型就知道已经读取过哪些记忆，避免重复调用工具
            new_history = req.history.copy()
            new_history.append({"role": "user", "content": req.message})
            
            # 如果有记忆内容，作为系统消息注入历史（用户不可见，但模型可见）
            if m3_context:
                new_history.append({
                    "role": "system", 
                    "content": f"[已检索的长期记忆]{m3_context}"
                })
                logger.info(f"[Memory Injected] 已将 {len(m3_context)} 字符的记忆内容注入历史")
            
            # 清理可能混入的 [STATUS] 标记
            clean_content = full_content
            import re
            clean_content = re.sub(r'\[STATUS\][^\n]*\n?', '', clean_content).strip()
            
            new_history.append({"role": "ai", "content": clean_content})
            
            # 注：摘要压缩逻辑已移除
            # 摘要只在凌晨自动任务或手动归档时更新，不在每次对话时触发
            # 参见 daily_archive.py 的 trigger_daily_archive() 函数

            # [V3.0] world_state_prompt 已移除，不再自动提取 pinned_facts/todos

            # 3. 发送元数据标记位
            try:
                end_time = time.time()
                metadata = {
                    "type": "metadata",
                    "summary": new_summary,
                    "history": new_history,

                    "debug": {
                        "raw_prompt": [
                            {"role": "system" if isinstance(m, SystemMessage) else "user" if isinstance(m, HumanMessage) else "assistant", "content": m.content} 
                            for m in messages
                        ],
                        "latency": {
                            "llm_chat": f"{chat_done_time - start_time:.2f}s",
                            "total": f"{end_time - start_time:.2f}s"
                        },
                        "system_prompt": system_content,
                        "history_count": len(req.history)
                    }
                }
                meta_json = json.dumps(metadata, ensure_ascii=False)
                yield f"event: metadata\ndata: {meta_json}\n\n"
                
                # 根据 auto_save 参数决定是否自动保存
                if req.auto_save:
                    # 主要保存到云端
                    from src.storage.sphere_storage import get_sphere_storage
                    storage = get_sphere_storage()
                    await storage.save_current_session(new_history, new_summary)
                    logger.info(f"[Session] Auto-saved to cloud, history length: {len(new_history)}")
                else:
                    logger.info(f"[Session] auto_save=False, skipped saving")
                
                logger.info(f"--- [Stream Chat End] Total Latency: {end_time - start_time:.2f}s ---")
                # 不在这里发送done事件，统一在finally中发送
            except Exception as me:
                logger.error(f"Metadata generation failed: {me}")
                yield f"event: error\ndata: {{\"error\": \"metadata_failed\"}}\n\n"
                # 不在这里发送done事件，统一在finally中发送

        except Exception as e:
            logger.error(f"Streaming failed: {e}", exc_info=True)
            yield f"event: error\ndata: {{\"error\": \"streaming_failed\", \"message\": \"{str(e)}\"}}\n\n"
        finally:
            yield "event: done\ndata: {}\n\n"

    return StreamingResponse(chat_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    # 启动 Uvicorn，优先读取 HF 环境要求的端口
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Sphere Backend Server is launching on port {port}...")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
