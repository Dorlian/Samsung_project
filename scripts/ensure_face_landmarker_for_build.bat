@echo off
setlocal EnableExtensions
REM Вызывать из корня репозитория: call scripts\ensure_face_landmarker_for_build.bat
cd /d "%~dp0.."

set "OUT=models\face_landmarker.task"
set "MIN_BYTES=10000"

if exist "%OUT%" for %%A in ("%OUT%") do if %%~zA GTR %MIN_BYTES% (
  exit /b 0
)

if exist "%OUT%" del /f /q "%OUT%" 2>nul

echo.
echo  Подготовка EXE: нужен %OUT% ^(MediaPipe Face Landmarker, ~3.5 МБ^).
echo  Без него в сборке нет blendshapes — закрытые глаза не определяются ^(пока не включён ResNet в настройках^).
echo.

if not exist "models\" mkdir models

set "URL=https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"

powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri '%URL%' -OutFile '%CD%\%OUT%' -UseBasicParsing" 2>nul
if exist "%OUT%" for %%A in ("%OUT%") do if %%~zA GTR %MIN_BYTES% goto OK

where curl >nul 2>&1
if errorlevel 1 goto FAIL
curl -fsSL -o "%OUT%" "%URL%"
if exist "%OUT%" for %%A in ("%OUT%") do if %%~zA GTR %MIN_BYTES% goto OK

:FAIL
echo  Ошибка: не удалось скачать face_landmarker.task ^(нужен интернет^).
exit /b 1

:OK
echo  Получен %OUT%
exit /b 0
