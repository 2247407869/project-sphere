# 使用轻量级 Python 镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量，确保 Python 输出直接同步到终端
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 安装系统依赖 (如有需要可在此添加)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 暴露端口 (Hugging Face Spaces 默认 7860)
EXPOSE 7860

# 启动脚本：使用环境变量 PORT (HF 会自动注入)
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-7860}
