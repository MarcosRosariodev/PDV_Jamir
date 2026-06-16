"""
main.py
Ponto de entrada do sistema PDV Jamir
Inicia o backend FastAPI em segundo plano e abre a interface do cliente.
"""

import subprocess
import sys
import time
import threading
import os
import httpx

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def iniciar_backend():
    """Inicializa o banco e sobe o servidor FastAPI em processo separado."""
    # Cria/popula o banco antes de tudo
    from database.db import criar_tabelas, popular_dados_iniciais
    criar_tabelas()
    popular_dados_iniciais()

    # Sobe o servidor
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.server:app",
         "--host", "127.0.0.1", "--port", "8000", "--log-level", "error"],
        cwd=BASE_DIR
    )
    return proc


def aguardar_servidor(timeout=15):
    """Espera o servidor responder antes de abrir a UI."""
    print("[PDV] Aguardando servidor...", end="", flush=True)
    inicio = time.time()
    while time.time() - inicio < timeout:
        try:
            httpx.get("http://127.0.0.1:8000/produtos", timeout=1)
            print(" OK")
            return True
        except Exception:
            print(".", end="", flush=True)
            time.sleep(0.5)
    print(" TIMEOUT")
    return False


def main():
    print("[PDV] Iniciando sistema Sorvetes Jamir...")
    proc_backend = iniciar_backend()

    if not aguardar_servidor():
        print("[PDV] Erro: backend não respondeu a tempo.")
        proc_backend.terminate()
        sys.exit(1)

    print("[PDV] Abrindo interface do cliente...")
    from ui.client_app import AppCliente
    app = AppCliente()

    try:
        app.mainloop()
    finally:
        print("[PDV] Encerrando backend...")
        proc_backend.terminate()


if __name__ == "__main__":
    main()
