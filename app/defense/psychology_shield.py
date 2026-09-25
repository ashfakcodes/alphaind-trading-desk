import time
from typing import Dict, Any, List

class PsychologyShield:
    """
    Pillar 5: Psychological Threats & Tilt Interceptor.
    Protects traders from emotional biases right before trade execution:
    - FOMO (parabolic impulse buying)
    - Revenge Trading (loss streak escalation)
    - Tilt & Leverage Overdose (martingale size doubling)
    - Overtrading & Panic Fatigue
    """

    @classmethod
    def evaluate(
        cls,
        symbol: str,
        side: str,
        size: float,
        leverage: int,
        quant_data: Dict[str, Any],
        recent_trades: List[Dict[str, Any]],
        portfolio_equity: float = 50000.0
    ) -> Dict[str, Any]:
        risk_score = 10  # baseline calm trader
        flags: List[str] = []
        tilt_indicators: List[str] = []

        notional = size * quant_data.get("current_price", 100.0)
        rsi = quant_data.get("rsi", 50.0)
        z_score = quant_data.get("z_score", 0.0)

        # 1. FOMO (Fear Of Missing Out) Chasing
        if side.lower() == "buy":
            if rsi > 76.0 or z_score > 2.5:
                risk_score += 40
                tilt_indicators.append("FOMO_CHASING")
                flags.append(f"FOMO Peak Alert: Market is violently overbought (RSI {rsi:.1f}, Z-Score +{z_score:.1f}σ). High risk of buying the top.")
            elif rsi > 68.0:
                risk_score += 20
                flags.append(f"Late momentum entry: RSI is {rsi:.1f}. Favorable risk/reward has diminished.")
        elif side.lower() == "sell":
            if rsi < 24.0 or z_score < -2.5:
                risk_score += 40
                tilt_indicators.append("PANIC_DUMPING")
                flags.append(f"Panic Sell Alert: Market is oversold (RSI {rsi:.1f}, Z-Score {z_score:.1f}σ). High risk of selling the bottom.")

        # 2. Revenge Trading Detection (Loss Streak Analysis)
        recent_closed = [t for t in recent_trades if "pnl" in t][-5:]
        consecutive_losses = 0
        for t in reversed(recent_closed):
            if t["pnl"] < 0:
                consecutive_losses += 1
            else:
                break

        if consecutive_losses >= 3:
            risk_score += 45
            tilt_indicators.append("REVENGE_TRADING")
            flags.append(f"Revenge Trading Alert: Trader has {consecutive_losses} consecutive loss trades. Cognitive tilt is statistically high.")
        elif consecutive_losses == 2:
            risk_score += 20
            flags.append("Caution: 2 consecutive loss trades. Maintain strict risk budget.")

        # 3. Position Size Escalation & Martingale Tilt
        if recent_closed:
            avg_past_notional = sum(t.get("size", 1) * t.get("entry_price", 100) for t in recent_closed) / len(recent_closed)
            if avg_past_notional > 0 and (notional / avg_past_notional) >= 2.5:
                risk_score += 35
                tilt_indicators.append("SIZE_ESCALATION")
                flags.append(f"Position size escalation: Current trade (${notional:,.2f}) is {notional/avg_past_notional:.1f}x larger than recent average.")

        # 4. Leverage Overdose
        if leverage > 20:
            risk_score += 40
            tilt_indicators.append("EXCESSIVE_LEVERAGE")
            flags.append(f"Dangerous leverage multiplier ({leverage}x). Liquidation distance is dangerously narrow.")
        elif leverage > 10:
            risk_score += 15
            flags.append(f"High leverage ({leverage}x). Volatility spike could trigger margin call.")

        # 5. Trading Cadence / Panic Frequency
        now = time.time()
        very_recent_orders = [t for t in recent_trades if (now - (t.get("timestamp", 0) / 1000.0)) < 120]
        if len(very_recent_orders) >= 3:
            risk_score += 30
            tilt_indicators.append("CADENCE_FATIGUE")
            flags.append(f"Overtrading cadence: {len(very_recent_orders)} trades initiated in past 2 minutes. Step back and breathe.")

        risk_score = min(100, risk_score)

        status = "SAFE"
        if risk_score >= 70:
            status = "DANGER"
        elif risk_score >= 35:
            status = "WARNING"

        return {
            "name": "Psychological & Tilt Interceptor",
            "score": risk_score,
            "status": status,
            "tilt_detected": len(tilt_indicators) > 0,
            "tilt_factors": tilt_indicators,
            "metrics": {
                "consecutive_loss_streak": consecutive_losses,
                "current_leverage": leverage,
                "trade_notional_usdt": round(notional, 2),
                "portfolio_exposure_pct": round((notional / portfolio_equity) * 100, 1) if portfolio_equity > 0 else 0.0
            },
            "flags": flags,
            "summary": "Trader discipline and mindset metrics are optimal." if status == "SAFE" else ("Cognitive bias or mild frustration detected." if status == "WARNING" else "PSYCHOLOGICAL EMERGENCY: Severe FOMO / Revenge Trading Tilt detected! Cool-off strongly recommended.")
        }
