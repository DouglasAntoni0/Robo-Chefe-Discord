import discord
from discord.ext import commands
from collections import defaultdict, deque
from datetime import timedelta
import logging
import re

from config import CORES

logger = logging.getLogger('bot.antispam')

MAX_MENSAGENS = 5
INTERVALO_SEGUNDOS = 5
TIMEOUT_MINUTOS = 5
MAX_MENCOES = 5
MAX_LINKS = 3
LINK_INTERVALO = 10


class AntiSpam(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.mensagens_historico = defaultdict(lambda: deque(maxlen=MAX_MENSAGENS + 5))
        self.links_historico = defaultdict(lambda: deque(maxlen=MAX_LINKS + 5))

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info("--- Anti-Spam System Carregado ---")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild or message.author.guild_permissions.administrator:
            return
        await self._check_flood(message)
        await self._check_mass_mentions(message)
        await self._check_link_spam(message)

    async def _check_flood(self, message: discord.Message):
        user_id = message.author.id
        agora = message.created_at
        self.mensagens_historico[user_id].append(agora)
        recentes = [t for t in self.mensagens_historico[user_id] if (agora - t).total_seconds() <= INTERVALO_SEGUNDOS]
        if len(recentes) >= MAX_MENSAGENS:
            await self._punir(message, "Flood de mensagens", f"{len(recentes)} msgs em {INTERVALO_SEGUNDOS}s")
            self.mensagens_historico[user_id].clear()

    async def _check_mass_mentions(self, message: discord.Message):
        total_mencoes = len(message.mentions) + len(message.role_mentions)
        if message.mention_everyone:
            total_mencoes += 10
        if total_mencoes >= MAX_MENCOES:
            await self._punir(message, "Menções em massa", f"{total_mencoes} menções")

    async def _check_link_spam(self, message: discord.Message):
        urls = re.findall(r'https?://\S+', message.content)
        if not urls:
            return
        user_id = message.author.id
        agora = message.created_at
        for _ in urls:
            self.links_historico[user_id].append(agora)
        recentes = [t for t in self.links_historico[user_id] if (agora - t).total_seconds() <= LINK_INTERVALO]
        if len(recentes) > MAX_LINKS:
            await self._punir(message, "Spam de links", f"{len(recentes)} links em {LINK_INTERVALO}s")
            self.links_historico[user_id].clear()

    async def _punir(self, message: discord.Message, tipo: str, detalhes: str):
        membro = message.author
        guild = message.guild

        try:
            await membro.timeout(timedelta(minutes=TIMEOUT_MINUTOS), reason=f"Anti-Spam: {tipo}")
            logger.warning(f"TIMEOUT em {membro.name} ({membro.id}) por {tipo}: {detalhes}")
        except discord.Forbidden:
            logger.warning(f"Sem permissão para timeout em {membro.name}")
            return
        except Exception as e:
            logger.error(f"Erro ao aplicar timeout: {e}")
            return

        try:
            await message.delete()
        except discord.Forbidden:
            pass

        embed_aviso = discord.Embed(title="🛡️ Anti-Spam Ativado", description=f"{membro.mention} foi silenciado por **{TIMEOUT_MINUTOS} minutos**.", color=CORES['moderacao'], timestamp=discord.utils.utcnow())
        embed_aviso.add_field(name="Motivo", value=tipo, inline=True)
        embed_aviso.add_field(name="Detalhes", value=detalhes, inline=True)
        embed_aviso.set_footer(text="Sistema automático de proteção")
        try:
            await message.channel.send(embed=embed_aviso, delete_after=15)
        except discord.Forbidden:
            pass

        log_channel = discord.utils.get(guild.text_channels, name="📜logs")
        if log_channel:
            embed_log = discord.Embed(title="🛡️ Anti-Spam — Ação Automática", color=CORES['log'], timestamp=discord.utils.utcnow())
            embed_log.add_field(name="Usuário", value=f"{membro.mention} ({membro.id})", inline=False)
            embed_log.add_field(name="Tipo", value=tipo, inline=True)
            embed_log.add_field(name="Detalhes", value=detalhes, inline=True)
            embed_log.add_field(name="Canal", value=message.channel.mention, inline=True)
            embed_log.add_field(name="Punição", value=f"Timeout de {TIMEOUT_MINUTOS} min", inline=False)
            try:
                await log_channel.send(embed=embed_log)
            except discord.Forbidden:
                pass

async def setup(bot):
    await bot.add_cog(AntiSpam(bot))
