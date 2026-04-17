@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

REM Один файл: первый запуск создаёт .venv и ставит пакеты; дальше сразу запуск приложения.
set "PYTHONUTF8=1"
set "VENV_PY=%~dp0.venv\Scripts\python.exe"
set "PIP_CACHE_DIR=%~dp0.pip_cache"

title Фотоассистент — установка и запуск

if exist "%VENV_PY%" goto RUN_APP

echo.
echo  === Фотоассистент: первый запуск на этом ПК ===
echo  Создаётся .venv и ставятся пакеты ^(opencv, torch, mediapipe — первый раз долго^).
echo.

call :FIND_BOOTSTRAP_PYTHON
if errorlevel 1 (
  call :TRY_WINGET_OR_HINT
  exit /b 1
)

if not defined BOOTSTRAP_PY (
  call :TRY_WINGET_OR_HINT
  exit /b 1
)

echo [1/3] Создаю виртуальное окружение .venv ...
"%BOOTSTRAP_PY%" -m venv "%~dp0.venv"
if errorlevel 1 (
  echo Ошибка venv. Попробуйте другую папку ^(без кириллицы в пути^) или права администратора.
  pause
  exit /b 1
)
if not exist "%VENV_PY%" (
  echo Ошибка: не создан %VENV_PY%
  pause
  exit /b 1
)

echo [2/3] Обновляю pip ...
"%VENV_PY%" -m pip install -q --upgrade pip
if errorlevel 1 (
  echo Ошибка pip.
  pause
  exit /b 1
)

echo [3/3] Устанавливаю зависимости ^(долго, 3-15+ мин. при медленном интернете^)...
"%VENV_PY%" -m pip install -r "%~dp0requirements\requirements.txt"
if errorlevel 1 (
  echo.
  echo Установка не удалась: проверьте интернет и версию Python ^(нужен 3.10+^).
  echo Если не ставится torch — см. https://pytorch.org/get-started/locally/
  pause
  exit /b 1
)

echo.
echo Готово. Дальше этот файл будет открывать приложение без ожидания.
echo.

:RUN_APP
if not exist "%~dp0app\__main__.py" (
  echo Не найден app\__main__.py. Нужна полная папка проекта.
  pause
  exit /b 1
)

REM Отдельный процесс — окно консоли можно закрыть, останется только окно программы
start "" /D "%~dp0" "%VENV_PY%" -m app
exit /b 0

REM ---------------------------------------------------------------------------
:FIND_BOOTSTRAP_PYTHON
set "BOOTSTRAP_PY="

call :TRY_PY_LAUNCHER py -3.12
if defined BOOTSTRAP_PY exit /b 0
call :TRY_PY_LAUNCHER py -3.11
if defined BOOTSTRAP_PY exit /b 0
call :TRY_PY_LAUNCHER py -3.10
if defined BOOTSTRAP_PY exit /b 0
call :TRY_PY_LAUNCHER py -3
if defined BOOTSTRAP_PY exit /b 0

where python >nul 2>&1
if errorlevel 1 goto :try_local_appdata
python -c "import sys; assert sys.version_info[:2] >= (3, 10)" 2>nul
if errorlevel 1 goto :try_local_appdata
for /f "delims=" %%U in ('python -c "import sys; print(sys.executable)" 2^>nul') do set "BOOTSTRAP_PY=%%U"
if defined BOOTSTRAP_PY exit /b 0

:try_local_appdata
if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
  "%LocalAppData%\Programs\Python\Python312\python.exe" -c "import sys; assert sys.version_info[:2] >= (3, 10)" 2>nul
  if not errorlevel 1 (
    set "BOOTSTRAP_PY=%LocalAppData%\Programs\Python\Python312\python.exe"
    exit /b 0
  )
)
if exist "%LocalAppData%\Programs\Python\Python311\python.exe" (
  "%LocalAppData%\Programs\Python\Python311\python.exe" -c "import sys; assert sys.version_info[:2] >= (3, 10)" 2>nul
  if not errorlevel 1 (
    set "BOOTSTRAP_PY=%LocalAppData%\Programs\Python\Python311\python.exe"
    exit /b 0
  )
)
if exist "%LocalAppData%\Programs\Python\Python310\python.exe" (
  "%LocalAppData%\Programs\Python\Python310\python.exe" -c "import sys; assert sys.version_info[:2] >= (3, 10)" 2>nul
  if not errorlevel 1 (
    set "BOOTSTRAP_PY=%LocalAppData%\Programs\Python\Python310\python.exe"
    exit /b 0
  )
)

exit /b 1

:TRY_PY_LAUNCHER
REM %~1 %~2 = например py и -3.12
set "BOOTSTRAP_PY="
"%~1" %~2 -c "import sys; assert sys.version_info[:2] >= (3, 10)" 2>nul
if errorlevel 1 exit /b 1
for /f "delims=" %%U in ('"%~1" %~2 -c "import sys; print(sys.executable)" 2^>nul') do set "BOOTSTRAP_PY=%%U"
if not defined BOOTSTRAP_PY exit /b 1
exit /b 0

REM ---------------------------------------------------------------------------
:TRY_WINGET_OR_HINT
echo Python 3.10+ не найден.

where winget >nul 2>&1
if errorlevel 1 goto SHOW_HINT

echo.
choice /C YN /M "Установить Python 3.12 через winget"
if errorlevel 2 goto SHOW_HINT

winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
echo.
echo Закройте окно и снова запустите Фотоассистент.bat
pause
exit /b 0

:SHOW_HINT
echo.
echo  1) Установите Python 3.10, 3.11 или 3.12: https://www.python.org/downloads/windows/
echo  2) Включите ^«Add python.exe to PATH^»
echo  3) Запустите этот bat снова из папки проекта
echo.
pause
exit /b 1
