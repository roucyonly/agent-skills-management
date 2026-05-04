@echo off
REM Skills Management System 安装脚本 (Windows)

echo Skills Management System - 安装
echo ================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到 Python
    echo 请先安装 Python 3.7+
    pause
    exit /b 1
)

echo ✓ Python 已安装

REM 检查 pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到 pip
    pause
    exit /b 1
)

echo ✓ pip 已安装

REM 安装依赖
echo.
echo 安装依赖包...
pip install pyyaml click rich watchdog

REM 获取脚本目录
set SCRIPT_DIR=%~dp0
set CLI_PATH=%SCRIPT_DIR%..\cli\main.py

REM 完成
echo.
echo ================================
echo ✓ 安装完成！
echo.
echo 使用方法:
echo   python %CLI_PATH% list
echo   python %CLI_PATH% stats
echo   python %CLI_PATH% discovery
echo.
echo 或者创建批处理文件:
echo   @echo off
echo   python %CLI_PATH% %%*
echo.
pause
