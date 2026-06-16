"""
database/db.py
Configuração do banco SQLite e modelos SQLAlchemy
"""

from sqlalchemy import (
    create_engine, Column, Integer, String,
    Float, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'pdv_jamir.db')}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


# ── Modelos ─────────────────────────────────────────────────────────────────

class Produto(Base):
    __tablename__ = "produtos"

    id          = Column(Integer, primary_key=True, index=True)
    nome        = Column(String(100), nullable=False)
    descricao   = Column(Text, default="")
    preco       = Column(Float, nullable=False)
    categoria   = Column(String(50), default="Sorvete")
    imagem      = Column(String(200), default="")   # caminho relativo em ui/assets/
    ativo       = Column(Integer, default=1)         # 1=ativo, 0=inativo
    criado_em   = Column(DateTime, default=datetime.now)

    estoque     = relationship("Estoque", back_populates="produto", uselist=False)
    itens       = relationship("ItemPedido", back_populates="produto")


class Estoque(Base):
    __tablename__ = "estoque"

    id          = Column(Integer, primary_key=True)
    produto_id  = Column(Integer, ForeignKey("produtos.id"), unique=True)
    quantidade  = Column(Integer, default=0)
    minimo      = Column(Integer, default=5)         # alerta de estoque baixo
    atualizado  = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    produto     = relationship("Produto", back_populates="estoque")


class Pedido(Base):
    __tablename__ = "pedidos"

    id            = Column(Integer, primary_key=True)
    status        = Column(String(20), default="pendente")  # pendente | pronto | cancelado
    total         = Column(Float, default=0.0)
    forma_pagto   = Column(String(30), default="dinheiro")
    criado_em     = Column(DateTime, default=datetime.now)
    observacao    = Column(Text, default="")

    itens         = relationship("ItemPedido", back_populates="pedido")


class ItemPedido(Base):
    __tablename__ = "itens_pedido"

    id          = Column(Integer, primary_key=True)
    pedido_id   = Column(Integer, ForeignKey("pedidos.id"))
    produto_id  = Column(Integer, ForeignKey("produtos.id"))
    quantidade  = Column(Integer, default=1)
    preco_unit  = Column(Float, nullable=False)

    pedido      = relationship("Pedido", back_populates="itens")
    produto     = relationship("Produto", back_populates="itens")


# ── Funções utilitárias ──────────────────────────────────────────────────────

def criar_tabelas():
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependência FastAPI — fornece sessão e fecha ao final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def popular_dados_iniciais():
    """Insere produtos e estoques de exemplo se o banco estiver vazio."""
    db = SessionLocal()
    if db.query(Produto).count() > 0:
        db.close()
        return

    sabores = [
        ("Chocolate",      "Cremoso sabor chocolate belga",        8.00),
        ("Morango",        "Feito com morangos frescos",           8.00),
        ("Baunilha",       "Clássico sabor baunilha",              7.50),
        ("Pistache",       "Pistache importado",                   10.00),
        ("Creme",          "Creme tradicional",                    7.00),
        ("Maracujá",       "Azedinho e refrescante",               8.50),
        ("Menta",          "Menta com gotas de chocolate",         9.00),
        ("Caramelo",       "Caramelo salgado",                     9.50),
        ("Limão Siciliano","Sorbet de limão siciliano",            8.00),
        ("Uva",            "Sabor uva italiana",                   7.50),
    ]

    for nome, desc, preco in sabores:
        p = Produto(nome=nome, descricao=desc, preco=preco)
        db.add(p)
        db.flush()
        db.add(Estoque(produto_id=p.id, quantidade=50, minimo=10))

    db.commit()
    db.close()
    print("[DB] Dados iniciais inseridos com sucesso.")


if __name__ == "__main__":
    criar_tabelas()
    popular_dados_iniciais()
    print("[DB] Banco de dados pronto:", DATABASE_URL)
