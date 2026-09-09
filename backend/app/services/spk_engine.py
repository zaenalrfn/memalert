import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class SPKEngine:
    @staticmethod
    def calculate_safety_score(security_data: Dict[str, Any]) -> float:
        """
        Menghitung skor 0-100 berdasarkan data keamanan.
        Jika top_holder_pct None (data tidak tersedia), skor dinormalisasi dari 3 komponen yang ada.
        """
        score = 0.0
        # mint_renounced: 25 poin
        score += 25 if security_data.get("mint_renounced") else 0
        # freeze_renounced: 25 poin
        score += 25 if security_data.get("freeze_renounced") else 0
        # lp_locked: 25 poin
        score += 25 if security_data.get("lp_status") in ["locked", "burned"] else 0

        pct = security_data.get("top_holder_pct")
        if pct is None:
            # Data holder tidak tersedia -> normalisasi ke skala 100 dari 75 basis
            # agar skor tidak inflate maupun deflate secara artifisial
            return round((score / 75.0 * 100.0) if score > 0 else 0.0, 2)

        # top_holder_pct: 25 poin sisanya
        try:
            pct_val = float(pct)
        except (TypeError, ValueError):
            pct_val = 0.0
        pct_val = max(0.0, min(1.0, pct_val))
        score += 25 * (1.0 - pct_val)

        return round(score, 2)

    @staticmethod
    def calculate_saw_score(token: Dict[str, Any], all_tokens: List[Dict[str, Any]]) -> float:
        """
        Metode SAW (Simple Additive Weighting).
        """
        weights = {
            "liquidity_usd": 0.20,
            "volume_5m_usd": 0.15,
            "safety_score": 0.35,
            "top_holder_pct": 0.10, # cost
            "market_cap_usd": 0.20
        }
        
        benefit_criteria = ["liquidity_usd", "volume_5m_usd", "safety_score", "market_cap_usd"]
        cost_criteria = ["top_holder_pct"]

        # Jika tidak ada satu pun token dengan data holder valid, redistribusi bobot cost ke benefit
        valid_holder_vals = [t.get(key) for t in all_tokens for key in cost_criteria if t.get(key) is not None]
        use_holder = len(valid_holder_vals) > 0
        adj_weights = dict(weights)
        if not use_holder:
            bonus = weights["top_holder_pct"] / len(benefit_criteria)
            for key in benefit_criteria:
                adj_weights[key] += bonus

        score = 0.0

        # Benefit
        for key in benefit_criteria:
            max_val = max((t.get(key, 0.0) or 0.0 for t in all_tokens), default=1)
            val = token.get(key, 0.0) or 0.0
            score += adj_weights[key] * (val / (max_val if max_val > 0 else 1))

        # Cost (hanya bila ada data valid)
        if use_holder:
            for key in cost_criteria:
                vals = [(t.get(key) if t.get(key) is not None else 0.0001) for t in all_tokens]
                min_val = min(vals, default=0.0001)
                raw = token.get(key)
                val = raw if raw is not None else 0.0001
                try:
                    val = float(val)
                except (TypeError, ValueError):
                    val = 0.0001
                score += adj_weights[key] * (min_val / (val if val > 0 else 0.0001))

        return round(score, 4)
