# 主程序入口：负责 Web 应用的启动与 API 路由调度
from fastapi import FastAPI
from src.utils.config import settings
from src.agents.knowledge_agent import knowledge_graph
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

# 初始化配置与日志系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Sphere-Core")
from pydantic import BaseModel

app = FastAPI(title=settings.PROJECT_NAME)

# 定义 API 请求模型
class CollectRequest(BaseModel):
    content: str
    source: str = "mobile"

class ChatRequest(BaseModel):
    message: str
    history: list = []
    summary: str = "" # 新增：当前对话的滚动摘要

# 配置 CORS 跨域支持 (允许移动端 Web 访问)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """健康检查接口：用于验证服务是否在线"""
    return {"status": "healthy", "project": settings.PROJECT_NAME}

@app.post("/collect")
async def collect_knowledge(req: CollectRequest):
    """
    知识采集核心端点：同步等待 AI 分析结果并返回
    """
    logger.info(f"收到来自 {req.source} 的采集请求")
    initial_state = {
        "content": req.content,
        "metadata": {"source": req.source},
        "summary": "",
        "status": "received"
    }
    result = knowledge_graph.invoke(initial_state)
    return {
        "status": result["status"],
        "summary": result["summary"],
        "metadata": result["metadata"]
    }

@app.get("/facts")
async def get_facts():
    """读取云端事实归档 (L3 记忆)"""
    import json
    import os
    facts_file = os.path.join("data", "facts.json")
    if os.path.exists(facts_file):
        try:
            with open(facts_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            return {"error": f"Failed to read facts: {e}"}
    return []

class SessionSyncRequest(BaseModel):
    history: list
    summary: str

@app.get("/session/load")
async def load_session():
    """从云端恢复会话状态"""
    import json
    import os
    session_file = os.path.join("data", "sessions.json")
    if os.path.exists(session_file):
        try:
            with open(session_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"history": [], "summary": ""}

@app.post("/session/sync")
async def sync_session(req: SessionSyncRequest):
    """同步会话状态至云端"""
    import json
    import os
    session_file = os.path.join("data", "sessions.json")
    os.makedirs("data", exist_ok=True)
    try:
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump({"history": req.history, "summary": req.summary}, f, ensure_ascii=False, indent=2)
        return {"status": "synced"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

class TodoItem(BaseModel):
    id: str
    task: str
    completed: bool = False
    created_at: str

@app.get("/todos")
async def get_todos():
    """获取所有待办事项"""
    import json
    import os
    todo_file = os.path.join("data", "todos.json")
    if os.path.exists(todo_file):
        try:
            with open(todo_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

@app.post("/todos/sync")
async def sync_todos(todos: list[TodoItem]):
    """同步待办事项库"""
    import json
    import os
    todo_file = os.path.join("data", "todos.json")
    os.makedirs("data", exist_ok=True)
    try:
        with open(todo_file, "w", encoding="utf-8") as f:
            json.dump([todo.dict() for todo in todos], f, ensure_ascii=False, indent=2)
        return {"status": "synced"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/pinned")
async def get_pinned_facts():
    """获取永不压缩的核心事实 (L2.5)"""
    import json
    import os
    pinned_file = os.path.join("data", "pinned_facts.json")
    if os.path.exists(pinned_file):
        try:
            with open(pinned_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

@app.post("/pinned/update")
async def update_pinned_facts(facts: list[str]):
    """更新核心事实库"""
    import json
    import os
    pinned_file = os.path.join("data", "pinned_facts.json")
    os.makedirs("data", exist_ok=True)
    try:
        with open(pinned_file, "w", encoding="utf-8") as f:
            json.dump(facts, f, ensure_ascii=False, indent=2)
        return {"status": "updated"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, FileResponse
import json
import asyncio
import os

# 挂载前端静态资源
# 假设 frontend 目录与 main.py 在同级
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
async def read_index():
    """入口重定向：访问根路径时直接返回聊天界面"""
    index_file = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Frontend index.html not found. Please check 'frontend' folder."}

@app.post("/chat")
async def chat_with_agent(req: ChatRequest):
    """
    三层记忆架构对话接口 (TMA Stage 1) - 流式版本:
    1. 动态注入 L2 摘要作为“长期背景”
    2. 使用 StreamingResponse 实现打字机效果
    3. 在流结束时回传 metadata (summary & history)
    """
    from src.agents.knowledge_agent import llm
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
    
    logger.info("--- [Stream Chat Session Start] ---")
    
    async def chat_generator():
        # --- L2.5 Pinned Context 注入 ---
        pinned_facts = []
        pinned_file = os.path.join("data", "pinned_facts.json")
        if os.path.exists(pinned_file):
            try:
                with open(pinned_file, "r", encoding="utf-8") as f:
                    pinned_facts = json.load(f)
            except: pass
            
        system_content = "你是一位博学且严谨的技术助手。你的目标是协助用户构建知识库。"
        if pinned_facts:
            system_content += "\n\n【核心锁定事实（永不压缩）】:\n" + "\n".join([f"- {f}" for f in pinned_facts])
            
        if req.summary:
            system_content += f"\n\n【前情提要（动态记忆）】：\n{req.summary}"
            
        messages = [SystemMessage(content=system_content)]
        for h in req.history:
            if h["role"] == "user":
                messages.append(HumanMessage(content=h["content"]))
            else:
                messages.append(AIMessage(content=h["content"]))
        messages.append(HumanMessage(content=req.message))

        full_content = ""
        try:
            # 1. 开启 LLM 异步流
            async for chunk in llm.astream(messages):
                token = chunk.content
                full_content += token
                yield token

            # 2. 对话结束后，处理记忆逻辑 (L2 压缩)
            new_summary = req.summary
            new_history = req.history + [{"role": "user", "content": req.message}, {"role": "ai", "content": full_content}]
            
            if len(new_history) >= 12: # 稍微提高阈值以减少压缩频率
                logger.info("!! [TMA Triggered] Detection of long context, initiating L2 compression...")
                compress_prompt = f"""
                基于以下【前情提要】和【新增对话】，生成一个内容丰满且结构化的新摘要（300字以内）。
                要求：
                1. 采用无序列表形式。
                2. 必须保留关键的技术参数、核心架构决策、用户显式提及的重要偏好。
                3. 保留当前未完成的待办任务。
                
                原提要：{req.summary}
                新增内容：{new_history[-1]["content"]} 
                """
                # 注意：摘要生成升级为异步 ainvoke 以保证非阻塞
                summary_response = await llm.ainvoke([
                    SystemMessage(content="你是一位记忆管理专家。你只输出极致压缩后的事实总结，不含废话。"),
                    HumanMessage(content=compress_prompt)
                ])
                new_summary = summary_response.content
                new_history = new_history[-4:]
                logger.info(f"New Summary: {new_summary[:50]}...")

            # --- 全局状态感知逻辑 (ToDo + L2.5 Pinned Context) ---
            pinned_file = os.path.join("data", "pinned_facts.json")
            todo_file = os.path.join("data", "todos.json")
            
            # 读取当前状态
            current_pinned = []
            if os.path.exists(pinned_file):
                try:
                    with open(pinned_file, "r", encoding="utf-8") as f: current_pinned = json.load(f)
                except: pass
            
            current_todos = []
            if os.path.exists(todo_file):
                try:
                    with open(todo_file, "r", encoding="utf-8") as f: current_todos = json.load(f)
                except: pass

            world_state_prompt = f"""
            分析对话，提取并更新用户的【核心锁定事实】及【待办事项】。
            
            【锁定事实（永不压缩）】：涉及日程规划、职业战略路线、核心原则等长期不变的信息。
            当前事实：{json.dumps(current_pinned, ensure_ascii=False)}
            
            【待办事项】：具体的任务动作。
            当前待办：{json.dumps(current_todos, ensure_ascii=False)}
            
            对话内容：User: {req.message} -> AI: {full_content}
            
            请返回更新后的 JSON 对象：
            {{
                "pinned_facts": ["事实1", "事实2", ...],
                "todos": [{{ "id": "uuid", "task": "具体事项", "completed": false, "created_at": "iso_date" }}]
            }}
            务必保持数据的完整性，如果没有变化请返回原内容。
            """
            try:
                state_res = await llm.ainvoke([
                    SystemMessage(content="你是一位知识架构师与任务管理专家。只输出纯 JSON，不含解释。"),
                    HumanMessage(content=world_state_prompt)
                ])
                raw_state = state_res.content.strip()
                if "```json" in raw_state: raw_state = raw_state.split("```json")[1].split("```")[0].strip()
                elif "```" in raw_state: raw_state = raw_state.split("```")[1].split("```")[0].strip()
                
                state_data = json.loads(raw_state)
                if "pinned_facts" in state_data:
                    current_pinned = state_data["pinned_facts"]
                    with open(pinned_file, "w", encoding="utf-8") as f:
                        json.dump(current_pinned, f, ensure_ascii=False, indent=2)
                if "todos" in state_data:
                    current_todos = state_data["todos"]
                    with open(todo_file, "w", encoding="utf-8") as f:
                        json.dump(current_todos, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"World State Sync Error: {e}")

            # 3. 发送元数据标记位 (用于前端更新状态)
            metadata = {
                "type": "metadata",
                "summary": new_summary,
                "history": new_history,
                "pinned_facts": current_pinned,
                "todos": current_todos
            }
            yield f"\n[METADATA]{json.dumps(metadata)}"
            logger.info("--- [Stream Chat Session End] ---")

        except Exception as e:
            logger.error(f"Streaming failed: {e}", exc_info=True)
            yield f"Error: 对话中断，请重试。"

    return StreamingResponse(chat_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    # 启动 Uvicorn，优先读取 HF 环境要求的端口
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Sphere Backend Server is launching on port {port}...")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
