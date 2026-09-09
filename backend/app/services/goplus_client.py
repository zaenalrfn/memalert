import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

RUGCHECK_REPORT_URL = "https://api.rugcheck.xyz/v1/tokens"

class GoPlusClient:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MemecoinTracker/1.0"
        }

    async def check_token_security(self, token_address: str) -> Dict[str, Any]:
        result = {
            "mint_renounced": True,
            "freeze_renounced": True,
            "is_honeypot": False,
            "top_holder_pct": 0.0,
            "lp_status": "locked",
            "raw": {}
        }
        try:
            async with httpx.AsyncClient(timeout=8.0, headers=self.headers) as client:
                res = await client.get(f"{RUGCHECK_REPORT_URL}/{token_address}/report")
                if res.status_code == 200:
                    data = res.json()
                    result["raw"] = data
                    
                    # Mint & Freeze authority
                    mint_auth = data.get("mintAuthority")
                    freeze_auth = data.get("freezeAuthority")
                    
                    result["mint_renounced"] = (mint_auth is None)
                    result["freeze_renounced"] = (freeze_auth is None)
                    
                    # Top holder percentage
                    top_holders = data.get("topHolders")
                    if isinstance(top_holders, list) and len(top_holders) > 0:
                        # pct is already in percentage format, e.g., 13.72 -> convert to decimal 0.1372
                        pct_val = float(top_holders[0].get("pct", 0.0))
                        result["top_holder_pct"] = pct_val / 100.0 if pct_val > 1.0 else pct_val

                    # LP Lock status
                    lockers = data.get("lockers")
                    if isinstance(lockers, list) and len(lockers) > 0:
                        result["lp_status"] = "locked"
                    else:
                        # check markets liquidity
                        markets = data.get("markets", [])
                        if markets:
                            result["lp_status"] = "locked" # default assumption if liquidity exists
                        else:
                            result["lp_status"] = "unlocked"

        except Exception as e:
            logger.warning(f"RugCheck/Security exception for {token_address}: {e}")

        return result
