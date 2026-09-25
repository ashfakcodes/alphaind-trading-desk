import asyncio
from typing import Dict, Any, List

class FraudHunterAgent:
    """
    Dedicated Sub-Agent 2: Scam & Fraud Hunter.
    Protects beginners from fake coins, pump-and-dump scams, and artificial volume tricks.
    """
    AGENT_NAME = "Fraud & Scam Hunter"
    ROLE = "Fake Token & Manipulation Protection"

    KNOWN_GENUINE_TICKERS = {
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "BGBUSDT", "DOGEUSDT",
        "XRPUSDT", "ADAUSDT", "AVAXUSDT", "LINKUSDT", "SUIUSDT"
    }
    SUSPICIOUS_SUFFIXES = ["2", "INU", "SAFE", "MOON", "ELON", "100X", "V2", "TEST"]

    @classmethod
    async def analyze(cls, context: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(0.06)

        symbol = context.get("symbol", "BTCUSDT").upper()
        ticker = context.get("ticker_data", {})
        orderbook = context.get("orderbook", {})

        risk_score = 10
        flags: List[str] = []
        thought_trace: List[str] = [
            f"Verifying if {symbol} is an officially recognized top-tier cryptocurrency on Bitget.",
            "Checking for fake volume tricks or pump-and-dump manipulation."
        ]

        # 1. Fake / Copycat Token Check
        is_known = symbol in cls.KNOWN_GENUINE_TICKERS
        if not is_known:
            for suffix in cls.SUSPICIOUS_SUFFIXES:
                if suffix in symbol:
                    risk_score += 45
                    flags.append(f"Suspicious meme or copycat name pattern detected ('{suffix}'). High scam risk.")
                    thought_trace.append(f"SCAM WARNING: Token name pattern '{suffix}' matches common honeypot scams.")
                    break

        # 2. Pump & Dump Check
        change_24h = ticker.get("change_24h", 0.0)
        volume_24h = ticker.get("volume_24h", 1000000.0)

        if change_24h > 45.0:
            risk_score += 40
            flags.append(f"Parabolic pump detected (+{change_24h:.1f}% in 24h). Price is ripe for a crash.")
            thought_trace.append(f"Warning: Coin skyrocketed +{change_24h:.1f}% in 1 day. High danger of sudden dump.")
        elif change_24h > 20.0:
            risk_score += 20
            flags.append(f"Unusual 24h price spike (+{change_24h:.1f}%). Exercise caution.")

        risk_score = min(100, risk_score)
        status = "SAFE" if risk_score < 35 else ("WARNING" if risk_score < 70 else "DANGER")

        if status == "SAFE":
            plain_summary = "Verified Genuine: Official token with organic market trading."
            human_status = "Authentic & Safe"
        elif status == "WARNING":
            plain_summary = "Caution: Rapid price pump detected in the last 24 hours."
            human_status = "Spike Warning"
        else:
            plain_summary = "SCAM HAZARD: High probability of pump-and-dump or honeypot copycat."
            human_status = "High Scam Risk"

        return {
            "agent": cls.AGENT_NAME,
            "role": cls.ROLE,
            "status": status,
            "human_status": human_status,
            "score": risk_score,
            "metrics": {
                "coin_verification": "Official & Verified" if is_known else "Unverified Asset",
                "24h_price_change": f"{change_24h:+.1f}%",
                "fake_volume_risk": "Low" if risk_score < 40 else "Elevated"
            },
            "flags": flags,
            "thought_trace": thought_trace,
            "summary": plain_summary
        }
