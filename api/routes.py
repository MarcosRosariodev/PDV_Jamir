"""
api/routes.py
Rotas FastAPI — pedidos, produtos, estoque
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_db, Produto, Estoque, Pedido, ItemPedido

router = APIRouter()


# ── Schemas Pydantic ────────────────────────────────────────────────────────

class ItemSchema(BaseModel):
    produto_id: int
    quantidade: int

class PedidoCreate(BaseModel):
    itens: List[ItemSchema]
    forma_pagto: str = "dinheiro"
    observacao: str = ""

class PedidoStatusUpdate(BaseModel):
    status: str

class ProdutoCreate(BaseModel):
    nome: str
    descricao: str = ""
    preco: float
    categoria: str = "Sorvete"
    imagem: str = ""

class EstoqueUpdate(BaseModel):
    quantidade: int

class ProdutoUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    preco: Optional[float] = None
    ativo: Optional[int] = None
    quantidade_estoque: Optional[int] = None


# ── Produtos ────────────────────────────────────────────────────────────────

@router.get("/produtos")
def listar_produtos(db: Session = Depends(get_db)):
    produtos = db.query(Produto).filter(Produto.ativo == 1).all()
    result = []
    for p in produtos:
        est = p.estoque.quantidade if p.estoque else 0
        result.append({
            "id": p.id, "nome": p.nome, "descricao": p.descricao,
            "preco": p.preco, "categoria": p.categoria,
            "imagem": p.imagem, "estoque": est
        })
    return result


@router.get("/produtos/admin")
def listar_produtos_admin(db: Session = Depends(get_db)):
    """Retorna todos os produtos incluindo inativos (para o admin)."""
    produtos = db.query(Produto).all()
    result = []
    for p in produtos:
        est = p.estoque.quantidade if p.estoque else 0
        minimo = p.estoque.minimo if p.estoque else 5
        result.append({
            "id": p.id, "nome": p.nome, "descricao": p.descricao,
            "preco": p.preco, "categoria": p.categoria,
            "ativo": p.ativo, "estoque": est, "minimo": minimo
        })
    return result


@router.post("/produtos")
def criar_produto(dados: ProdutoCreate, db: Session = Depends(get_db)):
    p = Produto(**dados.model_dump())
    db.add(p)
    db.flush()
    db.add(Estoque(produto_id=p.id, quantidade=0))
    db.commit()
    return {"id": p.id, "mensagem": "Produto criado"}


@router.put("/produtos/{produto_id}")
def atualizar_produto(produto_id: int, dados: ProdutoUpdate, db: Session = Depends(get_db)):
    p = db.query(Produto).filter(Produto.id == produto_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    if dados.nome is not None:      p.nome = dados.nome
    if dados.descricao is not None: p.descricao = dados.descricao
    if dados.preco is not None:     p.preco = dados.preco
    if dados.ativo is not None:     p.ativo = dados.ativo
    if dados.quantidade_estoque is not None and p.estoque:
        p.estoque.quantidade = dados.quantidade_estoque
        p.estoque.atualizado = datetime.now()
    db.commit()
    return {"mensagem": "Produto atualizado"}


# ── Pedidos ─────────────────────────────────────────────────────────────────

@router.post("/pedidos")
def criar_pedido(dados: PedidoCreate, db: Session = Depends(get_db)):
    total = 0.0
    itens_validados = []

    for item in dados.itens:
        produto = db.query(Produto).filter(Produto.id == item.produto_id).first()
        if not produto:
            raise HTTPException(status_code=404, detail=f"Produto {item.produto_id} não encontrado")

        estoque = db.query(Estoque).filter(Estoque.produto_id == item.produto_id).first()
        if not estoque or estoque.quantidade < item.quantidade:
            raise HTTPException(status_code=400, detail=f"Estoque insuficiente: {produto.nome}")

        subtotal = produto.preco * item.quantidade
        total += subtotal
        itens_validados.append((produto, estoque, item.quantidade, produto.preco))

    pedido = Pedido(total=total, forma_pagto=dados.forma_pagto, observacao=dados.observacao)
    db.add(pedido)
    db.flush()

    for produto, estoque, qtd, preco in itens_validados:
        db.add(ItemPedido(pedido_id=pedido.id, produto_id=produto.id,
                          quantidade=qtd, preco_unit=preco))
        estoque.quantidade -= qtd

    db.commit()
    return {"id": pedido.id, "total": total, "mensagem": "Pedido criado com sucesso"}


@router.get("/pedidos")
def listar_pedidos(status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Pedido)
    if status:
        q = q.filter(Pedido.status == status)
    pedidos = q.order_by(Pedido.criado_em.desc()).limit(100).all()
    result = []
    for p in pedidos:
        itens = [{"produto": i.produto.nome, "qtd": i.quantidade, "preco": i.preco_unit}
                 for i in p.itens]
        result.append({
            "id": p.id, "status": p.status, "total": p.total,
            "forma_pagto": p.forma_pagto, "criado_em": str(p.criado_em),
            "observacao": p.observacao, "itens": itens
        })
    return result


@router.put("/pedidos/{pedido_id}/status")
def atualizar_status(pedido_id: int, dados: PedidoStatusUpdate, db: Session = Depends(get_db)):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    pedido.status = dados.status
    db.commit()
    return {"mensagem": "Status atualizado"}


# ── Relatórios ───────────────────────────────────────────────────────────────

@router.get("/relatorios/vendas")
def relatorio_vendas(data_inicio: Optional[str] = None, data_fim: Optional[str] = None,
                     db: Session = Depends(get_db)):
    """Faturamento e ranking de produtos mais vendidos."""
    q = db.query(ItemPedido).join(Pedido).filter(Pedido.status != "cancelado")

    if data_inicio:
        q = q.filter(Pedido.criado_em >= datetime.fromisoformat(data_inicio))
    if data_fim:
        q = q.filter(Pedido.criado_em <= datetime.fromisoformat(data_fim + "T23:59:59"))

    itens = q.all()
    ranking = {}
    for item in itens:
        nome = item.produto.nome
        if nome not in ranking:
            ranking[nome] = {"quantidade": 0, "faturamento": 0.0}
        ranking[nome]["quantidade"] += item.quantidade
        ranking[nome]["faturamento"] += item.quantidade * item.preco_unit

    total_geral = sum(v["faturamento"] for v in ranking.values())
    sorted_ranking = sorted(ranking.items(), key=lambda x: x[1]["quantidade"], reverse=True)

    return {
        "total_faturamento": round(total_geral, 2),
        "total_pedidos": db.query(Pedido).filter(Pedido.status != "cancelado").count(),
        "ranking": [{"produto": k, **v} for k, v in sorted_ranking]
    }


@router.get("/estoque/alertas")
def alertas_estoque(db: Session = Depends(get_db)):
    """Retorna produtos com estoque abaixo do mínimo."""
    from sqlalchemy import text
    baixo = db.query(Estoque).join(Produto).filter(
        Estoque.quantidade <= Estoque.minimo,
        Produto.ativo == 1
    ).all()
    return [{"produto": e.produto.nome, "atual": e.quantidade, "minimo": e.minimo}
            for e in baixo]
