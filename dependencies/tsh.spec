# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['../main.py'],
    pathex=[],
    binaries=[],
    hiddenimports=[
        'loguru',
        'engineio.async_drivers.threading'
    ],
    datas=[
        ('../assets/contributors.txt', 'assets'),
        ('../assets/versions.json', 'assets'),
        ('../src/i18n/tournament_term/*.json', 'src/i18n/tournament_term'),
#       ('../src/i18n/round_names/*.json', 'src/i18n/round_names'),
        ('../src/i18n/*.json', 'src/i18n'),
        ('../src/i18n/*.qm', 'src/i18n'),
        ('../src/layout/*', 'src/layout'),
#       ('../stage_strike_app/build/*', 'stage_strike_app/build'),
        ('../src/TournamentDataProvider/*.txt', 'src/TournamentDataProvider')
    ],
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
    a.binaries,
    a.datas,
    [],
    name='TSH',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['../assets/icons/icon.ico'],
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
