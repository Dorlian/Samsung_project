# -*- mode: python ; coding: utf-8 -*-
# Сборка: build_exe_console.bat — EXE с консолью.

from pathlib import Path

from PyInstaller.utils.hooks import collect_all

block_cipher = None

_SPEC = Path(SPECPATH).resolve()
SPEC_DIR = _SPEC.parent
ROOT = SPEC_DIR.parent

mp_datas, mp_binaries, mp_hidden = collect_all("mediapipe")

extra_datas = []
face_task = ROOT / "models" / "face_landmarker.task"
eye_weights = ROOT / "models" / "eye_state_resnet18.pth"
if face_task.exists():
    extra_datas.append((str(face_task), "models"))
if eye_weights.exists():
    extra_datas.append((str(eye_weights), "models"))

a = Analysis(
    [str(ROOT / "app" / "__main__.py")],
    pathex=[str(ROOT)],
    binaries=mp_binaries,
    datas=mp_datas + extra_datas,
    hiddenimports=mp_hidden
    + [
        "app",
        "PIL._tkinter_finder",
        "torch",
        "torchvision",
        "cv2",
        "skimage",
        "skimage.filters",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(SPEC_DIR / "photo_assistant_rth.py")],
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
    name="FotoAssistantConsole",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
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
    upx=False,
    upx_exclude=[],
    name="FotoAssistantConsole",
)
