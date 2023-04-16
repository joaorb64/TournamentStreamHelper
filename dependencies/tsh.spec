# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)
exe = EXE(
    pyz,
    a.scripts,
    name='TSH',
    exclude_binaries=True,
    icon='assets/icons/icon.ico',
    noconsole=True,
    hiddenimports=['PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets'],
    windowed=True
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=None,
    upx=True,
    upx_exclude=[],
    name='TSH'
)
