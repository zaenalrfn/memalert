import asyncio
import logging
from datetime import datetime
from backend.app.core.database import get_db_connection
from backend.app.services.dexscreener_client import DexScreenerClient
from backend.app.services.filter_engine import FilterEngine
from backend.app.services.spk_engine import SPKEngine
from backend.app.services.telegram_service import TelegramBotService

logger = logging.getLogger(__name__)

class TrackerWorker:
    def __init__(self, telegram_service: TelegramBotService):
        self.dex_client = DexScreenerClient()
        self.filter_engine = FilterEngine()
        self.spk_engine = SPKEngine()
        self.telegram_service = telegram_service
        self.is_running = False

    async def start(self):
        self.is_running = True
        logger.info("Tracker Worker started loop.")
        while self.is_running:
            try:
                await self.poll_cycle()
            except Exception as e:
                logger.error(f"Error in TrackerWorker poll cycle: {e}")
            
            interval = 20
            try:
                async with get_db_connection() as db:
                    async with db.execute("SELECT polling_interval_seconds FROM filter_config WHERE id = 1") as cursor:
                        row = await cursor.fetchone()
                        if row: interval = int(row["polling_interval_seconds"])
            except: pass
            await asyncio.sleep(interval)

    async def poll_cycle(self):
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM filter_config WHERE id = 1") as cursor:
                cfg_row = await cursor.fetchone()
                config = dict(cfg_row) if cfg_row else {}
            
            async with db.execute("SELECT * FROM mute_state WHERE id = 1") as cursor:
                mute_row = await cursor.fetchone()
                mute_state = dict(mute_row) if mute_row else {}

        is_muted = bool(mute_state.get("is_muted", 0))
        pairs = await self.dex_client.fetch_latest_solana_pairs()
        if not pairs: return

        # Pre-calculate SPK Scores for the batch (SAW normalisasi)
        parsed_batch = [self.dex_client.parse_pair_data(p) for p in pairs]
        
        # We need safety scores for SAW
        for p in parsed_batch:
            p["safety_score"] = self.spk_engine.calculate_safety_score({"top_holder_pct": 0.3}) # default placeholder

        async with get_db_connection() as db:
            for parsed in parsed_batch:
                token_address = parsed.get("token_address")
                async with db.execute("SELECT 1 FROM tokens_seen WHERE token_address = ?", (token_address,)) as cursor:
                    if await cursor.fetchone(): continue

                passed, reason, updated_data = await self.filter_engine.evaluate_token(parsed, config)
                
                # Calculate SAW SPK Score
                updated_data["spk_score"] = self.spk_engine.calculate_saw_score(updated_data, parsed_batch)

                status = "rejected" if not passed else ("alerted_muted" if is_muted else "alerted")
                
                await db.execute("""
                    INSERT INTO tokens_seen (
                        token_address, pair_address, symbol, name, liquidity_usd, market_cap_usd, 
                        volume_5m_usd, safety_score, spk_score, graduation_status, 
                        mint_renounced, freeze_renounced, lp_status, top_holder_pct, status, rejection_reason
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    token_address, updated_data.get("pair_address", ""), updated_data.get("symbol", "UNKNOWN"), updated_data.get("name", "Unknown"),
                    updated_data.get("liquidity_usd", 0.0), updated_data.get("market_cap_usd", 0.0), updated_data.get("volume_5m_usd", 0.0),
                    updated_data.get("safety_score", 0.0), updated_data.get("spk_score", 0.0), updated_data.get("graduation_status", "bonding_curve"),
                    1 if updated_data.get("mint_renounced", True) else 0, 1 if updated_data.get("freeze_renounced", True) else 0,
                    updated_data.get("lp_status", "unknown"), updated_data.get("top_holder_pct"), status, reason if not passed else None
                ))
                await db.commit()

                if passed and not is_muted and self.telegram_service:
                    await self.telegram_service.send_alert(updated_data)
