import re
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
import httpx

from backend.app.core.config import settings
from backend.app.core.database import get_db_connection

logger = logging.getLogger(__name__)

def parse_duration(duration_str: str) -> Optional[int]:
    """
    Parse string durasi seperti '30m', '1h', '3h' ke total menit.
    """
    if not duration_str:
        return None
    match = re.match(r"^(\d+)([mh])$", duration_str.lower().strip())
    if not match:
        return None
    val, unit = match.groups()
    val = int(val)
    return val if unit == "m" else val * 60

class TelegramBotService:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.app: Optional[Application] = None

    def is_authorized(self, update: Update) -> bool:
        if not update.effective_chat:
            return False
        return str(update.effective_chat.id) == str(self.chat_id)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_authorized(update):
            return
        msg = (
            "🚀 <b>Solana Memecoin Tracker Bot Aktif!</b>\n\n"
            "Bot ini memantau token baru di Solana secara real-time.\n\n"
            "<b>Daftar Perintah:</b>\n"
            "• /status - Cek status bot & sisa waktu mute\n"
            "• /config - Lihat threshold filter aktif\n"
            "• /mute [30m|1h|3h] - Membisukan notifikasi alert\n"
            "• /unmute - Mengaktifkan kembali notifikasi\n"
            "• /history [limit] - Lihat token yang terlewat saat mute\n"
        )
        await update.message.reply_html(msg)

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_authorized(update):
            return
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM mute_state WHERE id = 1") as cursor:
                mute_row = await cursor.fetchone()
            
            async with db.execute("SELECT COUNT(*) as count FROM tokens_seen WHERE DATE(first_seen_at) = DATE('now') AND status = 'alerted'") as cursor:
                alerted_row = await cursor.fetchone()
                alerted_cnt = alerted_row["count"] if alerted_row else 0

            async with db.execute("SELECT COUNT(*) as count FROM tokens_seen WHERE DATE(first_seen_at) = DATE('now') AND status = 'alerted_muted'") as cursor:
                muted_row = await cursor.fetchone()
                muted_cnt = muted_row["count"] if muted_row else 0

        is_muted = bool(mute_row["is_muted"]) if mute_row else False
        mute_until = mute_row["mute_until"] if mute_row else None

        mute_status_text = "🔊 <b>Aktif (Unmuted)</b>"
        if is_muted:
            if mute_until:
                mute_status_text = f"🔇 <b>Muted</b> (Sampai: {mute_until} UTC)"
            else:
                mute_status_text = "🔇 <b>Muted Permanen</b> (Sampai /unmute)"

        msg = (
            "📊 <b>Status Bot Monitoring Solana</b>\n\n"
            f"<b>Status Alert:</b> {mute_status_text}\n"
            f"<b>Alert Terkirim Hari Ini:</b> {alerted_cnt}\n"
            f"<b>Alert Muted Hari Ini:</b> {muted_cnt}\n"
        )
        await update.message.reply_html(msg)

    async def config_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_authorized(update):
            return
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM filter_config WHERE id = 1") as cursor:
                cfg = await cursor.fetchone()

        if not cfg:
            await update.message.reply_text("Konfigurasi belum tersedia.")
            return

        msg = (
            "⚙️ <b>Filter Threshold Aktif</b>\n\n"
            f"• <b>Min Liquidity:</b> ${cfg['min_liquidity_usd']:,.0f}\n"
            f"• <b>Min Volume (5m):</b> ${cfg['min_volume_5m_usd']:,.0f}\n"
            f"• <b>Max Pool Age:</b> {cfg['max_age_minutes']} menit\n"
            f"• <b>Min Buy/Sell Ratio:</b> {cfg['min_buy_sell_ratio']}\n"
            f"• <b>Require LP Locked:</b> {'✅' if cfg['require_lp_locked'] else '❌'}\n"
            f"• <b>Require Mint Renounced:</b> {'✅' if cfg['require_mint_renounced'] else '❌'}\n"
            f"• <b>Blacklist Keywords:</b> <code>{cfg['blacklist_keywords']}</code>\n"
            f"• <b>Interval Polling:</b> {cfg['polling_interval_seconds']}s\n"
        )
        await update.message.reply_html(msg)

    async def mute_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_authorized(update):
            return
        args = context.args
        duration_str = args[0] if args else None
        minutes = parse_duration(duration_str) if duration_str else None

        now = datetime.utcnow()
        until_dt = now + timedelta(minutes=minutes) if minutes else None
        until_str = until_dt.strftime("%Y-%m-%d %H:%M:%S") if until_dt else None

        async with get_db_connection() as db:
            await db.execute("""
                UPDATE mute_state
                SET is_muted = 1, muted_at = ?, mute_until = ?, muted_by = 'telegram'
                WHERE id = 1
            """, (now.strftime("%Y-%m-%d %H:%M:%S"), until_str))
            await db.commit()

        if minutes:
            reply = f"🔇 Bot berhasil dibisukan selama <b>{duration_str}</b> (sampai {until_str} UTC).\nToken tetap dicatat di background."
        else:
            reply = "🔇 Bot dibisukan permanen sampai Anda mengirim perintah /unmute.\nToken tetap dicatat di background."
        
        await update.message.reply_html(reply)

    async def unmute_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_authorized(update):
            return
        async with get_db_connection() as db:
            await db.execute("""
                UPDATE mute_state
                SET is_muted = 0, muted_at = NULL, mute_until = NULL, muted_by = 'telegram'
                WHERE id = 1
            """, ())
            await db.commit()

        await update.message.reply_html("🔊 <b>Notifikasi Alert Diaktifkan Kembali!</b>\nAlert koin lolos filter akan langsung terkirim.")

    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_authorized(update):
            return
        args = context.args
        limit = int(args[0]) if args and args[0].isdigit() else 5

        async with get_db_connection() as db:
            async with db.execute("""
                SELECT symbol, name, token_address, liquidity_usd, first_seen_at
                FROM tokens_seen
                WHERE status = 'alerted_muted'
                ORDER BY first_seen_at DESC
                LIMIT ?
            """, (limit,)) as cursor:
                rows = await cursor.fetchall()

        if not rows:
            await update.message.reply_html("ℹ️ Tidak ada token yang terlewat saat mute.")
            return

        items = []
        for r in rows:
            items.append(
                f"• <b>${r['symbol']}</b> ({r['name']})\n"
                f"  <code>{r['token_address']}</code>\n"
                f"  💧 Liq: ${r['liquidity_usd']:,.0f} | ⏱️ {r['first_seen_at']}"
            )
        
        msg = f"📜 <b>{len(rows)} Token Terlewat Saat Mute Terakhir:</b>\n\n" + "\n\n".join(items)
        await update.message.reply_html(msg)

    async def send_alert(self, token_data: Dict[str, Any]):
        """
        Mengirimkan alert terformat ke Telegram chat
        """
        if not self.token or self.token == "YOUR_BOT_TOKEN":
            logger.warning("TELEGRAM_BOT_TOKEN belum dikonfigurasi.")
            return

        pair_url = token_data.get("url", f"https://dexscreener.com/solana/{token_data.get('pair_address')}")
        symbol = token_data.get("symbol", "UNKNOWN").upper()
        name = token_data.get("name", "Unknown Token")
        address = token_data.get("token_address", "")
        liquidity = token_data.get("liquidity_usd", 0.0)
        volume_5m = token_data.get("volume_5m_usd", 0.0)
        pair_created_at = token_data.get("pair_created_at")

        age_text = "Baru listing"
        if pair_created_at:
            age_min = (time.time() * 1000 - pair_created_at) / (1000 * 60)
            age_text = f"{age_min:.1f} menit"

        msg = (
            f"🚨 <b>NEW TOKEN ALERT — Solana</b>\n\n"
            f"🪙 <b>Token:</b> ${symbol} ({name})\n"
            f"📍 <b>Contract:</b> <code>{address}</code> <i>(tap to copy)</i>\n"
            f"💧 <b>Liquidity:</b> ${liquidity:,.0f}\n"
            f"📊 <b>Volume (5m):</b> ${volume_5m:,.0f}\n"
            f"⏱️ <b>Pool Age:</b> {age_text}\n\n"
            f"🔗 <a href='{pair_url}'>Lihat di DexScreener</a>\n\n"
            f"⚠️ <i>DYOR — Bukan saran finansial</i>\n"
            f"💡 <i>Ketik /mute 30m jika ingin membisukan alert</i>"
        )

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": msg,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code != 200:
                    logger.error(f"Failed to send Telegram alert: {res.text}")
        except Exception as e:
            logger.error(f"Exception sending Telegram alert: {e}")

    async def init_application(self) -> Optional[Application]:
        if not self.token or self.token == "YOUR_BOT_TOKEN":
            logger.warning("Telegram Bot Token is missing or placeholder.")
            return None

        try:
            builder = Application.builder().token(self.token)
            self.app = builder.build()

            self.app.add_handler(CommandHandler("start", self.start_command))
            self.app.add_handler(CommandHandler("status", self.status_command))
            self.app.add_handler(CommandHandler("config", self.config_command))
            self.app.add_handler(CommandHandler("mute", self.mute_command))
            self.app.add_handler(CommandHandler("unmute", self.unmute_command))
            self.app.add_handler(CommandHandler("history", self.history_command))

            await self.app.initialize()
            await self.app.start()
            if self.app.updater:
                await self.app.updater.start_polling()

            logger.info("Telegram Bot initialized and listening for commands.")
            return self.app
        except Exception as e:
            logger.error(f"Failed to start Telegram Application: {e}")
            return None
