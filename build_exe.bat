@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Установка PyInstaller...
python -m pip install pyinstaller --quiet
echo Сборка EXE (займёт несколько минут, размер ~500MB+ из-за PyTorch/Mediapipe)...
python -m PyInstaller --noconfirm packaging\photo_assistant.spec
if exist "dist\FotoAssistant\FotoAssistant.exe" (
  echo.
  echo Готово: dist\FotoAssistant\FotoAssistant.exe
  echo Скопируйте всю папку dist\FotoAssistant на другой ПК.
  echo Рядом с FotoAssistant.exe будут app_settings.json и папка models ^(как при запуске из bat^).
) else (
  echo Ошибка сборки. Запустите вручную: pyinstaller packaging\photo_assistant.spec
)
pause
