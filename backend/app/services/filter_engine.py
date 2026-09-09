import time
import logging
from typing import Dict, Any, Tuple
from backend.app.services.goplus_client import GoPlusClient
from backend.app.services.spk_engine import SPKEngine

logger = logging.getLogger(__name__)

class FilterEngine:
    def __init__(self):
        self.goplus_client = GoPlusClient()
        self.spk_engine = SPKEngine()

    @staticmethod
    def _with_defaults(token_data: Dict[str, Any]) -> Dict[str, Any]:
        token_data.setdefault("graduation_status", "bonding_curve")
        token_data.setdefault("safety_score", 0.0)
        token_data.setdefault("spk_score", 0.0)
        token_data.setdefault("mint_renounced", True)
        token_data.setdefault("freeze_renounced", True)
        token_data.setdefault("lp_status", "unknown")
        token_data.setdefault("top_holder_pct", None)
        return token_data

    async def evaluate_token(
        self,
        token_data: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Mengevaluasi token terhadap filter_config.
        Return: (is_passed: bool, rejection_reason: str, updated_token_data: dict)
        """
        token_data = self._with_defaults(token_data)
        symbol = token_data.get("symbol", "").upper()
        name = token_data.get("name", "").lower()
        liquidity = token_data.get("liquidity_usd", 0.0)
        volume_5m = token_data.get("volume_5m_usd", 0.0)
        pair_created_at = token_data.get("pair_created_at")

        # 1. Blacklist
        blacklist_raw = config.get("blacklist_keywords", "test,scam,airdrop,pump")
        blacklist = [k.strip().lower() for k in blacklist_raw.split(",") if k.strip()]
        for kw in blacklist:
            if kw in name or kw in symbol.lower():
                return False, f"Blacklisted: {kw}", token_data

        # 2. Liquidity & Volume
        if liquidity < float(config.get("min_liquidity_usd", 5000)):
            return False, "Low Liquidity", token_data
        if volume_5m < float(config.get("min_volume_5m_usd", 1000)):
            return False, "Low Volume", token_data

        # 3. Age
        if pair_created_at:
            age_min = (time.time() * 1000 - pair_created_at) / 60000
            if age_min > int(config.get("max_age_minutes", 60)):
                return False, "Too Old", token_data

        # 4. Security & Safety Score
        sec = await self.goplus_client.check_token_security(token_data["token_address"])
        if sec.get("is_honeypot"):
            return False, "Honeypot Detected", token_data

        token_data.update({
            "mint_renounced": sec.get("mint_renounced", True),
            "freeze_renounced": sec.get("freeze_renounced", True),
            "top_holder_pct": sec.get("top_holder_pct"),
            "lp_status": sec.get("lp_status", "unknown"),
            "graduation_status": "dex" if "raydium" in (token_data.get("url", "").lower()) else token_data.get("graduation_status", "bonding_curve")
        })
        
        token_data["safety_score"] = self.spk_engine.calculate_safety_score(token_data)

        return True, "PASSED", token_data
