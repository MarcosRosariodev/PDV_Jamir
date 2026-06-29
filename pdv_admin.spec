# -*- mode: python ; coding: utf-8 -*-
# Spec de empacotamento do Painel Administrativo — PDV Jamir

from PyInstaller.utils.hooks import collect_all, collect_data_files

datas_ctk,  bins_ctk,  hidden_ctk  = collect_all("customtkinter")
datas_mpl,  bins_mpl,  hidden_mpl  = collect_all("matplotlib")
datas_dark, bins_dark, hidden_dark = collect_all("darkdetect")

a = Analysis(
    ["main_admin.py"],
    pathex=["."],
    binaries=bins_ctk + bins_mpl + bins_dark,
    datas=datas_ctk + datas_mpl + datas_dark + [
        ("database",  "database"),
        ("api",       "api"),
        ("services",  "services"),
        ("admin",     "admin"),
        ("ui",        "ui"),
    ],
    hiddenimports=hidden_ctk + hidden_mpl + hidden_dark + [
        # uvicorn
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
        # fastapi / starlette
        "fastapi",
        "fastapi.middleware.cors",
        "starlette",
        "starlette.middleware",
        "starlette.middleware.cors",
        "anyio",
        "anyio._backends._asyncio",
        # banco
        "sqlalchemy",
        "sqlalchemy.dialects.sqlite",
        # serialização
        "pydantic",
        "pydantic.deprecated.decorator",
        "h11",
        "httpx",
        # impressora
        "escpos",
        # PIL
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
    name="PDV_Jamir_Admin",
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
    name="PDV_Jamir_Admin",
)
