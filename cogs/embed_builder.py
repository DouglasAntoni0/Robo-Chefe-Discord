import discord
from discord import app_commands
from discord.ext import commands
import logging

from config import CORES

logger = logging.getLogger('bot.embed')


class EmbedBuilderModal(discord.ui.Modal, title="Criador de Anúncios (Embed)"):

    titulo = discord.ui.TextInput(label="Título do Embed", placeholder="Ex: Atualização do Servidor", style=discord.TextStyle.short, required=True)
    descricao = discord.ui.TextInput(label="Descrição / Conteúdo Principal", placeholder="Use **texto** para negrito.", style=discord.TextStyle.paragraph, required=True)
    cor = discord.ui.TextInput(label="Cor da Barra Lateral (Código Hex)", placeholder="Ex: #3498db", style=discord.TextStyle.short, required=False)
    mencao = discord.ui.TextInput(label="Menção (Opcional)", placeholder="Ex: @everyone", style=discord.TextStyle.short, required=False)
    url_imagem_rodape = discord.ui.TextInput(label="URL da Imagem do Rodapé (Opcional)", placeholder="https://imgur.com/link.png", style=discord.TextStyle.short, required=False)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await interaction.response.send_message("Criando seu embed...", ephemeral=True)
            hex_color = self.cor.value.replace("#", "")
            final_color = discord.Color(CORES['principal'])
            if hex_color:
                final_color = discord.Color(int(hex_color, 16))
            embed = discord.Embed(title=self.titulo.value, description=self.descricao.value, color=final_color, timestamp=discord.utils.utcnow())
            if self.url_imagem_rodape.value:
                embed.set_footer(icon_url=self.url_imagem_rodape.value)
            mensagem_a_enviar = self.mencao.value if self.mencao.value else None
            await interaction.channel.send(content=mensagem_a_enviar, embed=embed)
            await interaction.edit_original_response(content="Embed enviado com sucesso!")
            logger.info(f"{interaction.user.name} criou um embed: '{self.titulo.value}'")
        except Exception as e:
            logger.error(f"Erro ao processar modal de embed: {e}", exc_info=True)
            await interaction.followup.send("Ocorreu um erro ao enviar o embed.", ephemeral=True)


class EmbedBuilderCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="criar-embed", description="Abre um formulário para criar um anúncio anônimo (Embed).")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.checks.cooldown(1, 10.0)
    async def criar_embed(self, interaction: discord.Interaction):
        await interaction.response.send_modal(EmbedBuilderModal())

async def setup(bot):
    await bot.add_cog(EmbedBuilderCog(bot))