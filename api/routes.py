"""
api/routes.py
Rotas FastAPI — categorias, produtos, pedidos, relatórios
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import threading
import shutil
import pathlib
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_db, Categoria, Produto, Pedido, PedidoItem
from services.printer import imprimir_cupom

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────────────

class CategoriaCreate(BaseModel):
    nome: str

class ItemSchema(BaseModel):
    produto_id: int
    quantidade: int

class PedidoCreate(BaseModel):
    itens: list[ItemSchema]
    forma_pagamento: str = "dinheiro"

class PedidoStatusUpdate(BaseModel):
    status: str

class ProdutoCreate(BaseModel):
    nome: str
    descricao: str = ""
    preco: float
    imagem: str = ""
    categoria_id: int | None = None

class ProdutoUpdate(BaseModel):
    nome: str | None = None
    descricao: str | None = None
    preco: float | None = None
    ativo: int | None = None
    categoria_id: int | None = None


# ── Categorias ───────────────────────────────────────────────────────────────

@router.get("/categorias")
def listar_categorias(db: Session = Depends(get_db)):
    cats = db.query(Categoria).order_by(Categoria.nome).all()
    return [{"id": c.id, "nome": c.nome} for c in cats]


@router.post("/categorias")
def criar_categoria(dados: CategoriaCreate, db: Session = Depends(get_db)):
    if db.query(Categoria).filter(Categoria.nome == dados.nome).first():
        raise HTTPException(status_code=400, detail="Categoria já existe")
    c = Categoria(nome=dados.nome)
    db.add(c)
    db.commit()
    return {"id": c.id, "mensagem": "Categoria criada"}


@router.delete("/categorias/{cat_id}")
def deletar_categoria(cat_id: int, db: Session = Depends(get_db)):
    c = db.query(Categoria).filter(Categoria.id == cat_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    if db.query(Produto).filter(Produto.categoria_id == cat_id).count() > 0:
        raise HTTPException(status_code=400, detail="Categoria possui produtos vinculados")
    db.delete(c)
    db.commit()
    return {"mensagem": "Categoria removida"}


# ── Produtos ─────────────────────────────────────────────────────────────────

@router.get("/produtos")
def listar_produtos(db: Session = Depends(get_db)):
    produtos = db.query(Produto).filter(Produto.ativo == 1).all()
    return [_produto_dict(p) for p in produtos]


@router.get("/produtos/admin")
def listar_produtos_admin(db: Session = Depends(get_db)):
    produtos = db.query(Produto).order_by(Produto.id).all()
    return [_produto_dict(p, admin=True) for p in produtos]


@router.post("/produtos")
def criar_produto(dados: ProdutoCreate, db: Session = Depends(get_db)):
    p = Produto(**dados.model_dump())
    db.add(p)
    db.commit()
    return {"id": p.id, "mensagem": "Produto criado"}


@router.post("/produtos/{produto_id}/imagem")
async def upload_imagem_produto(
    produto_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    images_dir = pathlib.Path(__file__).parent.parent / "images"
    images_dir.mkdir(exist_ok=True)

    ext = pathlib.Path(file.filename or "img.jpg").suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        ext = ".jpg"
    filename = f"produto_{produto_id}{ext}"
    dest = images_dir / filename

    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    p = db.query(Produto).filter(Produto.id == produto_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    p.imagem = filename
    db.commit()
    return {"imagem": filename}


@router.put("/produtos/{produto_id}")
def atualizar_produto(produto_id: int, dados: ProdutoUpdate, db: Session = Depends(get_db)):
    p = db.query(Produto).filter(Produto.id == produto_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    for campo, valor in dados.model_dump(exclude_none=True).items():
        setattr(p, campo, valor)
    db.commit()
    return {"mensagem": "Produto atualizado"}


def _produto_dict(p: Produto, admin: bool = False) -> dict:
    d = {
        "id": p.id,
        "nome": p.nome,
        "descricao": p.descricao,
        "preco": p.preco,
        "imagem": p.imagem,
        "categoria": p.categoria.nome if p.categoria else "",
        "categoria_id": p.categoria_id,
    }
    if admin:
        d["ativo"] = p.ativo
    return d


# ── Pedidos ──────────────────────────────────────────────────────────────────

@router.post("/pedidos")
def criar_pedido(dados: PedidoCreate, db: Session = Depends(get_db)):
    total = 0.0
    itens_validados = []

    for item in dados.itens:
        produto = db.query(Produto).filter(
            Produto.id == item.produto_id, Produto.ativo == 1
        ).first()
        if not produto:
            raise HTTPException(status_code=404,
                                detail=f"Produto {item.produto_id} não encontrado")
        total += produto.preco * item.quantidade
        itens_validados.append((produto, item.quantidade, produto.preco))

    pedido = Pedido(
        valor_total=round(total, 2),
        forma_pagamento=dados.forma_pagamento,
    )
    db.add(pedido)
    db.flush()
    pedido.numero = 1000 + pedido.id

    for produto, qtd, preco in itens_validados:
        db.add(PedidoItem(
            pedido_id=pedido.id,
            produto_id=produto.id,
            quantidade=qtd,
            valor=preco,
        ))

    db.commit()

    pedido_dict = _pedido_dict(pedido)
    threading.Thread(target=imprimir_cupom, args=(pedido_dict,), daemon=True).start()

    return {
        "id": pedido.id,
        "numero": pedido.numero,
        "valor_total": pedido.valor_total,
        "mensagem": "Pedido criado com sucesso",
    }


@router.get("/pedidos")
def listar_pedidos(status: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Pedido)
    if status:
        q = q.filter(Pedido.status == status)
    pedidos = q.order_by(Pedido.data_hora.desc()).limit(200).all()
    return [_pedido_dict(p) for p in pedidos]


@router.get("/pedidos/{pedido_id}")
def obter_pedido(pedido_id: int, db: Session = Depends(get_db)):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return _pedido_dict(pedido)


@router.put("/pedidos/{pedido_id}/status")
def atualizar_status(pedido_id: int, dados: PedidoStatusUpdate, db: Session = Depends(get_db)):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    pedido.status = dados.status
    db.commit()
    return {"mensagem": "Status atualizado"}


@router.post("/pedidos/{pedido_id}/reimprimir")
def reimprimir_pedido(pedido_id: int, db: Session = Depends(get_db)):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    threading.Thread(target=imprimir_cupom, args=(_pedido_dict(pedido),), daemon=True).start()
    return {"mensagem": "Reimpressão iniciada"}


def _pedido_dict(p: Pedido) -> dict:
    return {
        "id": p.id,
        "numero": p.numero,
        "status": p.status,
        "valor_total": p.valor_total,
        "data_hora": str(p.data_hora),
        "forma_pagamento": p.forma_pagamento,
        "itens": [
            {"produto": i.produto.nome, "quantidade": i.quantidade, "valor": i.valor}
            for i in p.itens
        ],
    }


# ── Relatórios ────────────────────────────────────────────────────────────────

@router.get("/relatorios/vendas")
def relatorio_vendas(
    data_inicio: str | None = None,
    data_fim: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(PedidoItem).join(Pedido).filter(Pedido.status != "cancelado")
    if data_inicio:
        q = q.filter(Pedido.data_hora >= datetime.fromisoformat(data_inicio))
    if data_fim:
        q = q.filter(Pedido.data_hora <= datetime.fromisoformat(data_fim + "T23:59:59"))

    ranking: dict[str, dict] = {}
    for item in q.all():
        nome = item.produto.nome
        if nome not in ranking:
            ranking[nome] = {"quantidade": 0, "faturamento": 0.0}
        ranking[nome]["quantidade"] += item.quantidade
        ranking[nome]["faturamento"] += item.quantidade * item.valor

    total_geral = sum(v["faturamento"] for v in ranking.values())
    sorted_ranking = sorted(ranking.items(), key=lambda x: x[1]["quantidade"], reverse=True)

    q_pedidos = db.query(Pedido).filter(Pedido.status != "cancelado")
    if data_inicio:
        q_pedidos = q_pedidos.filter(Pedido.data_hora >= datetime.fromisoformat(data_inicio))
    if data_fim:
        q_pedidos = q_pedidos.filter(Pedido.data_hora <= datetime.fromisoformat(data_fim + "T23:59:59"))

    return {
        "total_faturamento": round(total_geral, 2),
        "total_pedidos": q_pedidos.count(),
        "ranking": [{"produto": k, **v} for k, v in sorted_ranking],
    }
