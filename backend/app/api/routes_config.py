from fastapi import APIRouter, HTTPException
from backend.app.models.schemas import FilterConfigSchema
from backend.app.core.database import get_db_connection

PROFILES = {
    "conservative": {"min_liquidity_usd": 15000, "min_volume_5m_usd": 3000, "max_age_minutes": 120, "min_buy_sell_ratio": 1.5, "polling_interval_seconds": 30},
    "balanced": {"min_liquidity_usd": 5000, "min_volume_5m_usd": 1000, "max_age_minutes": 60, "min_buy_sell_ratio": 1.2, "polling_interval_seconds": 15},
    "aggressive": {"min_liquidity_usd": 1000, "min_volume_5m_usd": 200, "max_age_minutes": 15, "min_buy_sell_ratio": 1.0, "polling_interval_seconds": 10}
}

router = APIRouter(prefix="/api/config", tags=["Config"])

def row_to_config(row):
    return FilterConfigSchema(
        profile=row["profile"] if "profile" in row.keys() and row["profile"] else "balanced",
        min_liquidity_usd=row["min_liquidity_usd"],
        min_volume_5m_usd=row["min_volume_5m_usd"],
        max_age_minutes=row["max_age_minutes"],
        min_buy_sell_ratio=row["min_buy_sell_ratio"],
        require_lp_locked=bool(row["require_lp_locked"]),
        require_mint_renounced=bool(row["require_mint_renounced"]),
        blacklist_keywords=row["blacklist_keywords"],
        polling_interval_seconds=row["polling_interval_seconds"]
    )

@router.get("", response_model=FilterConfigSchema)
async def get_config():
    async with get_db_connection() as db:
        async with db.execute("SELECT * FROM filter_config WHERE id = 1") as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Configuration not found")
            return row_to_config(row)

@router.put("", response_model=FilterConfigSchema)
async def update_config(payload: FilterConfigSchema):
    # Apply profile preset values if profile changed
    if payload.profile in PROFILES:
        preset = PROFILES[payload.profile]
        payload.min_liquidity_usd = preset["min_liquidity_usd"]
        payload.min_volume_5m_usd = preset["min_volume_5m_usd"]
        payload.max_age_minutes = preset["max_age_minutes"]
        payload.min_buy_sell_ratio = preset["min_buy_sell_ratio"]
        payload.polling_interval_seconds = preset["polling_interval_seconds"]

    async with get_db_connection() as db:
        await db.execute("""
            UPDATE filter_config
            SET profile = ?,
                min_liquidity_usd = ?,
                min_volume_5m_usd = ?,
                max_age_minutes = ?,
                min_buy_sell_ratio = ?,
                require_lp_locked = ?,
                require_mint_renounced = ?,
                blacklist_keywords = ?,
                polling_interval_seconds = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
        """, (
            payload.profile,
            payload.min_liquidity_usd,
            payload.min_volume_5m_usd,
            payload.max_age_minutes,
            payload.min_buy_sell_ratio,
            1 if payload.require_lp_locked else 0,
            1 if payload.require_mint_renounced else 0,
            payload.blacklist_keywords,
            payload.polling_interval_seconds
        ))
        await db.commit()

    return payload

