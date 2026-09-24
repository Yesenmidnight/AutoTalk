@echo off
cd /d "%~dp0"
title AutoTalk

set "PY_CMD="

:: 优先检测兼容版本 3.12, 3.11, 3.10 (避开不支持 OCR 的 3.13+)
py -3.12 --version >nul 2>&1 && set "PY_CMD=py -3.12"
if not "%PY_CMD%"=="" goto RUN

py -3.11 --version >nul 2>&1 && set "PY_CMD=py -3.11"
if not "%PY_CMD%"=="" goto RUN

py -3.10 --version >nul 2>&1 && set "PY_CMD=py -3.10"
if not "%PY_CMD%"=="" goto RUN

:: 兜底检测默认 py -3 或 python
py -3 --version >nul 2>&1 && set "PY_CMD=py -3"
if not "%PY_CMD%"=="" goto RUN

python --version >nul 2>&1 && set "PY_CMD=python"
if not "%PY_CMD%"=="" goto RUN

echo [ERROR] Python not found!
echo Please install 64-bit Python 3.12 from:
echo https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe
echo Make sure to check Add python.exe to PATH during installation.
pause
exit /b 1

:RUN
%PY_CMD% main.py
if errorlevel 1 pause
