import discord
from discord.ext import commands, tasks
import asyncio
import logging
from datetime import datetime, timedelta, timezone

from config import CORES

logger = logging.getLogger('bot.logs')


class LoggingSystemCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.log_channel_name = "📜logs"
        self.LOG_MAX_DAYS = 7  # Dias para manter as logs antes de apagar
        self._auto_limpar_logs.start()

    def cog_unload(self):
        """Para o loop quando o cog é descarregado."""
        self._auto_limpar_logs.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info("--- Logging System Carregado ---")

    # ─── Auto-Limpeza de Logs ────────────────────────────────────────────

    async def _purgar_logs_antigos(self, guild: discord.Guild) -> int:
        """
        Apaga SOMENTE as mensagens com mais de LOG_MAX_DAYS dias
        no canal de logs do servidor.

        Cada mensagem é avaliada individualmente pelo seu created_at.
        Mensagens mais recentes são preservadas.

        Retorna: quantidade de mensagens apagadas.
        """
        log_channel = self._get_log_channel(guild)
        if not log_channel:
            return 0

        limite = discord.utils.utcnow() - timedelta(days=self.LOG_MAX_DAYS)
        apagadas = 0

        # Percorre o histórico do canal do mais antigo para o mais novo
        # Usa before=limite+1dia como otimização (pega msgs perto do limite)
        async for mensagem in log_channel.history(limit=None, before=limite, oldest_first=True):
            try:
                await mensagem.delete()
                apagadas += 1
                # Respeita o rate limit do Discord (pequena pausa)
                await asyncio.sleep(0.8)
            except discord.NotFound:
                # Mensagem já foi apagada por outra coisa
                continue
            except discord.Forbidden:
                logger.warning(
                    f"Sem permissão para apagar msgs de log em {guild.name}"
                )
                break
            except discord.HTTPException as e:
                logger.error(f"Erro ao apagar msg de log: {e}")
                await asyncio.sleep(2)

        return apagadas

    @tasks.loop(hours=6)
    async def _auto_limpar_logs(self):
        """Loop automático que roda a cada 6 horas limpando logs antigas."""
        logger.info("🧹 Iniciando limpeza automática de logs...")
        total = 0
        for guild in self.bot.guilds:
            try:
                apagadas = await self._purgar_logs_antigos(guild)
                if apagadas > 0:
                    logger.info(
                        f"🧹 {guild.name}: {apagadas} log(s) com +{self.LOG_MAX_DAYS} dias apagada(s)"
                    )
                    total += apagadas
            except Exception as e:
                logger.error(f"Erro na limpeza de logs de {guild.name}: {e}")

        if total > 0:
            logger.info(f"🧹 Limpeza automática concluída — {total} log(s) apagada(s) no total")
        else:
            logger.info("🧹 Limpeza automática concluída — nenhuma log antiga encontrada")

    @_auto_limpar_logs.before_loop
    async def _antes_limpar(self):
        """Espera o bot estar pronto antes de iniciar o loop."""
        await self.bot.wait_until_ready()

    # ─── Comando Manual de Limpeza ───────────────────────────────────────

    @discord.app_commands.command(
        name="limpar-logs",
        description="🧹 Apaga manualmente todas as logs com mais de 7 dias"
    )
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def limpar_logs_cmd(self, interaction: discord.Interaction):
        """Comando slash para forçar a limpeza de logs antigas."""
        await interaction.response.defer(ephemeral=True)

        apagadas = await self._purgar_logs_antigos(interaction.guild)

        if apagadas > 0:
            embed = discord.Embed(
                title="🧹 Limpeza de Logs Concluída",
                description=(
                    f"**{apagadas}** log(s) com mais de **{self.LOG_MAX_DAYS} dias** "
                    f"foram apagadas do canal de logs."
                ),
                color=CORES['sucesso'],
                timestamp=discord.utils.utcnow()
            )
        else:
            embed = discord.Embed(
                title="✅ Tudo Limpo",
                description=(
                    f"Nenhuma log com mais de **{self.LOG_MAX_DAYS} dias** encontrada.\n"
                    f"O canal já está em dia!"
                ),
                color=CORES['info'],
                timestamp=discord.utils.utcnow()
            )

        embed.set_footer(text=f"Executado por {interaction.user.name}")
        await interaction.followup.send(embed=embed, ephemeral=True)
        logger.info(
            f"MANUAL_PURGE | Por: {interaction.user.name} | "
            f"Servidor: {interaction.guild.name} | Apagadas: {apagadas}"
        )

    # ─── Helpers ─────────────────────────────────────────────────────────

    def _get_log_channel(self, guild: discord.Guild):
        """Retorna o canal de logs do servidor, se existir."""
        return discord.utils.get(guild.text_channels, name=self.log_channel_name)

    async def _investigar_quem_apagou(self, message: discord.Message):
        """
        Usa TODOS os métodos possíveis para descobrir quem apagou a mensagem.

        Como funciona o Audit Log do Discord:
        ─────────────────────────────────────
        • O Discord SÓ cria uma entrada no audit log quando OUTRA pessoa
          (moderador/bot) apaga a mensagem de alguém.
        • Se a PRÓPRIA pessoa apaga sua mensagem, NÃO gera audit log.
        • Portanto:
            - Encontrou entrada recente no audit log → um moderador/bot apagou.
            - NÃO encontrou → a própria pessoa apagou.

        Métodos de verificação utilizados:
        ──────────────────────────────────
        1. Audit Log: message_delete (moderador apagando mensagem individual)
        2. Audit Log: message_bulk_delete (moderador usando purge/limpeza)
        3. Comparação de timestamp (ignora entradas antigas/reutilizadas)
        4. Verificação se o deletador é bot
        5. Inferência por eliminação (sem audit log = auto-delete)

        Retorna: (deleter: Member|None, metodo: str, confianca: str)
        """
        guild = message.guild
        agora = discord.utils.utcnow()
        # Janela de tempo: entradas de audit log mais velhas que isso são ignoradas
        janela = timedelta(seconds=10)

        deleter = None
        metodo = "desconhecido"
        confianca = "❓ Baixa"

        # ── MÉTODO 1: Audit Log — message_delete ────────────────────────
        try:
            async for entry in guild.audit_logs(limit=10, action=discord.AuditLogAction.message_delete):
                # Só considera entradas recentes (dentro da janela de tempo)
                if (agora - entry.created_at) > janela:
                    continue

                # Verifica se o alvo é o autor e o canal bate
                if (entry.target
                        and entry.target.id == message.author.id
                        and hasattr(entry, 'extra')
                        and entry.extra
                        and hasattr(entry.extra, 'channel')
                        and entry.extra.channel.id == message.channel.id):
                    deleter = entry.user
                    if deleter.bot:
                        metodo = "🤖 Audit Log — Apagada por BOT"
                        confianca = "🟢 Alta (audit log confirmou — bot)"
                    else:
                        metodo = "🛡️ Audit Log — Apagada por MODERADOR"
                        confianca = "🟢 Alta (audit log confirmou — moderador)"
                    break
        except discord.Forbidden:
            logger.warning(f"Sem permissão para ver audit log em {guild.name}")
            metodo = "⚠️ Sem acesso ao Audit Log"
            confianca = "🔴 Impossível verificar (sem permissão)"
            return deleter, metodo, confianca
        except Exception as e:
            logger.error(f"Erro ao consultar audit log message_delete: {e}")

        # ── MÉTODO 2: Audit Log — message_bulk_delete ────────────────────
        if deleter is None:
            try:
                async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.message_bulk_delete):
                    if (agora - entry.created_at) > janela:
                        continue
                    if (hasattr(entry, 'extra')
                            and entry.extra
                            and hasattr(entry.extra, 'channel')
                            and entry.extra.channel.id == message.channel.id):
                        deleter = entry.user
                        if deleter.bot:
                            metodo = "🤖 Audit Log (Bulk) — Limpeza por BOT"
                            confianca = "🟢 Alta (audit log bulk confirmou — bot)"
                        else:
                            metodo = "🛡️ Audit Log (Bulk) — Limpeza por MODERADOR"
                            confianca = "🟢 Alta (audit log bulk confirmou — moderador)"
                        break
            except discord.Forbidden:
                pass
            except Exception as e:
                logger.error(f"Erro ao consultar audit log bulk_delete: {e}")

        # ── MÉTODO 3: Inferência — se não achou no audit log ─────────────
        if deleter is None:
            # Sem entrada no audit log = a própria pessoa apagou
            deleter = message.author
            metodo = "👤 Auto-exclusão (próprio autor)"
            confianca = "🟡 Média-Alta (sem registro no audit log = auto-delete)"

        return deleter, metodo, confianca

    def _truncar(self, texto: str, limite: int = 1024) -> str:
        """Trunca texto para caber nos limites do embed do Discord."""
        if len(texto) <= limite:
            return texto
        return texto[:limite - 20] + "\n… [truncado]"

    # ─── Voice State Logging ─────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        log_channel = self._get_log_channel(member.guild)
        if not log_channel:
            return
        if before.channel == after.channel:
            return

        if before.channel is None and after.channel is not None:
            embed = discord.Embed(title="🎤 Entrada em Canal de Voz", description=f"{member.mention} entrou no canal de voz **{after.channel.name}**.", color=CORES['sucesso'], timestamp=discord.utils.utcnow())
            embed.set_author(name=member.name, icon_url=member.avatar.url if member.avatar else None)
            await log_channel.send(embed=embed)

        elif before.channel is not None and after.channel is None:
            embed = discord.Embed(title="🔇 Saída de Canal de Voz", description=f"{member.mention} saiu do canal de voz **{before.channel.name}**.", color=CORES['erro'], timestamp=discord.utils.utcnow())
            embed.set_author(name=member.name, icon_url=member.avatar.url if member.avatar else None)
            await log_channel.send(embed=embed)

        elif before.channel is not None and after.channel is not None:
            embed = discord.Embed(title="🔄 Movido entre Canais de Voz", description=f"{member.mention} se moveu de **{before.channel.name}** para **{after.channel.name}**.", color=CORES['info'], timestamp=discord.utils.utcnow())
            embed.set_author(name=member.name, icon_url=member.avatar.url if member.avatar else None)
            await log_channel.send(embed=embed)

    # ─── Mensagem Individual Apagada ─────────────────────────────────────

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        # Ignora bots e mensagens do próprio canal de logs
        if message.author.bot or not message.guild:
            return
        if message.channel.name == self.log_channel_name:
            return

        log_channel = self._get_log_channel(message.guild)
        if not log_channel:
            return

        # Espera o Discord propagar a entrada no audit log
        await asyncio.sleep(1.5)

        # ── Investigação ──
        deleter, metodo, confianca = await self._investigar_quem_apagou(message)
        is_self_delete = (deleter and deleter.id == message.author.id)

        if is_self_delete:
            cor = CORES.get('aviso', 0xF39C12)
            titulo = "🗑️ Mensagem Apagada"
        else:
            cor = CORES.get('moderacao', 0xE74C3C)
            titulo = "🛡️ Mensagem Apagada por Moderação"

        embed = discord.Embed(
            title=titulo,
            color=cor,
            timestamp=discord.utils.utcnow()
        )

        embed.set_author(
            name=message.author.display_name,
            icon_url=message.author.avatar.url if message.author.avatar else None
        )

        embed.description = f"**Autor:** {message.author.mention}\n**Canal:** {message.channel.mention}"

        # ── Conteúdo ──
        if message.content:
            embed.add_field(
                name="📝 Conteúdo",
                value=self._truncar(f"```\n{message.content}\n```"),
                inline=False
            )

        # ── Anexos (simplificado) ──
        if message.attachments:
            nomes = [f"📎 {att.filename}" for att in message.attachments]
            embed.add_field(
                name=f"📁 Anexos ({len(message.attachments)})",
                value="\n".join(nomes),
                inline=False
            )

        # ── Quem apagou (só se não foi o próprio autor) ──
        if deleter and not is_self_delete:
            embed.add_field(
                name="🔍 Apagada por",
                value=deleter.mention,
                inline=False
            )

        # ── Footer ──
        if is_self_delete:
            embed.set_footer(text="Apagada pelo próprio autor")
        elif deleter:
            embed.set_footer(text=f"Apagada por {deleter.name}")

        await log_channel.send(embed=embed)
        logger.info(
            f"MSG_DELETE | Autor: {message.author.name} | Canal: #{message.channel.name} "
            f"| Deletada por: {deleter.name if deleter else '???'}"
        )

    # ─── Mensagem Editada ─────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        # Ignora bots, DMs e canal de logs
        if before.author.bot or not before.guild:
            return
        if before.channel.name == self.log_channel_name:
            return

        # Ignora edições que não mudaram o conteúdo (ex: embed de link carregando)
        if before.content == after.content:
            return

        log_channel = self._get_log_channel(before.guild)
        if not log_channel:
            return

        embed = discord.Embed(
            title="✏️ Mensagem Editada",
            color=CORES.get('info', 0x3498DB),
            timestamp=discord.utils.utcnow()
        )

        embed.set_author(
            name=f"{after.author.display_name} ({after.author.name})",
            icon_url=after.author.avatar.url if after.author.avatar else None
        )

        desc_lines = [
            f"**Autor:** {after.author.mention} (`{after.author.id}`)",
            f"**Canal:** {after.channel.mention} (`#{after.channel.name}`)",
            f"**ID da Mensagem:** `{after.id}`",
            f"**[Ir para a mensagem]({after.jump_url})**",
        ]
        embed.description = "\n".join(desc_lines)

        # Conteúdo ANTES
        if before.content:
            embed.add_field(
                name="📝 Antes",
                value=self._truncar(f"```\n{before.content}\n```"),
                inline=False
            )
        else:
            embed.add_field(name="📝 Antes", value="_[sem texto]_", inline=False)

        # Conteúdo DEPOIS
        if after.content:
            embed.add_field(
                name="✏️ Depois",
                value=self._truncar(f"```\n{after.content}\n```"),
                inline=False
            )
        else:
            embed.add_field(name="✏️ Depois", value="_[sem texto]_", inline=False)

        # Anexos removidos
        antes_anexos = {a.id for a in before.attachments}
        depois_anexos = {a.id for a in after.attachments}
        removidos = antes_anexos - depois_anexos
        adicionados = depois_anexos - antes_anexos

        if removidos:
            nomes = [a.filename for a in before.attachments if a.id in removidos]
            embed.add_field(
                name=f"📁 Anexos Removidos ({len(removidos)})",
                value="\n".join(f"❌ {n}" for n in nomes),
                inline=True
            )
        if adicionados:
            nomes = [a.filename for a in after.attachments if a.id in adicionados]
            embed.add_field(
                name=f"📁 Anexos Adicionados ({len(adicionados)})",
                value="\n".join(f"✅ {n}" for n in nomes),
                inline=True
            )

        # Timestamps
        embed.add_field(
            name="📅 Mensagem criada em",
            value=f"<t:{int(before.created_at.timestamp())}:F> (<t:{int(before.created_at.timestamp())}:R>)",
            inline=False
        )

        embed.set_footer(text=f"Editada por: {after.author.name}")

        await log_channel.send(embed=embed)
        logger.info(
            f"MSG_EDIT | Autor: {after.author.name} | Canal: #{after.channel.name} "
            f"| ID: {after.id}"
        )

    # ─── Bulk Delete (purge / limpeza em massa) ─────────────────────────

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: list[discord.Message]):
        if not messages:
            return

        guild = messages[0].guild
        if not guild:
            return
        canal = messages[0].channel

        log_channel = self._get_log_channel(guild)
        if not log_channel:
            return
        if canal.name == self.log_channel_name:
            return

        await asyncio.sleep(1.5)

        # ── Tenta descobrir quem fez o purge ──
        responsavel = None
        metodo = "desconhecido"
        agora = discord.utils.utcnow()
        janela = timedelta(seconds=10)

        try:
            # Primeiro checa message_bulk_delete
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.message_bulk_delete):
                if (agora - entry.created_at) > janela:
                    continue
                if (hasattr(entry, 'extra')
                        and entry.extra
                        and hasattr(entry.extra, 'channel')
                        and entry.extra.channel.id == canal.id):
                    responsavel = entry.user
                    metodo = "🛡️ Audit Log (bulk_delete)" if not responsavel.bot else "🤖 Audit Log (bulk_delete — bot)"
                    break

            # Se não achou, checa message_delete normal (alguns bots apagam 1 por 1 rápido)
            if responsavel is None:
                async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.message_delete):
                    if (agora - entry.created_at) > janela:
                        continue
                    if (hasattr(entry, 'extra')
                            and entry.extra
                            and hasattr(entry.extra, 'channel')
                            and entry.extra.channel.id == canal.id):
                        responsavel = entry.user
                        metodo = "🛡️ Audit Log (message_delete)" if not responsavel.bot else "🤖 Audit Log (message_delete — bot)"
                        break
        except discord.Forbidden:
            metodo = "⚠️ Sem acesso ao Audit Log"
        except Exception as e:
            logger.error(f"Erro ao consultar audit log para bulk delete: {e}")

        # ── Monta o Embed ──
        embed = discord.Embed(
            title=f"🗑️ Limpeza em Massa — {len(messages)} mensagens apagadas",
            description=f"**Canal:** {canal.mention} (`#{canal.name}`)",
            color=CORES.get('moderacao', 0xE74C3C),
            timestamp=discord.utils.utcnow()
        )

        # Lista de autores afetados
        autores = {}
        for msg in messages:
            nome = msg.author.name if msg.author else "Desconhecido"
            autores[nome] = autores.get(nome, 0) + 1
        autores_str = "\n".join(f"• **{nome}**: {qtd} msg(s)" for nome, qtd in autores.items())
        embed.add_field(
            name="👥 Autores Afetados",
            value=self._truncar(autores_str) if autores_str else "Desconhecido",
            inline=False
        )

        # Quem executou o purge
        if responsavel:
            embed.add_field(
                name="🔍 Responsável pela Limpeza",
                value=f"{responsavel.mention} (`{responsavel.name}` — ID: `{responsavel.id}`)\n**É bot?** {'Sim 🤖' if responsavel.bot else 'Não 👤'}",
                inline=False
            )
        embed.add_field(name="🔬 Método", value=metodo, inline=True)

        # Amostra das mensagens apagadas (últimas 5)
        amostra = []
        for msg in messages[:5]:
            conteudo = msg.content[:80] if msg.content else "[sem texto]"
            autor = msg.author.name if msg.author else "?"
            amostra.append(f"**{autor}:** {conteudo}")
        if len(messages) > 5:
            amostra.append(f"_…e mais {len(messages) - 5} mensagem(ns)_")
        embed.add_field(
            name="📝 Amostra das Mensagens",
            value=self._truncar("\n".join(amostra)),
            inline=False
        )

        embed.set_footer(text=f"Total: {len(messages)} mensagens | Canal: #{canal.name}")

        await log_channel.send(embed=embed)
        logger.info(
            f"BULK_DELETE | Canal: #{canal.name} | {len(messages)} msgs "
            f"| Por: {responsavel.name if responsavel else '???'} | Método: {metodo}"
        )


async def setup(bot):
    await bot.add_cog(LoggingSystemCog(bot))