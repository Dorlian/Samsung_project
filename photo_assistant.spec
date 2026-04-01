# -*- mode: python ; coding: utf-8 -*-
# Сборка: build_exe.bat  или  pyinstaller photo_assistant.spec
# Результат: dist/FotoAssistant/ — запускать FotoAssistant.exe из этой папки целиком.

import sys
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Mediapipe: подтянуть ресурсы задач
mp_datas, mp_binaries, mp_hidden = collect_all("mediapipe")

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=mp_binaries,
    datas=mp_datas,
    hiddenimports=mp_hidden
    + [
        "PIL._tkinter_finder",
        "torch",
        "torchvision",
        "cv2",
        "skimage",
        "skimage.filters",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="FotoAssistant",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="FotoAssistant",
)
