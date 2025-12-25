# Project Sphere 本地一键启动调试脚本 (Hot-Reload Mode)

$env:PORT = "8000"
$env:DEEPSEEK_API_KEY = "sk-..." # 用户需本地填入或依赖环境变量

Write-Host "🚀 Project Sphere 本地环境正在启动..." -ForegroundColor Cyan
Write-Host "📡 调试地址: http://localhost:8000" -ForegroundColor Green
Write-Host "📝 实时日志流已接入 Terminal..." -ForegroundColor Yellow
Write-Host "------------------------------------------------"

# 检查依赖
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python 未找到，请确保已安装并加入 PATH"
    exit
}

# 启动服务端
if (Test-Path ".\venv\Scripts\python.exe") {
    Write-Host "✅ 检测到本地虚拟环境，正在启动..." -ForegroundColor Gray
    .\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
}
else {
    python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
}
