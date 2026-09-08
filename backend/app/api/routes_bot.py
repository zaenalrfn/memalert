from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Request
from backend.app.models.schemas import BotStatusResponse, MuteStatusResponse, MuteRequest
from backend.app.core.database import get_db_connection

router = APIRouter(prefix="/api/bot", tags=["Bot"])

@router.get("/status", response_model=BotStatusResponse)
async def get_bot_status():
    async with get_db_connection() as db:
        async with db.execute("SELECT * FROM mute_state WHERE id = 1") as cursor:
            mute_row = await cursor.fetchone()

        async with db.execute("SELECT COUNT(*) as count FROM tokens_seen WHERE DATE(first_seen_at) = DATE('now') AND status = 'alerted'") as cursor:
            alerted_row = await cursor.fetchone()
            alerted_cnt = alerted_row["count"] if alerted_row else 0

        async with db.execute("SELECT COUNT(*) as count FROM tokens_seen WHERE DATE(first_seen_at) = DATE('now') AND status = 'alerted_muted'") as cursor:
            muted_row = await cursor.fetchone()
            muted_cnt = muted_row["count"] if muted_row else 0

        async with db.execute("SELECT COUNT(*) as count FROM tokens_seen WHERE DATE(first_seen_at) = DATE('now') AND status = 'rejected'") as cursor:
            rejected_row = await cursor.fetchone()
            rejected_cnt = rejected_row["count"] if rejected_row else 0

    is_muted = bool(mute_row["is_muted"]) if mute_row else False
    mute_until = mute_row["mute_until"] if mute_row else None

    return BotStatusResponse(
        is_worker_running=True,
        is_muted=is_muted,
        mute_until=mute_until,
        tokens_alerted_today=alerted_cnt,
        tokens_muted_today=muted_cnt,
        tokens_rejected_today=rejected_cnt
    )

@router.post("/mute", response_model=MuteStatusResponse)
async def mute_bot(req: MuteRequest):
    now = datetime.utcnow()
    until_dt = now + timedelta(minutes=req.duration_minutes) if req.duration_minutes else None
    until_str = until_dt.strftime("%Y-%m-%d %H:%M:%S") if until_dt else None
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    async with get_db_connection() as db:
        await db.execute("""
            UPDATE mute_state
            SET is_muted = 1, muted_at = ?, mute_until = ?, muted_by = 'web_ui'
            WHERE id = 1
        """, (now_str, until_str))
        await db.commit()

    return MuteStatusResponse(
        is_muted=True,
        muted_at=now_str,
        mute_until=until_str,
        muted_by="web_ui"
    )

@router.post("/unmute", response_model=MuteStatusResponse)
async def unmute_bot():
    async with get_db_connection() as db:
        await db.execute("""
            UPDATE mute_state
            SET is_muted = 0, muted_at = NULL, mute_until = NULL, muted_by = 'web_ui'
            WHERE id = 1
        """, ())
        await db.commit()

    return MuteStatusResponse(
        is_muted=False,
        muted_at=None,
        mute_until=None,
        muted_by="web_ui"
    )

@router.post("/test-alert")
async def test_alert(request: Request):
    telegram_service = getattr(request.app.state, "telegram_service", None)
    if not telegram_service:
        raise HTTPException(status_code=500, detail="Telegram service is not initialized")

    test_token = {
        "symbol": "SOLTEST",
        "name": "Solana Test Token",
        "token_address": "So11111111111111111111111111111111111111112",
        "pair_address": "8sLbNZo1M3spRY2qA3J1EwM6o8vBf4u3wN2eX9kL8",
        "liquidity_usd": 15200.0,
        "volume_5m_usd": 3400.0,
        "pair_created_at": None,
        "url": "https://dexscreener.com/solana"
    }

    await telegram_service.send_alert(test_token)
    return {"success": True, "message": "Test alert notification sent to Telegram!"}
