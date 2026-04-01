@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "PY="
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"
if "%PY%"=="" if exist ".venv312\Scripts\python.exe" set "PY=.venv312\Scripts\python.exe"
if "%PY%"=="" set "PY=python"

echo Проверка зависимостей...
"%PY%" -c "import cv2; from PIL import Image; import torch; import mediapipe" 2>nul
if errorlevel 1 (
  echo Не хватает пакетов. Устанавливаю из requirements.txt ^(первый раз долго^)...
  "%PY%" -m pip install -r requirements.txt
  if errorlevel 1 (
    echo Ошибка установки.
    pause
    exit /b 1
  )
)

"%PY%" main.py
if errorlevel 1 pause
