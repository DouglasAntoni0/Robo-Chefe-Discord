# 🤖 ROBÔ CHEFE — O Gerente do Discord

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Discord.py](https://img.shields.io/badge/discord.py-2.7+-5865F2?style=for-the-badge&logo=discord&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/Licença-DOUGLAS--V1-red?style=for-the-badge)

Bem-vindo ao repositório oficial do **Robô Chefe**. Este é um bot de administração, atendimento e utilidades focado em manter a ordem na casa (e garantir que ninguém faça bagunça).

Atualmente hospedado e rodando liso na **Koyeb**. 🚀

---

## 🛠️ O que esse robô faz?

Ele não tira café, mas faz quase todo o resto:

### 📩 Sistema de Tickets Avançado
- Cria canais privados para atendimento
- Salva o ID do usuário para garantir contato
- **Pesquisa de Satisfação:** Ao fechar o ticket, o bot vai no PV do usuário perguntar a nota (1-5), opinião e sugestões
- **Botões Persistentes:** Continuam funcionando mesmo após reiniciar o bot

### 🛡️ Moderação Inteligente
- Sistema de avisos (`/avisar`, `/avisos`, `/limpar-avisos`)
- Banco de dados **SQLite** (seguro e confiável)
- Migração automática de dados antigos em JSON

### 🤖 Anti-Spam Automático
- Detecta flood de mensagens (muitas mensagens rápidas)
- Detecta spam de menções em massa
- Detecta spam de links
- Aplica **timeout automático** e notifica moderadores

### 👋 Sistema de Boas-Vindas
- Mensagem automática quando alguém entra no servidor
- Mensagem de despedida quando alguém sai
- **Auto-Role:** Dá cargo automático a novos membros
- Configurável via `/config-welcome`

### 📊 Logs de Auditoria
- Monitora mensagens apagadas
- Entrada/saída de canais de voz
- Movimentação entre canais

### 🎭 Reaction Roles
- Dá cargos automaticamente por botões
- Painel configurável pelo administrador
- Botões persistentes após reinício

### 🎨 Embed Builder
- Cria mensagens bonitonas via formulário (`/criar-embed`)
- Cores customizáveis com código hex

### 📈 Utilitários
- `/sobre` — Painel de ajuda
- `/hora` — Data e hora atuais
- `/falar` — Mensagem anônima do bot
- `/status` — Informações técnicas (latência, uptime, servidores)

---

## ⚙️ Características Técnicas

- **Logging Profissional:** Sistema de logs com arquivo `bot.log` e console
- **Error Handler Global:** Trata erros de todos os comandos de forma amigável
- **Cooldowns:** Proteção contra uso excessivo de comandos
- **Cores Consistentes:** Paleta de cores padronizada via `config.py`
- **dotenv:** Suporte a `.env` para desenvolvimento local seguro
- **Health Check:** Servidor HTTP para Koyeb não derrubar o bot

---

## ⚠️ AVISO DE PROPRIEDADE E DIREITOS (LEIA!)

Este código está público no GitHub para **fins de estudo e portfólio**.

**📜 A Licença "DOUGLAS-V1" (Lei do Chefe):**

1.  **Pode olhar?** 👀 Pode. Fique à vontade para aprender como funciona.
2.  **Pode usar de base?** 📚 Pode, desde que você não faça um "Ctrl+C / Ctrl+V" safado e diga que foi você que criou.
3.  **Pode vender?** 🚫 **NEM PENSAR.** Se eu ver alguém vendendo esse código, o processo vem a galope (ou eu mando o bot travar seu Discord, brincadeira... ou não).
4.  **Autoria:** Se usar partes deste código, tenha a decência de manter os créditos ou pagar um salgado pro desenvolvedor.

**Resumo:** Não seja um "kibeiro". O código é aberto, mas a autoria é do **Douglas Antonio**. Respeite para ser respeitado. 🤝

---

## 🚀 Tecnologias

| Tecnologia | Versão |
|---|---|
| Python | 3.12+ |
| discord.py | 2.7+ |
| SQLite | via aiosqlite |
| Hospedagem | Koyeb (Worker) |

---

## 🔧 Como rodar (para devs)

Se você for rodar isso localmente (no seu PC):

1.  Clone o repositório:
    ```bash
    git clone https://github.com/DouglasAntoni0/Robo-Chefe-Discord..git Robo-Chefe-Discord
    ```

2.  Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```

3.  Configure o token — copie o exemplo e edite:
    ```bash
    cp .env.example .env
    # Edite o arquivo .env e cole seu DISCORD_TOKEN
    ```

4.  Rode o bot:
    ```bash
    python main.py
    ```

---

## 📁 Estrutura do Projeto

```
Robo-Chefe-Discord/
├── main.py              # Ponto de entrada do bot
├── config.py            # Configurações centrais (cores, logging, dotenv)
├── requirements.txt     # Dependências
├── .env.example         # Exemplo de variáveis de ambiente
├── .gitignore           # Arquivos ignorados pelo Git
├── cogs/
│   ├── anti_spam.py     # Sistema anti-spam automático
│   ├── embed_builder.py # Criador de embeds/anúncios
│   ├── general_commands.py  # Comandos gerais (/sobre, /hora, /status)
│   ├── logging_system.py    # Logs de auditoria
│   ├── moderation_system.py # Moderação com SQLite
│   ├── reaction_roles.py    # Cargos por botão
│   ├── ticket_system.py     # Sistema de tickets
│   └── welcome_system.py    # Boas-vindas e auto-role
└── README.md
```

---

*Desenvolvido com ☕ e ódio a bugs por Douglas Antonio.*
