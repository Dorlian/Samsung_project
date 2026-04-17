@echo off
REM Запуск с видимой консолью: если приложение падает, здесь останется текст ошибки.
chcp 65001 >nul
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PY=%~dp0.venv\Scripts\python.exe"

if not exist "%PY%" (
  echo Не найден %PY%
  echo Сначала один раз запустите Фотоассистент.bat — он создаст .venv и установит пакеты.
  pause
  exit /b 1
)
if not exist "%~dp0app\__main__.py" (
  echo Не найден app\__main__.py. Запускайте bat из корня папки проекта.
  pause
  exit /b 1
)

echo Запуск: "%PY%" -m app
echo Окно консоли не закрывайте до выхода из программы.
echo.
"%PY%" -m app
echo.
echo Код выхода: %ERRORLEVEL%
pause
