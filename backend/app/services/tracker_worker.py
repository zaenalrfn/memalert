import asyncio
import logging
from datetime import datetime
from backend.app.core.database import get_db_connection
from backend.app.services.dexscreener_client import DexScreenerClient
from backend.app.services.filter_engine import FilterEngine
from backend.app.services.telegram_service import TelegramBotService

logger = logging.getLogger(__name__)

class TrackerWorker:
    def __init__(self, telegram_service: TelegramBotService):
        self.dex_client = DexScreenerClient()
        self.filter_engine = FilterEngine()
        self.telegram_service = telegram_service
        self.is_running = False

    async def start(self):
        self.is_running = logger.info("Tracker Worker started loop.") or True
        while self.is_running:
            try:
                await self.poll_cycle()
            except Exception as e:
                logger.error(f"Error in TrackerWorker poll cycle: {e}")

            # Fetch polling interval from DB config
            interval = 20
            try:
                async with get_db_connection() as db:
                    async with db.execute("SELECT polling_interval_seconds FROM filter_config WHERE id = 1") as cursor:
                        row = await cursor.fetchone()
                        if row and row["polling_interval_seconds"]:
                            interval = int(row["polling_interval_seconds"])
            except Exception:
                pass

            await asyncio.sleep(interval)

    async def poll_cycle(self):
        # 1. Fetch config and mute state
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM filter_config WHERE id = 1") as cursor:
                cfg_row = await cursor.fetchone()
                config = dict(cfg_row) if cfg_row else {}

            async with db.execute("SELECT * FROM mute_state WHERE id = 1") as cursor:
                mute_row = await cursor.fetchone()
                mute_state = dict(mute_row) if mute_row else {}

        # Check auto-unmute expiration
        is_muted = bool(mute_state.get("is_muted", 0))
        mute_until = mute_state.get("mute_until")
        if is_muted and mute_until:
            try:
                until_dt = datetime.strptime(mute_until, "%Y-%m-%d %H:%M:%S")
                if datetime.utcnow() >= until_dt:
                    # Expired -> unmute and send summary
                    async with get_db_connection() as db:
                        async with db.execute("SELECT COUNT(*) as cnt FROM tokens_seen WHERE status = 'alerted_muted' AND first_seen_at >= ?", (mute_state.get("muted_at"),)) as cursor:
                            r = await cursor.fetchone()
                            muted_count = r["cnt"] if r else 0

                        await db.execute("""
                            UPDATE mute_state
                            SET is_muted = 0, muted_at = NULL, mute_until = NULL, muted_by = 'system'
                            WHERE id = 1
                        """)
                        await db.commit()

                    if self.telegram_service:
                        summary_msg = f"🔊 <b>Mute Berakhir Otomatis!</b>\nAda {muted_count} token lolos filter selama masa mute. Gunakan /history untuk melihat daftar."
                        # send direct message via telegram api
                        await self.send_raw_telegram(summary_msg)
                    is_muted = False
            except Exception as e:
                logger.error(f"Error checking mute expiration: {e}")

        # 2. Fetch latest solana pairs
        pairs = await self.dex_client.fetch_latest_solana_pairs()
        if not pairs:
            logger.info("No Solana pairs fetched in this cycle.")
            return
        logger.info(f"Processing {len(pairs)} Solana pairs...")

        async with get_db_connection() as db:
            for pair in pairs:
                parsed = self.dex_client.parse_pair_data(pair)
                token_address = parsed.get("token_address")
                if not token_address:
                    continue

                # 3. Check deduplication
                async with db.execute("SELECT 1 FROM tokens_seen WHERE token_address = ?", (token_address,)) as cursor:
                    exists = await cursor.fetchone()
                    if exists:
                        continue

                # 4. Evaluate filter engine
                passed, reason = await self.filter_engine.evaluate_token(parsed, config)

                if passed:
                    logger.info(f"TOKEN ALERTED: ${parsed.get('symbol')} | Liq=${parsed.get('liquidity_usd'):.0f} | Vol5m=${parsed.get('volume_5m_usd'):.0f}")
                else:
                    logger.info(f"Token REJECTED: ${parsed.get('symbol')} | Reason: {reason}")

                if not passed:
                    await db.execute("""
                        INSERT INTO tokens_seen (
                            token_address, pair_address, symbol, name, chain,
                            liquidity_usd, market_cap_usd, volume_5m_usd, pool_created_at, status, rejection_reason
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'rejected', ?)
                    """, (
                        token_address,
                        parsed["pair_address"],
                        parsed["symbol"],
                        parsed["name"],
                        parsed["chain"],
                        parsed["liquidity_usd"],
                        parsed["market_cap_usd"],
                        parsed["volume_5m_usd"],
                        None, # can be parsed if needed
                        reason
                    ))
                    await db.commit()
                    continue

                # 5. Token PASSED! Check mute state
                if is_muted:
                    status = "alerted_muted"
                    await db.execute("""
                        INSERT INTO tokens_seen (
                            token_address, pair_address, symbol, name, chain,
                            liquidity_usd, market_cap_usd, volume_5m_usd, pool_created_at, status, rejection_reason
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
                    """, (
                        token_address,
                        parsed["pair_address"],
                        parsed["symbol"],
                        parsed["name"],
                        parsed["chain"],
                        parsed["liquidity_usd"],
                        parsed["market_cap_usd"],
                        parsed["volume_5m_usd"],
                        None,
                        status
                    ))
                    await db.commit()
                else:
                    status = "alerted"
                    await db.execute("""
                        INSERT INTO tokens_seen (
                            token_address, pair_address, symbol, name, chain,
                            liquidity_usd, market_cap_usd, volume_5m_usd, pool_created_at, status, rejection_reason
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
                    """, (
                        token_address,
                        parsed["pair_address"],
                        parsed["symbol"],
                        parsed["name"],
                        parsed["chain"],
                        parsed["liquidity_usd"],
                        parsed["market_cap_usd"],
                        parsed["volume_5m_usd"],
                        None,
                        status
                    ))
                    await db.commit()

                    if self.telegram_service:
                        await self.telegram_service.send_alert(parsed)

    async def send_raw_telegram(self, text: str):
        if not self.telegram_service or not self.telegram_service.token:
            return
        import httpx
        url = f"https://api.telegram.org/bot{self.telegram_service.token}/sendMessage"
        payload = {"chat_id": self.telegram_service.chat_id, "text": text, "parse_mode": "HTML"}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(url, json=payload)
        except Exception as e:
            logger.error(f"Error sending raw telegram message: {e}")
