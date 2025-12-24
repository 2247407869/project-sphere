# Project Sphere 一键发布脚本
# 用法: .\deploy.ps1 "提交说明"

param (
    [string]$Message = "Routine update: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
)

Write-Host "🚀 开始推送至云端..." -ForegroundColor Cyan

# 1. 检查 git 状态
if (!(Test-Path .git)) {
    Write-Host "❌ 错误: 未检测到 Git 仓库。请先执行 git init。" -ForegroundColor Red
    exit
}

# 2. 提交更改
git add .
git commit -m "$Message"

# 动态获取当前分支名 (兼容 master/main)
$Branch = git branch --show-current
if (!$Branch) { $Branch = "master" }

# 3. 推送至双远端 (GitHub + Hugging Face)
Write-Host "📡 同步至 GitHub ($Branch)..." -ForegroundColor Gray
git push origin "$Branch"

Write-Host "📡 同步至 Hugging Face Spaces ($Branch)..." -ForegroundColor Cyan
# 假设远端名为 hf，若未配置则跳过并提示
$remotes = git remote
if ($remotes -contains "hf") {
    git push hf "$($Branch):main" --force
    Write-Host "✅ 全链路同步完成！" -ForegroundColor Green
}
else {
    Write-Host "⚠️ 警告: 未检测到名为 'hf' 的远端。代码已同步至 GitHub，但未同步至 Space。" -ForegroundColor Yellow
    Write-Host "请执行: git remote add hf https://huggingface.co/spaces/你的用户名/你的项目名" -ForegroundColor Gray
}
