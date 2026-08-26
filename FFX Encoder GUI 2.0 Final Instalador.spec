# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:\\scripts\\Projeto APP\\FFX Encoder 3.0.0 Python\\InstallerBuildGUI\\installer_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('D:\\scripts\\Projeto APP\\FFX Encoder 3.0.0 Python\\InstallerBuildGUI\\FFX Encoder GUI Payload.zip', '.')],
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
    a.binaries,
    a.datas,
    [],
    name='FFX Encoder GUI 2.0 Final Instalador',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['D:\\scripts\\Projeto APP\\FFX Encoder 3.0.0 Python\\icone.ico'],
)
