@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Сборка EXE с консолью (видны ошибки при сбое) — packaging\photo_assistant_console.spec
echo Результат: dist\FotoAssistantConsole\  — переносите всю папку.
echo.
python -m pip install pyinstaller --quiet
python -m PyInstaller --noconfirm packaging\photo_assistant_console.spec
if exist "dist\FotoAssistantConsole\FotoAssistantConsole.exe" (
  echo.
  echo Готово: dist\FotoAssistantConsole\FotoAssistantConsole.exe
) else (
  echo Ошибка сборки.
)
pause
