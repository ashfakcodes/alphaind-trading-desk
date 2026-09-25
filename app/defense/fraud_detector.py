import re
from typing import Dict, Any, List

class FraudDetector:
    """
    Pillar 2: Scam & Fraud Hunter.
    Inspects asset authentications, pump-and-dump anomalies, wash trading footprints,
    and orderbook spoofing before trade approval.
    """

    KNOWN_GENUINE_TICKERS = {
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "BGBUSDT", "DOGEUSDT",
        "XRPUSDT", "ADAUSDT", "AVAXUSDT", "LINKUSDT", "SUIUSDT"
    }

    SUSPICIOUS_SUFFIXES = ["2", "INU", "SAFE", "MOON", "ELON", "100X", "V2", "TEST"]

    @classmethod
    def evaluate(cls, symbol: str, ticker_data: Dict[str, Any], orderbook: Dict[str, Any]) -> Dict[str, Any]:
        symbol_upper = symbol.upper()
        risk_score = 10  # baseline safe score
        flags: List[str] = []

        # 1. Ticker Spoofing & Counterfeit Check
        is_known = symbol_upper in cls.KNOWN_GENUINE_TICKERS
        if not is_known:
            for suffix in cls.SUSPICIOUS_SUFFIXES:
                if suffix in symbol_upper:
                    risk_score += 45
                    flags.append(f"Suspicious meme/honeypot ticker pattern detected ({suffix} token naming).")
                    break

        # 2. Parabolic Pump & Dump Anomaly
        change_24h = ticker_data.get("change_24h", 0.0)
        volume_24h = ticker_data.get("volume_24h", 1000000.0)

        if change_24h > 45.0:
            risk_score += 40
            flags.append(f"Parabolic pump alert (+{change_24h:.1f}% in 24h). Severe dump risk within 1-4 hours.")
        elif change_24h > 20.0:
            risk_score += 20
            flags.append(f"High abnormal 24h gain (+{change_24h:.1f}%). Watch for distribution traps.")

        # 3. Wash Trading / Volume Inflation Anomaly
        if volume_24h < 50000.0 and change_24h > 15.0:
            risk_score += 35
            flags.append(f"Micro-liquidity pump ($24h vol: ${volume_24h:,.0f}). Unnatural price manipulation suspected.")

        # 4. Orderbook Spoofing / Fake Depth Asymmetry
        bids = orderbook.get("bids", [])
        asks = orderbook.get("asks", [])
        if bids and asks:
            bid_vol_top = sum(b[1] for b in bids[:5])
            ask_vol_top = sum(a[1] for a in asks[:5])
            total_vol = bid_vol_top + ask_vol_top
            if total_vol > 0:
                imbalance = abs(bid_vol_top - ask_vol_top) / total_vol
                if imbalance > 0.85:
                    risk_score += 25
                    dominant = "Bid" if bid_vol_top > ask_vol_top else "Ask"
                    flags.append(f"Severe L2 orderbook spoofing imbalance ({dominant} wall {imbalance*100:.0f}% dominant). Potential ghost wall.")

        risk_score = min(100, risk_score)

        status = "SAFE"
        if risk_score >= 70:
            status = "DANGER"
        elif risk_score >= 35:
            status = "WARNING"

        return {
            "name": "Scam & Fraud Hunter",
            "score": risk_score,
            "status": status,
            "metrics": {
                "verified_asset": is_known,
                "change_24h_pct": round(change_24h, 2),
                "volume_24h_usdt": round(volume_24h, 0),
                "spoofing_risk": "High" if risk_score > 50 else "Low"
            },
            "flags": flags,
            "summary": "Asset and orderbook display organic verification." if status == "SAFE" else ("Potential manipulation or spoofing detected." if status == "WARNING" else "CRITICAL FRAUD ALERT: High probability of pump & dump, spoofing, or honeypot!")
        }
