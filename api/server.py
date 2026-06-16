"""
api/server.py
Instância FastAPI com middleware CORS e rotas registradas
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.routes import router
from services.printer import imprimir_cupom
import httpx

app = FastAPI(title="PDV Jamir API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
async def startup():
    print("[API] Servidor PDV Jamir rodando em http://127.0.0.1:8000")


# Hook de impressão automática ao criar pedido
_original_criar = router.routes  # registrado via override abaixo

from fastapi import Request
from fastapi.responses import JSONResponse

@app.middleware("http")
async def imprimir_apos_pedido(request: Request, call_next):
    response = await call_next(request)

    if request.method == "POST" and request.url.path == "/pedidos" and response.status_code == 200:
        # Lê corpo da resposta para obter id do pedido e dispara impressão
        import json
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        try:
            data = json.loads(body)
            pedido_id = data.get("id")
            if pedido_id:
                # Busca detalhes do pedido para impressão
                try:
                    r = httpx.get(f"http://127.0.0.1:8000/pedidos?status=pendente", timeout=3)
                    pedidos = r.json()
                    pedido = next((p for p in pedidos if p["id"] == pedido_id), None)
                    if pedido:
                        import threading
                        threading.Thread(
                            target=imprimir_cupom, args=(pedido,), daemon=True
                        ).start()
                except Exception as e:
                    print(f"[IMPRESSORA] Erro ao buscar pedido para impressão: {e}")
        except Exception:
            pass

        from starlette.responses import Response
        return Response(content=body, status_code=response.status_code,
                        headers=dict(response.headers),
                        media_type=response.media_type)

    return response
