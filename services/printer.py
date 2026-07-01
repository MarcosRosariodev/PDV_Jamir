"""
services/printer.py
Serviço de impressão — Bematech MP-4200 TH via COM5 (USB-Serial / ESC/POS)
"""

from datetime import datetime

try:
    from escpos.printer import Serial
    ESCPOS_DISPONIVEL = True
except ImportError:
    ESCPOS_DISPONIVEL = False
    print("[IMPRESSORA] python-escpos não instalado. Modo fallback ativo.")

# Bematech MP-4200 TH — conectada em COM5 (USB-Serial)
PRINTER_PORT     = "COM5"
PRINTER_BAUDRATE = 9600   # padrão Bematech; tente 115200 se não imprimir
LARGURA          = 40     # colunas (papel 80 mm ≈ 40-48 chars; 57 mm ≈ 32)

NOME_ESTABELECIMENTO = "DinDin Jamir"
ENDERECO             = "Rua das Flores, 123 — Fortaleza/CE"
TELEFONE             = "(85) 9 9999-9999"


def _conectar():
    if not ESCPOS_DISPONIVEL:
        return None
    try:
        p = Serial(
            devfile=PRINTER_PORT,
            baudrate=PRINTER_BAUDRATE,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=1,
            dsrdtr=False,
        )
        return p
    except Exception as e:
        print(f"[IMPRESSORA] Falha ao conectar em {PRINTER_PORT}: {e}")
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
            print(f"[IMPRESSORA] Pedido #{pedido.get('numero')} impresso em {PRINTER_PORT}.")
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
    agora  = datetime.now().strftime("%d/%m/%Y %H:%M")

    linhas: list[str] = [
        f"PEDIDO #{numero}".center(LARGURA),
        "",
    ]

    for item in pedido.get("itens", []):
        nome = item["produto"][:22]
        qtd  = item["quantidade"]
        vlr  = item["valor"]
        sub  = f"R$ {qtd * vlr:.2f}"
        linha = f"{qtd}x {nome}"
        # alinha o subtotal à direita
        espacos = LARGURA - len(linha) - len(sub)
        linhas.append(linha + " " * max(1, espacos) + sub)

    subtotal = sum(i["quantidade"] * i["valor"] for i in pedido.get("itens", []))
    linhas += [
        "-" * LARGURA,
        f"TOTAL: R$ {subtotal:.2f}".rjust(LARGURA),
        "",
        agora.center(LARGURA),
    ]

    pagto = pedido.get("forma_pagamento", "")
    if pagto:
        linhas.append(f"Pagamento: {pagto.upper()}".center(LARGURA))

    return linhas
