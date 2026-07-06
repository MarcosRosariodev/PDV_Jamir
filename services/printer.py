"""
services/printer.py
Impressão via spooler do Windows (win32print) com dados RAW ESC/POS.
Funciona com qualquer impressora instalada pelo driver oficial da Bematech.
"""

from datetime import datetime
import os

# Nome da impressora exatamente como aparece em "Dispositivos e Impressoras".
# Pode ser sobrescrito pela variável de ambiente PDV_PRINTER_NAME.
PRINTER_NAME = os.environ.get("PDV_PRINTER_NAME", "MP-4200 TH")

LARGURA = 40   # colunas em tamanho normal (papel 80 mm)

NOME_ESTABELECIMENTO = "DinDin Show"
ENDERECO             = "Rua Dinamarca, 190 - Parangaba"
TELEFONE             = "(85) 996826-960"
VENDAS               = "Vendas: Varejo e atacado"

# ── Comandos ESC/POS ──────────────────────────────────────────────────────────

ESC = b'\x1b'
GS  = b'\x1d'

_INIT         = ESC + b'\x40'           # reinicializa impressora
_CODEPAGE_860 = ESC + b'\x74\x06'       # PC860 — Portugues (suporte a caracteres acentuados)
_ALIGN_LEFT   = ESC + b'\x61\x00'
_ALIGN_CENTER = ESC + b'\x61\x01'
_BOLD_ON      = ESC + b'\x45\x01'
_BOLD_OFF     = ESC + b'\x45\x00'
_SIZE_DOUBLE  = GS  + b'\x21\x11'      # largura + altura duplas
_SIZE_NORMAL  = GS  + b'\x21\x00'
_CUT          = GS  + b'\x56\x41\x05'  # corte parcial com avanco de 5 linhas
_LF           = b'\x0a'


def _t(texto: str) -> bytes:
    """Converte string para bytes CP860 + line feed."""
    return texto.encode("cp860", errors="replace") + _LF


# ── API publica ───────────────────────────────────────────────────────────────

def imprimir_cupom(pedido: dict):
    """Monta e envia o cupom para a impressora."""
    raw = _montar_raw(pedido)
    ok  = _enviar_raw(raw)
    if ok:
        print(f"[IMPRESSORA] Pedido #{pedido.get('numero')} impresso em '{PRINTER_NAME}'.")
    else:
        _fallback_console(_montar_linhas(pedido))


def listar_impressoras() -> list[str]:
    """Retorna os nomes das impressoras instaladas no Windows."""
    try:
        import win32print
        flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        return [p[2] for p in win32print.EnumPrinters(flags)]
    except Exception as e:
        print(f"[IMPRESSORA] Nao foi possivel listar impressoras: {e}")
        return []


# ── Internos ──────────────────────────────────────────────────────────────────

def _enviar_raw(dados: bytes) -> bool:
    """Envia bytes RAW para o spooler do Windows."""
    try:
        import win32print
        h = win32print.OpenPrinter(PRINTER_NAME)
        try:
            win32print.StartDocPrinter(h, 1, ("Cupom PDV", None, "RAW"))
            try:
                win32print.StartPagePrinter(h)
                win32print.WritePrinter(h, dados)
                win32print.EndPagePrinter(h)
            finally:
                win32print.EndDocPrinter(h)
        finally:
            win32print.ClosePrinter(h)
        return True
    except Exception as e:
        print(f"[IMPRESSORA] Erro ao imprimir: {e}")
        return False


def _montar_raw(pedido: dict) -> bytes:
    """Monta o buffer ESC/POS completo do cupom."""
    linhas = _montar_linhas(pedido)
    buf = bytearray()

    # Inicializacao
    buf += _INIT + _CODEPAGE_860

    # Cabecalho centralizado em tamanho duplo
    buf += _ALIGN_CENTER + _SIZE_DOUBLE + _BOLD_ON
    buf += _t(NOME_ESTABELECIMENTO)
    buf += _SIZE_NORMAL + _BOLD_OFF
    buf += _t(ENDERECO)
    buf += _t(TELEFONE)
    buf += _t(VENDAS)
    buf += _t("-" * LARGURA)

    # Nome do cliente (se informado), centralizado e em negrito
    nome_cliente = (pedido.get("nome_cliente") or "").strip()
    if nome_cliente:
        buf += _ALIGN_CENTER + _BOLD_ON
        buf += _t(f"Cliente: {nome_cliente}")
        buf += _BOLD_OFF

    # Itens alinhados a esquerda
    buf += _ALIGN_LEFT
    for linha in linhas:
        buf += _t(linha)

    # Rodape
    buf += _ALIGN_CENTER + _LF
    buf += _t("Obrigado pela preferencia!")
    buf += _CUT

    return bytes(buf)


def _montar_linhas(pedido: dict) -> list[str]:
    """Retorna as linhas de texto do cupom (sem formatacao ESC/POS)."""
    numero       = pedido.get("numero", pedido.get("id", "?"))
    nome_cliente = (pedido.get("nome_cliente") or "").strip()
    agora        = datetime.now().strftime("%d/%m/%Y %H:%M")

    linhas: list[str] = [
        f"PEDIDO #{numero}".center(LARGURA),
    ]
    if nome_cliente:
        linhas.append(f"Cliente: {nome_cliente}".center(LARGURA))
    linhas.append("")

    for item in pedido.get("itens", []):
        nome  = item["produto"][:22]
        qtd   = item["quantidade"]
        vlr   = item["valor"]
        sub   = f"R$ {qtd * vlr:.2f}"
        linha = f"{qtd}x {nome}"
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


def _fallback_console(linhas: list):
    print("\n" + "=" * LARGURA)
    print(NOME_ESTABELECIMENTO.center(LARGURA))
    print(ENDERECO.center(LARGURA))
    print("=" * LARGURA)
    for linha in linhas:
        print(linha)
    print("=" * LARGURA + "\n")
