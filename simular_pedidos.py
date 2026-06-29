"""
simular_pedidos.py
Simula 30 clientes com pedidos variados para fins de teste.
Uso: python simular_pedidos.py
"""

import httpx
import random
import time

API = "http://127.0.0.1:8000"

PAGAMENTOS = ["dinheiro", "cartao", "pix"]

# Distribuição realista de status pós-pedido
#   60% pronto, 20% pendente (ainda na fila), 20% cancelado
STATUS_DIST = (
    ["pronto"]    * 18 +
    ["pendente"]  * 6  +
    ["cancelado"] * 6
)
random.shuffle(STATUS_DIST)


def buscar_produtos() -> list[dict]:
    r = httpx.get(f"{API}/produtos/admin", timeout=10)
    r.raise_for_status()
    # Apenas produtos ativos com estoque
    return [p for p in r.json() if p.get("ativo") and (p.get("estoque") or 0) > 0]


def criar_pedido(produtos: list[dict], status_final: str) -> dict:
    # Cada cliente pede entre 1 e 4 itens diferentes
    n_itens = random.randint(1, 4)
    escolhidos = random.sample(produtos, min(n_itens, len(produtos)))

    itens = []
    for p in escolhidos:
        qtd = random.randint(1, 3)
        itens.append({"produto_id": p["id"], "quantidade": qtd})

    payload = {
        "itens": itens,
        "forma_pagamento": random.choice(PAGAMENTOS),
    }

    r = httpx.post(f"{API}/pedidos", json=payload, timeout=10)
    r.raise_for_status()
    pedido = r.json()

    # Atualiza status se não for pendente
    if status_final != "pendente":
        httpx.put(
            f"{API}/pedidos/{pedido['id']}/status",
            json={"status": status_final},
            timeout=10,
        )

    return pedido


def main():
    print("Buscando produtos disponíveis...")
    produtos = buscar_produtos()
    if not produtos:
        print("Nenhum produto ativo com estoque encontrado. Abortando.")
        return
    print(f"  {len(produtos)} produtos disponíveis\n")

    criados = 0
    erros   = 0

    for i, status in enumerate(STATUS_DIST, start=1):
        try:
            pedido = criar_pedido(produtos, status)
            print(f"  [{i:02d}/30] Pedido #{pedido['numero']} — "
                  f"R$ {pedido['valor_total']:.2f} — status final: {status}")
            criados += 1
        except Exception as e:
            print(f"  [{i:02d}/30] ERRO: {e}")
            erros += 1

        # Pequena pausa para não sobrecarregar o servidor
        time.sleep(0.15)

    print(f"\nConcluído: {criados} pedidos criados, {erros} erros.")
    print("  18 prontos | 6 pendentes | 6 cancelados")


if __name__ == "__main__":
    main()
