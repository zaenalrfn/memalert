import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

GOPLUS_SOLANA_SECURITY_URL = "https://api.gopluslabs.io/api/v1/solana/token_security"

class GoPlusClient:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MemecoinTracker/1.0"
        }

    async def check_token_security(self, token_address: str) -> Dict[str, Any]:
        result = {
            "is_mintable": False,
            "mint_renounced": True,
            "lp_locked": True,
            "is_honeypot": False,
            "raw": {}
        }
        try:
            async with httpx.AsyncClient(timeout=5.0, headers=self.headers) as client:
                res = await client.get(f"{GOPLUS_SOLANA_SECURITY_URL}/{token_address}")
                if res.status_code == 200:
                    data = res.json().get("result", {})
                    token_info = data.get(token_address, {}) if isinstance(data, dict) else {}
                    result["raw"] = token_info
                    
                    # Mint authority check
                    mintable = token_info.get("mintable", {})
                    if isinstance(mintable, dict) and mintable.get("status") == "1":
                        result["is_mintable"] = True
                        result["mint_renounced"] = False

                    # Honeypot check
                    if token_info.get("is_honeypot") == "1":
                        result["is_honeypot"] = True

        except Exception as e:
            logger.warning(f"GoPlus security check exception for {token_address}: {e}")

        return result
