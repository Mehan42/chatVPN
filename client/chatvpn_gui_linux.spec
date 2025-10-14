# -*- mode: python ; coding: utf-8 -*-
# Абсолютный путь: ~/chatvpn/client/chatvpn_gui_linux.spec
#
# 📝 Для Linux:
# - pystray принудительно использует Xlib (_xorg).
# - Исключены gi.repository, Qt, чтобы не тащить GTK/Qt.
# - Бинарь "chatvpn_client" (без консоли).

block_cipher = None

a = Analysis(
    ['chatvpn_gui.py'],
    pathex=['.'],
    binaries=[],
    datas=[('chatvpn_backend.py', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['gi', 'gi.repository', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6'],
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
    name='chatvpn_client',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='chatvpn_client'
)
