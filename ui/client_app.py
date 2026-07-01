"""
ui/client_app.py
Interface touchscreen do cliente — tela de quiosque (totem) "DinDin Show"
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import httpx
import threading
import os
import pathlib
from io import BytesIO
from PIL import Image, ImageTk

API_BASE = "http://127.0.0.1:8000"
ASSETS_DIR = pathlib.Path(__file__).parent.parent / "assets"
LOGO_PATH = ASSETS_DIR / "Logojamir.png"

# ── Paleta ───────────────────────────────────────────────────────────────────
COR_HEADER       = "#0F2A52"   # navy escuro do header
COR_HEADER_HOVER = "#163566"
COR_AMARELO      = "#FFC93C"   # acento amarelo
COR_FUNDO        = "#EEF1F5"   # fundo claro acinzentado
COR_CARD         = "#FFFFFF"
COR_TEXTO        = "#1A1A1A"
COR_TEXTO_LEVE   = "#6B7280"
COR_LARANJA      = "#FF7A1A"   # preço / CTA "Sabor" ativo
COR_VERDE        = "#22A559"
COR_VERDE_HOVER  = "#1B8C4A"
COR_PILL_INATIVA = "#1B3A66"
COR_ESGOTADO_BG  = "#E2E5EA"
COR_ESGOTADO_FX  = "#9CA3AF"
COR_FAIXA_ESG    = "#E25C73"
COR_PGTO_INATIVO = "#EEF1F5"
COR_BORDA_CARD   = "#ECEDF0"

SWATCH_PALETA = [
    "#E0395B", "#7B3FA0", "#E8D7A0", "#2E86DE", "#16A085",
    "#F39C12", "#D35400", "#8E44AD", "#27AE60", "#C0392B",
]


def _cor_sabor(nome: str) -> str:
    return SWATCH_PALETA[hash(nome) % len(SWATCH_PALETA)]


def _fmt_brl(valor: float) -> str:
    return f"R$ {valor:.2f}".replace(".", ",")


class AppCliente(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light")

        self.title("DinDin Show")
        self.configure(fg_color=COR_FUNDO)
        self._aplicar_icone_janela()

        # inicia em modo janela (com barra de título) para poder ser
        # arrastada livremente — inclusive entre monitores. Posição/tamanho
        # iniciais opcionais via PDV_TOTEM_X / PDV_TOTEM_Y / PDV_TOTEM_W / PDV_TOTEM_H.
        mon_x = os.environ.get("PDV_TOTEM_X")
        mon_y = os.environ.get("PDV_TOTEM_Y")
        largura = os.environ.get("PDV_TOTEM_W", "760")
        altura  = os.environ.get("PDV_TOTEM_H", "1000")
        geo = f"{largura}x{altura}"
        if mon_x is not None or mon_y is not None:
            geo += f"+{int(mon_x or 0)}+{int(mon_y or 0)}"
        self.geometry(geo)
        self.resizable(True, True)

        self._fullscreen = False
        self.bind("<Escape>", lambda e: self._sair_fullscreen())
        self.bind("<F11>", lambda e: self._toggle_fullscreen())

        self.carrinho: dict = {}   # {produto_id: {"nome", "preco", "qtd"}}
        self.produtos: list = []
        self._card_refs: dict = {}       # {produto_id: {widgets do card}}
        self._card_positions: dict = {}  # {produto_id: (row, col)}
        self.current_step = 1      # 1=Sabor  2=Quantidade  3=Pagamento

        self._fontes()
        self._build_header()
        self._build_body()
        self._build_botao_fullscreen()
        self._carregar_produtos()

    # ── Janela / tela cheia ──────────────────────────────────────────────────

    def _get_monitor_rect(self) -> tuple[int, int, int, int]:
        """Retorna (x, y, w, h) em pixels do monitor onde a janela está."""
        try:
            import ctypes

            class RECT(ctypes.Structure):
                _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                             ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

            class MONITORINFO(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.c_ulong),
                             ("rcMonitor", RECT),
                             ("rcWork", RECT),
                             ("dwFlags", ctypes.c_ulong)]

            user32 = ctypes.windll.user32
            hwnd = self.winfo_id()
            MONITOR_DEFAULTTONEAREST = 2
            hmon = user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)
            mi = MONITORINFO()
            mi.cbSize = ctypes.sizeof(MONITORINFO)
            user32.GetMonitorInfoW(hmon, ctypes.byref(mi))
            r = mi.rcMonitor
            return r.left, r.top, r.right - r.left, r.bottom - r.top
        except Exception:
            return 0, 0, self.winfo_screenwidth(), self.winfo_screenheight()

    def _build_botao_fullscreen(self):
        self.btn_fullscreen = ctk.CTkButton(
            self, text="⛶  Tela cheia", width=120, height=30, corner_radius=8,
            fg_color="#FFFFFF", text_color=COR_HEADER, hover_color="#E5E7EB",
            font=self.f_small, command=self._toggle_fullscreen)
        self.btn_fullscreen.place(relx=1.0, x=-12, y=12, anchor="ne")

    def _toggle_fullscreen(self):
        self._fullscreen = not self._fullscreen
        if self._fullscreen:
            self._geo_antes = self.geometry()
            x, y, w, h = self._get_monitor_rect()
            self.overrideredirect(True)
            self.geometry(f"{w}x{h}+{x}+{y}")
            self.btn_fullscreen.place_forget()
        else:
            self.overrideredirect(False)
            self.geometry(self._geo_antes)
            self.btn_fullscreen.place(relx=1.0, x=-12, y=12, anchor="ne")

    def _sair_fullscreen(self):
        if self._fullscreen:
            self._fullscreen = False
            self.overrideredirect(False)
            self.geometry(self._geo_antes)
            self.btn_fullscreen.place(relx=1.0, x=-12, y=12, anchor="ne")

    def _aplicar_icone_janela(self):
        if not LOGO_PATH.exists():
            return
        try:
            icone = Image.open(LOGO_PATH).resize((64, 64), Image.LANCZOS)
            self._icon_img = ImageTk.PhotoImage(icone)  # mantém referência viva
            self.iconphoto(True, self._icon_img)
        except Exception:
            pass

    def _fontes(self):
        self.f_titulo  = ctk.CTkFont(family="Segoe UI", size=24, weight="bold")
        self.f_sub     = ctk.CTkFont(family="Segoe UI", size=12)
        self.f_pill    = ctk.CTkFont(family="Segoe UI", size=12, weight="bold")
        self.f_letra   = ctk.CTkFont(family="Segoe UI", size=26, weight="bold")
        self.f_nome    = ctk.CTkFont(family="Segoe UI", size=14, weight="bold")
        self.f_preco   = ctk.CTkFont(family="Segoe UI", size=13)
        self.f_small   = ctk.CTkFont(family="Segoe UI", size=11)
        self.f_painel  = ctk.CTkFont(family="Segoe UI", size=18, weight="bold")
        self.f_item    = ctk.CTkFont(family="Segoe UI", size=12)
        self.f_total   = ctk.CTkFont(family="Segoe UI", size=18, weight="bold")
        self.f_btn     = ctk.CTkFont(family="Segoe UI", size=14, weight="bold")

    # ── Header ───────────────────────────────────────────────────────────────

    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color=COR_HEADER, corner_radius=0, height=88)
        hdr.pack(fill="x", side="top")
        hdr.pack_propagate(False)

        row_top = ctk.CTkFrame(hdr, fg_color="transparent")
        row_top.pack(fill="x", padx=20, pady=16)

        # logo real "DinDin Show" (com fallback caso o arquivo não exista)
        if LOGO_PATH.exists():
            logo_img = Image.open(LOGO_PATH).resize((58, 58), Image.LANCZOS)
            self._logo_ctk = ctk.CTkImage(light_image=logo_img, size=(58, 58))
            ctk.CTkLabel(row_top, image=self._logo_ctk, text="").pack(side="left")
        else:
            badge = ctk.CTkFrame(row_top, width=52, height=52, corner_radius=26, fg_color="#FFFFFF")
            badge.pack(side="left")
            badge.pack_propagate(False)
            bars = ctk.CTkFrame(badge, fg_color="transparent")
            bars.place(relx=0.5, rely=0.5, anchor="center")
            for cor in ["#E0395B", "#1F4FD8", "#FFFFFF"]:
                borda = {"border_width": 1, "border_color": "#CCCCCC"} if cor == "#FFFFFF" else {}
                ctk.CTkFrame(bars, width=7, height=26, corner_radius=4, fg_color=cor, **borda
                             ).pack(side="left", padx=1)

        txt_frame = ctk.CTkFrame(row_top, fg_color="transparent")
        txt_frame.pack(side="left", padx=(14, 0))
        ctk.CTkLabel(txt_frame, text="DinDin Show", text_color=COR_AMARELO,
                     font=self.f_titulo).pack(anchor="w")
        ctk.CTkLabel(txt_frame, text="Toque no sabor para adicionar",
                     text_color="#C9D6EA", font=self.f_sub).pack(anchor="w")

        self._pills = {}  # mantido para não quebrar _atualizar_pills

        # faixa amarela de acento
        ctk.CTkFrame(self, fg_color=COR_AMARELO, height=4, corner_radius=0).pack(fill="x", side="top")

    def _atualizar_pills(self):
        for num, pill in self._pills.items():
            pill.configure(fg_color=COR_LARANJA if num == self.current_step else COR_PILL_INATIVA)

    # ── Corpo ────────────────────────────────────────────────────────────────

    def _build_body(self):
        corpo = ctk.CTkFrame(self, fg_color=COR_FUNDO, corner_radius=0)
        corpo.pack(fill="both", expand=True)

        # 1. Wrapper do carrinho empacotado PRIMEIRO com side="bottom".
        #    O frame extra garante que o CTkScrollableFrame nunca invada
        #    o espaço reservado para o painel de pagamento.
        self._frm_carrinho_wrapper = ctk.CTkFrame(corpo, fg_color=COR_FUNDO, corner_radius=0)
        self._frm_carrinho_wrapper.pack(side="bottom", fill="x")
        self._build_painel_pedido(self._frm_carrinho_wrapper)

        # 2. Grade de sabores — preenche o restante e rola verticalmente
        self.frm_grid = ctk.CTkScrollableFrame(corpo, fg_color=COR_FUNDO, corner_radius=0)
        self.frm_grid.pack(side="top", fill="both", expand=True, padx=10, pady=(12, 0))
        for c in range(3):
            self.frm_grid.grid_columnconfigure(c, weight=1)

    def _build_painel_pedido(self, parent):
        sombra = ctk.CTkFrame(parent, fg_color="#D9DEE6", corner_radius=24)
        sombra.pack(fill="x", padx=8, pady=(0, 0))

        painel = ctk.CTkFrame(sombra, fg_color=COR_CARD, corner_radius=22,
                               border_width=1, border_color="#E5E7EB")
        painel.pack(fill="x", padx=2, pady=(2, 6))

        ctk.CTkFrame(painel, width=44, height=5, corner_radius=3, fg_color="#D1D5DB"
                     ).pack(pady=(10, 4))

        topo = ctk.CTkFrame(painel, fg_color="transparent")
        topo.pack(fill="x", padx=20, pady=(0, 6))
        ctk.CTkLabel(topo, text="Seu pedido", text_color=COR_HEADER, font=self.f_painel
                     ).pack(side="left")
        self.lbl_badge_itens = ctk.CTkLabel(
            topo, text="0 itens", text_color="#FFFFFF", fg_color=COR_LARANJA,
            corner_radius=999, font=self.f_pill, width=70, height=24)
        self.lbl_badge_itens.pack(side="right")

        self.frm_itens_wrap = ctk.CTkFrame(painel, fg_color="transparent", height=148)
        self.frm_itens_wrap.pack(fill="x", padx=20)
        self.frm_itens_wrap.pack_propagate(False)
        self._criar_linhas_carrinho()   # pré-cria linhas fixas para update in-place

        # pagamento
        frm_pgto = ctk.CTkFrame(painel, fg_color="transparent")
        frm_pgto.pack(fill="x", padx=20, pady=(6, 8))
        ctk.CTkLabel(frm_pgto, text="Pagamento", text_color=COR_TEXTO_LEVE, font=self.f_small
                     ).pack(anchor="w", pady=(0, 4))
        row_pgto = ctk.CTkFrame(frm_pgto, fg_color="transparent")
        row_pgto.pack(fill="x")
        self.var_pagamento = ctk.StringVar(value="dinheiro")
        self._btns_pgto = {}
        for label, valor in [("Dinheiro", "dinheiro"), ("Cartão", "cartao"), ("Pix", "pix")]:
            ativo = valor == "dinheiro"
            b = ctk.CTkButton(
                row_pgto, text=label, corner_radius=999, height=34,
                fg_color=COR_HEADER if ativo else COR_PGTO_INATIVO,
                text_color="#FFFFFF" if ativo else COR_TEXTO,
                hover_color=COR_HEADER_HOVER if ativo else "#E0E3E8",
                font=self.f_pill,
                command=lambda v=valor: self._selecionar_pagamento(v))
            b.pack(side="left", expand=True, fill="x", padx=4)
            self._btns_pgto[valor] = b

        self.lbl_total = ctk.CTkLabel(painel, text=f"Total: {_fmt_brl(0)}",
                                       text_color=COR_LARANJA, font=self.f_total)
        self.lbl_total.pack(pady=(8, 6))

        self.btn_confirmar = ctk.CTkButton(
            painel, text="✔  CONFIRMAR PEDIDO", height=46, corner_radius=14,
            fg_color=COR_VERDE, hover_color=COR_VERDE_HOVER, font=self.f_btn,
            command=self._confirmar_pedido)
        self.btn_confirmar.pack(fill="x", padx=20, pady=(0, 6))

        ctk.CTkButton(painel, text="Limpar carrinho", height=28, fg_color="transparent",
                      text_color=COR_TEXTO_LEVE, hover_color="#F3F4F6", font=self.f_small,
                      command=self._limpar_carrinho).pack(pady=(0, 14))

        self._renderizar_itens_carrinho()  # mostra o estado vazio inicial

    def _criar_linhas_carrinho(self):
        """Pré-cria MAX linhas de item do carrinho para atualização in-place.
        Nenhuma delas é destruída depois — só mostrada/ocultada via pack/pack_forget."""
        MAX = 5
        self._lbl_carrinho_vazio = ctk.CTkLabel(
            self.frm_itens_wrap,
            text="Nenhum sabor selecionado ainda.",
            text_color=COR_TEXTO_LEVE, font=self.f_item)
        self._lbl_carrinho_vazio.pack(anchor="w", pady=(4, 8))

        self._cart_rows: list[dict] = []
        for _ in range(MAX):
            row = ctk.CTkFrame(self.frm_itens_wrap, fg_color="transparent")
            lbl_nome = ctk.CTkLabel(row, text="", text_color=COR_TEXTO,
                                     anchor="w", font=self.f_item, width=110)
            lbl_nome.pack(side="left")
            btn_minus = ctk.CTkButton(
                row, text="−", width=26, height=26, corner_radius=13,
                fg_color=COR_PGTO_INATIVO, text_color=COR_TEXTO,
                hover_color="#E0E3E8", command=lambda: None)
            btn_minus.pack(side="left", padx=2)
            lbl_qtd = ctk.CTkLabel(row, text="", text_color=COR_TEXTO,
                                    width=20, font=self.f_item)
            lbl_qtd.pack(side="left")
            btn_plus = ctk.CTkButton(
                row, text="+", width=26, height=26, corner_radius=13,
                fg_color=COR_PGTO_INATIVO, text_color=COR_TEXTO,
                hover_color="#E0E3E8", command=lambda: None)
            btn_plus.pack(side="left", padx=2)
            lbl_sub = ctk.CTkLabel(
                row, text="", text_color=COR_LARANJA,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"))
            lbl_sub.pack(side="right")
            # começa oculta
            self._cart_rows.append({
                "row": row, "lbl_nome": lbl_nome, "btn_minus": btn_minus,
                "lbl_qtd": lbl_qtd, "btn_plus": btn_plus, "lbl_sub": lbl_sub,
                "packed": False,
            })

    # ── Produtos ─────────────────────────────────────────────────────────────

    def _carregar_produtos(self):
        def fetch():
            try:
                r = httpx.get(f"{API_BASE}/produtos", timeout=5)
                self.produtos = r.json()
                self.after(0, self._renderizar_produtos)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Erro de conexão", str(e)))
        threading.Thread(target=fetch, daemon=True).start()

    def _renderizar_produtos(self):
        for w in self.frm_grid.winfo_children():
            w.destroy()
        colunas = 3
        # produtos com estoque > 0 primeiro; esgotados ao final
        ordenados = sorted(self.produtos, key=lambda p: 0 if (p.get("estoque") or 0) > 0 else 1)
        self._card_refs.clear()
        self._card_positions.clear()
        for i, prod in enumerate(ordenados):
            row, col = i // colunas, i % colunas
            self._card_positions[prod["id"]] = (row, col)
            self._criar_card(self.frm_grid, prod, row, col)

    def _criar_card(self, parent, prod, row, col):
        """Monta a estrutura do card UMA vez. Mudanças de estado (esgotado
        por estoque/carrinho) depois só reconfiguram estes widgets — nunca
        são destruídos, o que evita o repaint/flicker do Canvas interno do
        CTkScrollableFrame."""
        pid = prod["id"]
        cor_swatch_base = _cor_sabor(prod["nome"])

        card = ctk.CTkFrame(parent, fg_color=COR_CARD, corner_radius=14,
                             border_width=1, border_color=COR_BORDA_CARD)
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

        swatch = ctk.CTkFrame(card, fg_color=cor_swatch_base, corner_radius=14, height=84)
        swatch.pack(fill="x", padx=2, pady=(2, 0))
        swatch.pack_propagate(False)

        lbl_letra = ctk.CTkLabel(swatch, text=prod["nome"][0].upper(), text_color="#FFFFFF",
                                  font=self.f_letra)
        lbl_letra.place(relx=0.5, rely=0.5, anchor="center")

        faixa = ctk.CTkFrame(swatch, fg_color=COR_FAIXA_ESG, corner_radius=0, height=18)
        lbl_faixa = ctk.CTkLabel(faixa, text="ESGOTADO", text_color="#FFFFFF",
                                  font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"))
        lbl_faixa.pack(pady=0)
        # faixa.place() só é chamado em _aplicar_estado_card quando necessário

        corpo_card = ctk.CTkFrame(card, fg_color="transparent")
        corpo_card.pack(fill="x", padx=8, pady=(6, 8))
        lbl_nome = ctk.CTkLabel(corpo_card, text=prod["nome"], anchor="w",
                     font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                     wraplength=130)
        lbl_nome.pack(anchor="w")
        lbl_preco = ctk.CTkLabel(corpo_card, text=_fmt_brl(prod["preco"]), anchor="w",
                     font=ctk.CTkFont(family="Segoe UI", size=11))
        lbl_preco.pack(anchor="w")

        self._card_refs[pid] = {
            "card": card, "swatch": swatch, "lbl_letra": lbl_letra,
            "faixa": faixa, "lbl_faixa": lbl_faixa,
            "lbl_nome": lbl_nome, "lbl_preco": lbl_preco, "corpo_card": corpo_card,
            "cor_swatch_base": cor_swatch_base,
            "img_normal": None, "img_esgotado": None,
        }

        if prod.get("imagem"):
            def _load(fname=prod["imagem"], pid=pid):
                try:
                    r = httpx.get(f"{API_BASE}/imagens/{fname}", timeout=5)
                    if r.status_code == 200:
                        foto = Image.open(BytesIO(r.content)).resize((160, 84), Image.LANCZOS)
                        img_normal = ctk.CTkImage(light_image=foto, size=(160, 84))
                        img_esgotado = ctk.CTkImage(
                            light_image=foto.convert("LA").convert("RGB"), size=(160, 84))

                        def _aplicar():
                            refs = self._card_refs.get(pid)
                            if refs and refs["lbl_letra"].winfo_exists():
                                refs["img_normal"] = img_normal
                                refs["img_esgotado"] = img_esgotado
                                self._aplicar_estado_card(pid)
                        self.after(0, _aplicar)
                except Exception:
                    pass
            threading.Thread(target=_load, daemon=True).start()

        self._aplicar_estado_card(pid)

    def _aplicar_estado_card(self, pid: int):
        """Atualiza cores/texto/clique do card de um produto sem destruir
        nenhum widget — usado a cada mudança no carrinho."""
        refs = self._card_refs.get(pid)
        if not refs:
            return
        prod = next((p for p in self.produtos if p["id"] == pid), None)
        if prod is None:
            return

        estoque     = prod.get("estoque") or 0
        no_carrinho = self.carrinho.get(pid, {}).get("qtd", 0)
        esgotado    = estoque == 0 or no_carrinho >= estoque

        card, swatch   = refs["card"], refs["swatch"]
        lbl_letra      = refs["lbl_letra"]
        faixa, lbl_fx  = refs["faixa"], refs["lbl_faixa"]
        lbl_nome       = refs["lbl_nome"]
        lbl_preco      = refs["lbl_preco"]
        corpo_card     = refs["corpo_card"]

        # Caching de estado: só reconfigura widgets se o estado mudou de fato.
        # Evita redraws desnecessários do Canvas do CTkScrollableFrame.
        if refs.get("_esgotado") == esgotado:
            return
        refs["_esgotado"] = esgotado

        card.configure(cursor="" if esgotado else "hand2")
        swatch.configure(fg_color=COR_ESGOTADO_BG if esgotado else refs["cor_swatch_base"])
        lbl_letra.configure(text_color=COR_ESGOTADO_FX if esgotado else "#FFFFFF")
        lbl_nome.configure(text_color=COR_ESGOTADO_FX if esgotado else COR_TEXTO)
        lbl_preco.configure(text_color=COR_ESGOTADO_FX if esgotado else COR_LARANJA)

        if refs["img_normal"] is not None:
            lbl_letra.configure(image=refs["img_esgotado"] if esgotado else refs["img_normal"])

        if esgotado:
            lbl_fx.configure(text="ESGOTADO" if estoque == 0 else "MÁXIMO NO CARRINHO")
            faixa.place(relx=0, rely=0, relwidth=1.0)
        else:
            faixa.place_forget()

        for w in (card, swatch, corpo_card):
            w.unbind("<Button-1>")
            if not esgotado:
                w.bind("<Button-1>", lambda e, p=prod: self._adicionar(p))

    # ── Carrinho ─────────────────────────────────────────────────────────────

    def _adicionar(self, prod):
        pid = prod["id"]
        if pid in self.carrinho:
            self.carrinho[pid]["qtd"] += 1
        else:
            self.carrinho[pid] = {"nome": prod["nome"], "preco": prod["preco"], "qtd": 1}
        if self.current_step == 1:
            self.current_step = 2
        # after_idle difere todos os redraws para depois que o evento de clique
        # é totalmente processado pelo Tk — os redraws são batched num único frame.
        self.after_idle(lambda p=pid: self._atualizar_ui_carrinho(p))

    def _remover(self, prod_id):
        if prod_id in self.carrinho:
            self.carrinho[prod_id]["qtd"] -= 1
            if self.carrinho[prod_id]["qtd"] <= 0:
                del self.carrinho[prod_id]
        if not self.carrinho:
            self.current_step = 1
        self.after_idle(lambda p=prod_id: self._atualizar_ui_carrinho(p))

    def _atualizar_ui_carrinho(self, pid: int | None = None):
        """Concentra todos os redraws pós-modificação de carrinho num único ponto."""
        self._atualizar_pills()
        self._renderizar_itens_carrinho()
        if pid is not None:
            self._aplicar_estado_card(pid)

    def _limpar_carrinho(self):
        pids_afetados = list(self.carrinho.keys())
        self.carrinho.clear()
        self.current_step = 1
        self._atualizar_pills()
        self._renderizar_itens_carrinho()
        for pid in pids_afetados:
            self._aplicar_estado_card(pid)

    def _selecionar_pagamento(self, valor):
        self.var_pagamento.set(valor)
        if self.carrinho:
            self.current_step = 3
            self._atualizar_pills()
        for v, btn in self._btns_pgto.items():
            ativo = v == valor
            btn.configure(fg_color=COR_HEADER if ativo else COR_PGTO_INATIVO,
                          text_color="#FFFFFF" if ativo else COR_TEXTO,
                          hover_color=COR_HEADER_HOVER if ativo else "#E0E3E8")

    def _renderizar_itens_carrinho(self):
        """Atualiza o carrinho in-place — nenhum widget é criado ou destruído."""
        itens  = list(self.carrinho.items())
        total  = 0.0
        n_itens = sum(i["qtd"] for i in self.carrinho.values())
        self.lbl_badge_itens.configure(text=f"{n_itens} itens")

        if not itens:
            self._lbl_carrinho_vazio.pack(anchor="w", pady=(4, 8))
        else:
            self._lbl_carrinho_vazio.pack_forget()

        for idx, ref in enumerate(self._cart_rows):
            if idx < len(itens):
                pid, item = itens[idx]
                subtotal = item["preco"] * item["qtd"]
                total += subtotal
                ref["lbl_nome"].configure(text=item["nome"][:16])
                ref["lbl_qtd"].configure(text=str(item["qtd"]))
                ref["lbl_sub"].configure(text=_fmt_brl(subtotal))
                ref["btn_minus"].configure(command=lambda p=pid: self._remover(p))
                ref["btn_plus"].configure(
                    command=lambda p=pid, pr=item["preco"], nm=item["nome"]:
                        self._adicionar({"id": p, "nome": nm, "preco": pr}))
                if not ref["packed"]:
                    ref["row"].pack(fill="x", pady=2)
                    ref["packed"] = True
            else:
                if ref["packed"]:
                    ref["row"].pack_forget()
                    ref["packed"] = False

        self.lbl_total.configure(text=f"Total: {_fmt_brl(total)}")

    # ── Confirmação ──────────────────────────────────────────────────────────

    def _confirmar_pedido(self):
        if not self.carrinho:
            messagebox.showwarning("Carrinho vazio", "Adicione itens antes de confirmar.")
            return

        payload = {
            "itens": [{"produto_id": pid, "quantidade": v["qtd"]}
                      for pid, v in self.carrinho.items()],
            "forma_pagamento": self.var_pagamento.get(),
        }

        def enviar():
            try:
                r = httpx.post(f"{API_BASE}/pedidos", json=payload, timeout=10)
                data = r.json()
                if r.status_code == 200:
                    self.after(0, lambda: self._pedido_confirmado(data))
                else:
                    self.after(0, lambda: messagebox.showerror("Erro", str(data)))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Erro", str(e)))

        threading.Thread(target=enviar, daemon=True).start()

    def _pedido_confirmado(self, data):
        self._limpar_carrinho()
        self._modal_confirmado(data["numero"], data["valor_total"])

    def _modal_confirmado(self, numero: int, total: float):
        VERDE = "#2E7D32"
        TEMPO = 15
        CW, CH = 480, 462

        # tk.Toplevel simples — aparece imediatamente sem setup assíncrono.
        # -topmost garante que fica acima da janela principal em qualquer monitor.
        modal = tk.Toplevel(self)
        modal.transient(self)
        modal.title("")
        modal.resizable(False, False)
        modal.configure(bg="#FFFFFF")
        modal.attributes("-topmost", True)

        def _fechar():
            if modal.winfo_exists():
                modal.grab_release()
                modal.destroy()
            self._carregar_produtos()

        # ── Conteúdo (apenas widgets nativos tk para garantir renderização) ────
        tk.Frame(modal, bg=VERDE, height=12).pack(fill="x")

        tk.Label(modal, text="✓", fg=VERDE, bg="#FFFFFF",
                 font=("Segoe UI", 72, "bold")).pack(pady=(18, 0))

        tk.Label(modal, text="Pedido Confirmado!", fg=COR_TEXTO, bg="#FFFFFF",
                 font=("Segoe UI", 20, "bold")).pack()

        frm_num = tk.Frame(modal, bg="#FFF3E0", pady=8, padx=24)
        frm_num.pack(pady=(12, 0))
        tk.Label(frm_num, text=f"Pedido  #{numero}", fg=COR_LARANJA, bg="#FFF3E0",
                 font=("Segoe UI", 26, "bold")).pack()

        tk.Label(modal, text=f"Total: {_fmt_brl(total)}", fg=COR_TEXTO_LEVE, bg="#FFFFFF",
                 font=("Segoe UI", 13)).pack(pady=(8, 0))

        tk.Label(modal, text="🍦  Aguarde o preparo!", fg=COR_TEXTO, bg="#FFFFFF",
                 font=("Segoe UI", 13)).pack(pady=(6, 0))

        # Barra de progresso com Canvas nativo
        canvas_barra = tk.Canvas(modal, height=10, bg="#EEEEEE",
                                  highlightthickness=0)
        canvas_barra.pack(fill="x", padx=36, pady=(14, 0))
        barra_id = canvas_barra.create_rectangle(0, 0, 999, 10, fill=VERDE, outline="")

        lbl_timer = tk.Label(modal, text=f"Fechando em {TEMPO}s...",
                              fg="#AAAAAA", bg="#FFFFFF", font=("Segoe UI", 10))
        lbl_timer.pack(pady=(4, 0))

        tk.Button(modal, text="OK", bg=COR_LARANJA, fg="white",
                  font=("Segoe UI", 13, "bold"), relief="flat",
                  padx=32, pady=10, cursor="hand2",
                  command=_fechar).pack(pady=(12, 0))

        # ── Posicionamento ────────────────────────────────────────────────────
        modal.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width()  - CW) // 2
        y = self.winfo_rooty() + (self.winfo_height() - CH) // 2
        modal.geometry(f"{CW}x{CH}+{x}+{y}")
        modal.lift()
        modal.focus_force()
        modal.grab_set()

        _restante = [TEMPO]
        def _tick():
            if not modal.winfo_exists():
                return
            _restante[0] -= 1
            frac = max(0.0, _restante[0] / TEMPO)
            try:
                larg = canvas_barra.winfo_width()
                canvas_barra.coords(barra_id, 0, 0, int(larg * frac), 10)
            except Exception:
                pass
            if _restante[0] <= 0:
                _fechar()
            else:
                lbl_timer.configure(text=f"Fechando em {_restante[0]}s...")
                modal.after(1000, _tick)
        modal.after(1000, _tick)


if __name__ == "__main__":
    app = AppCliente()
    app.mainloop()
