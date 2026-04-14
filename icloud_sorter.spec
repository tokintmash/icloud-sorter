# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for iCloud Photo Sorter."""

import os
import certifi
import fido2

block_cipher = None

a = Analysis(
    ['desktop_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('frontend/dist', 'frontend/dist'),
        (certifi.where(), 'certifi'),
        (os.path.join(os.path.dirname(fido2.__file__), 'public_suffix_list.dat'), 'fido2'),
    ],
    hiddenimports=[
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'backend',
        'backend.app',
        'backend.config',
        'backend.runtime_paths',
        'backend.lifecycle',
        'backend.dev_server',
        'backend.models',
        'backend.models.db',
        'backend.models.schemas',
        'backend.routers',
        'backend.routers.auth',
        'backend.routers.albums',
        'backend.routers.sort',
        'backend.routers.settings',
        'backend.services',
        'backend.services.icloud_service',
        'backend.services.sorter_service',
        'backend.services.state_service',
        'pyicloud',
        'webview',
        'certifi',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='iCloudPhotoSorter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='iCloudPhotoSorter',
)
