"""
main.py
Entry point do Totem — inicia backend FastAPI em thread e abre a tela do cliente.
"""

import sys
import os
import time
import threading
import logging
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Log em arquivo — facilita diagnóstico em máquinas cliente
_LOG_DIR = os.path.join(os.environ.get("PROGRAMDATA", r"C:\ProgramData"), "PDV_DinDin_Show")
os.makedirs(_LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(_LOG_DIR, "pdv_totem.log"),
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
    encoding="utf-8",
)
logging.info("=== PDV Totem iniciando ===")


def _start_server():
    try:
        import uvicorn
        uvicorn.run("api.server:app", host="127.0.0.1", port=8000, log_level="error")
    except Exception:
        logging.critical("Falha ao iniciar servidor:\n" + traceback.format_exc())


def _aguardar_servidor(timeout: int = 20) -> bool:
    import httpx
    logging.info("Aguardando servidor API...")
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            httpx.get("http://127.0.0.1:8000/produtos", timeout=1)
            logging.info("Servidor OK")
            return True
        except Exception:
            time.sleep(0.4)
    logging.error("Servidor não respondeu em %ds", timeout)
    return False


def _mostrar_erro(titulo: str, mensagem: str):
    try:
        import tkinter as tk
        from tkinter import messagebox
        r = tk.Tk()
        r.withdraw()
        messagebox.showerror(titulo, mensagem)
        r.destroy()
    except Exception:
        pass


def main():
    try:
        logging.info("Criando tabelas...")
        from database.db import criar_tabelas, popular_dados_iniciais
        criar_tabelas()
        popular_dados_iniciais()
        logging.info("Banco OK")
    except Exception:
        msg = traceback.format_exc()
        logging.critical("Erro no banco:\n" + msg)
        _mostrar_erro("PDV — Erro de Banco", f"Não foi possível abrir o banco de dados.\n\n{msg}\n\nLog: {_LOG_DIR}\\pdv_totem.log")
        sys.exit(1)

    try:
        import httpx
        httpx.get("http://127.0.0.1:8000/produtos", timeout=1)
        logging.info("Backend já em execução.")
    except Exception:
        logging.info("Iniciando backend...")
        threading.Thread(target=_start_server, daemon=True).start()
        if not _aguardar_servidor():
            msg = "O servidor interno não respondeu.\n\nVerifique se a porta 8000 está livre e tente novamente."
            logging.error(msg)
            _mostrar_erro("PDV — Erro de Servidor", msg + f"\n\nLog: {_LOG_DIR}\\pdv_totem.log")
            sys.exit(1)

    try:
        logging.info("Abrindo totem...")
        from ui.client_app import AppCliente
        AppCliente().mainloop()
        logging.info("Totem encerrado normalmente.")
    except Exception:
        msg = traceback.format_exc()
        logging.critical("Erro na interface:\n" + msg)
        _mostrar_erro("PDV — Erro de Interface", f"Erro ao abrir a tela.\n\n{msg}\n\nLog: {_LOG_DIR}\\pdv_totem.log")
        sys.exit(1)


if __name__ == "__main__":
    main()
