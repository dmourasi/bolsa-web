# bolsa-web

Plataforma web pública: recebe o currículo Lattes (XML ou PDF), pede os campos
que o Lattes não traz (nacionalidade, idiomas certificados, janela de início) e
devolve o relatório de bolsas que a pessoa pode aplicar.

A lógica de busca e de leitura do Lattes está no repositório **bolsa-core**,
instalado como dependência. Este repositório contém só a camada web (API
FastAPI + uma página HTML).

## Rodar localmente

```bash
uv sync
uv run bolsa-web                 # sobe em http://127.0.0.1:8000
uv run pytest                    # testes
```

## Endpoints

| Método | Caminho | O que faz |
|---|---|---|
| GET | `/` | Página única com o formulário |
| GET | `/api/target-levels` | Lista os níveis de bolsa aceitos |
| POST | `/api/lattes/parse` | Lê um Lattes (XML ou PDF, até 10 MB) |
| POST | `/api/funding/applicable` | Fontes automatizadas filtradas por nível |
| POST | `/api/report` | Relatório em Markdown e JSON para um perfil |

## Privacidade

- Nada enviado é guardado: não há login, banco de dados nem log do conteúdo.
- O Lattes é gravado em um arquivo temporário só durante a leitura e removido
  em seguida, mesmo quando a leitura falha.
- A resposta do `/api/lattes/parse` não inclui dados pessoais sensíveis
  (CPF, RG, endereço, telefone, data de nascimento).
- As fontes de bolsa são consultadas ao vivo a cada pedido.

## Estrutura

```
src/bolsa_web/
├── server.py          # entry point `bolsa-web` (uvicorn)
├── web/
│   ├── app.py         # cria o FastAPI e serve a página
│   ├── routes.py      # endpoints da API
│   └── schemas.py     # contratos de entrada e saída
└── web_static/
    └── index.html     # formulário em uma página só
tests/                 # testes da API (incluem o Lattes de exemplo sintético)
```
