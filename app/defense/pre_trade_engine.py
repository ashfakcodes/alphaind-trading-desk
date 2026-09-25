import logging
from typing import Dict, Any, List
from app.defense.volatility_sentinel import VolatilitySentinel
from app.defense.fraud_detector import FraudDetector
from app.defense.security_guard import SecurityGuard
from app.defense.liquidity_auditor import LiquidityAuditor
from app.defense.psychology_shield import PsychologyShield
from app.services.openrouter_client import openrouter_client

logger = logging.getLogger(__name__)

class PreTradeEngine:
    """
    Master Pre-Trade Zero-Trust Defense Shield Coordinator.
    Runs deep 5-pillar audits and LLM threat synthesis right before order dispatch.
    """

    @classmethod
    def execute_pre_trade_flight_check(
        cls,
        order_request: Dict[str, Any],
        ticker_data: Dict[str, Any],
        orderbook: Dict[str, Any],
        quant_data: Dict[str, Any],
        recent_trades: List[Dict[str, Any]],
        portfolio_equity: float = 50000.0
    ) -> Dict[str, Any]:
        symbol = order_request.get("symbol", "BTCUSDT")
        side = order_request.get("side", "buy")
        size = float(order_request.get("size", 0.1))
        leverage = int(order_request.get("leverage", 1))
        notional = size * ticker_data.get("last_price", 100.0)

        # 1. Run All 5 Pillars
        p1_vol = VolatilitySentinel.evaluate(symbol, quant_data, order_request)
        p2_fraud = FraudDetector.evaluate(symbol, ticker_data, orderbook)
        p3_sec = SecurityGuard.evaluate(symbol, notional)
        p4_liq = LiquidityAuditor.evaluate(symbol, side, size, orderbook, quant_data.get("annualized_volatility", 45.0))
        p5_psych = PsychologyShield.evaluate(symbol, side, size, leverage, quant_data, recent_trades, portfolio_equity)

        # 2. Weighted Composite Risk Score
        # Weights: Fraud (25%), Security (20%), Volatility (20%), Liquidity (15%), Psychology (20%)
        composite_score = int(
            (p1_vol["score"] * 0.20) +
            (p2_fraud["score"] * 0.25) +
            (p3_sec["score"] * 0.20) +
            (p4_liq["score"] * 0.15) +
            (p5_psych["score"] * 0.20)
        )
        composite_score = min(100, max(0, composite_score))

        # 3. Overall Verdict Determination
        # Auto-block if any single pillar reaches critical (>= 80) or composite >= 65
        any_critical_pillar = any(p["score"] >= 80 for p in [p1_vol, p2_fraud, p3_sec, p4_liq, p5_psych])

        if composite_score >= 65 or any_critical_pillar:
            overall_verdict = "BLOCKED"
        elif composite_score >= 38:
            overall_verdict = "CAUTION"
        else:
            overall_verdict = "SAFE"

        # 4. Aggregated Actionable Precautions & Threat Flags
        all_flags = (
            p1_vol["flags"] +
            p2_fraud["flags"] +
            p3_sec["flags"] +
            p4_liq["flags"] +
            p5_psych["flags"]
        )

        defense_report = {
            "symbol": symbol,
            "side": side.upper(),
            "size": size,
            "notional_usdt": round(notional, 2),
            "leverage": leverage,
            "composite_risk_score": composite_score,
            "overall_verdict": overall_verdict,
            "pillars": {
                "volatility": p1_vol,
                "scam_fraud": p2_fraud,
                "security": p3_sec,
                "liquidity": p4_liq,
                "psychology": p5_psych
            },
            "all_flags": all_flags
        }

        # 5. OpenRouter AI Threat Synthesis
        trade_details = {
            "symbol": symbol,
            "side": side.upper(),
            "order_type": order_request.get("order_type", "market"),
            "size": size,
            "notional_usdt": round(notional, 2),
            "leverage": leverage
        }
        ai_review = openrouter_client.review_pre_trade_threats(trade_details, defense_report)
        defense_report["ai_review"] = ai_review

        return defense_report

pre_trade_engine = PreTradeEngine()
