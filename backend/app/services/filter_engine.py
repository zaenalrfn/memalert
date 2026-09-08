import time
import logging
from typing import Dict, Any, Tuple
from backend.app.services.goplus_client import GoPlusClient

logger = logging.getLogger(__name__)

class FilterEngine:
    def __init__(self):
        self.goplus_client = GoPlusClient()

    async def evaluate_token(
        self,
        token_data: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Mengevaluasi token terhadap filter_config.
        Return: (is_passed: bool, rejection_reason: str)
        """
        symbol = token_data.get("symbol", "").upper()
        name = token_data.get("name", "").lower()
        liquidity = token_data.get("liquidity_usd", 0.0)
        volume_5m = token_data.get("volume_5m_usd", 0.0)
        buys = token_data.get("txns_buy", 0)
        sells = token_data.get("txns_sell", 0)
        pair_created_at = token_data.get("pair_created_at")  # ms timestamp

        # 1. Blacklist keywords check
        blacklist_raw = config.get("blacklist_keywords", "test,scam,airdrop,pump")
        blacklist = [k.strip().lower() for k in blacklist_raw.split(",") if k.strip()]
        for kw in blacklist:
            if kw in name or kw in symbol.lower():
                return False, f"Name/Symbol contains blacklisted keyword: '{kw}'"

        # 2. Minimum liquidity check
        min_liq = float(config.get("min_liquidity_usd", 5000.0))
        if liquidity < min_liq:
            return False, f"Liquidity ${liquidity:,.0f} < min ${min_liq:,.0f}"

        # 3. Minimum volume 5m check
        min_vol = float(config.get("min_volume_5m_usd", 1000.0))
        if volume_5m < min_vol:
            return False, f"Volume 5m ${volume_5m:,.0f} < min ${min_vol:,.0f}"

        # 4. Max age minutes check
        max_age = int(config.get("max_age_minutes", 60))
        if pair_created_at:
            now_ms = time.time() * 1000
            age_minutes = (now_ms - pair_created_at) / (1000 * 60)
            if age_minutes > max_age:
                return False, f"Pool age {age_minutes:.1f}m > max {max_age}m"

        # 5. Buy/Sell ratio check
        min_bs = float(config.get("min_buy_sell_ratio", 1.2))
        bs_ratio = buys / max(sells, 1)
        if bs_ratio < min_bs:
            return False, f"Buy/Sell ratio {bs_ratio:.2f} < min {min_bs}"

        # 6. Basic security check via GoPlus API
        req_mint = bool(config.get("require_mint_renounced", True))
        req_lp = bool(config.get("require_lp_locked", True))

        if req_mint or req_lp:
            sec = await self.goplus_client.check_token_security(token_data["token_address"])
            if req_mint and not sec.get("mint_renounced", True):
                return False, "Mint authority not renounced"
            if sec.get("is_honeypot", False):
                return False, "Detected as honeypot risk"

        return True, "PASSED"
