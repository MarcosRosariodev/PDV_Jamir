# PDV Jamir — Sistema Self-Service de Sorvete

## Estrutura do projeto

```
PDV_Jamir/
├── main.py               # Inicia tudo (backend + totem)
├── configurar.bat        # Instala dependências (rodar 1x)
├── iniciar.bat           # Inicia o sistema completo
├── admin.bat             # Abre só o painel admin
├── requirements.txt
├── pdv_jamir.db          # Banco SQLite (criado automaticamente)
│
├── api/
│   ├── server.py         # App FastAPI + middleware de impressão
│   └── routes.py         # Rotas: produtos, pedidos, relatórios
│
├── database/
│   └── db.py             # Models SQLAlchemy + seed inicial
│
├── services/
│   └── printer.py        # Integração impressora USB ESC/POS
│
├── ui/
│   ├── client_app.py     # Interface touchscreen do cliente
│   └── assets/           # Imagens dos sabores (opcional)
│
└── admin/
    └── admin_app.py      # Painel administrativo completo
```

## Instalação

1. Instale Python 3.11+ em https://python.org  
   ⚠ Marque **"Add Python to PATH"** durante a instalação.

2. Dê duplo clique em `configurar.bat`  
   Isso cria o ambiente virtual, instala as dependências e cria o banco.

3. Para iniciar o sistema: duplo clique em `iniciar.bat`

4. Para o painel admin (em outro computador ou outra janela): `admin.bat`

## Configurar impressora USB

Edite o arquivo `services/printer.py` e ajuste o VID e PID da sua impressora:

```python
PRINTER_VID = 0x04b8   # Vendor ID
PRINTER_PID = 0x0202   # Product ID
```

### Como descobrir VID e PID no Windows

1. Conecte a impressora via USB
2. Abra o **Gerenciador de Dispositivos**
3. Expanda "Impressoras" ou "Dispositivos USB"
4. Botão direito na impressora → Propriedades → Detalhes
5. Selecione "IDs de Hardware" — você verá algo como `USB\VID_04B8&PID_0202`

### Modelos comuns

| Impressora        | VID    | PID    |
|-------------------|--------|--------|
| Epson TM-T20      | 0x04b8 | 0x0202 |
| Bematech MP-4200  | 0x0dd4 | 0x0186 |
| Elgin i9          | 0x0fe6 | 0x811e |
| Daruma DR800      | 0x0483 | 0x5720 |

### Driver USB no Windows

Instale o **Zadig** (https://zadig.akeo.ie/) para substituir o driver da impressora por `WinUSB` ou `libusb-win32`, necessário para o python-escpos funcionar.

## Personalização

### Alterar nome/endereço no cupom

Edite `services/printer.py`:
```python
NOME_ESTABELECIMENTO = "Sorvetes Jamir"
ENDERECO             = "Rua das Flores, 123 — Fortaleza/CE"
TELEFONE             = "(85) 9 9999-9999"
```

### Adicionar imagens dos sabores

Coloque arquivos `.png` ou `.jpg` em `ui/assets/` com o mesmo nome do produto  
(ex: `Chocolate.png`) e ajuste a coluna `imagem` no banco.

### Rodar em modo quiosque no Windows (travado fullscreen)

No atalho de inicialização, adicione ao `iniciar.bat`:
```bat
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer" /v NoDesktop /t REG_DWORD /d 1 /f
```
Ou configure uma conta de usuário restrita no Windows dedicada ao totem.

## API — Endpoints disponíveis

| Método | Rota                           | Descrição                    |
|--------|--------------------------------|------------------------------|
| GET    | /produtos                      | Lista produtos ativos         |
| GET    | /produtos/admin                | Lista todos (incluindo inativos) |
| POST   | /produtos                      | Cria novo produto             |
| PUT    | /produtos/{id}                 | Atualiza produto/estoque      |
| POST   | /pedidos                       | Cria pedido + baixa estoque   |
| GET    | /pedidos                       | Lista pedidos (filtro status) |
| PUT    | /pedidos/{id}/status           | Atualiza status do pedido     |
| GET    | /relatorios/vendas             | Ranking + faturamento         |
| GET    | /estoque/alertas               | Produtos com estoque baixo    |

Documentação interativa disponível em: http://127.0.0.1:8000/docs
