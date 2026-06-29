"""
main_admin.py
Entry point do Painel Administrativo — inicia backend se necessário e abre o admin.
"""

import sys
import os
import time
import threading
import httpx

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)


def _start_server():
    import uvicorn
    uvicorn.run("api.server:app", host="127.0.0.1", port=8000, log_level="error")


def _aguardar_servidor(timeout: int = 15) -> bool:
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            httpx.get("http://127.0.0.1:8000/produtos", timeout=1)
            return True
        except Exception:
            time.sleep(0.4)
    return False


def main():
    from database.db import criar_tabelas, popular_dados_iniciais
    criar_tabelas()
    popular_dados_iniciais()

    try:
        httpx.get("http://127.0.0.1:8000/produtos", timeout=1)
        print("[ADMIN] Backend já em execução.")
    except Exception:
        print("[ADMIN] Iniciando backend...")
        threading.Thread(target=_start_server, daemon=True).start()
        if not _aguardar_servidor():
            print("[ADMIN] Erro: servidor não respondeu.")
            sys.exit(1)

    print("[ADMIN] Abrindo painel administrativo...")
    from admin.admin_app import AdminApp
    AdminApp().mainloop()


if __name__ == "__main__":
    main()
