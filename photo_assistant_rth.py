# PyInstaller runtime hook: выполняется до main.py.
# Рабочая папка = каталог exe (как при запуске через .bat из корня проекта):
# app_settings.json, models/, относительные пути ведут себя предсказуемо.
import os
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    try:
        os.chdir(Path(sys.executable).resolve().parent)
    except OSError:
        pass
