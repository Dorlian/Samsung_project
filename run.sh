#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

PY=""
if [[ -x ".venv/bin/python" ]]; then
  PY=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PY="python3"
else
  PY="python"
fi

echo "Проверка зависимостей..."
if ! "$PY" -c "import cv2; from PIL import Image; import torch; import mediapipe" 2>/dev/null; then
  echo "Устанавливаю пакеты из requirements.txt (первый раз может занять время)..."
  "$PY" -m pip install --upgrade pip
  "$PY" -m pip install -r requirements.txt
fi

exec "$PY" main.py
