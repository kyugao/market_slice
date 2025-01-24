# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[('src/utils', 'utils'), ('src/ui', 'ui'), ('src/widgets', 'widgets'), ('src/constants.py', '.')],
    hiddenimports=['numpy', 'pandas', 'matplotlib', 'matplotlib.backends.backend_qt5', 'matplotlib.backends.backend_qt5agg'],
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
    name='main',
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
    icon=['assets/icon.ico'],
)
app = BUNDLE(
    exe,
    name='main.app',
    icon='assets/icon.ico',
    bundle_identifier=None,
)
