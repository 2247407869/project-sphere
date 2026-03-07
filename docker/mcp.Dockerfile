FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖（如果 Graphiti 需要）
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件（后续会创建）
COPY requirements_mcp.txt .
RUN pip install --no-cache-dir -r requirements_mcp.txt

# 复制源代码
COPY . .

# 暴露端口（如果是通过 SSE 模式集成）
EXPOSE 8000

# 启动 MCP 服务器 (具体启动命令待定)
CMD ["python", "src/agents/memory/mcp_server.py"]
