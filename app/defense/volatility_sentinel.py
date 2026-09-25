import math
from typing import Dict, Any, List
import numpy as np

class VolatilitySentinel:
    """
    Pillar 1: Market Volatility Sentinel.
    Evaluates sudden ATR surges, Bollinger Band expansion, realized volatility spikes,
    and liquidation cascade hazards before trade execution.
    """

    @classmethod
    def evaluate(cls, symbol: str, quant_data: Dict[str, Any], order_details: Dict[str, Any]) -> Dict[str, Any]:
        vol = quant_data.get("annualized_volatility", 45.0)
        atr_pct = quant_data.get("atr_pct", 1.2)
        bandwidth = quant_data.get("bollinger_bandwidth", 4.0)
        z_score = abs(quant_data.get("z_score", 0.0))

        risk_score = 15  # baseline safe market score
        flags: List[str] = []

        # 1. Extreme Annualized Volatility Check
        if vol > 120.0:
            risk_score += 40
            flags.append(f"Extreme annualized volatility detected ({vol:.1f}%). High whipsaw risk.")
        elif vol > 75.0:
            risk_score += 25
            flags.append(f"Elevated market volatility ({vol:.1f}%). Wide stop distance advised.")
        elif vol < 20.0:
            risk_score += 10
            flags.append(f"Compressed volatility regime ({vol:.1f}%). Potential explosive breakout pending.")

        # 2. ATR Expansion Shock
        if atr_pct > 4.0:
            risk_score += 30
            flags.append(f"Intense candle expansion (ATR {atr_pct:.2f}% of price). Immediate stop-hunt zone.")
        elif atr_pct > 2.5:
            risk_score += 15
            flags.append(f"Above-average ATR range ({atr_pct:.2f}%). Adjust position size down.")

        # 3. Bollinger Bandwidth Surge (Breakout Hazard)
        if bandwidth > 14.0:
            risk_score += 20
            flags.append(f"Bollinger Bandwidth blown out ({bandwidth:.1f}%). High tail-risk environment.")

        # 4. Statistical Deviation from Mean
        if z_score > 2.8:
            risk_score += 25
            flags.append(f"Price is extended at {z_score:.1f}σ standard deviations. Mean reversion risk elevated.")

        risk_score = min(100, risk_score)

        status = "SAFE"
        if risk_score >= 70:
            status = "DANGER"
        elif risk_score >= 40:
            status = "WARNING"

        return {
            "name": "Market Volatility Sentinel",
            "score": risk_score,
            "status": status,
            "metrics": {
                "annualized_volatility_pct": round(vol, 1),
                "atr_pct": round(atr_pct, 2),
                "bollinger_bandwidth_pct": round(bandwidth, 2),
                "z_score": round(z_score, 2)
            },
            "flags": flags,
            "summary": "Volatility is benign." if status == "SAFE" else ("Moderate volatility surge detected." if status == "WARNING" else "Severe volatility hazard present! High risk of immediate liquidation.")
        }
