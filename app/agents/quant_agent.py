import asyncio
import logging
from typing import Dict, Any, List
from app.quant.analyst import QuantAnalyst

logger = logging.getLogger(__name__)

class QuantAnalystAgent:
    """
    Quantitative Analyst Sub-Agent for Alphaind.
    Evaluates statistical persistence (Hurst exponent), mean-reversion boundaries,
    momentum exhaustion, and composite alpha factor scores.
    """
    AGENT_NAME = "Quantitative Analyst"
    ROLE = "Statistical Factors, Regime Detection & Multi-Factor Alpha"

    @classmethod
    async def analyze(cls, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze price action using quantitative factor modeling.
        """
        await asyncio.sleep(0.04) # non-blocking async cadence

        quant = context.get("quant_data")
        if not quant:
            candles = context.get("candles", [])
            if candles:
                quant = QuantAnalyst.analyze_candles(candles)
            else:
                quant = QuantAnalyst._empty_quant_metrics()

        order_intent = context.get("order_intent", {})
        side = order_intent.get("side", "buy").lower()

        hurst = quant.get("hurst_exponent", 0.50)
        alpha_score = quant.get("composite_alpha_score", 0.0)
        rsi = quant.get("rsi", 50.0)
        z_score = quant.get("z_score", 0.0)
        atr_pct = quant.get("atr_pct", 1.5)
        regime = quant.get("market_regime", "Calm")

        flags: List[str] = []
        thought_trace: List[str] = [
            f"Measuring statistical persistence: Hurst Exponent is {hurst:.3f}.",
            f"Evaluating multi-factor composite alpha factor: {alpha_score:+.2f}."
        ]

        # 1. Hurst Exponent Interpretation
        if hurst > 0.53:
            hurst_regime = "Persistent / Trending"
            thought_trace.append(f"Hurst H={hurst:.2f} > 0.50 indicates positive autocorrelation. Momentum strategies carry statistical tailwind.")
        elif hurst < 0.47:
            hurst_regime = "Anti-Persistent / Mean-Reverting"
            thought_trace.append(f"Hurst H={hurst:.2f} < 0.50 indicates mean-reverting regime. Breakout strategies risk whip-saws; trade the boundaries.")
        else:
            hurst_regime = "Geometric Brownian / Random Walk"
            thought_trace.append(f"Hurst H={hurst:.2f} near 0.50 indicates noise-dominant random walk. Reduced statistical edge.")

        # 2. Side-Specific Alignment & Factor Check
        conviction_points = 50 # neutral baseline

        if side == "buy":
            # Bullish edge evaluation
            if alpha_score > 0.2:
                conviction_points += 25
                thought_trace.append(f"Positive composite alpha score ({alpha_score:+.2f}) confirms structural buying pressure.")
            elif alpha_score < -0.2:
                conviction_points -= 25
                flags.append(f"Negative composite alpha ({alpha_score:+.2f}) indicates structural headwind for Long entry.")

            if rsi < 35:
                conviction_points += 15
                thought_trace.append(f"Oversold RSI ({rsi:.1f}) provides discounted valuation buffer for dip-buyers.")
            elif rsi > 70:
                conviction_points -= 20
                flags.append(f"Overbought RSI ({rsi:.1f}) indicates buyer exhaustion; high risk of mean-reversion pullback.")

            if z_score < -1.8:
                thought_trace.append(f"Bollinger Z-Score is deeply stretched ({z_score:.2f}); statistical mean reversion favors upside bounce.")
            elif z_score > 2.0:
                flags.append(f"Price is +{z_score:.2f} standard deviations above 20-period mean; adverse risk-reward for new longs.")

        else: # sell / short
            if alpha_score < -0.2:
                conviction_points += 25
                thought_trace.append(f"Negative composite alpha score ({alpha_score:+.2f}) confirms structural selling pressure.")
            elif alpha_score > 0.2:
                conviction_points -= 25
                flags.append(f"Positive composite alpha ({alpha_score:+.2f}) indicates upward momentum counter-acting Short entry.")

            if rsi > 65:
                conviction_points += 15
                thought_trace.append(f"Elevated RSI ({rsi:.1f}) favors short sellers anticipating mean-reversion relief.")
            elif rsi < 30:
                conviction_points -= 20
                flags.append(f"Oversold RSI ({rsi:.1f}) warns of imminent short squeeze risk.")

            if z_score > 1.8:
                thought_trace.append(f"Bollinger Z-Score is extended (+{z_score:.2f}); favorable risk-reward for short mean-reversion.")

        conviction_points = min(100, max(0, conviction_points))

        # Status classification
        if conviction_points >= 65:
            status = "STRONG_EDGE"
            human_status = f"Strong Edge ({hurst_regime})"
            plain_summary = f"High Statistical Edge: Multi-factor alpha ({alpha_score:+.2f}) and Hurst ({hurst:.2f}) strongly align with {side.upper()} order."
        elif conviction_points >= 40:
            status = "MODERATE_EDGE"
            human_status = f"Moderate Edge ({hurst_regime})"
            plain_summary = f"Acceptable Statistical Edge: Market regime is {regime} with moderate factor backing."
        else:
            status = "UNFAVORABLE_REGIME"
            human_status = f"Unfavorable Regime ({hurst_regime})"
            plain_summary = f"Statistical Headwind: Indicators show counter-trend risk and reduced expectancy for {side.upper()}."

        # Risk score for defense synthesis (higher = higher risk)
        risk_score = 100 - conviction_points

        return {
            "agent": cls.AGENT_NAME,
            "role": cls.ROLE,
            "status": status,
            "human_status": human_status,
            "score": risk_score,
            "alpha_conviction_score": conviction_points,
            "metrics": {
                "hurst_exponent": round(hurst, 3),
                "hurst_regime": hurst_regime,
                "composite_alpha": round(alpha_score, 3),
                "rsi_14": round(rsi, 1),
                "z_score": round(z_score, 2),
                "hourly_atr_pct": round(atr_pct, 2),
                "market_regime": regime
            },
            "flags": flags,
            "thought_trace": thought_trace,
            "summary": plain_summary
        }
