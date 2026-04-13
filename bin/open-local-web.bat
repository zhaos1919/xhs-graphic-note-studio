@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "ROOT_DIR=%SCRIPT_DIR%\.."
set "APP_SCRIPT=%ROOT_DIR%\xhs-render\web_ui.py"

set "PY_CMD="

where py >nul 2>nul
if not errorlevel 1 set "PY_CMD=py -3"

if not defined PY_CMD (
  where python >nul 2>nul
  if not errorlevel 1 set "PY_CMD=python"
)

if not defined PY_CMD (
  echo.
  echo 未找到 Python。
  echo 请先安装 Python 3，并在安装时勾选 "Add python.exe to PATH"。
  echo.
  pause
  exit /b 1
)

start "" %PY_CMD% "%APP_SCRIPT%" %*
exit /b 0
