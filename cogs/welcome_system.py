import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import logging

from config import CORES

logger = logging.getLogger('bot.welcome')

SETTINGS_FILE = 'guild_settings.json'


class WelcomeSystem(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.settings = self._load_settings()

    def _load_settings(self) -> dict:
        if not os.path.exists(SETTINGS_FILE):
            return {}
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}

    def _save_settings(self):
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=4, ensure_ascii=False)

    def _get_guild_settings(self, guild_id: int) -> dict:
        return self.settings.get(str(guild_id), {})

    @app_commands.command(name="config-welcome", description="Configura o sistema de boas-vindas do servidor.")
    @app_commands.describe(canal="Canal de boas-vindas.", cargo_auto="Cargo automático para novos membros.", ativar="Ativa ou desativa o sistema.")
    @app_commands.checks.has_permissions(administrator=True)
    async def config_welcome(self, interaction: discord.Interaction, canal: discord.TextChannel = None, cargo_auto: discord.Role = None, ativar: bool = True):
        guild_id = str(interaction.guild.id)
        if guild_id not in self.settings:
            self.settings[guild_id] = {}
        if canal:
            self.settings[guild_id]['welcome_channel_id'] = canal.id
        if cargo_auto:
            self.settings[guild_id]['auto_role_id'] = cargo_auto.id
        self.settings[guild_id]['enabled'] = ativar
        self._save_settings()

        embed = discord.Embed(title="✅ Boas-Vindas Configurado", color=CORES['sucesso'])
        if canal:
            embed.add_field(name="📢 Canal", value=canal.mention, inline=True)
        if cargo_auto:
            embed.add_field(name="🎭 Auto-Cargo", value=cargo_auto.mention, inline=True)
        embed.add_field(name="⚡ Status", value="Ativado" if ativar else "Desativado", inline=True)
        logger.info(f"Boas-vindas configurado em {interaction.guild.name}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        settings = self._get_guild_settings(member.guild.id)
        if not settings.get('enabled', False):
            return

        auto_role_id = settings.get('auto_role_id')
        if auto_role_id:
            role = member.guild.get_role(auto_role_id)
            if role:
                try:
                    await member.add_roles(role)
                    logger.info(f"Auto-role '{role.name}' dado para {member.name}")
                except discord.Forbidden:
                    logger.warning(f"Sem permissão para dar auto-role em {member.guild.name}")

        channel_id = settings.get('welcome_channel_id')
        if not channel_id:
            return
        channel = member.guild.get_channel(channel_id)
        if not channel:
            return

        embed = discord.Embed(
            title="👋 Bem-vindo(a) ao servidor!",
            description=f"Olá {member.mention}! Seja muito bem-vindo(a) ao **{member.guild.name}**!\n\nVocê é nosso **{member.guild.member_count}º** membro. 🎉\n\nLeia as regras e divirta-se!",
            color=CORES['boas_vindas'],
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text=f"ID: {member.id}")
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            logger.warning(f"Sem permissão para enviar boas-vindas em {member.guild.name}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        settings = self._get_guild_settings(member.guild.id)
        if not settings.get('enabled', False):
            return
        channel_id = settings.get('welcome_channel_id')
        if not channel_id:
            return
        channel = member.guild.get_channel(channel_id)
        if not channel:
            return

        embed = discord.Embed(title="😢 Alguém nos deixou...", description=f"**{member.name}** saiu do servidor. Sentiremos sua falta!", color=CORES['despedida'], timestamp=discord.utils.utcnow())
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            logger.warning(f"Sem permissão para enviar despedida em {member.guild.name}")

async def setup(bot):
    await bot.add_cog(WelcomeSystem(bot))
