import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
import asyncio
import logging
from datetime import datetime, timedelta

from config import CORES

logger = logging.getLogger('bot.tickets')

NOME_CARGO_FUNCIONARIO = "Funcionário"

def buscar_cargo_funcionario(guild: discord.Guild):
    """Busca o cargo que contém 'Funcionário' no nome (ignora emojis e maiúsculas)."""
    for role in guild.roles:
        if NOME_CARGO_FUNCIONARIO.lower() in role.name.lower():
            return role
    return None

def tem_permissao_ticket(member: discord.Member) -> bool:
    """Retorna True se o membro é admin OU tem o cargo 'Funcionário'."""
    if member.guild_permissions.administrator:
        return True
    cargo = buscar_cargo_funcionario(member.guild)
    if cargo and cargo in member.roles:
        return True
    return False

TITULO_EMBED = "Suporte e atendimento"
DESCRICAO_EMBED = "Precisa de ajuda, quer fazer um pedido ou tem alguma dúvida? Clique no botão abaixo para abrir um ticket privado com nossa equipe."
TEXTO_BOTAO_CRIAR = "Abrir Ticket"
LOG_CHANNEL_NAME = "avaliações"


# --- Formulário de Avaliação ---
class AvaliacaoModal(Modal, title="Avaliação de Atendimento"):
    nota = TextInput(label="Nota (1 a 5)", placeholder="Ex: 5", min_length=1, max_length=1)
    opiniao = TextInput(label="O que achou do atendimento?", style=discord.TextStyle.paragraph, placeholder="Digite sua opinião aqui...", required=True)
    sugestao = TextInput(label="Sugestões de melhoria (Opcional)", style=discord.TextStyle.paragraph, required=False)

    def __init__(self, user, original_message):
        super().__init__()
        self.user = user
        self.original_message = original_message

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ **Obrigado!** Sua avaliação foi enviada com sucesso.", ephemeral=True)

        try:
            view_desativada = View(timeout=None)
            botao_desativado = Button(label="Avaliação Enviada", style=discord.ButtonStyle.grey, disabled=True)
            view_desativada.add_item(botao_desativado)
            await self.original_message.edit(view=view_desativada)
        except Exception as e:
            logger.error(f"Erro ao desativar botão: {e}")

        log_channel = None
        for g in interaction.client.guilds:
            c = discord.utils.get(g.text_channels, name=LOG_CHANNEL_NAME)
            if c:
                log_channel = c
                break

        if log_channel:
            embed = discord.Embed(title="📊 Nova Avaliação Recebida", color=CORES['cargo'], timestamp=discord.utils.utcnow())
            embed.add_field(name="Cliente", value=f"{self.user.name} (ID: {self.user.id})", inline=False)
            embed.add_field(name="Nota", value=f"{self.nota.value}/5 ⭐", inline=True)
            embed.add_field(name="Opinião", value=self.opiniao.value, inline=False)
            if self.sugestao.value:
                embed.add_field(name="Sugestão", value=self.sugestao.value, inline=False)
            embed.set_footer(text="Enviado via Formulário")
            await log_channel.send(embed=embed)
            logger.info(f"Avaliação recebida de {self.user.name}: {self.nota.value}/5")


# --- Botão de Avaliação (Persistente) ---
class BotaoAvaliar(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Responder Pesquisa de Satisfação", style=discord.ButtonStyle.blurple, emoji="📝", custom_id="botao_avaliar_ticket")
    async def abrir_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AvaliacaoModal(interaction.user, interaction.message))


# --- Botões de Encerramento (Concluído / Parcial / Não Entregue) ---
class TicketEncerramento(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Concluído com Sucesso", style=discord.ButtonStyle.green, custom_id="ticket_concluido_btn", emoji="✅")
    async def concluido(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not tem_permissao_ticket(interaction.user):
            await interaction.response.send_message("⛔ Sem permissão.", ephemeral=True)
            return

        await interaction.response.send_message("✅ Encerrando como **concluído** e notificando o cliente...", ephemeral=True)

        channel = interaction.channel
        topic = channel.topic
        guild = interaction.guild

        user_id = None
        if topic and "ID:" in topic:
            try:
                user_id = int(topic.split("ID: ")[1])
            except:
                pass

        logger.info(f"Ticket #{channel.name} encerrado como CONCLUÍDO por {interaction.user.name}")
        TicketControls._cooldowns.pop(channel.id, None)
        await asyncio.sleep(2)
        await channel.delete()

        if user_id:
            user = guild.get_member(user_id)
            if user:
                try:
                    embed_dm = discord.Embed(
                        title="✅ Pedido Finalizado com Sucesso!",
                        description=(
                            f"O seu pedido no servidor **{guild.name}** foi finalizado com sucesso! 🎉\n\n"
                            f"Foi um prazer atendê-lo e tê-lo como nosso cliente. "
                            f"Esperamos te ver novamente em breve!\n\n"
                            f"Dedique alguns segundos para nos avaliar e nos dizer como podemos melhorar. "
                            f"Sua opinião é muito importante para nós.\n\n"
                            f"Obrigado pela confiança e até a próxima! 💙"
                        ),
                        color=CORES['sucesso']
                    )
                    await user.send(embed=embed_dm, view=BotaoAvaliar())
                    logger.info(f"DM de conclusão enviada para {user.name}")
                except:
                    logger.warning(f"Não consegui enviar DM para {user.name}")

    @discord.ui.button(label="Não foi possível entregar", style=discord.ButtonStyle.red, custom_id="ticket_nao_entregue_btn", emoji="❌")
    async def nao_entregue(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not tem_permissao_ticket(interaction.user):
            await interaction.response.send_message("⛔ Sem permissão.", ephemeral=True)
            return

        await interaction.response.send_message("❌ Encerrando como **não entregue** e notificando o cliente...", ephemeral=True)

        channel = interaction.channel
        topic = channel.topic
        guild = interaction.guild

        user_id = None
        if topic and "ID:" in topic:
            try:
                user_id = int(topic.split("ID: ")[1])
            except:
                pass

        logger.info(f"Ticket #{channel.name} encerrado como NÃO ENTREGUE por {interaction.user.name}")
        TicketControls._cooldowns.pop(channel.id, None)
        await asyncio.sleep(2)
        await channel.delete()

        if user_id:
            user = guild.get_member(user_id)
            if user:
                try:
                    embed_dm = discord.Embed(
                        title="Seu ticket foi encerrado",
                        description=(
                            f"Seu ticket no servidor **{guild.name}** foi encerrado. 😔\n\n"
                            f"Infelizmente, não foi possível concluir o seu pedido da forma que gostaríamos. "
                            f"Sentimos muito por qualquer inconveniente causado.\n\n"
                            f"Mas gostaríamos muito de vê-lo novamente conosco! "
                            f"Dedique alguns segundos para nos avaliar e nos dizer como podemos melhorar. "
                            f"E qualquer coisa, não hesite em nos procurar novamente.\n\n"
                            f"Estamos sempre aqui para te ajudar! 💙"
                        ),
                        color=CORES['aviso']
                    )
                    await user.send(embed=embed_dm, view=BotaoAvaliar())
                    logger.info(f"DM de não-entrega enviada para {user.name}")
                except:
                    logger.warning(f"Não consegui enviar DM para {user.name}")

    @discord.ui.button(label="Parcialmente Concluído", style=discord.ButtonStyle.secondary, custom_id="ticket_parcial_btn", emoji="⚠️")
    async def parcial(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not tem_permissao_ticket(interaction.user):
            await interaction.response.send_message("⛔ Sem permissão.", ephemeral=True)
            return

        await interaction.response.send_message("⚠️ Encerrando como **parcialmente concluído** e notificando o cliente...", ephemeral=True)

        channel = interaction.channel
        topic = channel.topic
        guild = interaction.guild

        user_id = None
        if topic and "ID:" in topic:
            try:
                user_id = int(topic.split("ID: ")[1])
            except:
                pass

        logger.info(f"Ticket #{channel.name} encerrado como PARCIALMENTE CONCLUÍDO por {interaction.user.name}")
        TicketControls._cooldowns.pop(channel.id, None)
        await asyncio.sleep(2)
        await channel.delete()

        if user_id:
            user = guild.get_member(user_id)
            if user:
                try:
                    embed_dm = discord.Embed(
                        title="⚠️ Seu pedido foi parcialmente concluído",
                        description=(
                            f"Seu ticket no servidor **{guild.name}** foi encerrado. ⚠️\n\n"
                            f"O seu pedido foi parcialmente concluído — nem tudo saiu como planejávamos, "
                            f"mas fizemos o possível para atender parte da sua solicitação.\n\n"
                            f"Sabemos que não é o ideal e pedimos desculpas por qualquer inconveniente. "
                            f"Caso precise de algo mais, não hesite em abrir um novo ticket!\n\n"
                            f"Dedique alguns segundos para nos avaliar e nos dizer como podemos melhorar. "
                            f"Sua opinião nos ajuda a evoluir.\n\n"
                            f"Contamos com você! 💙"
                        ),
                        color=CORES['aviso']
                    )
                    await user.send(embed=embed_dm, view=BotaoAvaliar())
                    logger.info(f"DM de conclusão parcial enviada para {user.name}")
                except:
                    logger.warning(f"Não consegui enviar DM para {user.name}")


# --- Controles do Ticket (Fechar / Chamar) ---
class TicketControls(View):
    # Cooldown de 15 minutos por canal para o botão "Chamar Cliente"
    _cooldowns: dict[int, datetime] = {}
    COOLDOWN_MINUTOS = 15

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Fechar Ticket", style=discord.ButtonStyle.red, custom_id="fechar_ticket_btn", emoji="🔒")
    async def fechar_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not tem_permissao_ticket(interaction.user):
            await interaction.response.send_message("⛔ **Apenas Administradores ou Funcionários podem fechar o ticket!**", ephemeral=True)
            return

        embed_escolha = discord.Embed(
            title="🔒 Encerrar Ticket",
            description="Como deseja encerrar este ticket? Escolha uma opção abaixo:",
            color=CORES['ticket']
        )
        await interaction.response.send_message(embed=embed_escolha, view=TicketEncerramento(), ephemeral=True)

    @discord.ui.button(label="Chamar Cliente", style=discord.ButtonStyle.secondary, custom_id="chamar_cliente_btn", emoji="🔔")
    async def chamar_cliente(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not tem_permissao_ticket(interaction.user):
            await interaction.response.send_message("⛔ Apenas Admins ou Funcionários podem chamar o cliente.", ephemeral=True)
            return

        # --- Verificação de cooldown de 15 minutos ---
        channel_id = interaction.channel.id
        agora = datetime.now()
        ultimo_uso = TicketControls._cooldowns.get(channel_id)

        if ultimo_uso:
            tempo_passado = agora - ultimo_uso
            cooldown_total = timedelta(minutes=TicketControls.COOLDOWN_MINUTOS)
            if tempo_passado < cooldown_total:
                restante = cooldown_total - tempo_passado
                minutos_rest = int(restante.total_seconds() // 60)
                segundos_rest = int(restante.total_seconds() % 60)
                await interaction.response.send_message(
                    f"⏳ **Calma lá!** Você só pode chamar o cliente a cada **{TicketControls.COOLDOWN_MINUTOS} minutos** para evitar spam.\n"
                    f"Tente novamente em **{minutos_rest}m {segundos_rest}s**.",
                    ephemeral=True
                )
                return

        topic = interaction.channel.topic
        user_id = None
        if topic and "ID:" in topic:
            try:
                user_id = int(topic.split("ID: ")[1])
            except:
                pass

        if user_id:
            user = interaction.guild.get_member(user_id)
            if user:
                try:
                    embed_aviso = discord.Embed(title="🔔 Atualização no seu Ticket", description=f"Olá! A equipe do **{interaction.guild.name}** respondeu seu ticket e está aguardando seu retorno.\n\nCorre lá no canal: {interaction.channel.mention}", color=CORES['aviso'])
                    await user.send(embed=embed_aviso)
                    # Registra o momento do envio no cooldown
                    TicketControls._cooldowns[channel_id] = agora
                    await interaction.response.send_message(f"✅ Notificação enviada para o privado de {user.mention}!\n⏳ Próximo envio liberado em **{TicketControls.COOLDOWN_MINUTOS} minutos**.", ephemeral=True)
                    logger.info(f"{interaction.user.name} chamou {user.name} no ticket #{interaction.channel.name}")
                except:
                    await interaction.response.send_message(f"❌ O cliente {user.mention} está com o privado bloqueado.", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Cliente não está mais no servidor.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Erro: Não achei o ID do cliente no tópico do canal.", ephemeral=True)


# --- Botão de Criar Ticket (Persistente) ---
class TicketLauncher(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label=TEXTO_BOTAO_CRIAR, style=discord.ButtonStyle.green, custom_id="criar_ticket_btn_v2", emoji="📩")
    async def criar_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild

        for channel in guild.text_channels:
            if channel.topic and f"ID: {interaction.user.id}" in channel.topic:
                await interaction.response.send_message("Ei, você já tem um ticket aberto!", ephemeral=True)
                return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        # Permitir que membros com cargo "Funcionário" vejam e respondam nos tickets
        cargo_funcionario = buscar_cargo_funcionario(guild)
        if cargo_funcionario:
            overwrites[cargo_funcionario] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        # Buscar (ou criar) a categoria "TICKETS"
        categoria_tickets = discord.utils.get(guild.categories, name="TICKETS")
        if not categoria_tickets:
            categoria_tickets = await guild.create_category("TICKETS")
            logger.info(f"Categoria 'TICKETS' criada automaticamente no servidor {guild.name}")

        channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            topic=f"Ticket de {interaction.user.name} | ID: {interaction.user.id}",
            category=categoria_tickets,
            overwrites=overwrites
        )

        await interaction.response.send_message(f"✅ Ticket criado: {channel.mention}", ephemeral=True)
        logger.info(f"Ticket criado por {interaction.user.name}: #{channel.name}")

        # Embed 1 — Boas-vindas e prazos
        embed_boas_vindas = discord.Embed(
            title="🧵 Atendimento Iniciado",
            description=(
                "Olá! Bem-vindo(a) ao atendimento da equipe **Artesanato de BW**! 🎨\n\n"
                "Você já pode descrever sua solicitação aqui neste canal. "
                "Nossa equipe irá atendê-lo(a) o mais rápido possível."
            ),
            color=CORES['ticket']
        )
        embed_boas_vindas.add_field(
            name="📋 Prazo de Produção",
            value="A equipe tem um prazo de até **48 horas úteis** para confeccionar o seu pedido.",
            inline=False
        )
        embed_boas_vindas.add_field(
            name="📦 Retirada / Entrega",
            value="Após a finalização, o cliente tem **24 horas úteis** para buscar ou receber o pedido.",
            inline=False
        )

        # Embed 2 — Política de desistência
        embed_aviso = discord.Embed(
            title="⚠️ Atenção — Política de Desistência",
            description=(
                "Caso o cliente não responda mais neste ticket ou não retire/receba o pedido dentro do prazo, "
                "o pedido poderá ser **vendido para outros clientes** ou **colocado na loja**, pois será "
                "entendido como **desistência**. O ticket poderá ser **encerrado sem aviso prévio**."
            ),
            color=CORES['aviso']
        )

        await channel.send(embeds=[embed_boas_vindas, embed_aviso], view=TicketControls())
        await channel.send("@everyone")



# --- Cog Principal ---
class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup-ticket", description="Envia o painel de abertura de tickets no canal atual.")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_ticket(self, interaction: discord.Interaction):
        embed = discord.Embed(title=TITULO_EMBED, description=DESCRICAO_EMBED, color=CORES['ticket'])
        await interaction.channel.send(embed=embed, view=TicketLauncher())
        await interaction.response.send_message("✅ Painel de tickets enviado!", ephemeral=True)
        logger.info(f"Painel de tickets enviado em #{interaction.channel.name} por {interaction.user.name}")

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info("--- Ticket System V5.0 Carregado ---")
        self.bot.add_view(TicketLauncher())
        self.bot.add_view(TicketControls())
        self.bot.add_view(TicketEncerramento())
        self.bot.add_view(BotaoAvaliar())

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))
