"""
database/db.py
Configuração do banco SQLite e modelos SQLAlchemy
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'pdv_jamir.db')}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


class Categoria(Base):
    __tablename__ = "categoria"

    id   = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False, unique=True)

    produtos = relationship("Produto", back_populates="categoria")


class Produto(Base):
    __tablename__ = "produto"

    id           = Column(Integer, primary_key=True)
    nome         = Column(String(100), nullable=False)
    descricao    = Column(Text, default="")
    preco        = Column(Float, nullable=False)
    imagem       = Column(String(200), default="")
    ativo        = Column(Integer, default=1)
    estoque      = Column(Integer, default=0)
    categoria_id = Column(Integer, ForeignKey("categoria.id"), nullable=True)

    categoria = relationship("Categoria", back_populates="produtos")
    itens     = relationship("PedidoItem", back_populates="produto")


class Pedido(Base):
    __tablename__ = "pedido"

    id              = Column(Integer, primary_key=True)
    numero          = Column(Integer, unique=True)
    status          = Column(String(20), default="pendente")
    valor_total     = Column(Float, default=0.0)
    data_hora       = Column(DateTime, default=datetime.now)
    forma_pagamento = Column(String(30), default="dinheiro")

    itens = relationship("PedidoItem", back_populates="pedido")


class PedidoItem(Base):
    __tablename__ = "pedido_item"

    id         = Column(Integer, primary_key=True)
    pedido_id  = Column(Integer, ForeignKey("pedido.id"))
    produto_id = Column(Integer, ForeignKey("produto.id"))
    quantidade = Column(Integer, default=1)
    valor      = Column(Float, nullable=False)

    pedido  = relationship("Pedido", back_populates="itens")
    produto = relationship("Produto", back_populates="itens")


def criar_tabelas():
    Base.metadata.create_all(bind=engine)
    # Migração: adiciona coluna estoque se ainda não existir
    with engine.connect() as conn:
        cols = [row[1] for row in conn.execute(text("PRAGMA table_info(produto)"))]
        if "estoque" not in cols:
            conn.execute(text("ALTER TABLE produto ADD COLUMN estoque INTEGER DEFAULT 0"))
            conn.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def popular_dados_iniciais():
    db = SessionLocal()
    if db.query(Categoria).count() > 0:
        db.close()
        return

    categorias = ["DinDin", "Picolé", "Sorvete"]
    cat_map = {}
    for nome in categorias:
        c = Categoria(nome=nome)
        db.add(c)
        db.flush()
        cat_map[nome] = c.id

    sabores = [
        ("Chocolate",  "Cremoso sabor chocolate",    3.00, "DinDin"),
        ("Morango",    "Feito com morangos frescos",  3.00, "DinDin"),
        ("Uva",        "Sabor uva gelada",            3.00, "DinDin"),
        ("Maracujá",   "Azedinho e refrescante",      3.50, "DinDin"),
        ("Creme",      "Creme tradicional",           2.50, "DinDin"),
        ("Limão",      "Sabor limão gelado",          3.00, "DinDin"),
        ("Abacaxi",    "Tropical e refrescante",      3.00, "DinDin"),
        ("Manga",      "Sabor manga tropical",        3.00, "DinDin"),
        ("Tamarindo",  "Especial de tamarindo",       3.50, "DinDin"),
        ("Caju",       "Sabor caju nordestino",       3.00, "DinDin"),
    ]

    for nome, desc, preco, cat in sabores:
        db.add(Produto(
            nome=nome, descricao=desc, preco=preco,
            categoria_id=cat_map[cat], estoque=50,
        ))

    db.commit()
    db.close()
    print("[DB] Dados iniciais inseridos com sucesso.")


if __name__ == "__main__":
    criar_tabelas()
    popular_dados_iniciais()
    print("[DB] Banco de dados pronto:", DATABASE_URL)
