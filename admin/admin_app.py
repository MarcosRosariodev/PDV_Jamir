"""
admin/admin_app.py
Painel Administrativo — CustomTkinter (tema escuro moderno)
"""

import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
from io import BytesIO
import httpx
import threading
import os
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

API_BASE = "http://127.0.0.1:8000"


def _aplicar_estilo_treeview():
    st = ttk.Style()
    st.theme_use("clam")
    st.configure("PDV.Treeview",
        background="#2b2b2b",
        foreground="#DCE4EE",
        rowheight=30,
        fieldbackground="#2b2b2b",
        font=("Segoe UI", 10),
        borderwidth=0,
    )
    st.configure("PDV.Treeview.Heading",
        background="#1f538d",
        foreground="white",
        font=("Segoe UI", 10, "bold"),
        relief="flat",
        padding=(6, 5),
    )
    st.map("PDV.Treeview",
        background=[("selected", "#1f6aa5")],
        foreground=[("selected", "white")],
    )


def api_get(endpoint: str):
    r = httpx.get(f"{API_BASE}{endpoint}", timeout=10)
    r.raise_for_status()
    return r.json()


def api_post(endpoint: str, payload: dict):
    r = httpx.post(f"{API_BASE}{endpoint}", json=payload, timeout=10)
    r.raise_for_status()
    return r.json()


def api_put(endpoint: str, payload: dict):
    r = httpx.put(f"{API_BASE}{endpoint}", json=payload, timeout=10)
    r.raise_for_status()
    return r.json()


def api_delete(endpoint: str):
    r = httpx.delete(f"{API_BASE}{endpoint}", timeout=10)
    r.raise_for_status()
    return r.json()


class AdminApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PDV Jamir — Painel Administrativo")
        self.geometry("1360x780")
        self.minsize(1100, 660)

        _aplicar_estilo_treeview()
        self._build_layout()
        self._nav("dashboard")

    # ── Layout base ───────────────────────────────────────────────────────────

    def _build_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ---- Sidebar ----
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(8, weight=1)

        ctk.CTkLabel(
            self.sidebar, text="🍦 Jamir Admin",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(28, 20), sticky="w")

        nav_items = [
            ("dashboard",  "  📊  Dashboard"),
            ("pedidos",    "  📋  Pedidos"),
            ("produtos",   "  🍦  Produtos"),
            ("categorias", "  🏷️  Categorias"),
            ("relatorios", "  📈  Relatórios"),
        ]
        self._nav_btns: dict[str, ctk.CTkButton] = {}
        for row, (key, label) in enumerate(nav_items, start=1):
            btn = ctk.CTkButton(
                self.sidebar, text=label, anchor="w",
                height=44, corner_radius=8,
                fg_color="transparent",
                hover_color=("gray75", "gray25"),
                font=ctk.CTkFont(size=13),
                command=lambda k=key: self._nav(k),
            )
            btn.grid(row=row, column=0, padx=12, pady=3, sticky="ew")
            self._nav_btns[key] = btn

        # Tema toggle
        def toggle_tema():
            novo = "Light" if ctk.get_appearance_mode() == "Dark" else "Dark"
            ctk.set_appearance_mode(novo)
            lbl_tema.configure(text="🌙 Escuro" if novo == "Dark" else "☀️ Claro")

        lbl_tema = ctk.CTkButton(
            self.sidebar, text="☀️ Claro", anchor="w",
            height=36, corner_radius=8, fg_color="transparent",
            hover_color=("gray75", "gray25"),
            font=ctk.CTkFont(size=11),
            command=toggle_tema,
        )
        lbl_tema.grid(row=9, column=0, padx=12, pady=4, sticky="ew")

        ctk.CTkLabel(
            self.sidebar, text="v2.0.0", text_color="gray50",
            font=ctk.CTkFont(size=10),
        ).grid(row=10, column=0, padx=20, pady=(4, 16), sticky="sw")

        # ---- Área principal ----
        self.main = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray93", "gray13"))
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)

    def _nav(self, key: str):
        for k, b in self._nav_btns.items():
            b.configure(fg_color=("gray75", "gray25") if k == key else "transparent")
        for w in self.main.winfo_children():
            w.destroy()
        self.main.grid_rowconfigure(1, weight=1)
        {
            "dashboard":  self._view_dashboard,
            "pedidos":    self._view_pedidos,
            "produtos":   self._view_produtos,
            "categorias": self._view_categorias,
            "relatorios": self._view_relatorios,
        }[key]()

    def _titulo(self, texto: str):
        ctk.CTkLabel(
            self.main, text=texto,
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, padx=24, pady=(20, 6), sticky="w")

    def _card_metrica(self, parent, titulo: str, valor: str, cor: str) -> ctk.CTkFrame:
        card = ctk.CTkFrame(parent, corner_radius=12)
        ctk.CTkLabel(card, text=titulo, text_color="gray60",
                     font=ctk.CTkFont(size=11)).pack(anchor="w", padx=18, pady=(16, 2))
        ctk.CTkLabel(card, text=valor, text_color=cor,
                     font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", padx=18, pady=(0, 16))
        return card

    def _tree_frame(self, cols_config: list[tuple]) -> tuple[ctk.CTkFrame, ttk.Treeview]:
        """Cria um CTkFrame com Treeview + scrollbar estilizados."""
        frm = ctk.CTkFrame(self.main, corner_radius=10)
        cols = [c[0] for c in cols_config]
        tree = ttk.Treeview(frm, columns=cols, show="headings", style="PDV.Treeview")
        for col, lbl, width, anchor in cols_config:
            tree.heading(col, text=lbl)
            tree.column(col, width=width, anchor=anchor)
        vsb = ttk.Scrollbar(frm, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y", padx=(0, 4), pady=4)
        tree.pack(fill="both", expand=True, padx=4, pady=4)
        return frm, tree

    # ── Dashboard ─────────────────────────────────────────────────────────────

    def _view_dashboard(self):
        self._titulo("Dashboard")
        scroll = ctk.CTkScrollableFrame(self.main, fg_color="transparent")
        scroll.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        scroll.grid_columnconfigure((0, 1, 2), weight=1)

        def carregar():
            try:
                vendas  = api_get("/relatorios/vendas")
                pedidos = api_get("/pedidos?status=pendente")
                self.after(0, lambda: montar(vendas, pedidos))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Erro", str(e)))

        def montar(vendas, pedidos):
            metricas = [
                ("Faturamento Total",  f"R$ {vendas['total_faturamento']:.2f}", "#4CAF50"),
                ("Total de Pedidos",   str(vendas["total_pedidos"]),             "#2196F3"),
                ("Pedidos Pendentes",  str(len(pedidos)),                        "#FF9800"),
            ]
            for col, (t, v, c) in enumerate(metricas):
                self._card_metrica(scroll, t, v, c).grid(
                    row=0, column=col, padx=8, pady=8, sticky="ew", ipady=4)

            sep = ctk.CTkFrame(scroll, height=2, fg_color=("gray80", "gray28"))
            sep.grid(row=1, column=0, columnspan=3, padx=8, pady=(20, 8), sticky="ew")

            ctk.CTkLabel(scroll, text="Pedidos Pendentes",
                         font=ctk.CTkFont(size=14, weight="bold"),
                         ).grid(row=2, column=0, columnspan=3, padx=8, pady=(4, 6), sticky="w")

            if not pedidos:
                ctk.CTkLabel(scroll, text="Nenhum pedido pendente no momento.",
                             text_color="gray55", font=ctk.CTkFont(size=12),
                             ).grid(row=3, column=0, columnspan=3, padx=8, pady=8, sticky="w")
                return

            for idx, p in enumerate(pedidos[:10]):
                row_frm = ctk.CTkFrame(scroll, corner_radius=8)
                row_frm.grid(row=3 + idx, column=0, columnspan=3,
                             padx=8, pady=3, sticky="ew")
                row_frm.grid_columnconfigure(1, weight=1)

                ctk.CTkLabel(row_frm, text=f"#{p['numero']}",
                             font=ctk.CTkFont(size=13, weight="bold"),
                             width=70).grid(row=0, column=0, padx=14, pady=10)

                itens_str = ", ".join(
                    f"{i['quantidade']}x {i['produto']}" for i in p["itens"])
                ctk.CTkLabel(row_frm, text=itens_str, text_color="gray65",
                             anchor="w").grid(row=0, column=1, padx=4, pady=10, sticky="w")

                ctk.CTkLabel(row_frm,
                             text=f"R$ {p['valor_total']:.2f}",
                             font=ctk.CTkFont(weight="bold"),
                             text_color="#4CAF50",
                             ).grid(row=0, column=2, padx=14, pady=10)

        threading.Thread(target=carregar, daemon=True).start()

    # ── Pedidos ──────────────────────────────────────────────────────────────

    def _view_pedidos(self):
        self._titulo("Pedidos")
        self.main.grid_rowconfigure(2, weight=1)
        self.main.grid_rowconfigure(3, weight=0)

        # Filtros
        frm_f = ctk.CTkFrame(self.main, fg_color="transparent")
        frm_f.grid(row=1, column=0, padx=24, pady=(0, 4), sticky="nw")
        var_status = ctk.StringVar(value="")
        for lbl, val in [("Todos", ""), ("Pendentes", "pendente"),
                          ("Prontos", "pronto"), ("Cancelados", "cancelado")]:
            ctk.CTkRadioButton(frm_f, text=lbl, variable=var_status, value=val,
                               command=lambda: carregar(),
                               ).pack(side="left", padx=10)

        # Treeview
        _id_por_numero: dict[int, int] = {}
        cols_cfg = [
            ("numero",     "#",          65,  "center"),
            ("data_hora",  "Data/Hora",  150, "center"),
            ("status",     "Status",     100, "center"),
            ("valor_total","Total",       90, "center"),
            ("pagamento",  "Pagamento",  100, "center"),
            ("itens",      "Itens",      440, "w"),
        ]
        frm_tree, tree = self._tree_frame(cols_cfg)
        frm_tree.grid(row=2, column=0, padx=24, pady=4, sticky="nsew")

        # Botões de ação
        frm_act = ctk.CTkFrame(self.main, fg_color="transparent")
        frm_act.grid(row=3, column=0, padx=24, pady=(4, 16), sticky="w")

        def _num_selecionado() -> int | None:
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Aviso", "Selecione um pedido.")
                return None
            return int(tree.item(sel[0])["values"][0])

        def mudar_status(novo: str):
            num = _num_selecionado()
            if num is None:
                return
            pid = _id_por_numero[num]
            def _put():
                try:
                    api_put(f"/pedidos/{pid}/status", {"status": novo})
                    self.after(0, carregar)
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Erro", str(e)))
            threading.Thread(target=_put, daemon=True).start()

        def reimprimir():
            num = _num_selecionado()
            if num is None:
                return
            pid = _id_por_numero[num]
            def _post():
                try:
                    api_post(f"/pedidos/{pid}/reimprimir", {})
                    self.after(0, lambda: messagebox.showinfo("Impressão", f"Reimprimindo #{num}..."))
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Erro", str(e)))
            threading.Thread(target=_post, daemon=True).start()

        acoes = [
            ("✔  Pronto",       "#2E7D32", "#1B5E20", lambda: mudar_status("pronto")),
            ("✖  Cancelar",     "#C62828", "#B71C1C", lambda: mudar_status("cancelado")),
            ("🖨  Reimprimir",  "#455A64", "#37474F", reimprimir),
            ("↻  Atualizar",    None,      None,      lambda: carregar()),
        ]
        for txt, fg, hover, cmd in acoes:
            kw: dict = {}
            if fg:
                kw = {"fg_color": fg, "hover_color": hover}
            ctk.CTkButton(frm_act, text=txt, width=130, height=36,
                          corner_radius=8, command=cmd, **kw,
                          ).pack(side="left", padx=5)

        def preencher(pedidos: list):
            _id_por_numero.clear()
            tree.delete(*tree.get_children())
            for p in pedidos:
                _id_por_numero[p["numero"]] = p["id"]
                itens_str = ", ".join(
                    f"{i['quantidade']}x {i['produto']}" for i in p["itens"])
                tag = p["status"]
                tree.insert("", "end", values=(
                    p["numero"], p["data_hora"][:16], p["status"],
                    f"R$ {p['valor_total']:.2f}", p["forma_pagamento"], itens_str,
                ), tags=(tag,))
            tree.tag_configure("pendente",  foreground="#FF9800")
            tree.tag_configure("pronto",    foreground="#4CAF50")
            tree.tag_configure("cancelado", foreground="#EF5350")

        def carregar():
            st = var_status.get()
            url = "/pedidos" + (f"?status={st}" if st else "")
            def _get():
                try:
                    dados = api_get(url)
                    self.after(0, lambda: preencher(dados))
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Erro", str(e)))
            threading.Thread(target=_get, daemon=True).start()

        carregar()

    # ── Produtos ─────────────────────────────────────────────────────────────

    def _view_produtos(self):
        self._titulo("Produtos")
        self.main.grid_rowconfigure(2, weight=1)
        self.main.grid_rowconfigure(3, weight=0)

        frm_top = ctk.CTkFrame(self.main, fg_color="transparent")
        frm_top.grid(row=1, column=0, padx=24, pady=(0, 4), sticky="nw")
        ctk.CTkButton(frm_top, text="+ Novo Produto", width=140, height=36,
                      corner_radius=8, command=self._dlg_novo_produto,
                      ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(frm_top, text="↻ Atualizar", width=110, height=36,
                      corner_radius=8, fg_color="gray40", hover_color="gray30",
                      command=self._view_produtos,
                      ).pack(side="left")

        cols_cfg = [
            ("id",        "ID",        55,  "center"),
            ("nome",      "Nome",      220, "w"),
            ("categoria", "Categoria", 140, "w"),
            ("preco",     "Preço",     95,  "center"),
            ("ativo",     "Ativo",     70,  "center"),
        ]
        frm_tree, tree = self._tree_frame(cols_cfg)
        frm_tree.grid(row=2, column=0, padx=24, pady=4, sticky="nsew")

        # Edição rápida
        frm_edit = ctk.CTkFrame(self.main, corner_radius=10)
        frm_edit.grid(row=3, column=0, padx=24, pady=(4, 16), sticky="ew")
        frm_edit.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(frm_edit, text="Edição rápida:",
                     text_color="gray55", font=ctk.CTkFont(size=11),
                     ).grid(row=0, column=0, padx=16, pady=14, sticky="w")

        var_preco = ctk.StringVar()
        ctk.CTkLabel(frm_edit, text="Novo preço R$:"
                     ).grid(row=0, column=1, padx=(20, 4), pady=14, sticky="e")
        ctk.CTkEntry(frm_edit, textvariable=var_preco, width=100, height=34,
                     ).grid(row=0, column=2, padx=4, pady=14)

        def salvar_preco():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Aviso", "Selecione um produto.")
                return
            pid = int(tree.item(sel[0])["values"][0])
            raw = var_preco.get().strip()
            if not raw:
                return
            try:
                preco = float(raw.replace(",", "."))
            except ValueError:
                messagebox.showerror("Erro", "Preço inválido.")
                return
            def _put():
                try:
                    api_put(f"/produtos/{pid}", {"preco": preco})
                    self.after(0, self._view_produtos)
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Erro", str(e)))
            threading.Thread(target=_put, daemon=True).start()

        def toggle_ativo():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Aviso", "Selecione um produto.")
                return
            vals = tree.item(sel[0])["values"]
            pid = int(vals[0])
            ativo_atual = vals[4] == "Sim"
            def _put():
                try:
                    api_put(f"/produtos/{pid}", {"ativo": 0 if ativo_atual else 1})
                    self.after(0, self._view_produtos)
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Erro", str(e)))
            threading.Thread(target=_put, daemon=True).start()

        def alterar_foto():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Aviso", "Selecione um produto.")
                return
            pid = int(tree.item(sel[0])["values"][0])
            self.update()
            path = filedialog.askopenfilename(
                title="Selecionar nova foto",
                filetypes=[("Imagens", "*.jpg *.jpeg *.png *.webp"), ("Todos", "*.*")],
            )
            if not path:
                return
            def _upload():
                try:
                    with open(path, "rb") as f:
                        httpx.post(
                            f"{API_BASE}/produtos/{pid}/imagem",
                            files={"file": (os.path.basename(path), f)},
                            timeout=15,
                        )
                    self.after(0, lambda: messagebox.showinfo("OK", "Foto atualizada!"))
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Erro", str(e)))
            threading.Thread(target=_upload, daemon=True).start()

        ctk.CTkButton(frm_edit, text="Salvar Preço", width=120, height=34,
                      corner_radius=8, command=salvar_preco,
                      ).grid(row=0, column=3, padx=10, pady=14)
        ctk.CTkButton(frm_edit, text="Ativar / Desativar", width=150, height=34,
                      corner_radius=8, fg_color="#607D8B", hover_color="#546E7A",
                      command=toggle_ativo,
                      ).grid(row=0, column=4, padx=(0, 8), pady=14)
        ctk.CTkButton(frm_edit, text="📷 Alterar Foto", width=130, height=34,
                      corner_radius=8, fg_color="#37474F", hover_color="#263238",
                      command=alterar_foto,
                      ).grid(row=0, column=5, padx=(0, 16), pady=14)

        def preencher(prods: list):
            tree.delete(*tree.get_children())
            for p in prods:
                tag = "ativo" if p["ativo"] else "inativo"
                tree.insert("", "end", values=(
                    p["id"], p["nome"], p.get("categoria", ""),
                    f"R$ {p['preco']:.2f}", "Sim" if p["ativo"] else "Não",
                ), tags=(tag,))
            tree.tag_configure("inativo", foreground="#888888")

        def carregar():
            def _get():
                try:
                    prods = api_get("/produtos/admin")
                    self.after(0, lambda: preencher(prods))
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Erro", str(e)))
            threading.Thread(target=_get, daemon=True).start()

        carregar()

    def _dlg_novo_produto(self):
        try:
            cats = api_get("/categorias")
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            return

        dlg = ctk.CTkToplevel(self)
        dlg.title("Novo Produto")
        dlg.geometry("560x460")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.after(100, dlg.lift)
        dlg.grid_columnconfigure(1, weight=1)

        # ── Campos de texto ──
        campos = [
            ("Nome *",    ctk.StringVar()),
            ("Descrição", ctk.StringVar()),
            ("Preço *",   ctk.StringVar()),
        ]
        for i, (lbl, var) in enumerate(campos):
            ctk.CTkLabel(dlg, text=lbl).grid(row=i, column=0, padx=20, pady=8, sticky="e")
            ctk.CTkEntry(dlg, textvariable=var, width=260, height=34,
                         ).grid(row=i, column=1, padx=20, pady=8, sticky="w")

        ctk.CTkLabel(dlg, text="Categoria").grid(row=3, column=0, padx=20, pady=8, sticky="e")
        var_cat  = ctk.StringVar()
        cat_nomes = [c["nome"] for c in cats]
        cat_ids   = {c["nome"]: c["id"] for c in cats}
        if cat_nomes:
            var_cat.set(cat_nomes[0])
        ctk.CTkComboBox(dlg, variable=var_cat, values=cat_nomes, state="readonly", width=260,
                        ).grid(row=3, column=1, padx=20, pady=8, sticky="w")

        # ── Seção de foto ──
        sep = ctk.CTkFrame(dlg, height=2, fg_color=("gray80", "gray28"))
        sep.grid(row=4, column=0, columnspan=2, padx=20, pady=(12, 4), sticky="ew")

        ctk.CTkLabel(dlg, text="Foto do produto:", font=ctk.CTkFont(size=12, weight="bold"),
                     ).grid(row=5, column=0, columnspan=2, padx=20, pady=(4, 8), sticky="w")

        frm_foto = ctk.CTkFrame(dlg, corner_radius=8)
        frm_foto.grid(row=6, column=0, columnspan=2, padx=20, pady=(0, 8), sticky="ew")
        frm_foto.grid_columnconfigure(1, weight=1)

        # Preview 110×110
        preview_frm = ctk.CTkFrame(frm_foto, width=110, height=110, corner_radius=8,
                                   fg_color=("gray85", "gray25"))
        preview_frm.grid(row=0, column=0, padx=12, pady=12)
        preview_frm.grid_propagate(False)
        preview_lbl = ctk.CTkLabel(preview_frm, text="Sem\nfoto", text_color="gray55",
                                   font=ctk.CTkFont(size=11))
        preview_lbl.place(relx=0.5, rely=0.5, anchor="center")

        var_img_path: dict[str, str | None] = {"path": None}
        lbl_nome_img = ctk.CTkLabel(frm_foto, text="Nenhuma imagem selecionada",
                                    text_color="gray55", font=ctk.CTkFont(size=11), anchor="w")
        lbl_nome_img.grid(row=0, column=1, padx=8, pady=(12, 4), sticky="w")

        def escolher_foto():
            dlg.update()
            path = filedialog.askopenfilename(
                parent=dlg,
                title="Selecionar foto do produto",
                filetypes=[("Imagens", "*.jpg *.jpeg *.png *.webp"), ("Todos", "*.*")],
            )
            if not path:
                return
            var_img_path["path"] = path
            lbl_nome_img.configure(text=os.path.basename(path), text_color=("gray20", "gray90"))
            try:
                pil = Image.open(path).resize((110, 110), Image.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=pil, dark_image=pil, size=(110, 110))
                preview_lbl.configure(image=ctk_img, text="")
                preview_lbl._ctk_image = ctk_img  # evita garbage collect
            except Exception:
                pass

        ctk.CTkButton(frm_foto, text="📷  Escolher Foto", width=150, height=34,
                      corner_radius=8, fg_color="gray40", hover_color="gray30",
                      command=escolher_foto,
                      ).grid(row=0, column=1, padx=8, pady=(40, 12), sticky="w")

        # ── Salvar ──
        def salvar():
            nome    = campos[0][1].get().strip()
            desc    = campos[1][1].get().strip()
            preco_s = campos[2][1].get().strip()
            if not nome or not preco_s:
                messagebox.showwarning("Aviso", "Nome e preço são obrigatórios.", parent=dlg)
                return
            try:
                preco = float(preco_s.replace(",", "."))
            except ValueError:
                messagebox.showerror("Erro", "Preço inválido.", parent=dlg)
                return

            payload = {
                "nome": nome, "descricao": desc, "preco": preco,
                "categoria_id": cat_ids.get(var_cat.get()),
            }

            def _post():
                try:
                    result = api_post("/produtos", payload)
                    produto_id = result["id"]

                    img_path = var_img_path["path"]
                    if img_path and os.path.exists(img_path):
                        with open(img_path, "rb") as f:
                            httpx.post(
                                f"{API_BASE}/produtos/{produto_id}/imagem",
                                files={"file": (os.path.basename(img_path), f)},
                                timeout=15,
                            )

                    self.after(0, dlg.destroy)
                    self.after(0, self._view_produtos)
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Erro", str(e)))

            threading.Thread(target=_post, daemon=True).start()

        ctk.CTkButton(dlg, text="Salvar Produto", height=40, corner_radius=8,
                      command=salvar,
                      ).grid(row=7, column=0, columnspan=2, padx=20, pady=16, sticky="e")

    # ── Categorias ───────────────────────────────────────────────────────────

    def _view_categorias(self):
        self._titulo("Categorias")
        self.main.grid_rowconfigure(2, weight=1)
        self.main.grid_rowconfigure(3, weight=0)

        frm_top = ctk.CTkFrame(self.main, fg_color="transparent")
        frm_top.grid(row=1, column=0, padx=24, pady=(0, 4), sticky="nw")

        var_nova = ctk.StringVar()
        ctk.CTkLabel(frm_top, text="Nova categoria:").pack(side="left", padx=(0, 8))
        ctk.CTkEntry(frm_top, textvariable=var_nova, width=220, height=36,
                     ).pack(side="left", padx=(0, 8))

        cols_cfg = [
            ("id",   "ID",   70,  "center"),
            ("nome", "Nome", 460, "w"),
        ]
        frm_tree, tree = self._tree_frame(cols_cfg)
        frm_tree.grid(row=2, column=0, padx=24, pady=4, sticky="nsew")

        def adicionar():
            nome = var_nova.get().strip()
            if not nome:
                return
            def _post():
                try:
                    api_post("/categorias", {"nome": nome})
                    var_nova.set("")
                    self.after(0, carregar)
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Erro", str(e)))
            threading.Thread(target=_post, daemon=True).start()

        def remover():
            sel = tree.selection()
            if not sel:
                return
            cat_id = int(tree.item(sel[0])["values"][0])
            nome   = tree.item(sel[0])["values"][1]
            if not messagebox.askyesno("Confirmar", f"Remover a categoria '{nome}'?"):
                return
            def _del():
                try:
                    api_delete(f"/categorias/{cat_id}")
                    self.after(0, carregar)
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Erro", str(e)))
            threading.Thread(target=_del, daemon=True).start()

        ctk.CTkButton(frm_top, text="Adicionar", width=110, height=36,
                      corner_radius=8, command=adicionar,
                      ).pack(side="left")

        frm_bot = ctk.CTkFrame(self.main, fg_color="transparent")
        frm_bot.grid(row=3, column=0, padx=24, pady=(4, 16), sticky="w")
        ctk.CTkButton(frm_bot, text="Remover Selecionada", width=180, height=36,
                      corner_radius=8, fg_color="#C62828", hover_color="#B71C1C",
                      command=remover,
                      ).pack(side="left")

        def preencher(cats: list):
            tree.delete(*tree.get_children())
            for c in cats:
                tree.insert("", "end", values=(c["id"], c["nome"]))

        def carregar():
            def _get():
                try:
                    cats = api_get("/categorias")
                    self.after(0, lambda: preencher(cats))
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Erro", str(e)))
            threading.Thread(target=_get, daemon=True).start()

        carregar()

    # ── Relatórios ────────────────────────────────────────────────────────────

    def _view_relatorios(self):
        self._titulo("Relatórios de Vendas")
        self.main.grid_rowconfigure(2, weight=1)

        frm_f = ctk.CTkFrame(self.main, fg_color="transparent")
        frm_f.grid(row=1, column=0, padx=24, pady=(0, 4), sticky="nw")

        hoje = datetime.now()
        periodos = [
            ("Hoje",    hoje.strftime("%Y-%m-%d"),              hoje.strftime("%Y-%m-%d")),
            ("7 dias",  (hoje - timedelta(days=7)).strftime("%Y-%m-%d"), hoje.strftime("%Y-%m-%d")),
            ("30 dias", (hoje - timedelta(days=30)).strftime("%Y-%m-%d"), hoje.strftime("%Y-%m-%d")),
            ("Tudo",    "", ""),
        ]
        for lbl, ini, fim in periodos:
            ctk.CTkButton(frm_f, text=lbl, width=82, height=34, corner_radius=8,
                          fg_color="gray40", hover_color="gray30",
                          command=lambda i=ini, f=fim: carregar(i, f),
                          ).pack(side="left", padx=4)

        self.frm_graf = ctk.CTkFrame(self.main, corner_radius=10)
        self.frm_graf.grid(row=2, column=0, padx=24, pady=(4, 16), sticky="nsew")

        def carregar(ini: str = "", fim: str = ""):
            params = []
            if ini:
                params.append(f"data_inicio={ini}")
            if fim:
                params.append(f"data_fim={fim}")
            url = "/relatorios/vendas" + (("?" + "&".join(params)) if params else "")
            def _get():
                try:
                    dados = api_get(url)
                    self.after(0, lambda: renderizar(dados))
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Erro", str(e)))
            threading.Thread(target=_get, daemon=True).start()

        def renderizar(dados: dict):
            for w in self.frm_graf.winfo_children():
                w.destroy()

            ranking = dados["ranking"]
            if not ranking:
                ctk.CTkLabel(self.frm_graf, text="Nenhum dado no período selecionado.",
                             text_color="gray55", font=ctk.CTkFont(size=13),
                             ).pack(pady=60)
                return

            is_dark   = ctk.get_appearance_mode() == "Dark"
            bg_fig    = "#1e1e1e" if is_dark else "#f0f0f0"
            txt_color = "#DCE4EE" if is_dark else "#1A1A1A"

            nomes = [r["produto"]     for r in ranking[:10]]
            qtds  = [r["quantidade"]  for r in ranking[:10]]
            fats  = [r["faturamento"] for r in ranking[:10]]
            cores = plt.cm.tab10.colors

            fig = Figure(figsize=(10, 4.8), dpi=96, facecolor=bg_fig)
            ax1 = fig.add_subplot(1, 2, 1)
            ax2 = fig.add_subplot(1, 2, 2)
            ax1.set_facecolor(bg_fig)
            ax2.set_facecolor(bg_fig)

            bars = ax1.barh(nomes[::-1], qtds[::-1],
                            color=[cores[i % 10] for i in range(len(nomes))])
            ax1.set_title("Mais vendidos (unidades)", fontsize=10, pad=8, color=txt_color)
            ax1.tick_params(labelsize=8, colors=txt_color)
            for sp in ax1.spines.values():
                sp.set_color("gray40")
            for bar, val in zip(bars, qtds[::-1]):
                ax1.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2,
                         str(val), va="center", fontsize=8, color=txt_color)

            ax2.pie(fats, labels=nomes, autopct="%1.1f%%",
                    colors=[cores[i % 10] for i in range(len(nomes))],
                    textprops={"fontsize": 8, "color": txt_color})
            ax2.set_title(f"Faturamento — R$ {dados['total_faturamento']:.2f}",
                          fontsize=10, pad=8, color=txt_color)
            fig.tight_layout(pad=1.5)

            canvas = FigureCanvasTkAgg(fig, master=self.frm_graf)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=4, pady=4)

            ctk.CTkLabel(self.frm_graf,
                         text=f"Total: {dados['total_pedidos']} pedidos   |   "
                              f"Faturamento: R$ {dados['total_faturamento']:.2f}",
                         font=ctk.CTkFont(size=12),
                         ).pack(pady=6)

        carregar()


if __name__ == "__main__":
    app = AdminApp()
    app.mainloop()
