"""
api/server.py
Instância FastAPI com CORS, rotas e arquivos estáticos de imagens
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import pathlib
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.routes import router

IMAGES_DIR = pathlib.Path(__file__).parent.parent / "images"
IMAGES_DIR.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[API] Servidor PDV Jamir rodando em http://127.0.0.1:8000")
    yield


app = FastAPI(title="PDV Jamir API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.mount("/imagens", StaticFiles(directory=str(IMAGES_DIR)), name="imagens")
