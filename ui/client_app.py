"""
ui/client_app.py
Interface touchscreen do cliente — tela de quiosque
"""

import tkinter as tk
from tkinter import font as tkfont, messagebox
import httpx
import threading
import os
from PIL import Image, ImageTk, ImageDraw

API_BASE = "http://127.0.0.1:8000"

# ── Paleta de cores ──────────────────────────────────────────────────────────
COR_FUNDO       = "#F5F0E8"
COR_PRIMARIA    = "#D55A2B"   # laranja queimado
COR_SECUNDARIA  = "#2B4D6F"   # azul escuro
COR_CARD        = "#FFFFFF"
COR_CARD_SEL    = "#FFF0E6"
COR_BORDA_SEL   = "#D55A2B"
COR_TEXTO       = "#1A1A1A"
COR_TEXTO_LEVE  = "#666666"
COR_VERDE       = "#2E7D32"
COR_BTN_CONF    = "#D55A2B"


def _placeholder_img(nome: str, size=120):
    """Gera imagem placeholder colorida com inicial do sabor."""
    cores = ["#E57373","#81C784","#64B5F6","#FFD54F","#BA68C8",
             "#4DB6AC","#FF8A65","#A1887F","#90A4AE","#F06292"]
    cor = cores[hash(nome) % len(cores)]
    img = Image.new("RGB", (size, size), cor)
    draw = ImageDraw.Draw(img)
    draw.text((size//2 - 10, size//2 - 16), nome[0].upper(),
              fill="white")
    return ImageTk.PhotoImage(img)


class AppCliente(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sorvetes Jamir")
        self.configure(bg=COR_FUNDO)

        # Fullscreen
        self.attributes("-fullscreen", True)
        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False))

        self.carrinho = {}     # {produto_id: {"nome", "preco", "qtd"}}
        self.produtos = []
        self._imgs = {}        # mantém refs de imagem

        self._fontes()
        self._build_ui()
        self._carregar_produtos()

    def _fontes(self):
        self.f_titulo  = tkfont.Font(family="Segoe UI", size=22, weight="bold")
        self.f_card    = tkfont.Font(family="Segoe UI", size=13, weight="bold")
        self.f_preco   = tkfont.Font(family="Segoe UI", size=12)
        self.f_btn     = tkfont.Font(family="Segoe UI", size=14, weight="bold")
        self.f_total   = tkfont.Font(family="Segoe UI", size=16, weight="bold")
        self.f_small   = tkfont.Font(family="Segoe UI", size=10)

    def _build_ui(self):
        # ── Header
        hdr = tk.Frame(self, bg=COR_SECUNDARIA, height=70)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🍦 Sorvetes Jamir", bg=COR_SECUNDARIA,
                 fg="white", font=self.f_titulo).pack(side="left", padx=20, pady=12)
        tk.Label(hdr, text="Toque no sabor para adicionar ao pedido",
                 bg=COR_SECUNDARIA, fg="#BBCCE0", font=self.f_small).pack(side="left", padx=8)

        # ── Corpo
        corpo = tk.Frame(self, bg=COR_FUNDO)
        corpo.pack(fill="both", expand=True)

        # Painel de produtos (esquerda — 72%)
        self.frm_produtos = tk.Frame(corpo, bg=COR_FUNDO)
        self.frm_produtos.pack(side="left", fill="both", expand=True, padx=12, pady=12)

        # Canvas + scrollbar para grid de produtos
        self.canvas_prod = tk.Canvas(self.frm_produtos, bg=COR_FUNDO, highlightthickness=0)
        scroll = tk.Scrollbar(self.frm_produtos, orient="vertical",
                              command=self.canvas_prod.yview)
        self.canvas_prod.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.canvas_prod.pack(fill="both", expand=True)
        self.frm_grid = tk.Frame(self.canvas_prod, bg=COR_FUNDO)
        self.canvas_prod.create_window((0, 0), window=self.frm_grid, anchor="nw")
        self.frm_grid.bind("<Configure>",
            lambda e: self.canvas_prod.configure(
                scrollregion=self.canvas_prod.bbox("all")))

        # Painel carrinho (direita — 28%)
        self._build_carrinho(corpo)

    def _build_carrinho(self, parent):
        frm = tk.Frame(parent, bg=COR_CARD, width=320, relief="flat",
                       bd=0, highlightthickness=1,
                       highlightbackground="#DDDDDD")
        frm.pack(side="right", fill="y", padx=(0, 12), pady=12)
        frm.pack_propagate(False)

        tk.Label(frm, text="Seu Pedido", bg=COR_CARD, fg=COR_SECUNDARIA,
                 font=self.f_btn).pack(pady=(16, 8))

        # Lista de itens
        self.frm_itens = tk.Frame(frm, bg=COR_CARD)
        self.frm_itens.pack(fill="both", expand=True, padx=12)

        # Pagamento
        frm_pgto = tk.Frame(frm, bg=COR_CARD)
        frm_pgto.pack(fill="x", padx=12, pady=(4, 0))
        tk.Label(frm_pgto, text="Pagamento:", bg=COR_CARD, fg=COR_TEXTO_LEVE,
                 font=self.f_small).pack(anchor="w")
        self.var_pagto = tk.StringVar(value="dinheiro")
        for op in [("Dinheiro", "dinheiro"), ("Cartão", "cartao"), ("Pix", "pix")]:
            tk.Radiobutton(frm_pgto, text=op[0], variable=self.var_pagto,
                           value=op[1], bg=COR_CARD, fg=COR_TEXTO,
                           activebackground=COR_CARD,
                           font=self.f_small).pack(side="left")

        # Total
        self.lbl_total = tk.Label(frm, text="Total: R$ 0,00",
                                  bg=COR_CARD, fg=COR_PRIMARIA, font=self.f_total)
        self.lbl_total.pack(pady=8)

        # Botão confirmar
        self.btn_confirmar = tk.Button(
            frm, text="✔  CONFIRMAR PEDIDO",
            bg=COR_BTN_CONF, fg="white", font=self.f_btn,
            relief="flat", cursor="hand2", bd=0,
            padx=10, pady=12,
            command=self._confirmar_pedido
        )
        self.btn_confirmar.pack(fill="x", padx=12, pady=(4, 4))

        # Botão limpar
        tk.Button(frm, text="Limpar carrinho", bg="#EEEEEE",
                  fg=COR_TEXTO_LEVE, font=self.f_small, relief="flat",
                  cursor="hand2", command=self._limpar_carrinho
                  ).pack(fill="x", padx=12, pady=(0, 16))

    # ── Carregamento de produtos ─────────────────────────────────────────────

    def _carregar_produtos(self):
        def fetch():
            try:
                r = httpx.get(f"{API_BASE}/produtos", timeout=5)
                self.produtos = r.json()
                self.after(0, self._renderizar_produtos)
            except Exception as e:
                self.after(0, lambda: self._mostrar_erro(f"Sem conexão com o servidor.\n{e}"))
        threading.Thread(target=fetch, daemon=True).start()

    def _renderizar_produtos(self):
        for w in self.frm_grid.winfo_children():
            w.destroy()

        colunas = 3
        for i, prod in enumerate(self.produtos):
            col = i % colunas
            row = i // colunas
            self._card_produto(self.frm_grid, prod, row, col)

    def _card_produto(self, parent, prod, row, col):
        frm = tk.Frame(parent, bg=COR_CARD, relief="flat", bd=0,
                       highlightthickness=1, highlightbackground="#E0E0E0",
                       cursor="hand2")
        frm.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        # Imagem placeholder
        img = _placeholder_img(prod["nome"])
        self._imgs[prod["id"]] = img
        lbl_img = tk.Label(frm, image=img, bg=COR_CARD)
        lbl_img.pack(pady=(12, 4))

        tk.Label(frm, text=prod["nome"], bg=COR_CARD, fg=COR_TEXTO,
                 font=self.f_card, wraplength=140).pack()
        tk.Label(frm, text=f"R$ {prod['preco']:.2f}", bg=COR_CARD,
                 fg=COR_PRIMARIA, font=self.f_preco).pack()
        tk.Label(frm, text=f"Estoque: {prod['estoque']}", bg=COR_CARD,
                 fg=COR_TEXTO_LEVE, font=self.f_small).pack(pady=(0, 12))

        # Bind clique em todos os widgets do card
        for w in [frm, lbl_img] + frm.winfo_children():
            w.bind("<Button-1>", lambda e, p=prod: self._adicionar(p))

    # ── Carrinho ─────────────────────────────────────────────────────────────

    def _adicionar(self, prod):
        pid = prod["id"]
        if pid in self.carrinho:
            self.carrinho[pid]["qtd"] += 1
        else:
            self.carrinho[pid] = {"nome": prod["nome"],
                                  "preco": prod["preco"], "qtd": 1}
        self._atualizar_carrinho_ui()

    def _remover(self, prod_id):
        if prod_id in self.carrinho:
            self.carrinho[prod_id]["qtd"] -= 1
            if self.carrinho[prod_id]["qtd"] <= 0:
                del self.carrinho[prod_id]
        self._atualizar_carrinho_ui()

    def _limpar_carrinho(self):
        self.carrinho.clear()
        self._atualizar_carrinho_ui()

    def _atualizar_carrinho_ui(self):
        for w in self.frm_itens.winfo_children():
            w.destroy()

        total = 0.0
        for pid, item in self.carrinho.items():
            subtotal = item["preco"] * item["qtd"]
            total += subtotal
            row = tk.Frame(self.frm_itens, bg=COR_CARD)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=item["nome"][:18], bg=COR_CARD, fg=COR_TEXTO,
                     font=self.f_small, width=16, anchor="w").pack(side="left")
            tk.Button(row, text="−", bg="#EEEEEE", fg=COR_TEXTO,
                      font=self.f_small, relief="flat", cursor="hand2",
                      command=lambda p=pid: self._remover(p)).pack(side="left")
            tk.Label(row, text=str(item["qtd"]), bg=COR_CARD, fg=COR_TEXTO,
                     font=self.f_small, width=2).pack(side="left")
            tk.Button(row, text="+", bg="#EEEEEE", fg=COR_TEXTO,
                      font=self.f_small, relief="flat", cursor="hand2",
                      command=lambda p=pid, pr=item["preco"]: self._adicionar(
                          {"id": p, "nome": item["nome"], "preco": pr, "estoque": 99}
                      )).pack(side="left")
            tk.Label(row, text=f"R${subtotal:.2f}", bg=COR_CARD, fg=COR_PRIMARIA,
                     font=self.f_small).pack(side="right")

        self.lbl_total.config(text=f"Total: R$ {total:.2f}")

    # ── Confirmação ──────────────────────────────────────────────────────────

    def _confirmar_pedido(self):
        if not self.carrinho:
            messagebox.showwarning("Carrinho vazio", "Adicione itens antes de confirmar.")
            return

        payload = {
            "itens": [{"produto_id": pid, "quantidade": v["qtd"]}
                      for pid, v in self.carrinho.items()],
            "forma_pagto": self.var_pagto.get(),
            "observacao": ""
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
        self._carregar_produtos()
        messagebox.showinfo("Pedido confirmado!",
                            f"Pedido #{data['id']} recebido!\nTotal: R$ {data['total']:.2f}\n\nAguarde o preparo 🍦")

    def _mostrar_erro(self, msg):
        messagebox.showerror("Erro de conexão", msg)


if __name__ == "__main__":
    app = AppCliente()
    app.mainloop()
