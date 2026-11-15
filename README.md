# 🛡️ Sentinela

**Status de jogador e guerra para Clash.**

Aplicativo web para consultar e analisar dados de jogadores e clãs do Clash Royale, com histórico de batalhas, guerras, gráficos de desempenho e exportação de dados.

---

## 📋 Índice

- [Funcionalidades](#-funcionalidades)
- [Stack Tecnológica](#-stack-tecnológica)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Requisitos](#-requisitos)
- [Instalação e Execução](#-instalação-e-execução)
- [Configuração da API Key](#-configuração-da-api-key)
- [Guia de Uso](#-guia-de-uso)
- [Exportação de Dados](#-exportação-de-dados)
- [Gráficos Disponíveis](#-gráficos-disponíveis)
- [Limitações Conhecidas](#-limitações-conhecidas)
- [Estrutura do Código](#-estrutura-do-código)

---

## ✨ Funcionalidades

### 👤 Jogador
| Recurso | Descrição |
|---|---|
| Perfil completo | Troféus, nível, vitórias, derrotas, 3 coroas, clã atual |
| Histórico de batalhas | Últimas batalhas com resultado, coroas e arena |
| Guerras detalhadas | Batalhas PvP, ataques ao barco, decks usados, HP das torres |
| Torneios e desafios | Batalhas filtradas por tipo |
| Gráficos com filtro | 6 gráficos com filtro por período (7/15/30/90 dias ou intervalo) |
| Download de dados | Exportação em JSON (completo) e CSV (formatado para Excel) |

### 🏰 Clã
| Recurso | Descrição |
|---|---|
| Visão geral | Pontuação, troféus de guerra, tipo, localização, doações |
| Membros atuais | Cargo, troféus, nível, arena, último online |
| Histórico de guerras | River Race log com posição, fama e participantes por temporada |
| Gráficos com filtro | 7 gráficos com filtro por número de temporadas |
| Download de dados | Exportação em JSON e CSV com participantes individuais por guerra |

---

## 🛠️ Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| Backend | Python 3 + Flask |
| Requisições HTTP | requests |
| Frontend | HTML5 + CSS3 + JavaScript (Vanilla) |
| Gráficos | Chart.js 4.4 + chartjs-adapter-date-fns |
| Fontes | Google Fonts (Cinzel + Nunito) |
| API | Clash Royale Official API v1 |

---

## 📁 Estrutura do Projeto

```
sentinela/
│
├── app.py                  # Rotas Flask (proxy, downloads, headers de segurança)
├── config.py               # Configuração via variáveis de ambiente
├── cr_client.py            # Cliente da API (sessão com retry, cache TTL, validação de tag)
├── csv_export.py           # Geração dos CSVs (com proteção contra injeção de fórmula)
├── requirements.txt        # Dependências Python
├── requirements-dev.txt    # Dependências de desenvolvimento (pytest)
├── vercel.json             # Deploy serverless na Vercel
│
├── api/
│   └── index.py            # Entry point da Vercel (reexporta o app de app.py)
├── templates/
│   └── index.html          # Estrutura da interface
├── static/
│   ├── css/style.css
│   ├── js/app.js
│   ├── manifest.webmanifest   # instalação como app (PWA)
│   └── icons/                 # ícones (escudo com coroa) em SVG e PNG
└── tests/
    └── test_app.py         # Testes do backend (sem acesso à rede)
```

---

## 📦 Requisitos

- Python 3.10 ou superior
- pip (gerenciador de pacotes Python)
- Conexão com internet
- Conta no [developer.clashroyale.com](https://developer.clashroyale.com)

---

## 🚀 Instalação e Execução

### 1. Clone o repositório

```bash
git clone https://github.com/alexnascimento1980/sentinela.git
cd sentinela
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Execute o servidor

```bash
python app.py
```

Você verá no terminal:
```
✅ Sentinela rodando em http://localhost:5000
```

### Instalar no celular

O Sentinela pode ser instalado como app a partir do navegador, sem loja:
- **Android (Chrome):** menu ⋮ → *Instalar app* (ou *Adicionar à tela inicial*)
- **iPhone (Safari):** botão Compartilhar → *Adicionar à Tela de Início*

Precisa de conexão: os dados vêm da API em tempo real, então não há modo offline.

### Testes

```bash
pip install -r requirements-dev.txt
pytest
```

### 4. Abra no navegador

```
http://localhost:5000
```

---

## 🔑 Configuração da API Key

A API do Clash Royale exige uma chave de autenticação vinculada a um IP. Por padrão, este projeto **não** chama a API oficial diretamente: ele usa o proxy público da [RoyaleAPI](https://docs.royaleapi.com/proxy.html) (`https://proxy.royaleapi.dev/v1`), que tem IP fixo. Isso é necessário na Vercel, onde o IP de saída muda a cada execução.

### Passo a passo (padrão — proxy da RoyaleAPI)

1. Acesse [developer.clashroyale.com](https://developer.clashroyale.com) e faça login
2. Clique em **"My Account"** → **"Create New Key"**
3. No campo **"Allowed IP Addresses"** informe o IP do proxy: `45.79.218.79`
4. Salve e copie a chave gerada
5. Cole a chave no campo **🔑 API Key** no topo do aplicativo

### Usando a API oficial direto (servidor com IP fixo)

Defina `CR_BASE_URL=https://api.clashroyale.com/v1` e cadastre na chave o **IP público** do seu servidor (descubra em [meuip.com.br](https://meuip.com.br)). Nesse modo, se o seu provedor mudar o IP, a API devolve HTTP 403 e é preciso atualizar a chave no portal.

### Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `CR_BASE_URL` | `https://proxy.royaleapi.dev/v1` | URL base da API |
| `CR_TIMEOUT` | `10` | Timeout por chamada (segundos) |
| `CR_MAX_RETRIES` | `2` | Tentativas em erro transitório (502/503/504, timeout) |
| `CACHE_TTL_SECONDS` | `60` | TTL do cache em memória (`0` desativa) |
| `CACHE_MAX_ENTRIES` | `256` | Limite de entradas do cache |
| `FLASK_DEBUG` | `0` | `1` ativa o debug (nunca em produção) |
| `FLASK_HOST` / `FLASK_PORT` | `0.0.0.0` / `5000` | Endereço do servidor local |

---

## ☁️ Deploy na Vercel

O `vercel.json` aponta para `api/index.py`, que reexporta o app Flask. Basta importar o repositório na Vercel — não é necessário configurar a chave de API no servidor, pois ela é digitada na interface.

---

## 📖 Guia de Uso

### Buscar um Jogador

1. Clique na aba **👤 Jogador**
2. Digite a tag do jogador no campo (com ou sem `#`, ex: `#2PP` ou `2PP`)
3. Pressione **Enter** ou clique em **🔍 Buscar**
4. Navegue pelas abas: **Perfil**, **Batalhas**, **Guerras**, **Torneios**, **Gráficos**

### Buscar um Clã

1. Clique na aba **🏰 Clã**
2. Digite a tag do clã
3. Clique em **🔍 Buscar**
4. Navegue pelas abas: **Visão Geral**, **Membros**, **Guerras**, **Gráficos**

### Onde encontrar as Tags

- **Tag do jogador:** Perfil do jogador no jogo (abaixo do nome)
- **Tag do clã:** Tela do clã no jogo (abaixo do nome do clã)

---

## 📥 Exportação de Dados

Após realizar uma busca, a barra de download aparece no topo dos resultados.

### 📄 JSON

Exporta **todos os dados brutos** retornados pela API sem filtragem.

| Arquivo | Conteúdo |
|---|---|
| `jogador_TAG.json` | `perfil` + `historico_batalhas` |
| `cla_TAG.json` | `clan` + `membros` + `historico_guerras` |

### 📊 CSV (compatível com Excel)

Arquivo com BOM UTF-8 para abertura correta no Microsoft Excel.

**CSV do Jogador — Seções:**

| Seção | Campos |
|---|---|
| Perfil | Nome, tag, nível, troféus, arena, liga, carta favorita, dados do clã |
| Deck Atual | 8 cartas com nível e custo de elixir |
| Coleção de Cartas | Todas as cartas com quantidade e cartas para upgrade |
| Conquistas | Nome, nível e progresso de cada badge |
| Batalhas | Deck usado, deck do oponente, HP das torres, resultado |

**CSV do Clã — Seções:**

| Seção | Campos |
|---|---|
| Informações | Nome, tag, tipo, localização, pontuação, troféus de guerra |
| Membros Atuais | Cargo, nível, troféus, arena, rank, doações, último online |
| Guerras — Resumo | Por temporada: posição, fama, reparos, participantes, top 5 |
| Guerras — Participantes | Por jogador por temporada: fama, reparos, decks usados |

---

## 📈 Gráficos Disponíveis

### Gráficos do Jogador

> Filtros: **7 dias / 15 dias / 30 dias / 90 dias / Tudo / Intervalo personalizado**

| Gráfico | Tipo | Descrição |
|---|---|---|
| Troféus ao longo do tempo | Linha | Evolução dos troféus em cada batalha |
| Resultados no período | Doughnut | Pizza de vitórias, derrotas e empates |
| Coroas por dia | Barras agrupadas | Suas coroas vs coroas sofridas por dia |
| Batalhas por tipo | Doughnut | Distribuição entre ladder, guerra, torneio, etc. |
| Taxa de vitória por arena | Barras horizontais | Verde ≥ 50%, vermelho < 50% |
| Batalhas por dia da semana | Barras duplas | Dias mais ativos e de maior taxa de vitória |

### Gráficos de Guerra do Jogador

> Disponíveis na aba **🏴 Guerras**, sem filtro adicional

| Gráfico | Tipo | Descrição |
|---|---|---|
| Resultados nas guerras | Doughnut | Vitórias/derrotas específicas de guerra |
| PvP vs Barco vs Outros | Doughnut | Distribuição entre tipos de batalha |
| Coroas por batalha | Barras agrupadas | Suas coroas vs sofridas em ordem cronológica |

### Gráficos do Clã

> Filtros: **Últimas 5 / 10 / 20 temporadas / Todas**

| Gráfico | Tipo | Descrição |
|---|---|---|
| Fama por temporada | Barras | Ouro ≥ 3500, azul ≥ 2000 |
| Posição por temporada | Linha | Eixo Y invertido (1º lugar no topo) |
| Participantes por temporada | Barras | Engajamento ao longo das guerras |
| Distribuição de troféus | Histograma | Membros agrupados por faixa de troféus |
| Top 15 contribuidores | Barras horizontais | Fama total acumulada em todas as guerras |
| Top 10 doadores | Barras horizontais | Doações da semana atual |
| Membros por cargo | Doughnut | Líder / Co-Líder / Ancião / Membro |

---

## ⚠️ Limitações Conhecidas

### Histórico de Batalhas
A API oficial retorna apenas as **últimas 25 batalhas** de cada jogador. Não existe endpoint para batalhas anteriores. Para manter um histórico maior, seria necessário um sistema de coleta periódica com banco de dados.

### Datas de Entrada/Saída de Membros
A API **não fornece** histórico de quando membros entraram ou saíram de um clã. O endpoint `/members` retorna apenas os membros presentes no momento da consulta. Para monitorar movimentações seria necessário salvar snapshots periódicos e comparar os dados.

### IP Autorizado na Chave
A chave precisa autorizar o IP de quem faz a chamada: `45.79.218.79` ao usar o proxy da RoyaleAPI (padrão) ou o IP público do servidor ao usar a API oficial. Erro **403** indica IP não autorizado ou chave inválida.

### Rate Limiting
A API tem limite de requisições por intervalo de tempo. Em caso de erro **429 (Too Many Requests)**, aguarde alguns segundos antes de tentar novamente.

---

## 🧩 Estrutura do Código

### Rotas (app.py)

| Rota | Método | Descrição |
|---|---|---|
| `/` | GET | Serve o index.html |
| `/api/player/<tag>` | GET | Proxy para perfil do jogador |
| `/api/player/<tag>/battlelog` | GET | Proxy para histórico de batalhas |
| `/api/clan/<tag>` | GET | Proxy para dados do clã |
| `/api/clan/<tag>/members` | GET | Proxy para membros do clã |
| `/api/clan/<tag>/warlog` | GET | Proxy para histórico de guerras |
| `/download/player/<tag>/json` | GET | Download JSON completo do jogador |
| `/download/player/<tag>/csv` | GET | Download CSV do jogador |
| `/download/clan/<tag>/json` | GET | Download JSON completo do clã |
| `/download/clan/<tag>/csv` | GET | Download CSV do clã |

### Autenticação

A API Key é transmitida de duas formas:
- **Consultas normais:** Header HTTP `X-Api-Key` (enviado pelo `fetch` do JavaScript)
- **Downloads:** Query parameter `?key=...` (necessário por ser navegação direta via `window.location.href`)

Sem chave, o backend responde **401** sem chamar a API externa. As respostas de `/api/*` e `/download/*` saem com `Cache-Control: no-store`.

> ⚠️ Como a chave vai na URL dos downloads, ela pode aparecer em logs de acesso do servidor/Vercel. Use uma chave dedicada a este app.

### Segurança

- **XSS:** textos vindos da API (nomes, tags, cartas) são escapados (`esc()` em `static/js/app.js`) antes de entrar no DOM.
- **CSV injection:** células de texto iniciadas por `=`, `+`, `-`, `@` ganham um apóstrofo (`csv_export.safe_cell`), evitando execução de fórmulas no Excel/Sheets.
- **Cache:** a chave do cache inclui o hash da API Key, então uma resposta nunca é servida a outra chave.

---

## 📄 Licença

Projeto de uso pessoal. Dados fornecidos pela [API Oficial do Clash Royale](https://developer.clashroyale.com).  
Sentinela é um projeto de fã, não afiliado, endossado nem patrocinado pela Supercell.  
Clash Royale é marca registrada da Supercell Oy.
