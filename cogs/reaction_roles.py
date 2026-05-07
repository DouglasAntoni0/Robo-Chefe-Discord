import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View
import logging

from config import CORES

logger = logging.getLogger('bot.roles')


class PainelCargos(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="PC Gamer", style=discord.ButtonStyle.primary, custom_id="botao_cargo_pc")
    async def botao_cargo_pc_callback(self, interaction: discord.Interaction, button: Button):
        membro = interaction.user
        cargo = discord.utils.get(membro.guild.roles, name="PC Gamer")

        if cargo:
            if cargo in membro.roles:
                await membro.remove_roles(cargo)
                await interaction.response.send_message(f"Seu cargo '{cargo.name}' foi removido!", ephemeral=True)
                logger.info(f"{membro.name} removeu o cargo '{cargo.name}'")
            else:
                await membro.add_roles(cargo)
                await interaction.response.send_message(f"Você recebeu o cargo '{cargo.name}'!", ephemeral=True)
                logger.info(f"{membro.name} recebeu o cargo '{cargo.name}'")
        else:
            await interaction.response.send_message("ERRO: O cargo 'PC Gamer' não foi encontrado no servidor.", ephemeral=True)
            logger.warning(f"Cargo 'PC Gamer' não encontrado em {interaction.guild.name}")

    @discord.ui.button(label="Mobile Gamer", style=discord.ButtonStyle.green, custom_id="botao_cargo_mobile")
    async def botao_cargo_mobile_callback(self, interaction: discord.Interaction, button: Button):
        membro = interaction.user
        cargo = discord.utils.get(membro.guild.roles, name="Mobile Gamer")

        if cargo:
            if cargo in membro.roles:
                await membro.remove_roles(cargo)
                await interaction.response.send_message(f"Seu cargo '{cargo.name}' foi removido!", ephemeral=True)
                logger.info(f"{membro.name} removeu o cargo '{cargo.name}'")
            else:
                await membro.add_roles(cargo)
                await interaction.response.send_message(f"Você recebeu o cargo '{cargo.name}'!", ephemeral=True)
                logger.info(f"{membro.name} recebeu o cargo '{cargo.name}'")
        else:
            await interaction.response.send_message("ERRO: O cargo 'Mobile Gamer' não foi encontrado no servidor.", ephemeral=True)
            logger.warning(f"Cargo 'Mobile Gamer' não encontrado em {interaction.guild.name}")


class ReactionRolesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(PainelCargos())
        logger.info("--- Reaction Roles System Carregado ---")

    @app_commands.command(name="painel-cargos", description="Envia o painel de cargos por botão no canal atual.")
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_cargos(self, interaction: discord.Interaction):
        embed_painel = discord.Embed(
            title="✨ Painel de Cargos ✨",
            description="Reaja com os botões abaixo para receber o cargo de sua plataforma preferida!",
            color=CORES['cargo']
        )
        await interaction.channel.send(embed=embed_painel, view=PainelCargos())
        await interaction.response.send_message("✅ Painel de cargos enviado!", ephemeral=True)
        logger.info(f"Painel de cargos enviado em #{interaction.channel.name} por {interaction.user.name}")

async def setup(bot):
    await bot.add_cog(ReactionRolesCog(bot))