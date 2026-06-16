"""
services/printer.py
Serviço de impressão — impressora térmica USB via ESC/POS
"""

from datetime import datetime

# Tenta importar escpos; se não tiver, usa modo de fallback (apenas log)
try:
    from escpos.printer import Usb
    ESCPOS_DISPONIVEL = True
except ImportError:
    ESCPOS_DISPONIVEL = False
    print("[IMPRESSORA] python-escpos não instalado. Modo fallback ativo.")

# ── Configuração da impressora ───────────────────────────────────────────────
# Altere VID e PID conforme sua impressora.
# Para descobrir: no Windows, vá em Gerenciador de Dispositivos → USB.
# Exemplos comuns:
#   Epson TM-T20:  VID=0x04b8  PID=0x0202
#   Bematech:      VID=0x0dd4  PID=0x0186
#   Elgin i9:      VID=0x0fe6  PID=0x811e
PRINTER_VID = 0x04b8
PRINTER_PID = 0x0202

NOME_ESTABELECIMENTO = "Sorvetes Jamir"
ENDERECO             = "Rua das Flores, 123 — Fortaleza/CE"
TELEFONE             = "(85) 9 9999-9999"


def _conectar():
    """Retorna instância da impressora ou None se falhar."""
    if not ESCPOS_DISPONIVEL:
        return None
    try:
        p = Usb(PRINTER_VID, PRINTER_PID, timeout=0, in_ep=0x81, out_ep=0x01)
        return p
    except Exception as e:
        print(f"[IMPRESSORA] Falha ao conectar: {e}")
        return None


def imprimir_cupom(pedido: dict):
    """
    Imprime cupom do pedido.

    pedido = {
        "id": 1,
        "itens": [{"produto": "Chocolate", "qtd": 2, "preco": 8.00}],
        "total": 16.00,
        "forma_pagto": "dinheiro",
        "observacao": ""
    }
    """
    linhas = _montar_cupom(pedido)

    impressora = _conectar()
    if impressora:
        try:
            impressora.set(align="center", bold=True, width=2, height=2)
            impressora.text(NOME_ESTABELECIMENTO + "\n")
            impressora.set(align="center", bold=False, width=1, height=1)
            impressora.text(ENDERECO + "\n")
            impressora.text(TELEFONE + "\n")
            impressora.text("-" * 32 + "\n")

            impressora.set(align="left")
            for linha in linhas:
                impressora.text(linha + "\n")

            impressora.text("-" * 32 + "\n")
            impressora.set(align="center")
            impressora.text("Obrigado pela preferência!\n\n\n")
            impressora.cut()
            print(f"[IMPRESSORA] Cupom do pedido #{pedido['id']} impresso.")
        except Exception as e:
            print(f"[IMPRESSORA] Erro ao imprimir: {e}")
        finally:
            try:
                impressora.close()
            except Exception:
                pass
    else:
        # Fallback: imprime no console
        print("\n" + "=" * 40)
        print(f"  {NOME_ESTABELECIMENTO}".center(40))
        print("=" * 40)
        for linha in linhas:
            print(linha)
        print("=" * 40 + "\n")


def _montar_cupom(pedido: dict) -> list:
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    linhas = [
        f"Pedido #: {pedido['id']}",
        f"Data   : {agora}",
        "-" * 32,
        f"{'Produto':<18} {'Qtd':>3} {'Valor':>8}",
        "-" * 32,
    ]
    for item in pedido.get("itens", []):
        subtotal = item["qtd"] * item["preco"]
        linhas.append(f"{item['produto'][:18]:<18} {item['qtd']:>3} R${subtotal:>6.2f}")

    linhas += [
        "-" * 32,
        f"{'TOTAL':>22}  R${pedido['total']:>6.2f}",
        f"Pagamento: {pedido['forma_pagto'].upper()}",
    ]
    if pedido.get("observacao"):
        linhas += ["-" * 32, f"Obs: {pedido['observacao']}"]

    return linhas
