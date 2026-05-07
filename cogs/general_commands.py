import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import platform
import logging

from config import CORES

logger = logging.getLogger('bot.general')


class GeneralCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="sobre", description="Mostra informações sobre o bot.")
    @app_commands.checks.cooldown(1, 10.0)
    async def sobre_slash(self, interaction: discord.Interaction):
        embed_sobre = discord.Embed(title="Painel de Ajuda do CHEFE", description="Estes são os comandos que eu conheço!", color=CORES['principal'])
        embed_sobre.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        embed_sobre.add_field(name="`/sobre`", value="Mostra este painel de ajuda.", inline=False)
        embed_sobre.add_field(name="`/hora`", value="Mostra a data e hora atuais.", inline=False)
        embed_sobre.add_field(name="`/falar`", value="Faz o bot enviar uma mensagem anônima.", inline=False)
        embed_sobre.add_field(name="`/status`", value="Mostra informações técnicas do bot.", inline=False)
        embed_sobre.add_field(name="`/criar-embed`", value="Abre formulário para criar anúncio.", inline=False)
        embed_sobre.add_field(name="`/config-welcome`", value="Configura o sistema de boas-vindas.", inline=False)
        embed_sobre.set_footer(text=f"Solicitado por: {interaction.user.name}")
        await interaction.response.send_message(embed=embed_sobre)
        logger.info(f"{interaction.user.name} usou /sobre")

    @app_commands.command(name="hora", description="Mostra a data e hora atuais.")
    @app_commands.checks.cooldown(1, 5.0)
    async def hora_slash(self, interaction: discord.Interaction):
        agora = datetime.now()
        await interaction.response.send_message(f"Agora são {agora.strftime('%H:%M:%S')} do dia {agora.strftime('%d/%m/%Y')}.")

    @app_commands.command(name="falar", description="Faz o bot enviar uma mensagem anônima no canal.")
    @app_commands.describe(mensagem="O texto que o bot deve falar.")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.checks.cooldown(1, 5.0)
    async def falar_slash(self, interaction: discord.Interaction, mensagem: str):
        await interaction.response.send_message("Mensagem enviada com sucesso!", ephemeral=True)
        await interaction.channel.send(mensagem)
        logger.info(f"{interaction.user.name} usou /falar em #{interaction.channel.name}")

    @app_commands.command(name="status", description="Mostra informações técnicas do bot.")
    @app_commands.checks.cooldown(1, 10.0)
    async def status_slash(self, interaction: discord.Interaction):
        uptime = datetime.now() - self.bot.start_time
        horas, resto = divmod(int(uptime.total_seconds()), 3600)
        minutos, segundos = divmod(resto, 60)
        uptime_str = f"{horas}h {minutos}m {segundos}s" if horas > 0 else f"{minutos}m {segundos}s"
        total_membros = sum(g.member_count for g in self.bot.guilds)
        latencia = round(self.bot.latency * 1000)

        embed = discord.Embed(title="📊 Status do Robô Chefe", color=CORES['principal'], timestamp=discord.utils.utcnow())
        embed.add_field(name="🏓 Latência", value=f"`{latencia}ms`", inline=True)
        embed.add_field(name="⏱️ Uptime", value=f"`{uptime_str}`", inline=True)
        embed.add_field(name="🌐 Servidores", value=f"`{len(self.bot.guilds)}`", inline=True)
        embed.add_field(name="👥 Membros", value=f"`{total_membros}`", inline=True)
        embed.add_field(name="🐍 Python", value=f"`{platform.python_version()}`", inline=True)
        embed.add_field(name="📦 discord.py", value=f"`{discord.__version__}`", inline=True)
        embed.set_footer(text=f"Solicitado por {interaction.user.name}")
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        logger.info(f"{interaction.user.name} usou /status")

async def setup(bot):
    await bot.add_cog(GeneralCommands(bot))
