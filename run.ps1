# Запуск из PowerShell (Windows). Аналог run.sh / run.bat — без sh, chmod и CRLF-проблем.
# Запуск:  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#          .\run.ps1
# Или:    powershell -ExecutionPolicy Bypass -File .\run.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$venvPy = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$py = $null

if (Test-Path -LiteralPath $venvPy) {
    $py = $venvPy
}
elseif (Get-Command py -ErrorAction SilentlyContinue) {
    foreach ($ver in @("-3.12", "-3.11", "-3.10", "-3")) {
        try {
            $out = & py $ver -c "import sys; print(sys.executable)" 2>$null
            if ($LASTEXITCODE -eq 0 -and $out) {
                $py = ($out | Select-Object -First 1).ToString().Trim()
                break
            }
        }
        catch { }
    }
}
if (-not $py -and (Get-Command python -ErrorAction SilentlyContinue)) {
    $py = (Get-Command python).Source
}

if (-not $py) {
    Write-Host "Python не найден. Установите 3.10–3.12 с python.org или запустите Фотоассистент.bat" -ForegroundColor Red
    exit 1
}

Write-Host "Проверка зависимостей..."
& $py -c "import cv2; from PIL import Image; import torch; import mediapipe" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Устанавливаю пакеты из requirements.txt (первый раз может занять время)..."
    & $py -m pip install --upgrade pip
    & $py -m pip install -r (Join-Path $PSScriptRoot "requirements.txt")
}

& $py (Join-Path $PSScriptRoot "main.py")
