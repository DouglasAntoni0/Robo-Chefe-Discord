import discord
from discord import app_commands
from discord.ext import commands
import os
import logging
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime

from config import setup_logging, CORES, DISCORD_TOKEN

setup_logging()
logger = logging.getLogger('bot.main')


# --- Health Check para Koyeb ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"O Chefe ta ON e roteando!")

    def log_message(self, format, *args):
        return

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

def start_health_check():
    t = Thread(target=run_server)
    t.daemon = True
    t.start()
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Health Check HTTP server iniciado na porta {port}")


# --- Bot ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
bot.start_time = datetime.now()


@bot.event
async def setup_hook():
    logger.info('Carregando Cogs...')
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                logger.info(f'  ✅ Cog {filename} carregado')
            except Exception as e:
                logger.error(f'  ❌ Falha ao carregar {filename}: {e}')
    logger.info('Carregamento de Cogs concluído')


@bot.event
async def on_ready():
    logger.info(f'Logado como {bot.user} (ID: {bot.user.id})')
    logger.info(f'Conectado a {len(bot.guilds)} servidor(es)')
    logger.info('------------------------------------')
    logger.info('Robô está online e pronto para uso!')


# --- Error Handler Global ---
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    embed_erro = discord.Embed(color=CORES['erro'])
    cmd_name = interaction.command.name if interaction.command else "desconhecido"

    if isinstance(error, app_commands.CommandNotFound):
        embed_erro.title = "❌ Comando Desatualizado"
        embed_erro.description = "Este comando não existe mais. Use `!sync` para atualizar os comandos."
        logger.warning(f"Comando não encontrado: {error}")

    elif isinstance(error, app_commands.MissingPermissions):
        embed_erro.title = "⛔ Sem Permissão"
        embed_erro.description = "Você não tem permissão para usar este comando."
        logger.warning(f"Permissão negada: {interaction.user} tentou usar /{cmd_name}")

    elif isinstance(error, app_commands.CommandOnCooldown):
        embed_erro.title = "⏳ Cooldown Ativo"
        embed_erro.description = f"Aguarde **{error.retry_after:.1f}s** antes de usar este comando novamente."

    elif isinstance(error, app_commands.BotMissingPermissions):
        embed_erro.title = "🤖 Bot Sem Permissão"
        embed_erro.description = "Eu não tenho permissão suficiente para executar essa ação. Verifique meus cargos!"
        logger.warning(f"Bot sem permissão para /{cmd_name} em {interaction.guild.name}")

    else:
        embed_erro.title = "❌ Erro Inesperado"
        embed_erro.description = "Ocorreu um erro ao executar este comando. Os administradores foram notificados."
        logger.error(f"Erro em /{cmd_name}: {error}", exc_info=True)

    try:
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed_erro, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed_erro, ephemeral=True)
    except Exception:
        pass


# --- Sync (único comando com prefixo — necessário para sincronizar slash commands) ---
@bot.command()
@commands.is_owner()
async def sync(ctx, spec: str = None):
    if spec == "clear":
        ctx.bot.tree.clear_commands(guild=ctx.guild)
        await ctx.bot.tree.sync(guild=ctx.guild)
        await ctx.send("Comandos locais limpos para este servidor.")
        return
    guild = ctx.guild
    ctx.bot.tree.copy_global_to(guild=guild)
    synced = await ctx.bot.tree.sync(guild=guild)
    await ctx.send(f"Sincronizado {len(synced)} comandos para este servidor.")
    logger.info(f"Sincronizado {len(synced)} comandos para {guild.name}")


if not DISCORD_TOKEN:
    logger.critical("DISCORD_TOKEN não encontrado! Configure a variável de ambiente ou o arquivo .env")
    exit(1)

start_health_check()
bot.run(DISCORD_TOKEN, log_handler=None)
