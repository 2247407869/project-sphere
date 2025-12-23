# 主程序入口：负责 Web 应用的启动与 API 路由调度
from fastapi import FastAPI
from src.utils.config import settings
from src.agents.knowledge_agent import knowledge_graph
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

# 初始化配置与日志系统
logger = logging.getLogger(__name__)
app = FastAPI(title=settings.PROJECT_NAME)

# 开启 CORS 跨域支持 (允许移动端 Web UI 访问)
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
async def collect_knowledge(content: str, source: str = "mobile"):
    """
    知识采集核心端点：
    1. 接收移动端发送的原始文本
    2. 封装并触发 LangGraph Agent 状态机
    3. 同步等待 AI 分析结果并返回
    """
    logger.info(f"收到来自 {source} 的采集请求")
    
    # 构造 Agent 初始状态容器
    initial_state = {
        "content": content,
        "metadata": {"source": source},
        "summary": "",
        "status": "received"
    }
    
    # 驱动 LangGraph 工作流进行逻辑处理
    result = knowledge_graph.invoke(initial_state)
    
    return {
        "status": result["status"],
        "summary": result["summary"],
        "metadata": result["metadata"]
    }

if __name__ == "__main__":
    # 启动 Uvicorn 高性能 Web 服务器
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
