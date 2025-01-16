# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# 获取项目源码路径
src_path = os.path.abspath('src')
if src_path not in sys.path:
    sys.path.append(src_path)

# 添加排除列表
excludes = [
    'scipy', 'tk', 'tkinter', 'PyQt5.QtBluetooth',
    'PyQt5.QtMultimedia', 'PyQt5.Qt3D', 'PyQt5.QtQuick', 'PyQt5.QtQuickWidgets',
    'PyQt5.QtSensors', 'PyQt5.QtSerialPort', 'PyQt5.QtSql', 'PyQt5.QtTest',
    'PyQt5.QtXml', 'PyQt5.QtXmlPatterns'
]

a = Analysis(
    ['src/main.py'],
    pathex=[src_path],  # 添加源码路径
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('src/utils', 'utils/'),
        ('src/widgets', 'widgets/'),
        ('src/constants.py', '.'),
    ],
    hiddenimports=[
        'PyQt5',
        'pandas',
        'loguru',
        'utils',
        'matplotlib',
        'matplotlib.backends.backend_qt5agg',
        'matplotlib.backends.backend_qt5',
        'utils.trading_day_util',
        'utils.five_min_kline_service',
        'widgets.contract_trading_volume_chart_widget',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook.py'],
    excludes=excludes,  # 添加排除
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
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
    a.zipfiles,
    a.datas,
    [],
    name='MarketAnalyzer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,  # 启用strip
    upx=True,    # 启用UPX压缩
    upx_exclude=[
        'vcruntime140.dll'
    ],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src/assets/icon.ico'
) 