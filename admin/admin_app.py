"""
admin/admin_app.py
Painel Administrativo — Gestão de estoque e relatórios de vendas
"""

import tkinter as tk
from tkinter import ttk, font as tkfont, messagebox, simpledialog
import httpx
import threading
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

API_BASE = "http://127.0.0.1:8000"

COR_FUNDO       = "#F0F2F5"
COR_SIDEBAR     = "#2B4D6F"
COR_PRIMARIA    = "#D55A2B"
COR_CARD        = "#FFFFFF"
COR_TEXTO       = "#1A1A1A"
COR_TEXTO_LEVE  = "#666666"
COR_VERDE       = "#2E7D32"
COR_ALERTA      = "#C62828"


def api_get(endpoint):
    r = httpx.get(f"{API_BASE}{endpoint}", timeout=10)
    return r.json()


def api_put(endpoint, payload):
    r = httpx.put(f"{API_BASE}{endpoint}", json=payload, timeout=10)
    return r.json()


def api_post(endpoint, payload):
    r = httpx.post(f"{API_BASE}{endpoint}", json=payload, timeout=10)
    return r.json()


class AdminApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDV Jamir — Painel Administrativo")
        self.geometry("1200x700")
        self.configure(bg=COR_FUNDO)

        self.f_titulo = tkfont.Font(family="Segoe UI", size=14, weight="bold")
        self.f_normal = tkfont.Font(family="Segoe UI", size=11)
        self.f_small  = tkfont.Font(family="Segoe UI", size=10)
        self.f_btn    = tkfont.Font(family="Segoe UI", size=11, weight="bold")

        self._build_layout()
        self._mostrar_dashboard()

    # ── Layout base ──────────────────────────────────────────────────────────

    def _build_layout(self):
        # Sidebar
        self.sidebar = tk.Frame(self, bg=COR_SIDEBAR, width=200)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="Jamir Admin", bg=COR_SIDEBAR,
                 fg="white", font=self.f_titulo).pack(pady=(24, 16))

        menus = [
            ("📊  Dashboard",    self._mostrar_dashboard),
            ("🍦  Estoque",      self._mostrar_estoque),
            ("📋  Pedidos",      self._mostrar_pedidos),
            ("📈  Relatórios",   self._mostrar_relatorios),
        ]
        for texto, cmd in menus:
            tk.Button(self.sidebar, text=texto, bg=COR_SIDEBAR, fg="white",
                      font=self.f_normal, relief="flat", anchor="w",
                      padx=16, pady=10, cursor="hand2",
                      activebackground="#3D6A96", activeforeground="white",
                      command=cmd).pack(fill="x")

        # Área principal
        self.main = tk.Frame(self, bg=COR_FUNDO)
        self.main.pack(side="left", fill="both", expand=True)

    def _limpar_main(self):
        for w in self.main.winfo_children():
            w.destroy()

    def _card(self, parent, titulo, valor, cor=COR_PRIMARIA):
        frm = tk.Frame(parent, bg=COR_CARD, relief="flat", bd=0,
                       highlightthickness=1, highlightbackground="#DEDEDE")
        tk.Label(frm, text=titulo, bg=COR_CARD, fg=COR_TEXTO_LEVE,
                 font=self.f_small).pack(anchor="w", padx=14, pady=(10, 2))
        tk.Label(frm, text=valor, bg=COR_CARD, fg=cor,
                 font=self.f_titulo).pack(anchor="w", padx=14, pady=(0, 12))
        return frm

    # ── Dashboard ─────────────────────────────────────────────────────────────

    def _mostrar_dashboard(self):
        self._limpar_main()
        tk.Label(self.main, text="Dashboard", bg=COR_FUNDO,
                 fg=COR_TEXTO, font=self.f_titulo).pack(anchor="w", padx=20, pady=(16, 8))

        def carregar():
            try:
                vendas   = api_get("/relatorios/vendas")
                alertas  = api_get("/estoque/alertas")
                pedidos  = api_get("/pedidos?status=pendente")
                self.after(0, lambda: _montar(vendas, alertas, pedidos))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Erro", str(e)))

        def _montar(vendas, alertas, pedidos):
            frm_cards = tk.Frame(self.main, bg=COR_FUNDO)
            frm_cards.pack(fill="x", padx=20, pady=8)
            cards = [
                ("Faturamento total",  f"R$ {vendas['total_faturamento']:.2f}", COR_VERDE),
                ("Total de pedidos",   str(vendas["total_pedidos"]),            COR_PRIMARIA),
                ("Pedidos pendentes",  str(len(pedidos)),                       "#E65100"),
                ("Alertas de estoque", str(len(alertas)),                       COR_ALERTA),
            ]
            for titulo, valor, cor in cards:
                c = self._card(frm_cards, titulo, valor, cor)
                c.pack(side="left", fill="y", padx=6, ipadx=20)

            if alertas:
                tk.Label(self.main, text="⚠ Estoque baixo:", bg=COR_FUNDO,
                         fg=COR_ALERTA, font=self.f_normal).pack(anchor="w", padx=24, pady=(12, 4))
                for a in alertas:
                    tk.Label(self.main,
                             text=f"  • {a['produto']} — {a['atual']} un. (mín. {a['minimo']})",
                             bg=COR_FUNDO, fg=COR_TEXTO, font=self.f_small).pack(anchor="w", padx=28)

        threading.Thread(target=carregar, daemon=True).start()

    # ── Estoque ──────────────────────────────────────────────────────────────

    def _mostrar_estoque(self):
        self._limpar_main()
        tk.Label(self.main, text="Gestão de Estoque", bg=COR_FUNDO,
                 fg=COR_TEXTO, font=self.f_titulo).pack(anchor="w", padx=20, pady=(16, 4))

        frm_btn = tk.Frame(self.main, bg=COR_FUNDO)
        frm_btn.pack(anchor="w", padx=20, pady=4)
        tk.Button(frm_btn, text="↻ Atualizar", font=self.f_small, relief="flat",
                  bg="#E0E0E0", cursor="hand2",
                  command=self._mostrar_estoque).pack(side="left", padx=4)

        # Tabela
        cols = ("id", "nome", "preco", "estoque", "minimo", "status", "ativo")
        tree = ttk.Treeview(self.main, columns=cols, show="headings", height=22)
        hdrs = {"id": ("ID", 40), "nome": ("Produto", 160), "preco": ("Preço", 80),
                "estoque": ("Estoque", 80), "minimo": ("Mínimo", 70),
                "status": ("Status", 90), "ativo": ("Ativo", 60)}
        for c, (label, w) in hdrs.items():
            tree.heading(c, text=label)
            tree.column(c, width=w, anchor="center")
        tree.pack(fill="both", expand=True, padx=20, pady=8)

        # Scroll
        sb = ttk.Scrollbar(self.main, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)

        # Painel de edição rápida
        frm_edit = tk.Frame(self.main, bg=COR_CARD, relief="flat", bd=0,
                            highlightthickness=1, highlightbackground="#DEDEDE")
        frm_edit.pack(fill="x", padx=20, pady=(0, 12))

        tk.Label(frm_edit, text="Edição rápida — selecione um produto na tabela",
                 bg=COR_CARD, fg=COR_TEXTO_LEVE, font=self.f_small).pack(side="left", padx=12, pady=10)

        var_qtd   = tk.StringVar()
        var_preco = tk.StringVar()

        tk.Label(frm_edit, text="Qtd:", bg=COR_CARD, font=self.f_small).pack(side="left")
        ent_qtd = tk.Entry(frm_edit, textvariable=var_qtd, width=7, font=self.f_small)
        ent_qtd.pack(side="left", padx=4)

        tk.Label(frm_edit, text="Preço:", bg=COR_CARD, font=self.f_small).pack(side="left")
        ent_preco = tk.Entry(frm_edit, textvariable=var_preco, width=8, font=self.f_small)
        ent_preco.pack(side="left", padx=4)

        def salvar_edicao():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Aviso", "Selecione um produto.")
                return
            pid = int(tree.item(sel[0])["values"][0])
            payload = {}
            try:
                if var_qtd.get():
                    payload["quantidade_estoque"] = int(var_qtd.get())
                if var_preco.get():
                    payload["preco"] = float(var_preco.get().replace(",", "."))
            except ValueError:
                messagebox.showerror("Erro", "Valores inválidos.")
                return
            if not payload:
                return
            def _put():
                try:
                    api_put(f"/produtos/{pid}", payload)
                    self.after(0, self._mostrar_estoque)
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Erro", str(e)))
            threading.Thread(target=_put, daemon=True).start()

        tk.Button(frm_edit, text="Salvar", bg=COR_PRIMARIA, fg="white",
                  font=self.f_small, relief="flat", cursor="hand2",
                  command=salvar_edicao).pack(side="left", padx=8, pady=8)

        def carregar():
            try:
                prods = api_get("/produtos/admin")
                self.after(0, lambda: preencher(prods))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Erro", str(e)))

        def preencher(prods):
            tree.delete(*tree.get_children())
            for p in prods:
                status = "🔴 Baixo" if p["estoque"] <= p["minimo"] else "🟢 OK"
                ativo = "Sim" if p["ativo"] else "Não"
                tree.insert("", "end", values=(
                    p["id"], p["nome"], f"R$ {p['preco']:.2f}",
                    p["estoque"], p["minimo"], status, ativo
                ))

        threading.Thread(target=carregar, daemon=True).start()

    # ── Pedidos ──────────────────────────────────────────────────────────────

    def _mostrar_pedidos(self):
        self._limpar_main()
        tk.Label(self.main, text="Pedidos", bg=COR_FUNDO,
                 fg=COR_TEXTO, font=self.f_titulo).pack(anchor="w", padx=20, pady=(16, 4))

        # Filtro status
        frm_f = tk.Frame(self.main, bg=COR_FUNDO)
        frm_f.pack(anchor="w", padx=20, pady=4)
        var_status = tk.StringVar(value="")
        for lbl, val in [("Todos",""),("Pendentes","pendente"),("Prontos","pronto"),("Cancelados","cancelado")]:
            tk.Radiobutton(frm_f, text=lbl, variable=var_status, value=val,
                           bg=COR_FUNDO, font=self.f_small,
                           command=lambda: carregar()).pack(side="left", padx=6)

        cols = ("id","data","status","total","pagto","itens")
        tree = ttk.Treeview(self.main, columns=cols, show="headings", height=18)
        for c, (lbl, w) in zip(cols, [("ID",40),("Data/Hora",140),("Status",90),
                                       ("Total",80),("Pagamento",90),("Itens",300)]):
            tree.heading(c, text=lbl)
            tree.column(c, width=w)
        tree.pack(fill="both", expand=True, padx=20, pady=8)

        frm_act = tk.Frame(self.main, bg=COR_FUNDO)
        frm_act.pack(anchor="w", padx=20, pady=(0, 12))

        def mudar_status(novo):
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Aviso", "Selecione um pedido.")
                return
            pid = int(tree.item(sel[0])["values"][0])
            def _put():
                try:
                    api_put(f"/pedidos/{pid}/status", {"status": novo})
                    self.after(0, carregar)
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Erro", str(e)))
            threading.Thread(target=_put, daemon=True).start()

        for txt, st, cor in [("✔ Marcar Pronto","pronto",COR_VERDE),
                               ("✖ Cancelar","cancelado",COR_ALERTA)]:
            tk.Button(frm_act, text=txt, bg=cor, fg="white", font=self.f_small,
                      relief="flat", cursor="hand2",
                      command=lambda s=st: mudar_status(s)).pack(side="left", padx=6)

        def carregar():
            st = var_status.get()
            url = f"/pedidos" + (f"?status={st}" if st else "")
            def _get():
                try:
                    pedidos = api_get(url)
                    self.after(0, lambda: preencher(pedidos))
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Erro", str(e)))
            threading.Thread(target=_get, daemon=True).start()

        def preencher(pedidos):
            tree.delete(*tree.get_children())
            for p in pedidos:
                itens_str = ", ".join([f"{i['produto']} x{i['qtd']}" for i in p["itens"]])
                tree.insert("", "end", values=(
                    p["id"], p["criado_em"][:16], p["status"],
                    f"R$ {p['total']:.2f}", p["forma_pagto"], itens_str
                ))

        carregar()

    # ── Relatórios ────────────────────────────────────────────────────────────

    def _mostrar_relatorios(self):
        self._limpar_main()
        tk.Label(self.main, text="Relatórios de Vendas", bg=COR_FUNDO,
                 fg=COR_TEXTO, font=self.f_titulo).pack(anchor="w", padx=20, pady=(16, 4))

        # Filtro de período
        frm_f = tk.Frame(self.main, bg=COR_FUNDO)
        frm_f.pack(anchor="w", padx=20, pady=4)
        hoje = datetime.now()
        periodos = [
            ("Hoje",     hoje.strftime("%Y-%m-%d"), hoje.strftime("%Y-%m-%d")),
            ("7 dias",   (hoje - timedelta(days=7)).strftime("%Y-%m-%d"), hoje.strftime("%Y-%m-%d")),
            ("30 dias",  (hoje - timedelta(days=30)).strftime("%Y-%m-%d"), hoje.strftime("%Y-%m-%d")),
            ("Tudo",     "", ""),
        ]
        self._periodo = ("", "")
        for lbl, ini, fim in periodos:
            tk.Button(frm_f, text=lbl, bg="#E0E0E0", font=self.f_small,
                      relief="flat", cursor="hand2",
                      command=lambda i=ini, f=fim: carregar(i, f)
                      ).pack(side="left", padx=4)

        # Área do gráfico
        self.frm_graf = tk.Frame(self.main, bg=COR_FUNDO)
        self.frm_graf.pack(fill="both", expand=True, padx=20, pady=8)

        def carregar(ini="", fim=""):
            params = []
            if ini: params.append(f"data_inicio={ini}")
            if fim: params.append(f"data_fim={fim}")
            url = "/relatorios/vendas" + (("?" + "&".join(params)) if params else "")
            def _get():
                try:
                    dados = api_get(url)
                    self.after(0, lambda: renderizar(dados))
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Erro", str(e)))
            threading.Thread(target=_get, daemon=True).start()

        def renderizar(dados):
            for w in self.frm_graf.winfo_children():
                w.destroy()

            ranking = dados["ranking"]
            if not ranking:
                tk.Label(self.frm_graf, text="Nenhum dado no período.",
                         bg=COR_FUNDO, fg=COR_TEXTO_LEVE, font=self.f_normal).pack(pady=40)
                return

            nomes  = [r["produto"] for r in ranking[:10]]
            qtds   = [r["quantidade"] for r in ranking[:10]]
            fats   = [r["faturamento"] for r in ranking[:10]]

            fig = Figure(figsize=(10, 4.5), dpi=96, facecolor="#F0F2F5")
            ax1 = fig.add_subplot(1, 2, 1)
            ax2 = fig.add_subplot(1, 2, 2)

            cores = plt.cm.tab10.colors

            # Gráfico de barras — quantidade
            bars = ax1.barh(nomes[::-1], qtds[::-1], color=[cores[i % 10] for i in range(len(nomes))])
            ax1.set_title("Mais vendidos (unidades)", fontsize=10, pad=8)
            ax1.set_facecolor("#FAFAFA")
            ax1.tick_params(labelsize=8)
            for bar, val in zip(bars, qtds[::-1]):
                ax1.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                         str(val), va="center", fontsize=8)

            # Gráfico de pizza — faturamento
            ax2.pie(fats, labels=nomes, autopct="%1.1f%%",
                    colors=[cores[i % 10] for i in range(len(nomes))],
                    textprops={"fontsize": 8})
            ax2.set_title(f"Faturamento total: R$ {dados['total_faturamento']:.2f}",
                          fontsize=10, pad=8)

            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=self.frm_graf)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

            # Resumo em texto
            tk.Label(self.frm_graf,
                     text=f"Total de pedidos: {dados['total_pedidos']}   |   "
                          f"Faturamento: R$ {dados['total_faturamento']:.2f}",
                     bg=COR_FUNDO, fg=COR_TEXTO, font=self.f_normal).pack(pady=4)

        carregar()


if __name__ == "__main__":
    app = AdminApp()
    app.mainloop()
