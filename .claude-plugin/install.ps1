# Bole Plugin — Windows 安装后初始化脚本
$PluginDir = Split-Path -Parent $PSScriptRoot

Write-Host "🔧 Installing Bole plugin..." -ForegroundColor Cyan

# 检查 Python3
$py = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $py = "python"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $py = "python3"
} else {
    Write-Host "⚠️  Python3 not found, analyze-task script will not work" -ForegroundColor Yellow
}

# 验证脚本
if ($py) {
    & $py "$PluginDir\scripts\analyze-task.py" --help 2>$null
}

Write-Host "✅ Bole plugin installed successfully" -ForegroundColor Green
Write-Host "   Usage: describe your task in Claude Code, e.g."
Write-Host "   > 开发一个用户管理系统，需求文档在 /path/to/req.md"
