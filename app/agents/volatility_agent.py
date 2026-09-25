import asyncio
from typing import Dict, Any, List

class VolatilityAgent:
    """
    Dedicated Sub-Agent 1: Volatility Sentinel.
    Evaluates market price turbulence, sudden swings, and liquidation risk in plain English.
    """
    AGENT_NAME = "Volatility Sentinel"
    ROLE = "Market Turbulence & Sudden Price Swings"

    @classmethod
    async def analyze(cls, context: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(0.06)

        quant = context.get("quant_data", {})
        vol = quant.get("annualized_volatility", 45.0)
        atr_pct = quant.get("atr_pct", 1.2)
        bandwidth = quant.get("bollinger_bandwidth", 4.0)
        z_score = abs(quant.get("z_score", 0.0))

        risk_score = 15
        flags: List[str] = []
        thought_trace: List[str] = [
            f"Measuring recent price swings: Average swing is {atr_pct:.1f}% per hour.",
            "Checking if current market is in a calm state or facing explosive turbulence."
        ]

        if vol > 120.0 or atr_pct > 3.5:
            risk_score += 45
            flags.append("Wild price swings detected: high danger of sudden dips triggering liquidation.")
            thought_trace.append("Market is experiencing intense volatility. Stop losses are prone to get hunted.")
            plain_summary = "Wild Price Turbulence: High risk of fast, unexpected drops."
            human_status = "Turbulent (High Risk)"
        elif vol > 70.0 or atr_pct > 2.2:
            risk_score += 25
            flags.append("Elevated price volatility: expect bigger ups and downs than usual.")
            plain_summary = "Moderate Price Swings: Price is moving faster than normal."
            human_status = "Active Swings"
        else:
            thought_trace.append("Price action is disciplined and steady. Safe to trade.")
            plain_summary = "Calm & Steady: Normal price movement, safe from wild whipsaws."
            human_status = "Calm & Stable"

        risk_score = min(100, risk_score)
        status = "SAFE" if risk_score < 40 else ("WARNING" if risk_score < 70 else "DANGER")

        return {
            "agent": cls.AGENT_NAME,
            "role": cls.ROLE,
            "status": status,
            "human_status": human_status,
            "score": risk_score,
            "metrics": {
                "price_swing_level": "High" if risk_score > 60 else ("Moderate" if risk_score > 35 else "Low"),
                "annualized_vol_pct": round(vol, 1),
                "hourly_swing_pct": round(atr_pct, 1)
            },
            "flags": flags,
            "thought_trace": thought_trace,
            "summary": plain_summary
        }
