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
        system_content = "你是一位博学且严谨的技术助手。你的目标是协助用户构建知识库。"
        if req.summary:
            system_content += f"\n\n【前情提要（记忆）】：\n{req.summary}"
            
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
                """
                # 注意：摘要生成升级为异步 ainvoke 以保证非阻塞
                summary_response = await llm.ainvoke([
                    SystemMessage(content="你是一位记忆管理专家。你只输出极致压缩后的事实总结，不含废话。"),
                    HumanMessage(content=compress_prompt)
                ])
                new_summary = summary_response.content
                new_history = new_history[-4:]
                logger.info(f"New Summary: {new_summary[:50]}...")

            # 3. 发送元数据标记位 (用于前端更新状态)
            metadata = {
                "type": "metadata",
                "summary": new_summary,
                "history": new_history
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
