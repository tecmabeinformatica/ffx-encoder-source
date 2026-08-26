# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

ROOT = Path(SPECPATH)


a = Analysis(
    [str(ROOT / 'gui_main.py')],
    pathex=[],
    binaries=[],
    datas=[
        (str(ROOT / 'ffx_encoder'), 'ffx_encoder'),
        (str(ROOT / 'bin' / 'ffmpeg.exe'), 'bin'),
        (str(ROOT / 'bin' / 'ffprobe.exe'), 'bin'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FFX Encoder GUI',
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
    icon=[str(ROOT / 'icone.ico')],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FFX Encoder GUI',
)
