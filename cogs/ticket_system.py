import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
import asyncio
import logging

from config import CORES

logger = logging.getLogger('bot.tickets')

NOME_CARGO_FUNCIONARIO = "Funcionário"

def tem_permissao_ticket(member: discord.Member) -> bool:
    """Retorna True se o membro é admin OU tem o cargo 'Funcionário'."""
    if member.guild_permissions.administrator:
        return True
    return discord.utils.get(member.roles, name=NOME_CARGO_FUNCIONARIO) is not None

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


# --- Controles do Ticket (Fechar / Chamar) ---
class TicketControls(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Fechar Ticket", style=discord.ButtonStyle.red, custom_id="fechar_ticket_btn", emoji="🔒")
    async def fechar_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not tem_permissao_ticket(interaction.user):
            await interaction.response.send_message("⛔ **Apenas Administradores ou Funcionários podem fechar o ticket!**", ephemeral=True)
            return

        await interaction.response.send_message("Fechando ticket e enviando formulário para o cliente...", ephemeral=True)

        channel = interaction.channel
        topic = channel.topic

        user_id = None
        if topic and "ID:" in topic:
            try:
                user_id = int(topic.split("ID: ")[1])
            except:
                pass

        logger.info(f"Ticket #{channel.name} fechado por {interaction.user.name}")
        await asyncio.sleep(2)
        await channel.delete()

        if user_id:
            user = interaction.guild.get_member(user_id)
            if user:
                try:
                    embed_dm = discord.Embed(title="Atendimento Encerrado", description=f"Olá! Seu ticket no servidor **{interaction.guild.name}** foi fechado.\nPor favor, dedique um segundo para nos avaliar clicando abaixo.", color=CORES['ticket'])
                    await user.send(embed=embed_dm, view=BotaoAvaliar())
                    logger.info(f"Formulário de avaliação enviado para {user.name}")
                except:
                    logger.warning(f"Não consegui enviar DM para {user.name}")

    @discord.ui.button(label="Chamar Cliente", style=discord.ButtonStyle.secondary, custom_id="chamar_cliente_btn", emoji="🔔")
    async def chamar_cliente(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not tem_permissao_ticket(interaction.user):
            await interaction.response.send_message("⛔ Apenas Admins ou Funcionários podem chamar o cliente.", ephemeral=True)
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
                    await interaction.response.send_message(f"✅ Notificação enviada para o privado de {user.mention}!", ephemeral=True)
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
        cargo_funcionario = discord.utils.get(guild.roles, name=NOME_CARGO_FUNCIONARIO)
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

        embed = discord.Embed(title="Atendimento Iniciado", description="Olá! Descreva sua solicitação. A equipe administrativa logo irá atendê-lo.", color=CORES['ticket'])
        await channel.send(embed=embed, view=TicketControls())


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
        logger.info("--- Ticket System V4.0 Carregado ---")
        self.bot.add_view(TicketLauncher())
        self.bot.add_view(TicketControls())
        self.bot.add_view(BotaoAvaliar())

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))
