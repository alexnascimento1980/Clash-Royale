# ⚔️ Clash Royale Tracker

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
clash-royale/
│
├── app.py                  # Servidor Flask (backend / proxy / downloads)
├── requirements.txt        # Dependências Python
│
└── templates/
    └── index.html          # Interface completa (HTML + CSS + JS)
```

---

## 📦 Requisitos

- Python 3.10 ou superior
- pip (gerenciador de pacotes Python)
- Conexão com internet
- Conta no [developer.clashroyale.com](https://developer.clashroyale.com)

---

## 🚀 Instalação e Execução

### 1. Clone ou baixe os arquivos

Certifique-se de que a estrutura de pastas está correta:
```
clash-royale/
├── app.py
├── requirements.txt
└── templates/
    └── index.html
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
✅ Clash Royale Tracker rodando em http://localhost:5000
```

### 4. Abra no navegador

```
http://localhost:5000
```

---

## 🔑 Configuração da API Key

A API do Clash Royale exige uma chave de autenticação vinculada ao seu IP público.

### Passo a passo

1. Acesse [developer.clashroyale.com](https://developer.clashroyale.com) e faça login
2. Clique em **"My Account"** → **"Create New Key"**
3. Descubra seu IP público em [meuip.com.br](https://meuip.com.br)
4. Preencha o campo **"Allowed IP Addresses"** com seu IP público (ex: `189.45.123.67`)
5. Salve e copie a chave gerada
6. Cole a chave no campo **🔑 API Key** no topo do aplicativo

> ⚠️ **IP Dinâmico:** A maioria dos provedores residenciais muda o IP periodicamente. Quando isso ocorrer, volte ao portal, edite a chave e atualize o IP. O erro retornado pela API nesse caso é HTTP 403.

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

### IP Público Obrigatório
IPs privados (127.0.0.1, 192.168.x.x) são rejeitados pelo portal de desenvolvedores. Use sempre o IP público da máquina. Em caso de erro **403**, atualize o IP cadastrado na chave.

### Rate Limiting
A API tem limite de requisições por intervalo de tempo. Em caso de erro **429 (Too Many Requests)**, aguarde alguns segundos antes de tentar novamente.

---

## 🧩 Estrutura do Código

### app.py — Rotas Principais

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

---

## 📄 Licença

Projeto de uso pessoal. Dados fornecidos pela [API Oficial do Clash Royale](https://developer.clashroyale.com).  
Clash Royale é marca registrada da Supercell Oy.
