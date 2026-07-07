<div align="center">

# 🤖 ROBÔ CHEFE

### O Gerente do seu Discord

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Discord.py](https://img.shields.io/badge/discord.py-2.7+-5865F2?style=for-the-badge&logo=discord&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-aiosqlite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/Licença-DOUGLAS--V1-E74C3C?style=for-the-badge)

**Bot completo de administração, atendimento e moderação para servidores Discord.**

Tickets com pesquisa de satisfação · Anti-spam inteligente · Logs forenses · Reaction Roles · Boas-vindas

[Funcionalidades](#-funcionalidades) · [Como Rodar](#-como-rodar) · [Estrutura](#-estrutura-do-projeto) · [Licença](#-aviso-de-propriedade-e-direitos)

</div>

---

## ✨ Funcionalidades

### 📩 Sistema de Tickets — v5.0

O coração do bot. Um sistema completo de atendimento ao cliente com fluxo profissional:

| Recurso | Descrição |
|---|---|
| **Abertura por botão** | Painel persistente com botão de criar ticket (`/setup-ticket`) |
| **Canais privados** | Cada ticket cria um canal com permissões exclusivas para o cliente e equipe |
| **Cargo "Funcionário"** | Busca automática por cargo com nome `Funcionário` — equipe de atendimento |
| **Chamar Cliente** | Botão que envia DM ao cliente avisando que há resposta, com cooldown de 15 min |
| **3 tipos de encerramento** | ✅ Concluído · ⚠️ Parcialmente Concluído · ❌ Não Entregue |
| **DMs personalizadas** | Cada tipo de encerramento envia uma mensagem diferente no privado do cliente |
| **Pesquisa de satisfação** | Modal com nota (1-5), opinião e sugestões — enviada via DM após fechamento |
| **Log de avaliações** | Resultados da pesquisa são postados no canal `#avaliações` |
| **Botões persistentes** | Todos os botões continuam funcionando após reiniciar o bot |
| **Política de desistência** | Aviso automático sobre prazos de produção (48h) e retirada (24h) |

### 🛡️ Anti-Spam Automático

Proteção em tempo real contra comportamento abusivo — sem precisar de moderador online:

- **Flood de mensagens** — 5+ mensagens em 5 segundos → timeout automático
- **Menções em massa** — 5+ menções (incluindo `@everyone`) → timeout
- **Spam de links** — 3+ links em 10 segundos → timeout
- **Timeout configurável** — 5 minutos por padrão
- **Log automático** — Registra a ação no canal `#📜logs` com embed detalhado
- **Ignora admins** — Administradores são isentos

### ⚖️ Moderação com SQLite

Sistema de avisos persistente e confiável:

| Comando | Permissão | Descrição |
|---|---|---|
| `/avisar @membro motivo` | Kick Members | Registra um aviso com timestamp e moderador |
| `/avisos @membro` | Todos | Consulta o histórico completo de avisos |
| `/limpar-avisos @membro` | Administrador | Remove todos os avisos de um membro |
| `/limpar-canal` | Administrador | Apaga todas as mensagens do canal (cooldown: 30s) |

> Migração automática de dados legados em JSON para SQLite na primeira inicialização.

### 📊 Logs de Auditoria Forenses

O sistema de logs mais detalhado que você vai ver em um bot:

**Mensagens apagadas:**
- Investiga **quem apagou** usando múltiplos métodos (audit log individual, bulk delete, inferência)
- Identifica se foi: 👤 auto-exclusão, 🛡️ moderador ou 🤖 bot
- Exibe **nível de confiança** da detecção (Alta / Média-Alta / Baixa)
- Captura conteúdo, anexos, embeds e stickers da mensagem
- Timestamps formatados com notação do Discord (`<t:...>`)

**Mensagens editadas:**
- Registra conteúdo **antes** e **depois**
- Detecta anexos adicionados/removidos
- Link direto para a mensagem editada

**Canais de voz:**
- 🎤 Entrada em canal de voz
- 🔇 Saída de canal de voz
- 🔄 Movimentação entre canais

**Limpeza em massa (purge):**
- Contagem de mensagens apagadas
- Lista de autores afetados com quantidade
- Amostra das 5 primeiras mensagens
- Identificação do responsável via audit log

> Todos os logs são enviados para o canal `#📜logs`.

### 👋 Boas-Vindas & Auto-Role

| Comando | Descrição |
|---|---|
| `/config-welcome canal:#geral cargo:@Membro ativar:True` | Configura tudo de uma vez |

- **Mensagem de entrada** — Embed com avatar, contagem de membros e boas-vindas
- **Mensagem de saída** — Despedida quando alguém sai do servidor
- **Auto-Role** — Atribui cargo automaticamente a novos membros
- **Persistente** — Configurações salvas em JSON por servidor

### 🎭 Reaction Roles

- Painel de cargos com botões persistentes (`/painel-cargos`)
- Cargos configurados: **PC Gamer** e **Mobile Gamer**
- Toggle automático — clicou de novo, remove o cargo
- Funciona mesmo após reiniciar o bot

### 🎨 Embed Builder

- Cria anúncios formatados via formulário interativo (`/criar-embed`)
- Campos: título, descrição, cor hex, menção opcional, imagem de rodapé
- Perfeito para comunicados do servidor

### 📈 Comandos Gerais

| Comando | Descrição |
|---|---|
| `/sobre` | Painel de ajuda com todos os comandos |
| `/hora` | Data e hora atuais |
| `/falar` | Bot envia mensagem anônima no canal |
| `/status` | Latência, uptime, servidores, membros, versão do Python e discord.py |

---

## ⚙️ Características Técnicas

- **Arquitetura Modular** — Sistema de Cogs do discord.py para separação de funcionalidades
- **Slash Commands** — Todos os comandos usam a API de interações do Discord
- **Botões Persistentes** — Views com `timeout=None` e `custom_id` para sobreviver a restarts
- **Error Handler Global** — Trata `MissingPermissions`, `CommandOnCooldown`, `BotMissingPermissions` e erros inesperados
- **Cooldowns** — Proteção contra spam em todos os comandos
- **Logging Profissional** — Arquivo `bot.log` + console com formato padronizado
- **dotenv** — Variáveis de ambiente via `.env` para segurança
- **Health Check HTTP** — Servidor HTTP integrado para plataformas como Koyeb
- **Docker Ready** — Dockerfile pronto para deploy containerizado
- **DisCloud Ready** — Configuração `discloud.config` inclusa

---

## 🚀 Como Rodar

### Pré-requisitos

- Python 3.12+
- Um bot criado no [Discord Developer Portal](https://discord.com/developers/applications)
- Intents habilitadas: `Message Content` e `Server Members`

### Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/DouglasAntoni0/Robo-Chefe-Discord.git
cd Robo-Chefe-Discord

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Configure o token
cp .env.example .env
# Edite o .env e cole seu DISCORD_TOKEN

# 4. Rode o bot
python main.py
```

### Docker

```bash
docker build -t robo-chefe .
docker run -d --env-file .env robo-chefe
```

### Primeiro uso no servidor

1. Use `!sync` para registrar os slash commands (somente o dono do bot)
2. Crie um canal chamado `📜logs` para receber os logs de auditoria
3. Crie um canal chamado `avaliações` para receber as pesquisas de satisfação
4. Use `/setup-ticket` no canal onde deseja o painel de tickets
5. Use `/config-welcome` para configurar boas-vindas
6. Use `/painel-cargos` para configurar reaction roles

---

## 📁 Estrutura do Projeto

```
Robo-Chefe-Discord/
├── main.py                  # Entry point — bot, health check, error handler, sync
├── config.py                # Cores, logging, dotenv
├── requirements.txt         # discord.py, python-dotenv, aiosqlite
├── .env.example             # Template de variáveis de ambiente
├── Dockerfile               # Deploy com Docker
├── discloud.config          # Deploy na DisCloud
│
├── cogs/
│   ├── ticket_system.py     # Sistema de tickets v5.0 (19KB)
│   ├── logging_system.py    # Logs forenses de mensagens e voz (21KB)
│   ├── moderation_system.py # Avisos com SQLite + migração JSON (7KB)
│   ├── anti_spam.py         # Anti-flood, menções e links (5KB)
│   ├── welcome_system.py    # Boas-vindas, despedida e auto-role (5KB)
│   ├── general_commands.py  # /sobre, /hora, /falar, /status (4KB)
│   ├── reaction_roles.py    # Cargos por botão persistente (4KB)
│   └── embed_builder.py     # Criador de embeds/anúncios (3KB)
│
└── README.md                # Documentação do projeto
```

Arquivos gerados em runtime e não versionados:

- `warnings.db`
- `bot.log`

---

## 🛠️ Tecnologias

| Tecnologia | Uso |
|---|---|
| **Python 3.12+** | Linguagem principal |
| **discord.py 2.7+** | Framework do bot |
| **aiosqlite** | Banco de dados assíncrono para avisos |
| **python-dotenv** | Variáveis de ambiente seguras |
| **Docker** | Containerização para deploy |

---

## ⚠️ Aviso de Propriedade e Direitos

Este código está público no GitHub para **fins de estudo e portfólio**.

### 📜 Licença "DOUGLAS-V1" (Lei do Chefe)

| | Regra |
|---|---|
| 👀 **Pode olhar?** | Pode. Fique à vontade para aprender como funciona. |
| 📚 **Pode usar de base?** | Pode, desde que não faça um "Ctrl+C / Ctrl+V" e diga que foi você que criou. |
| 🚫 **Pode vender?** | **NEM PENSAR.** |
| 🤝 **Créditos** | Se usar partes deste código, mantenha os créditos ou pague um salgado pro dev. |

**Resumo:** O código é aberto, mas a autoria é do **Douglas Antonio**. Respeite para ser respeitado. 🤝

---

<div align="center">

*Desenvolvido com ☕ e ódio a bugs por **Douglas Antonio**.*

</div>
