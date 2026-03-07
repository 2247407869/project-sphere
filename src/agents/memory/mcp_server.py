import os
import asyncio
import json
import urllib.parse
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from mcp.server import Server
from mcp.types import Tool, TextContent, EmbeddedResource
from mcp.server.sse import SseServerTransport
from graphiti_core import Graphiti
from graphiti_core.driver.falkordb_driver import FalkorDriver
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.llm_client.openai_generic_client import OpenAIGenericClient
from dotenv import load_dotenv

load_dotenv()

# --- 强制修复 DeepSeek 角色兼容性补丁 (Monkey Patch) ---
import openai
from openai.resources.chat.completions import AsyncCompletions

_original_create = AsyncCompletions.create

async def _patched_create(self, *args, **kwargs):
    if "messages" in kwargs:
        msgs = list(kwargs["messages"])
        modified = False
        for i, msg in enumerate(msgs):
            if isinstance(msg, dict):
                if msg.get("role") == "developer":
                    msg["role"] = "system"
                    modified = True
            elif hasattr(msg, "role") and getattr(msg, "role") == "developer":
                if hasattr(msg, "model_copy"):
                    msgs[i] = msg.model_copy(update={"role": "system"})
                else:
                    try:
                        setattr(msg, "role", "system")
                    except:
                        # 如果无法修改且无法克隆，则暴力替换为 dict
                        if hasattr(msg, "content"):
                            msgs[i] = {"role": "system", "content": msg.content}
                modified = True
        if modified:
            kwargs["messages"] = msgs
    return await _original_create(self, *args, **kwargs)

AsyncCompletions.create = _patched_create
# --------------------------------------------------

# --- 初始化 Graphiti 逻辑 ---
DB_URL = os.getenv("GRAPHITI_DB_URL", "falkordb://localhost:6379")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

parsed_url = urllib.parse.urlparse(DB_URL)
db_host = parsed_url.hostname or "localhost"
db_port = parsed_url.port or 6379

graph_driver = FalkorDriver(host=db_host, port=db_port)
llm_config = LLMConfig(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
    model="deepseek-chat"
)
llm_client = OpenAIGenericClient(config=llm_config)
graphiti = Graphiti(graph_driver=graph_driver, llm_client=llm_client)

# --- 初始化 MCP Server 逻辑 ---
server = Server("Cognition Sphere Memory")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(
            name="add_episode",
            description="向记忆图谱添加一个情节（Episode）。当对话中出现重要事实、决定或用户偏好时调用。",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "情节内容"},
                    "source": {"type": "string", "description": "来源，默认为 chat"}
                },
                "required": ["content"]
            }
        ),
        Tool(
            name="search_memory",
            description="搜索长期记忆。支持模糊语义搜索和图检索。",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "limit": {"type": "integer", "description": "返回结果上限", "default": 5}
                },
                "required": ["query"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[TextContent | EmbeddedResource]:
    if name == "add_episode":
        content = arguments.get("content")
        source = arguments.get("source", "chat")
        now = datetime.utcnow().isoformat()
        try:
            episode_id = await graphiti.add_episode(content=content, valid_at=now, metadata={"source": source})
            return [TextContent(type="text", text=f"情节已添加，ID: {episode_id}")]
        except Exception as e:
            return [TextContent(type="text", text=f"添加失败: {str(e)}")]
            
    elif name == "search_memory":
        query = arguments.get("query")
        limit = arguments.get("limit", 5)
        try:
            results = await graphiti.search(query, limit=limit)
            if not results:
                return [TextContent(type="text", text="未找到相关记忆。")]
            formatted = "\n".join([f"- {res.content} (相关度: {res.score:.2f})" for res in results])
            return [TextContent(type="text", text=formatted)]
        except Exception as e:
            return [TextContent(type="text", text=f"搜索失败: {str(e)}")]
    
    raise ValueError(f"Unknown tool: {name}")

# --- FastAPI 包装层 ---
app = FastAPI()

# 启用 CORS 支持，允许 LobeChat 从前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

sse = SseServerTransport("/messages")

@app.get("/sse")
async def handle_sse(request: Request):
    async with sse.connect_sse(request.scope, request.receive, request._send) as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

@app.post("/messages")
@app.post("/sse") # 兼容某些客户端直接向 SSE 路径进行 POST 的行为
async def handle_messages(request: Request):
    await sse.handle_post_message(request.scope, request.receive, request._send)

# 增加 LobeChat 要求的 Manifest
@app.get("/")
@app.get("/manifest.json")
@app.post("/manifest.json")
async def get_manifest(request: Request):
    # 动态获取当前 host 以确保 sse 路径正确
    base_url = str(request.base_url).rstrip("/")
    return {
        "api": [],
        "identifier": "cognition-sphere-mcp",
        "meta": {
            "title": "Cognition Sphere Memory",
            "description": "2026 记忆图谱 MCP 插件。提供长期记忆的情节存储与语义搜索功能。",
            "avatar": "🧠",
            "author": "Antigravity"
        },
        "type": "default",
        "mcp": {
            "sse": f"{base_url}/sse"
        },
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
