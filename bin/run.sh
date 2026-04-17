#!/usr/bin/env bash
# Запуск из bin/: корень репозитория — родитель этой папки.
if [ -z "${BASH_VERSION:-}" ]; then
  exec /usr/bin/env bash "$0" "$@"
fi
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

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
  echo "Устанавливаю пакеты из requirements/requirements.txt (первый раз может занять время)..."
  "$PY" -m pip install --upgrade pip
  "$PY" -m pip install -r requirements/requirements.txt
fi

exec "$PY" -m app
