#!/bin/bash
# Skills Management System 安装脚本

echo "Skills Management System - 安装"
echo "================================"
echo ""

# 检查 Python
if ! command -v python &> /dev/null; then
    echo "❌ 未找到 Python"
    echo "请先安装 Python 3.7+"
    exit 1
fi

echo "✓ Python 已安装"

# 检查 pip
if ! command -v pip &> /dev/null; then
    echo "❌ 未找到 pip"
    exit 1
fi

echo "✓ pip 已安装"

# 安装依赖
echo ""
echo "安装依赖包..."
pip install pyyaml click rich watchdog

# 创建 CLI 链接
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI_PATH="$SCRIPT_DIR/../cli/main.py"

# 添加到 PATH（可选）
echo ""
echo "================================"
echo "✓ 安装完成！"
echo ""
echo "使用方法:"
echo "  python $CLI_PATH list"
echo "  python $CLI_PATH stats"
echo "  python $CLI_PATH discovery"
echo ""
echo "或者创建别名:"
echo "  alias skills='python $CLI_PATH'"
echo ""
