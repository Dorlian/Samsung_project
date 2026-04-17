#!/usr/bin/env bash
set -euo pipefail
cd /app

if [[ "${PHOTOASSISTANT_HEADLESS:-1}" == "1" ]]; then
  exec xvfb-run -a python -m app "$@"
fi
if [[ -z "${DISPLAY:-}" ]]; then
  echo "WARNING: DISPLAY пуст, PHOTOASSISTANT_HEADLESS=0 — запуск через xvfb."
  exec xvfb-run -a python -m app "$@"
fi
exec python -m app "$@"
