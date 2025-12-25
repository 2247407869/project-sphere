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
$venvPath = Join-Path $PSScriptRoot "venv\Scripts\python.exe"

if (Test-Path $venvPath) {
    Write-Host "✅ 定位到虚拟环境: $venvPath" -ForegroundColor Gray
    & $venvPath -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
}
else {
    Write-Warning "未找到虚拟环境，将尝试使用系统 Python..."
    python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
}
