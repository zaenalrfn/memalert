import httpx
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

DEXSCREENER_PROFILES_URL = "https://api.dexscreener.com/token-profiles/latest/v1"
DEXSCREENER_BOOSTS_URL = "https://api.dexscreener.com/token-boosts/latest/v1"
DEXSCREENER_SEARCH_URL = "https://api.dexscreener.com/latest/dex/search"
DEXSCREENER_TOKENS_URL = "https://api.dexscreener.com/latest/dex/tokens"

SOL_WRAPPED = "So11111111111111111111111111111111111111112"

class DexScreenerClient:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MemecoinTracker/1.0"
        }

    async def fetch_latest_solana_pairs(self) -> List[Dict[str, Any]]:
        solana_token_addresses = set()
        pairs = []

        try:
            async with httpx.AsyncClient(timeout=10.0, headers=self.headers) as client:
                # 1. Fetch token profiles
                try:
                    res_prof = await client.get(DEXSCREENER_PROFILES_URL)
                    if res_prof.status_code == 200 and isinstance(res_prof.json(), list):
                        for item in res_prof.json():
                            if item.get("chainId") == "solana" and item.get("tokenAddress"):
                                solana_token_addresses.add(item.get("tokenAddress"))
                except Exception as e:
                    logger.warning(f"Error fetching token-profiles: {e}")

                # 2. Fetch token boosts
                try:
                    res_boost = await client.get(DEXSCREENER_BOOSTS_URL)
                    if res_boost.status_code == 200 and isinstance(res_boost.json(), list):
                        for item in res_boost.json():
                            if item.get("chainId") == "solana" and item.get("tokenAddress"):
                                solana_token_addresses.add(item.get("tokenAddress"))
                except Exception as e:
                    logger.warning(f"Error fetching token-boosts: {e}")

                # 3. Query details for discovered token addresses in batch
                if solana_token_addresses:
                    addrs_list = list(solana_token_addresses)[:30]
                    addrs_str = ",".join(addrs_list)
                    try:
                        res_tokens = await client.get(f"{DEXSCREENER_TOKENS_URL}/{addrs_str}")
                        if res_tokens.status_code == 200:
                            raw_pairs = res_tokens.json().get("pairs") or []
                            for p in raw_pairs:
                                if p.get("chainId") == "solana":
                                    pairs.append(p)
                    except Exception as e:
                        logger.warning(f"Error fetching token details batch: {e}")

                # 4. Fallback search if empty
                if not pairs:
                    try:
                        res_search = await client.get(DEXSCREENER_SEARCH_URL, params={"q": "pump"})
                        if res_search.status_code == 200:
                            raw_pairs = res_search.json().get("pairs") or []
                            for p in raw_pairs:
                                if p.get("chainId") == "solana":
                                    pairs.append(p)
                    except Exception as e:
                        logger.warning(f"Error search fallback: {e}")

        except Exception as e:
            logger.error(f"Error fetching DexScreener pairs: {e}")

        logger.info(f"DexScreenerClient fetched {len(pairs)} Solana pairs.")
        return pairs

    @staticmethod
    def parse_pair_data(pair: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalisasi data pair dari DexScreener.
        Menjadikan baseToken sebagai memecoin (jika baseToken san WSOL, swap dengan quoteToken).
        """
        base_token = pair.get("baseToken") or {}
        quote_token = pair.get("quoteToken") or {}

        # Jika baseToken adalah WSOL, pakai quoteToken sebagai target memecoin
        if base_token.get("address") == SOL_WRAPPED and quote_token.get("address"):
            target_token = quote_token
        else:
            target_token = base_token

        txns = pair.get("txns", {}).get("m5", {})
        volume = pair.get("volume", {})
        liquidity = pair.get("liquidity") or {}
        market_cap = float(pair.get("marketCap", 0.0) or 0.0)

        token_address = target_token.get("address", "")
        pair_address = pair.get("pairAddress", "")
        symbol = target_token.get("symbol", "UNKNOWN")
        name = target_token.get("name", "Unknown")

        liquidity_usd = 0.0
        if isinstance(liquidity, dict):
            liquidity_usd = float(liquidity.get("usd", 0.0) or 0.0)

        volume_5m = 0.0
        if isinstance(volume, dict):
            volume_5m = float(volume.get("m5", 0.0) or 0.0)

        buys = int(txns.get("buys", 0) or 0) if isinstance(txns, dict) else 0
        sells = int(txns.get("sells", 0) or 0) if isinstance(txns, dict) else 0
        pair_created_at = pair.get("pairCreatedAt")  # timestamp in ms

        dex_id = (pair.get("dexId") or "").lower()
        url_lower = (pair.get("url") or "").lower()
        if dex_id in ("raydium", "orca", "meteora") or "raydium" in url_lower:
            graduation_status = "dex"
        else:
            graduation_status = "bonding_curve"

        return {
            "token_address": token_address,
            "pair_address": pair_address,
            "symbol": symbol,
            "name": name,
            "chain": "solana",
            "liquidity_usd": liquidity_usd,
            "market_cap_usd": market_cap,
            "volume_5m_usd": volume_5m,
            "txns_buy": buys,
            "txns_sell": sells,
            "pair_created_at": pair_created_at,
            "url": pair.get("url", f"https://dexscreener.com/solana/{pair_address}"),
            "graduation_status": graduation_status,
            "safety_score": 0.0,
            "spk_score": 0.0,
            "mint_renounced": True,
            "freeze_renounced": True,
            "lp_status": "unknown",
            "top_holder_pct": 0.0,
        }
