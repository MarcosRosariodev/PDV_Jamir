# -*- mode: python ; coding: utf-8 -*-
# Spec de empacotamento do Totem (tela cliente) — PDV Jamir

from PyInstaller.utils.hooks import collect_all

datas_mpl, bins_mpl, hidden_mpl = collect_all("matplotlib")

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=bins_mpl,
    datas=datas_mpl + [
        ("database",  "database"),
        ("api",       "api"),
        ("services",  "services"),
        ("ui",        "ui"),
    ],
    hiddenimports=hidden_mpl + [
        "uvicorn",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.loops.asyncio",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "fastapi",
        "fastapi.middleware.cors",
        "starlette",
        "starlette.middleware",
        "starlette.middleware.cors",
        "anyio",
        "anyio._backends._asyncio",
        "sqlalchemy",
        "sqlalchemy.dialects.sqlite",
        "pydantic",
        "pydantic.deprecated.decorator",
        "h11",
        "httpx",
        "escpos",
        "PIL._tkinter_finder",
    ],
    hookspath=[],
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
    name="PDV_Jamir_Totem",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="PDV_Jamir_Totem",
)
