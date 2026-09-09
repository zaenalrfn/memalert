import aiosqlite
import logging
from contextlib import asynccontextmanager
from backend.app.core.config import settings, load_yaml_config

logger = logging.getLogger(__name__)

@asynccontextmanager
async def get_db_connection():
    async with aiosqlite.connect(settings.DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA journal_mode=WAL;")
        await db.execute("PRAGMA synchronous=NORMAL;")
        yield db

async def init_db():
    async with get_db_connection() as db:
        # 1. Tabel tokens_seen
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tokens_seen (
                token_address TEXT PRIMARY KEY,
                pair_address TEXT NOT NULL,
                symbol TEXT NOT NULL,
                name TEXT NOT NULL,
                chain TEXT DEFAULT 'solana',
                liquidity_usd REAL NOT NULL,
                market_cap_usd REAL DEFAULT 0,
                volume_5m_usd REAL NOT NULL,
                safety_score REAL DEFAULT 0,
                spk_score REAL DEFAULT 0,
                graduation_status TEXT DEFAULT 'bonding_curve',
                mint_renounced INTEGER DEFAULT 1,
                freeze_renounced INTEGER DEFAULT 1,
                lp_status TEXT DEFAULT 'locked',
                top_holder_pct REAL DEFAULT 0.0,
                pool_created_at DATETIME,
                first_seen_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL,
                rejection_reason TEXT
            );
        """)
        # Check and add missing columns if upgrading from older db
        cursor = await db.execute("PRAGMA table_info(tokens_seen)")
        columns = [row[1] for row in await cursor.fetchall()]
        for col_name, col_def in [
            ("market_cap_usd", "REAL DEFAULT 0"),
            ("safety_score", "REAL DEFAULT 0"),
            ("spk_score", "REAL DEFAULT 0"),
            ("graduation_status", "TEXT DEFAULT 'bonding_curve'"),
            ("mint_renounced", "INTEGER DEFAULT 1"),
            ("freeze_renounced", "INTEGER DEFAULT 1"),
            ("lp_status", "TEXT DEFAULT 'locked'"),
            ("top_holder_pct", "REAL DEFAULT 0.0")
        ]:
            if col_name not in columns:
                await db.execute(f"ALTER TABLE tokens_seen ADD COLUMN {col_name} {col_def};")


        await db.execute("CREATE INDEX IF NOT EXISTS idx_tokens_seen_first_seen ON tokens_seen(first_seen_at);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tokens_seen_status ON tokens_seen(status);")

        # 2. Tabel filter_config (Single row)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS filter_config (
                id INTEGER PRIMARY KEY CHECK(id = 1),
                profile TEXT DEFAULT 'balanced',
                min_liquidity_usd REAL DEFAULT 5000.0,
                min_volume_5m_usd REAL DEFAULT 1000.0,
                max_age_minutes INTEGER DEFAULT 60,
                min_buy_sell_ratio REAL DEFAULT 1.2,
                require_lp_locked INTEGER DEFAULT 1,
                require_mint_renounced INTEGER DEFAULT 1,
                blacklist_keywords TEXT DEFAULT 'test,scam,airdrop,pump',
                polling_interval_seconds INTEGER DEFAULT 20,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Add profile if missing
        cursor = await db.execute("PRAGMA table_info(filter_config)")
        columns = [row[1] for row in await cursor.fetchall()]
        if 'profile' not in columns:
            await db.execute("ALTER TABLE filter_config ADD COLUMN profile TEXT DEFAULT 'balanced';")


        # Populate default filter_config if empty
        yaml_cfg = load_yaml_config().get("filters", {})
        min_liq = yaml_cfg.get("min_liquidity_usd", 5000.0)
        min_vol = yaml_cfg.get("min_volume_5m_usd", 1000.0)
        max_age = yaml_cfg.get("max_age_minutes", 60)
        min_bs = yaml_cfg.get("min_buy_sell_ratio", 1.2)
        req_lp = 1 if yaml_cfg.get("require_lp_locked", True) else 0
        req_mint = 1 if yaml_cfg.get("require_mint_renounced", True) else 0
        blacklist = ",".join(yaml_cfg.get("blacklist_keywords", ["test", "scam", "airdrop", "pump"]))
        poll_int = yaml_cfg.get("polling_interval_seconds", 20)

        await db.execute("""
            INSERT INTO filter_config (
                id, min_liquidity_usd, min_volume_5m_usd, max_age_minutes, min_buy_sell_ratio,
                require_lp_locked, require_mint_renounced, blacklist_keywords, polling_interval_seconds
            ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO NOTHING;
        """, (min_liq, min_vol, max_age, min_bs, req_lp, req_mint, blacklist, poll_int))

        # 3. Tabel mute_state (Single row)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS mute_state (
                id INTEGER PRIMARY KEY CHECK(id = 1),
                is_muted INTEGER DEFAULT 0,
                muted_at DATETIME,
                mute_until DATETIME,
                muted_by TEXT DEFAULT 'system'
            );
        """)

        await db.execute("""
            INSERT INTO mute_state (id, is_muted, muted_at, mute_until, muted_by)
            VALUES (1, 0, NULL, NULL, 'system')
            ON CONFLICT(id) DO NOTHING;
        """)

        await db.commit()
        logger.info("Database initialized successfully with WAL mode.")
