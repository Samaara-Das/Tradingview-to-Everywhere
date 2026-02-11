# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for TTE Combo Mode GUI
# Build with: pyinstaller tte_gui.spec --onedir

a = Analysis(
    ['tte_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('combo_settings.yaml', '.'),
    ],
    hiddenimports=['yaml'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TTE',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window (GUI app)
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TTE',
)
