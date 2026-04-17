@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

title Фотоассистент — Docker

set "COMPOSE_FILE=%~dp0deploy\docker-compose.yml"

where docker >nul 2>&1
if errorlevel 1 (
  echo Не найден Docker в PATH.
  echo Установите Docker Desktop и включите интеграцию с WSL2 при запросе:
  echo   https://docs.docker.com/desktop/setup/install/windows-install/
  pause
  exit /b 1
)

docker compose version >nul 2>&1
if errorlevel 1 (
  echo Не работает команда «docker compose». Обновите Docker Desktop ^(нужен Compose V2^).
  pause
  exit /b 1
)

if not exist "%COMPOSE_FILE%" (
  echo Не найден файл: %COMPOSE_FILE%
  echo Запускайте bat из корня репозитория ^(рядом с папкой deploy^).
  pause
  exit /b 1
)

if not exist "%~dp0deploy\Dockerfile" (
  echo Не найден deploy\Dockerfile
  pause
  exit /b 1
)

if not exist "%~dp0app\__main__.py" (
  echo Не найден app\__main__.py — нужна полная папка проекта.
  pause
  exit /b 1
)

echo.
echo  Фотоассистент в Docker
echo  Папка проекта: %~dp0
echo.
if /i "%~1"=="--no-cache" (
  echo  Режим: полная пересборка образа ^(--no-cache^)
  echo.
  docker compose -f "%COMPOSE_FILE%" build --no-cache
) else (
  echo  Сборка образа ^(инкрементально; для полной: Фотоассистент_Docker.bat --no-cache^)
  echo.
  docker compose -f "%COMPOSE_FILE%" build
)
if errorlevel 1 (
  echo.
  echo Сборка не удалась. Проверьте, что Docker Desktop запущен и есть интернет.
  pause
  exit /b 1
)

echo.
echo  Запуск контейнера ^(GUI через xvfb по умолчанию; см. README^)
echo  Останов: закройте окно приложения или Ctrl+C в этой консоли.
echo.

docker compose -f "%COMPOSE_FILE%" run --rm photo-assistant
if errorlevel 1 (
  echo.
  echo Контейнер завершился с ошибкой.
  pause
  exit /b 1
)

exit /b 0
