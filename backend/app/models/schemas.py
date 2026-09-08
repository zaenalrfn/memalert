from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class TokenBase(BaseModel):
    token_address: str
    pair_address: str
    symbol: str
    name: str
    chain: str = "solana"
    liquidity_usd: float
    market_cap_usd: float = 0.0
    volume_5m_usd: float
    pool_created_at: Optional[datetime] = None

class TokenCreate(TokenBase):
    status: str  # 'alerted', 'alerted_muted', 'rejected'
    rejection_reason: Optional[str] = None

class TokenResponse(TokenBase):
    first_seen_at: datetime
    status: str
    rejection_reason: Optional[str] = None

class TokenListResponse(BaseModel):
    total: int
    items: List[TokenResponse]

class FilterConfigSchema(BaseModel):
    min_liquidity_usd: float = Field(default=5000.0, ge=0)
    min_volume_5m_usd: float = Field(default=1000.0, ge=0)
    max_age_minutes: int = Field(default=60, ge=1)
    min_buy_sell_ratio: float = Field(default=1.2, ge=0)
    require_lp_locked: bool = True
    require_mint_renounced: bool = True
    blacklist_keywords: str = "test,scam,airdrop,pump"
    polling_interval_seconds: int = Field(default=20, ge=5, le=300)

class MuteStatusResponse(BaseModel):
    is_muted: bool
    muted_at: Optional[str] = None
    mute_until: Optional[str] = None
    muted_by: str = "system"

class MuteRequest(BaseModel):
    duration_minutes: Optional[int] = Field(default=30, ge=1)

class BotStatusResponse(BaseModel):
    is_worker_running: bool = True
    is_muted: bool
    mute_until: Optional[str] = None
    tokens_alerted_today: int
    tokens_muted_today: int
    tokens_rejected_today: int
