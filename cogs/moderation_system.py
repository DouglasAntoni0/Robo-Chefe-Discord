import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite
import os
import json
import logging
from datetime import datetime

from config import CORES

logger = logging.getLogger('bot.moderation')

DB_FILE = 'warnings.db'
JSON_LEGACY = 'warnings.json'


class ModerationSystemCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS warnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    membro_id INTEGER NOT NULL,
                    moderador_id INTEGER NOT NULL,
                    moderador_nome TEXT NOT NULL,
                    motivo TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            ''')
            await db.commit()
        logger.info("--- Moderation System (SQLite) Carregado ---")
        await self._migrate_from_json()

    async def _migrate_from_json(self):
        if not os.path.exists(JSON_LEGACY):
            return
        logger.info("Migrando warnings.json para SQLite...")
        try:
            with open(JSON_LEGACY, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
            if not old_data:
                return
            async with aiosqlite.connect(DB_FILE) as db:
                for membro_id, avisos in old_data.items():
                    for aviso in avisos:
                        await db.execute(
                            'INSERT INTO warnings (guild_id, membro_id, moderador_id, moderador_nome, motivo, timestamp) VALUES (?, ?, ?, ?, ?, ?)',
                            (0, int(membro_id), aviso.get('moderador_id', 0), aviso.get('moderador_nome', 'Desconhecido'), aviso.get('motivo', 'Sem motivo'), aviso.get('timestamp', 'Data desconhecida'))
                        )
                await db.commit()
            os.rename(JSON_LEGACY, JSON_LEGACY + '.bak')
            logger.info("Migração concluída!")
        except Exception as e:
            logger.error(f"Erro durante migração do JSON: {e}")

    @app_commands.command(name="avisar", description="Aplica um aviso a um membro.")
    @app_commands.describe(membro="O membro que você quer avisar.", motivo="O motivo do aviso.")
    @app_commands.checks.has_permissions(kick_members=True)
    @app_commands.checks.cooldown(1, 5.0)
    async def avisar(self, interaction: discord.Interaction, membro: discord.Member, motivo: str):
        timestamp = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute(
                'INSERT INTO warnings (guild_id, membro_id, moderador_id, moderador_nome, motivo, timestamp) VALUES (?, ?, ?, ?, ?, ?)',
                (interaction.guild.id, membro.id, interaction.user.id, interaction.user.name, motivo, timestamp)
            )
            await db.commit()
            cursor = await db.execute('SELECT COUNT(*) FROM warnings WHERE membro_id = ? AND guild_id = ?', (membro.id, interaction.guild.id))
            total = (await cursor.fetchone())[0]

        embed_aviso = discord.Embed(title="✅ Aviso Aplicado", description=f"O membro {membro.mention} foi avisado.", color=CORES['moderacao'])
        embed_aviso.add_field(name="Motivo", value=motivo, inline=False)
        embed_aviso.add_field(name="Total de Avisos", value=f"⚠️ {total} aviso(s)", inline=True)
        embed_aviso.set_footer(text=f"Avisado por: {interaction.user.name}")
        await interaction.response.send_message(embed=embed_aviso)
        logger.info(f"{interaction.user.name} avisou {membro.name} por: {motivo} (total: {total})")

    @app_commands.command(name="avisos", description="Mostra o histórico de avisos de um membro.")
    @app_commands.describe(membro="O membro cujo histórico você quer ver.")
    @app_commands.checks.cooldown(1, 5.0)
    async def avisos(self, interaction: discord.Interaction, membro: discord.Member):
        async with aiosqlite.connect(DB_FILE) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT * FROM warnings WHERE membro_id = ? AND guild_id = ? ORDER BY id', (membro.id, interaction.guild.id))
            avisos = await cursor.fetchall()

        if not avisos:
            embed = discord.Embed(title=f"Histórico de {membro.name}", description="Histórico limpo! Nenhum aviso.", color=CORES['sucesso'])
            await interaction.response.send_message(embed=embed)
            return

        embed_lista = discord.Embed(title=f"Histórico de Avisos de {membro.name}", color=CORES['aviso'])
        embed_lista.set_thumbnail(url=membro.avatar.url if membro.avatar else None)
        for i, aviso in enumerate(avisos):
            embed_lista.add_field(name=f"📝 Aviso #{i + 1} - Em {aviso['timestamp']}", value=f"**Por:** {aviso['moderador_nome']}\n**Motivo:** {aviso['motivo']}", inline=False)
        await interaction.response.send_message(embed=embed_lista)

    @app_commands.command(name="limpar-avisos", description="Remove todos os avisos de um membro.")
    @app_commands.describe(membro="O membro cujos avisos serão removidos.")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 10.0)
    async def limpar_avisos(self, interaction: discord.Interaction, membro: discord.Member):
        async with aiosqlite.connect(DB_FILE) as db:
            cursor = await db.execute('SELECT COUNT(*) FROM warnings WHERE membro_id = ? AND guild_id = ?', (membro.id, interaction.guild.id))
            total = (await cursor.fetchone())[0]
            await db.execute('DELETE FROM warnings WHERE membro_id = ? AND guild_id = ?', (membro.id, interaction.guild.id))
            await db.commit()

        embed = discord.Embed(title="🗑️ Avisos Removidos", description=f"Todos os **{total}** aviso(s) de {membro.mention} foram removidos.", color=CORES['sucesso'])
        embed.set_footer(text=f"Removido por: {interaction.user.name}")
        await interaction.response.send_message(embed=embed)
        logger.info(f"{interaction.user.name} limpou {total} avisos de {membro.name}")

    @app_commands.command(name="limpar-canal", description="Apaga TODAS as mensagens do canal atual.")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 30.0)
    async def limpar_canal(self, interaction: discord.Interaction):
        await interaction.response.send_message("🗑️ Apagando todas as mensagens...", ephemeral=True)
        canal = interaction.channel
        total = 0
        while True:
            deleted = await canal.purge(limit=100)
            total += len(deleted)
            if len(deleted) < 100:
                break
        logger.info(f"{interaction.user.name} limpou {total} mensagens em #{canal.name}")

async def setup(bot):
    await bot.add_cog(ModerationSystemCog(bot))