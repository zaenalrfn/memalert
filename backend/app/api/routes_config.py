from fastapi import APIRouter, HTTPException
from backend.app.models.schemas import FilterConfigSchema
from backend.app.core.database import get_db_connection

router = APIRouter(prefix="/api/config", tags=["Config"])

@router.get("", response_model=FilterConfigSchema)
async def get_config():
    async with get_db_connection() as db:
        async with db.execute("SELECT * FROM filter_config WHERE id = 1") as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Configuration not found")
            return FilterConfigSchema(
                min_liquidity_usd=row["min_liquidity_usd"],
                min_volume_5m_usd=row["min_volume_5m_usd"],
                max_age_minutes=row["max_age_minutes"],
                min_buy_sell_ratio=row["min_buy_sell_ratio"],
                require_lp_locked=bool(row["require_lp_locked"]),
                require_mint_renounced=bool(row["require_mint_renounced"]),
                blacklist_keywords=row["blacklist_keywords"],
                polling_interval_seconds=row["polling_interval_seconds"]
            )

@router.put("", response_model=FilterConfigSchema)
async def update_config(payload: FilterConfigSchema):
    async with get_db_connection() as db:
        await db.execute("""
            UPDATE filter_config
            SET min_liquidity_usd = ?,
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
