@echo off
cd /d "%~dp0"

if "%~1"=="" (
  echo Usage:
  echo   deploy_toolkit.bat TARGET_DIR
  echo Example:
  echo   deploy_toolkit.bat "..\MyProject\kb_toolkit"
  exit /b 1
)

powershell -ExecutionPolicy Bypass -File "%~dp0scripts\deploy_toolkit.ps1" -TargetDir "%~1"
