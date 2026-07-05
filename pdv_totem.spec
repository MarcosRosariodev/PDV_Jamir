# -*- mode: python ; coding: utf-8 -*-
# Totem (cliente) + Servidor API — PDV DinDin Show

from PyInstaller.utils.hooks import collect_all

datas_ctk,  bins_ctk,  hidden_ctk  = collect_all("customtkinter")
datas_dark, bins_dark, hidden_dark = collect_all("darkdetect")

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=bins_ctk + bins_dark,
    datas=datas_ctk + datas_dark + [
        ("database",  "database"),
        ("api",       "api"),
        ("services",  "services"),
        ("admin",     "admin"),
        ("ui",        "ui"),
        ("assets",    "assets"),
    ],
    hiddenimports=hidden_ctk + hidden_dark + [
        # uvicorn
        "uvicorn", "uvicorn.logging", "uvicorn.loops", "uvicorn.loops.auto",
        "uvicorn.loops.asyncio", "uvicorn.protocols", "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto", "uvicorn.protocols.http.h11_impl",
        "uvicorn.protocols.websockets", "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan", "uvicorn.lifespan.on",
        # fastapi / starlette
        "fastapi", "fastapi.middleware.cors",
        "starlette", "starlette.middleware", "starlette.middleware.cors",
        "anyio", "anyio._backends._asyncio",
        # banco
        "sqlalchemy", "sqlalchemy.dialects.sqlite",
        # serialização
        "pydantic", "pydantic.deprecated.decorator",
        "h11", "httpx",
        # impressora
        "win32print", "win32api", "pywintypes",
        # PIL / opencv
        "PIL._tkinter_finder", "cv2",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="PDV_Totem",
    debug=False,
    strip=False,
    upx=True,
    console=False,
    icon="assets/Logojamir.png",
)

coll = COLLECT(
    exe, a.binaries, a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="PDV_Totem",
)
