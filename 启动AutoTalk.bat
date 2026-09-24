@echo off
chcp 65001 >nul
cd /d "%~dp0"
title AutoTalk 对话助手

:: 检查 Python 运行命令 (优先 py -3, 其次 python)
set PYTHON_CMD=
py -3 --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=py -3
) else (
    python --version >nul 2>&1
    if not errorlevel 1 (
        set PYTHON_CMD=python
    )
)

if "%PYTHON_CMD%"=="" (
    echo.
    echo ==========================================================
    echo [错误] 未检测到 Python 环境！
    echo 请先安装 Python (推荐 3.10 ~ 3.12 64位版本):
    echo https://www.python.org/downloads/
    echo 安装时请务必勾选 "Add python.exe to PATH" !
    echo ==========================================================
    echo.
    pause
    exit /b 1
)

:: 检查依赖是否已就绪
%PYTHON_CMD% -c "import rapidocr_onnxruntime, mss, keyboard, PIL, requests, numpy" >nul 2>&1
if errorlevel 1 (
    echo.
    echo ==========================================================
    echo [提示] 检测到尚未安装必要依赖，正在为您自动安装...
    echo (采用清华镜像源加速，请保持网络畅通)
    echo ==========================================================
    echo.
    %PYTHON_CMD% -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (
        echo.
        echo [重试] 清华源下载受阻，切换为阿里云镜像源重试...
        %PYTHON_CMD% -m pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
    )
    
    :: 再次验证
    %PYTHON_CMD% -c "import rapidocr_onnxruntime, mss, keyboard, PIL, requests, numpy" >nul 2>&1
    if errorlevel 1 (
        echo.
        echo ==========================================================
        echo [安装失败] 依赖安装未完全成功，常见原因排查：
        echo 1. Python 必须是 64 位版本 (32 位不支持 onnxruntime OCR 库)
        echo 2. Python 版本建议为 3.10 ~ 3.12 (Python 3.13 暂无预编译 wheel)
        echo 3. 缺少微软 VC++ 运行库：请下载安装 Visual C++ 2015-2022 x64
        echo 详细排查步骤请参考 README.md
        echo ==========================================================
        echo.
        pause
        exit /b 1
    )
    echo.
    echo [成功] 依赖安装完成！正在启动 AutoTalk...
    echo.
)

:: 启动程序
%PYTHON_CMD% main.py
if errorlevel 1 (
    echo.
    echo ==========================================================
    echo [提示] 程序已退出。如遇崩溃请查看上方报错信息。
    echo ==========================================================
    pause
)
