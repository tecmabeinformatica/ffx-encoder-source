# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:\\scripts\\Projeto APP\\FFX Encoder 3.0.0 Python\\main.py'],
    pathex=[],
    binaries=[('C:\\FFmpeg\\bin\\ffmpeg.exe', 'bin'), ('C:\\FFmpeg\\bin\\ffprobe.exe', 'bin')],
    datas=[],
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
    name='FFX Encoder 3.0',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['D:\\scripts\\imagens do projeto\\icone.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FFX Encoder 3.0',
)
