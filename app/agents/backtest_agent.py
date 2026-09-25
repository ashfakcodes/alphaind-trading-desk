import asyncio
import logging
from typing import Dict, Any, List, Optional
from app.quant.backtester import IndustrialBacktester
from app.services.bitget_client import bitget_client

logger = logging.getLogger(__name__)

class BacktestAgent:
    """
    Strategy Backtester Sub-Agent for Alphaind.
    Executes bar-by-bar historical backtesting with realistic Bitget fees & slippage,
    evaluates Sharpe/Sortino ratios, and stress-tests trade setups using
    500-run Monte Carlo permutations for drawdown and ruin probability.
    """
    AGENT_NAME = "Strategy Backtester"
    ROLE = "Empirical Strategy Simulation & Monte Carlo Ruin Modeling"

    @classmethod
    async def analyze(cls, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze trade intent by running a backtest on recent historical candles.
        """
        await asyncio.sleep(0.05) # non-blocking async cadence

        order_intent = context.get("order_intent", {})
        symbol = order_intent.get("symbol", context.get("symbol", "BTCUSDT")).upper()
        leverage = int(order_intent.get("leverage", 1))
        strategy_type = context.get("strategy_type", "regime_alpha")

        # Fetch candles if not present
        candles = context.get("candles")
        if not candles:
            candles = bitget_client.get_historical_candles(symbol, "1h", limit=120)

        # Calibrate bracket SL/TP based on leverage if not explicitly provided
        sl_pct = context.get("stop_loss_pct", round(min(0.08, max(0.015, 0.25 / max(1, leverage))), 3))
        tp_pct = context.get("take_profit_pct", round(sl_pct * 2.4, 3))

        tester = IndustrialBacktester(
            initial_capital=10000.0,
            fee_rate=0.0006,
            slippage_rate=0.0004,
            stop_loss_pct=sl_pct,
            take_profit_pct=tp_pct,
            risk_per_trade=0.02
        )

        backtest_result = tester.run_backtest(candles=candles, strategy_type=strategy_type, symbol=symbol)
        summary = backtest_result.get("summary", {})
        monte_carlo = backtest_result.get("monte_carlo", {})

        total_return = summary.get("total_return_pct", 0.0)
        win_rate = summary.get("win_rate_pct", 50.0)
        sharpe = summary.get("sharpe_ratio", 0.0)
        profit_factor = summary.get("profit_factor", 1.0)
        max_dd = summary.get("max_drawdown_pct", 0.0)
        total_trades = summary.get("total_trades", 0)

        mc_worst_dd = monte_carlo.get("worst_drawdown_pct", max_dd)
        mc_median_return = monte_carlo.get("median_return_pct", total_return)
        mc_confidence_95 = monte_carlo.get("confidence_interval_95", [0.0, 0.0])

        flags: List[str] = []
        thought_trace: List[str] = [
            f"Simulated {total_trades} historical trade executions on {symbol} using '{strategy_type}' strategy.",
            f"Net Return: {total_return:+.2f}% | Win Rate: {win_rate:.1f}% | Profit Factor: {profit_factor:.2f}."
        ]

        # Edge & Ruin Evaluation
        thought_trace.append(
            f"Monte Carlo analysis (500 permutations): 95% worst-case drawdown is {mc_worst_dd:.1f}%."
        )

        if sharpe > 1.2 and win_rate >= 55.0 and total_return > 0:
            status = "STRONG_EMPIRICAL_EDGE"
            human_status = "Profitable Historical Edge"
            plain_summary = (
                f"Robust Historical Track Record: {strategy_type} achieved {win_rate:.1f}% win rate "
                f"with a Sharpe of {sharpe:.2f} and +{total_return:+.1f}% simulated return."
            )
            risk_score = max(10, int(max_dd * 2.5))
        elif total_return >= 0 and profit_factor >= 1.0:
            status = "ACCEPTABLE_EDGE"
            human_status = "Positive Expectancy"
            plain_summary = (
                f"Modest Historical Edge: Strategy generated +{total_return:+.1f}% return across "
                f"{total_trades} trades. Max drawdown capped at -{max_dd:.1f}%."
            )
            risk_score = 35
        else:
            status = "NEGATIVE_EXPECTANCY"
            human_status = "Unfavorable Historical Performance"
            plain_summary = (
                f"Historical Warning: Strategy yielded negative expectancy ({total_return:+.1f}% return, "
                f"Sharpe {sharpe:.2f}). Consider adjusting entry filters or SL/TP."
            )
            flags.append(f"Historical backtest indicates negative expectancy ({total_return:+.1f}% return).")
            risk_score = 65

        if mc_worst_dd > 15.0:
            flags.append(f"Monte Carlo tail-risk alert: 95th percentile worst drawdown reached -{mc_worst_dd:.1f}%.")
            risk_score = min(90, risk_score + 20)

        risk_score = min(100, max(5, risk_score))

        return {
            "agent": cls.AGENT_NAME,
            "role": cls.ROLE,
            "status": status,
            "human_status": human_status,
            "score": risk_score,
            "metrics": {
                "strategy": strategy_type,
                "total_trades": total_trades,
                "win_rate_pct": win_rate,
                "profit_factor": profit_factor,
                "sharpe_ratio": sharpe,
                "sortino_ratio": summary.get("sortino_ratio", 0.0),
                "max_drawdown_pct": max_dd,
                "total_return_pct": total_return,
                "monte_carlo_worst_dd_pct": mc_worst_dd,
                "monte_carlo_median_return_pct": mc_median_return,
                "monte_carlo_confidence_95": mc_confidence_95,
                "bracket_sl_pct": round(sl_pct * 100, 2),
                "bracket_tp_pct": round(tp_pct * 100, 2)
            },
            "flags": flags,
            "thought_trace": thought_trace,
            "summary": plain_summary,
            "full_report": backtest_result
        }

    @classmethod
    async def run_simulation(
        cls,
        symbol: str = "BTCUSDT",
        strategy_type: str = "regime_alpha",
        initial_capital: float = 10000.0,
        stop_loss_pct: float = 0.025,
        take_profit_pct: float = 0.060,
        candle_limit: int = 150
    ) -> Dict[str, Any]:
        """Direct execution for ReAct tool or API."""
        symbol = symbol.upper()
        candles = bitget_client.get_historical_candles(symbol, "1h", limit=candle_limit)
        context = {
            "symbol": symbol,
            "order_intent": {"symbol": symbol, "side": "buy", "leverage": 3},
            "strategy_type": strategy_type,
            "candles": candles,
            "stop_loss_pct": stop_loss_pct,
            "take_profit_pct": take_profit_pct
        }
        return await cls.analyze(context)
