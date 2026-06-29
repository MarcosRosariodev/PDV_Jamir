"""
services/printer.py
Serviço de impressão — impressora térmica Bematech via ESC/POS
"""

from datetime import datetime

try:
    from escpos.printer import Usb
    ESCPOS_DISPONIVEL = True
except ImportError:
    ESCPOS_DISPONIVEL = False
    print("[IMPRESSORA] python-escpos não instalado. Modo fallback ativo.")

# Bematech — ajuste VID e PID conforme seu modelo.
# Para descobrir: Gerenciador de Dispositivos → Controladores de Barramento USB
# Modelos comuns:
#   Bematech MP-4200 TH:  VID=0x0dd4  PID=0x0186
#   Bematech MP-100S TH:  VID=0x0dd4  PID=0x0200
PRINTER_VID = 0x0dd4   # TODO: confirmar com seu modelo
PRINTER_PID = 0x0186   # TODO: confirmar com seu modelo

NOME_ESTABELECIMENTO = "DinDin Jamir"
ENDERECO             = "Rua das Flores, 123 — Fortaleza/CE"
TELEFONE             = "(85) 9 9999-9999"
LARGURA              = 32  # colunas (papel 57 mm ≈ 32 chars)


def _conectar():
    if not ESCPOS_DISPONIVEL:
        return None
    try:
        return Usb(PRINTER_VID, PRINTER_PID, timeout=0, in_ep=0x81, out_ep=0x01)
    except Exception as e:
        print(f"[IMPRESSORA] Falha ao conectar: {e}")
        return None


def imprimir_cupom(pedido: dict):
    linhas = _montar_cupom(pedido)
    impressora = _conectar()

    if impressora:
        try:
            impressora.set(align="center", bold=True, width=2, height=2)
            impressora.text(NOME_ESTABELECIMENTO + "\n")
            impressora.set(align="center", bold=False, width=1, height=1)
            impressora.text(ENDERECO + "\n")
            impressora.text(TELEFONE + "\n")
            impressora.text("-" * LARGURA + "\n")
            impressora.set(align="left")
            for linha in linhas:
                impressora.text(linha + "\n")
            impressora.set(align="center")
            impressora.text("\nObrigado pela preferência!\n\n\n")
            impressora.cut()
            print(f"[IMPRESSORA] Pedido #{pedido.get('numero')} impresso.")
        except Exception as e:
            print(f"[IMPRESSORA] Erro ao imprimir: {e}")
        finally:
            try:
                impressora.close()
            except Exception:
                pass
    else:
        _fallback_console(linhas)


def _fallback_console(linhas: list):
    print("\n" + "=" * LARGURA)
    print(NOME_ESTABELECIMENTO.center(LARGURA))
    print(ENDERECO.center(LARGURA))
    print("=" * LARGURA)
    for linha in linhas:
        print(linha)
    print("=" * LARGURA + "\n")


def _montar_cupom(pedido: dict) -> list[str]:
    numero = pedido.get("numero", pedido.get("id", "?"))
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")

    linhas: list[str] = [
        f"PEDIDO #{numero}".center(LARGURA),
        "",
    ]

    for item in pedido.get("itens", []):
        nome = item["produto"][:20]
        linhas.append(f"{item['quantidade']} X {nome}")

    subtotal = sum(i["quantidade"] * i["valor"] for i in pedido.get("itens", []))
    linhas += [
        "",
        f"TOTAL: R$ {subtotal:.2f}",
        "",
        agora,
    ]

    pagto = pedido.get("forma_pagamento", "")
    if pagto:
        linhas.append(f"Pagamento: {pagto.upper()}")

    return linhas
