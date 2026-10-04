# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for PaintedDesktop (one-folder build, packaged by installer/setup.iss)

a = Analysis(
    ['PaintedDesktop/main.py'],
    pathex=['PaintedDesktop'],
    datas=[('PaintedDesktop/assets', 'assets')],
    hiddenimports=['pystray._win32', 'winrt.windows.foundation'],  # pystray picks its backend at runtime
    excludes=['pytest'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PaintedDesktop',
    console=False,
    icon='PaintedDesktop/assets/icon.ico',
    upx=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    upx=False,
    name='PaintedDesktop',
)
