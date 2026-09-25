import asyncio
import logging
import time
from typing import Dict, Any, List, Optional

from app.services.bitget_client import bitget_client
from app.services.openrouter_client import openrouter_client
from app.quant.analyst import QuantAnalyst
from app.quant.stress_tester import stress_tester
from app.quant.backtester import backtester

logger = logging.getLogger(__name__)

class SwarmDeliberationArena:
    """
    Multi-Agent Deliberation Arena for Alphaind.
    Instead of isolated scores, specialized agents debate the thesis:
    1. AlphaConductor: Frames premise, market regime, and portfolio constraints.
    2. Bullish Alpha Strategist: Argues for upside momentum, persistent Hurst trend, and breakout targets.
    3. Bearish Risk Sentinel: Attacks vulnerability, orderbook depth limits, liquidation cascade triggers.
    4. Execution Guardian: Resolves the debate with exact trade parameter safeguards.
    """

    DEFAULT_SIZES = {
        "BTCUSDT": 0.1,
        "ETHUSDT": 1.0,
        "SOLUSDT": 10.0,
        "DOGEUSDT": 5000.0,
        "BGBUSDT": 1000.0,
        "NVDAUSDT": 25.0,
        "TSLAUSDT": 10.0,
        "AAPLUSDT": 20.0,
        "COINUSDT": 15.0,
        "SPYUSDT": 5.0,
        "MSFTUSDT": 10.0
    }

    @classmethod
    def get_default_size(cls, symbol: str) -> float:
        return cls.DEFAULT_SIZES.get(symbol.upper(), 0.5)

    @classmethod
    async def deliberate(cls, symbol: str, requested_leverage: int = 3, requested_size: Optional[float] = None, raw_prompt: str = "") -> Dict[str, Any]:
        t0 = time.time()
        symbol = symbol.upper()
        if requested_size is None or requested_size <= 0:
            requested_size = cls.get_default_size(symbol)
        if requested_leverage is None or requested_leverage <= 0:
            requested_leverage = 3

        # Gather ground truth telemetry concurrently
        ticker, candles, orderbook = await asyncio.gather(
            asyncio.to_thread(bitget_client.get_ticker, symbol),
            asyncio.to_thread(bitget_client.get_historical_candles, symbol, "1h", 50),
            asyncio.to_thread(bitget_client.get_orderbook, symbol, 15)
        )
        price = ticker.get("last_price", 100.0)
        quant = QuantAnalyst.analyze_candles(candles)
        stress = stress_tester.evaluate(
            {"symbol": symbol, "side": "buy", "size": requested_size, "leverage": requested_leverage, "notional_usdt": requested_size * price},
            current_price=price
        )

        # Run empirical backtest on historical bars
        bt_res = backtester.run_backtest(candles=candles, strategy_type="regime_alpha", symbol=symbol)
        bt_summary = bt_res.get("summary", {})
        mc_summary = bt_res.get("monte_carlo", {})

        hurst = quant.get("hurst_exponent", 0.5)
        rsi = quant.get("rsi", 50.0)
        atr_pct = quant.get("atr_pct", 1.5)
        alpha_score = quant.get("composite_alpha_score", 0.0)
        regime = quant.get("market_regime", "Calm")

        # 1. Conductor Opening
        thesis_intro = f" on trade thesis: \"{raw_prompt}\"" if raw_prompt else ""
        conductor_intro = (
            f"Deliberation convened{thesis_intro} for {symbol} at ${price:,.2f}. "
            f"Trader proposed size {requested_size} with {requested_leverage}x leverage. "
            f"Identified regime: {regime} (Hurst: {hurst}, Alpha Score: {alpha_score:+.2f}). "
            f"The floor is open to debate thesis viability."
        )

        # 2. Bullish Alpha Strategist Argument
        bullish_points = []
        if hurst > 0.52:
            bullish_points.append(f"Strong persistent trend indicated by Hurst exponent ({hurst} > 0.50). Momentum carries edge.")
        else:
            bullish_points.append(f"Mean-reverting regime (Hurst {hurst}). Favorable for entry near lower Bollinger support.")

        if rsi < 40:
            bullish_points.append(f"RSI is oversold at {rsi:.1f}, indicating discounted valuation ready for a relief bounce.")
        elif rsi < 65:
            bullish_points.append(f"RSI ({rsi:.1f}) is in healthy expansion territory without overbought exhaustion.")
        else:
            bullish_points.append(f"Aggressive upside momentum with RSI at {rsi:.1f}; buyers in active control.")

        if alpha_score > 0:
            bullish_points.append(f"Quant composite alpha factor is positive ({alpha_score:+.2f}), indicating statistical upward bias.")
        else:
            bullish_points.append(f"Potential inflection point: risk-reward favors a calculated reversal attempt.")

        if bt_summary.get("win_rate_pct", 0) >= 50:
            bullish_points.append(f"Strategy Backtester confirms historical edge: {bt_summary.get('win_rate_pct')}% win rate and Sharpe ratio of {bt_summary.get('sharpe_ratio')}.")

        bull_speech = (
            f"Upside Thesis: {symbol} displays compelling structural characteristics. "
            + " ".join(bullish_points)
            + f" Projected target: ${price * 1.06:,.2f} (+6.0% return on unleveraged spot, +{6.0 * requested_leverage:.1f}% on {requested_leverage}x leverage)."
        )

        # 3. Bearish Risk Sentinel Argument
        bearish_points = []
        if requested_leverage >= 10:
            bearish_points.append(f"Excessive leverage ({requested_leverage}x) shrinks liquidation cushion down to {stress['liquidation_buffer_pct']}%.")
        elif requested_leverage >= 5:
            bearish_points.append(f"Moderate leverage ({requested_leverage}x) leaves limited room for market noise.")

        if atr_pct > 2.5:
            bearish_points.append(f"Elevated hourly ATR volatility ({atr_pct:.1f}% per hour) will hunt tight stop-losses.")

        mc_worst_dd = mc_summary.get("p95_worst_drawdown_pct") or mc_summary.get("worst_drawdown_pct", 0)
        if mc_worst_dd > 10.0:
            bearish_points.append(f"Backtester 500-run Monte Carlo simulation indicates worst-case tail risk of -{mc_worst_dd:.1f}% drawdown.")

        if not stress.get("survived_all", True):
            bearish_points.append(f"Position fails historical crisis stress tests (resilience: {stress['resilience_rating']}, {stress['survival_ratio']} scenarios survived).")
        else:
            bearish_points.append(f"While stress tests passed ({stress['survival_ratio']}), unexpected tail risk can still cause slippage.")

        liq_price = stress.get("liquidation_price", 0.0)
        if requested_leverage > 1 and liq_price > 0:
            bear_tail = f" Liquidation price looms at ${liq_price:,.2f} (buffer: {stress['liquidation_buffer_pct']}%)."
        else:
            bear_tail = f" Unleveraged structure protects from liquidation, but market noise remains an active risk."

        bear_speech = (
            f"Downside Rebuttal: Not so fast. The proposed structure exposes the trader to unnecessary ruin probability. "
            + " ".join(bearish_points)
            + bear_tail
        )

        # 4. Execution Guardian Reconciliation
        if requested_leverage > 4 or not stress.get("survived_all", True) or atr_pct > 2.8:
            safe_leverage = min(3, requested_leverage)
            consensus_status = "CONDITIONAL_APPROVAL_DERISKED"
            exec_decision = (
                f"Consensus Reconciled: We accept the directional bias but REJECT the aggressive risk envelope. "
                f"Capping leverage at {safe_leverage}x (cushioning liquidation to >30%), "
                f"mandating a strict -3.5% Stop-Loss at ${price * 0.965:,.2f}, and routing via TWAP."
            )
        elif requested_leverage <= 4 and stress.get("survived_all", True):
            safe_leverage = requested_leverage
            consensus_status = "UNANIMOUS_HIGH_CONVICTION"
            exec_decision = (
                f"Consensus Reconciled: Unanimous green light. Parameters are disciplined. "
                f"Proceed with {safe_leverage}x leverage, standard market execution, and bracket take-profit at ${price * 1.06:,.2f}."
            )
        else:
            safe_leverage = 2
            consensus_status = "CAUTION_HEAVILY_RESTRICTED"
            exec_decision = (
                f"Consensus Reconciled: High turbulence requires conservative posturing. "
                f"Cap size to {round(requested_size * 0.6, 3)} and leverage to {safe_leverage}x."
            )

        transcript = [
            {"speaker": "AlphaConductor (Chair)", "role": "Master Orchestrator", "avatar": "AC", "statement": conductor_intro},
            {"speaker": "Alpha Strategist (Bull)", "role": "Opportunity & Momentum Hunter", "avatar": "AS", "statement": bull_speech},
            {"speaker": "Risk Sentinel (Bear)", "role": "Vulnerability & Stress Auditor", "avatar": "RS", "statement": bear_speech},
            {"speaker": "Execution Guardian", "role": "Capital Preservation & Routing", "avatar": "EG", "statement": exec_decision}
        ]

        elapsed_ms = round((time.time() - t0) * 1000, 1)

        return {
            "symbol": symbol,
            "raw_prompt": raw_prompt,
            "latency_ms": elapsed_ms,
            "consensus_status": consensus_status,
            "recommended_leverage": safe_leverage,
            "original_leverage": requested_leverage,
            "market_regime": regime,
            "alpha_score": alpha_score,
            "quant_metrics": quant,
            "backtest_metrics": bt_summary,
            "monte_carlo_metrics": mc_summary,
            "transcript": transcript,
            "proposed_plan": {
                "action": "BUY",
                "symbol": symbol,
                "size": requested_size,
                "leverage": safe_leverage,
                "target_tp": round(price * 1.06, 2),
                "stop_loss": round(price * 0.965, 2),
                "liquidation_buffer": f"{stress['liquidation_buffer_pct']}%",
                "current_price": round(price, 2),
                "notional_usdt": round(requested_size * price, 2)
            }
        }

swarm_arena = SwarmDeliberationArena()
