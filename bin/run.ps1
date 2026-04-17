# Запуск из bin/ — корень репозитория на уровень выше.
# .\bin\run.ps1  или  Set-Location ...; .\run.ps1 из bin

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $Root

$venvPy = Join-Path $Root '.venv\Scripts\python.exe'
$py = $null

if (Test-Path -LiteralPath $venvPy) {
    $py = $venvPy
}
elseif (Get-Command py -ErrorAction SilentlyContinue) {
    foreach ($ver in @('-3.12', '-3.11', '-3.10', '-3')) {
        try {
            $out = & py $ver -c 'import sys; print(sys.executable)' 2>$null
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
    Write-Host 'Python ne nayden. Nuzhen 3.10-3.12. Zapustite Fotoassistent.bat' -ForegroundColor Red
    exit 1
}

Write-Host 'Proverka moduley (cv2, PIL, torch, mediapipe)...'
& $py -c 'import cv2; from PIL import Image; import torch; import mediapipe' 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Ustanavlivayu requirements (dolgo pri pervom zapuske)...'
    & $py -m pip install --upgrade pip
    $req = Join-Path $Root 'requirements\requirements.txt'
    & $py -m pip install -r $req
}

& $py -m app
