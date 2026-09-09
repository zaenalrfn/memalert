from typing import Optional
from fastapi import APIRouter, Query
from backend.app.models.schemas import TokenListResponse, TokenResponse
from backend.app.core.database import get_db_connection

router = APIRouter(prefix="/api/tokens", tags=["Tokens"])

@router.get("", response_model=TokenListResponse)
async def get_tokens(
    status: Optional[str] = Query(default="all", description="Status filter: all, alerted, alerted_muted, rejected"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0)
):
    query_count = "SELECT COUNT(*) as count FROM tokens_seen"
    query_select = "SELECT * FROM tokens_seen"
    params = []

    if status and status != "all":
        query_count += " WHERE status = ?"
        query_select += " WHERE status = ?"
        params.append(status)

    query_select += " ORDER BY first_seen_at DESC LIMIT ? OFFSET ?"
    select_params = params + [limit, offset]

    async with get_db_connection() as db:
        async with db.execute(query_count, params) as cursor:
            count_row = await cursor.fetchone()
            total = count_row["count"] if count_row else 0

        async with db.execute(query_select, select_params) as cursor:
            rows = await cursor.fetchall()

    items = []
    for r in rows:
        items.append(TokenResponse(
            token_address=r["token_address"],
            pair_address=r["pair_address"],
            symbol=r["symbol"],
            name=r["name"],
            chain=r["chain"] or "solana",
            liquidity_usd=r["liquidity_usd"],
            market_cap_usd=r["market_cap_usd"] if "market_cap_usd" in r.keys() else 0.0,
            volume_5m_usd=r["volume_5m_usd"],
            safety_score=r["safety_score"] if "safety_score" in r.keys() else 0.0,
            spk_score=r["spk_score"] if "spk_score" in r.keys() else 0.0,
            graduation_status=r["graduation_status"] if "graduation_status" in r.keys() and r["graduation_status"] else "bonding_curve",
            mint_renounced=bool(r["mint_renounced"]) if "mint_renounced" in r.keys() else True,
            freeze_renounced=bool(r["freeze_renounced"]) if "freeze_renounced" in r.keys() else True,
            lp_status=r["lp_status"] if "lp_status" in r.keys() and r["lp_status"] else "locked",
            top_holder_pct=r["top_holder_pct"] if "top_holder_pct" in r.keys() else None,
            pool_created_at=r["pool_created_at"],
            first_seen_at=r["first_seen_at"],
            status=r["status"],
            rejection_reason=r["rejection_reason"]
        ))

    return TokenListResponse(total=total, items=items)
