#!/usr/bin/env bash
# Bole Plugin — 安装后初始化脚本

PLUGIN_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "🔧 Installing Bole plugin..."

# 确保 scripts 可执行
chmod +x "$PLUGIN_DIR/scripts/analyze-task.py" 2>/dev/null

# 检查 Python3
if command -v python3 &>/dev/null; then
    PY=python3
elif command -v python &>/dev/null; then
    PY=python
else
    echo "⚠️  Python3 not found, analyze-task script will not work"
    PY=""
fi

# 验证脚本
if [ -n "$PY" ]; then
    "$PY" "$PLUGIN_DIR/scripts/analyze-task.py" --help 2>/dev/null || true
fi

echo "✅ Bole plugin installed successfully"
echo "   Usage: describe your task in Claude Code, e.g."
echo "   > 开发一个用户管理系统，需求文档在 /path/to/req.md"
