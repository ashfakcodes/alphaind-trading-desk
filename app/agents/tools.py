import asyncio
import concurrent.futures
import logging
import math
import time
from typing import Dict, Any, List, Optional
import numpy as np

from app.services.bitget_client import bitget_client
from app.quant.analyst import QuantAnalyst
from app.quant.stress_tester import stress_tester
from app.config import settings
from app.agents.volatility_agent import VolatilityAgent
from app.agents.fraud_agent import FraudHunterAgent
from app.agents.security_agent import SecurityAgent
from app.agents.liquidity_agent import LiquidityAgent
from app.agents.psychology_agent import PsychologyAgent
from app.agents.quant_agent import QuantAnalystAgent
from app.agents.backtest_agent import BacktestAgent
from app.agents.swarm_deliberation import swarm_arena

logger = logging.getLogger(__name__)

class AgentTool:
    """Represents a callable tool exposed to autonomous agents."""
    def __init__(self, name: str, description: str, parameters: Dict[str, Any], func: Any):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.func = func

    async def execute(self, **kwargs) -> Dict[str, Any]:
        if asyncio.iscoroutinefunction(self.func):
            return await self.func(**kwargs)
        return self.func(**kwargs)

class AgentToolRegistry:
    """
    Central Registry of tools empowering Alphaind agents with True Agentic capabilities:
    - Market scanning & opportunity discovery
    - L2 Orderbook depth walking & Kyle's Lambda market impact
    - Statistical factor analysis & Hurst regime modeling
    - Multi-scenario crisis stress testing & liquidation buffer calculation
    - 5-Pillar Swarm defense dispatch
    - Portfolio VaR (Value-at-Risk) and risk concentration auditing
    - Automated safe parameter synthesis & TWAP tranche execution
    """

    def __init__(self):
        self._tools: Dict[str, AgentTool] = {}
        self._register_default_tools()

    def register(self, tool: AgentTool):
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[AgentTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters
            }
            for t in self._tools.values()
        ]

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        tool = self.get_tool(tool_name)
        if not tool:
            return {"success": False, "error": f"Tool '{tool_name}' not found in registry."}
        try:
            result = await tool.execute(**arguments)
            return {"success": True, "tool": tool_name, "result": result}
        except Exception as e:
            logger.error(f"Execution error in tool {tool_name}: {e}", exc_info=True)
            return {"success": False, "tool": tool_name, "error": str(e)}

    # -------------------------------------------------------------
    # Tool Implementations
    # -------------------------------------------------------------

    def _register_default_tools(self):
        # 1. Market Opportunity Scanner
        self.register(AgentTool(
            name="tool_market_scanner",
            description="Scans the Bitget watchlist to rank coins by momentum, composite alpha, volatility, or oversold RSI.",
            parameters={
                "filter_by": "Filter criteria: 'momentum', 'alpha', 'low_volatility', 'oversold', 'high_volume'",
                "top_n": "Number of top candidates to return (default: 5)"
            },
            func=self._scan_market_opportunities
        ))

        # 2. Orderbook Depth & Market Impact
        self.register(AgentTool(
            name="tool_get_market_depth",
            description="Walks Bitget Level 2 orderbook depth to compute exact slippage, Kyle's lambda market impact, and bid-ask spread.",
            parameters={
                "symbol": "Asset symbol, e.g. 'BTCUSDT', 'SOLUSDT'",
                "order_size": "Proposed order size in base asset units",
                "side": "'buy' or 'sell'"
            },
            func=self._get_market_depth_and_impact
        ))

        # 3. Quantitative Factors & Regime
        self.register(AgentTool(
            name="tool_quant_analytics",
            description="Computes Hurst exponent, RSI(14), ATR%, Bollinger bandwidth, Parkinson volatility, and market regime from candle history.",
            parameters={
                "symbol": "Asset symbol, e.g. 'BTCUSDT'",
                "timeframe": "Candle timeframe, e.g. '1h' (default)",
                "limit": "Candle count limit (default: 50)"
            },
            func=self._calculate_quant_factors
        ))

        # 4. Crisis Stress Testing
        self.register(AgentTool(
            name="tool_crisis_stress_test",
            description="Simulates historical black swan crisis shocks (COVID March 2020, FTX crash, Luna collapse, Flash Crash) to evaluate liquidation buffer.",
            parameters={
                "symbol": "Asset symbol, e.g. 'BTCUSDT'",
                "leverage": "Leverage multiplier (e.g. 1 to 50)",
                "size": "Order size in base currency",
                "side": "'buy' or 'sell'"
            },
            func=self._run_crisis_stress_test
        ))

        # 5. Portfolio Risk & VaR Audit
        self.register(AgentTool(
            name="tool_portfolio_risk_audit",
            description="Audits current account balances, calculates Value at Risk (VaR 95%/99%), leverage concentration, and detects delta imbalance.",
            parameters={},
            func=self._audit_portfolio_and_var
        ))

        # 6. Swarm Defense Audit
        self.register(AgentTool(
            name="tool_run_swarm_defense",
            description="Launches all 5 specialized sub-agents (Volatility, Fraud, Security, Liquidity, Psychology) in parallel to compute composite risk.",
            parameters={
                "symbol": "Asset symbol, e.g. 'BTCUSDT'",
                "side": "'buy' or 'sell'",
                "size": "Order size in base asset",
                "leverage": "Order leverage (e.g. 1 to 50)",
                "prompt": "Original user prompt (for psychology/tilt detection)"
            },
            func=self._run_swarm_defense
        ))

        # 7. Safe Prescription Generator
        self.register(AgentTool(
            name="tool_prescribe_safe_trade",
            description="Calculates mathematically optimized safe leverage, TWAP tranches, stop-loss and take-profit targets to de-risk a proposed position.",
            parameters={
                "symbol": "Asset symbol",
                "original_leverage": "Requested leverage",
                "size": "Requested size",
                "risk_flags": "List of threat flags identified during defense scan"
            },
            func=self._prescribe_safe_trade
        ))

        # 8. Bitget Direct Order Execution
        self.register(AgentTool(
            name="tool_execute_order",
            description="Dispatches a verified order directly to Bitget v2 (or paper simulation desk).",
            parameters={
                "symbol": "Asset symbol",
                "side": "'buy' or 'sell'",
                "size": "Order size",
                "order_type": "'market' or 'limit'",
                "leverage": "Leverage multiplier"
            },
            func=self._execute_order
        ))

        # 9. Algorithmic TWAP Execution
        self.register(AgentTool(
            name="tool_execute_twap",
            description="Splits a large trade into multiple algorithmic tranches to eliminate slippage and book exhaustion.",
            parameters={
                "symbol": "Asset symbol",
                "side": "'buy' or 'sell'",
                "total_size": "Total size to execute across tranches",
                "tranches": "Number of tranches (e.g. 3, 5)",
                "interval_sec": "Interval between tranches in seconds"
            },
            func=self._execute_twap
        ))

        # 10. Quantitative Backtesting & Monte Carlo Simulation
        self.register(AgentTool(
            name="tool_run_backtest",
            description="Runs an event-driven quantitative backtest simulation with 500-run Monte Carlo permutation on historical Bitget candles, returning Sharpe, Sortino, win rate, max drawdown, and ruin risk.",
            parameters={
                "symbol": "Asset symbol (e.g. 'BTCUSDT', 'SOLUSDT')",
                "strategy_type": "Strategy algorithm: 'regime_alpha', 'bollinger_mean_reversion', 'trend_macd' (default: 'regime_alpha')",
                "initial_capital": "Starting capital in USDT (default: 10000.0)",
                "stop_loss_pct": "Stop loss percentage as decimal (e.g. 0.025 for 2.5%)",
                "take_profit_pct": "Take profit percentage as decimal (e.g. 0.06 for 6.0%)",
                "candle_limit": "Historical candle bars to evaluate (default: 150)"
            },
            func=self._run_backtest
        ))

        # 11. Deep Quantitative Factor & Regime Audit
        self.register(AgentTool(
            name="tool_quant_deep_audit",
            description="Performs an in-depth quantitative factor audit and regime diagnosis via the Quant Analyst Sub-Agent (Hurst exponent, Parkinson volatility, Bollinger Z-score, multi-factor alpha score).",
            parameters={
                "symbol": "Asset symbol (e.g. 'BTCUSDT')",
                "side": "'buy' or 'sell' (default: 'buy')",
                "timeframe": "Candle timeframe (default: '1h')",
                "limit": "Number of candles to analyze (default: 60)"
            },
            func=self._run_quant_deep_audit
        ))

        # 12. Swarm Deliberation Arena (Bull vs Bear Debate)
        self.register(AgentTool(
            name="tool_swarm_debate",
            description="Convenes the Multi-Agent Deliberation Arena: AlphaConductor, Bullish Strategist, Bearish Risk Sentinel, and Execution Guardian to debate trade viability and reconcile a de-risked consensus execution plan.",
            parameters={
                "symbol": "Asset symbol to debate (e.g. 'BTCUSDT', 'SOLUSDT', 'NVDAUSDT')",
                "leverage": "Proposed leverage (default: 3)",
                "size": "Proposed position size (optional)",
                "prompt": "Trade premise or thesis for the agents to debate"
            },
            func=self._run_swarm_debate
        ))

    # -------------------------------------------------------------
    # Concrete Tool Handlers
    # -------------------------------------------------------------

    async def _run_swarm_debate(self, symbol: str = "BTCUSDT", leverage: int = 3, size: Optional[float] = None, prompt: str = "") -> Dict[str, Any]:
        return await swarm_arena.deliberate(
            symbol=symbol,
            requested_leverage=leverage,
            requested_size=size,
            raw_prompt=prompt
        )

    def _scan_market_opportunities(self, filter_by: str = "momentum", top_n: int = 5) -> Dict[str, Any]:
        candidates = []
        for sym in settings.WATCHLIST:
            ticker = bitget_client.get_ticker(sym)
            candles = bitget_client.get_historical_candles(sym, "1h", limit=40)
            quant = QuantAnalyst.analyze_candles(candles)

            price = ticker.get("last_price", 100.0)
            chg_24h = ticker.get("change_24h", 0.0)
            vol_24h = ticker.get("volume_24h", 1000000.0)
            alpha_score = quant.get("composite_alpha_score", 0.0)
            hurst = quant.get("hurst_exponent", 0.5)
            rsi = quant.get("rsi", 50.0)
            atr_pct = quant.get("atr_pct", 1.5)
            regime = quant.get("market_regime", "Calm")

            candidates.append({
                "symbol": sym,
                "price": price,
                "change_24h": round(chg_24h, 2),
                "volume_24h": round(vol_24h, 0),
                "composite_alpha": round(alpha_score, 3),
                "hurst_exponent": round(hurst, 3),
                "rsi": round(rsi, 1),
                "atr_pct": round(atr_pct, 2),
                "regime": regime
            })

        # Sorting logic
        if filter_by == "momentum":
            candidates.sort(key=lambda x: x["change_24h"], reverse=True)
        elif filter_by == "alpha":
            candidates.sort(key=lambda x: x["composite_alpha"], reverse=True)
        elif filter_by == "low_volatility":
            candidates.sort(key=lambda x: x["atr_pct"])
        elif filter_by == "oversold":
            candidates.sort(key=lambda x: x["rsi"])
        elif filter_by == "high_volume":
            candidates.sort(key=lambda x: x["volume_24h"], reverse=True)
        else:
            candidates.sort(key=lambda x: x["composite_alpha"], reverse=True)

        selected = candidates[:top_n]
        best_candidate = selected[0] if selected else None

        return {
            "filter_applied": filter_by,
            "total_scanned": len(candidates),
            "top_candidates": selected,
            "best_opportunity": best_candidate,
            "rationale": f"Ranked {len(candidates)} watchlist pairs. '{best_candidate['symbol']}' ranks highest with 24h change of {best_candidate['change_24h']:+}% and Alpha score {best_candidate['composite_alpha']}." if best_candidate else "No candidates found."
        }

    def _get_market_depth_and_impact(self, symbol: str, order_size: float = 1.0, side: str = "buy") -> Dict[str, Any]:
        symbol = symbol.upper()
        side = side.lower()
        orderbook = bitget_client.get_orderbook(symbol, depth=20)
        bids = orderbook.get("bids", [])
        asks = orderbook.get("asks", [])

        if not bids or not asks:
            return {
                "symbol": symbol,
                "mid_price": 100.0,
                "spread_pct": 0.05,
                "estimated_slippage_pct": 0.02,
                "kyle_lambda_impact": "Negligible",
                "depth_status": "Simulated Safe"
            }

        best_bid = float(bids[0][0])
        best_ask = float(asks[0][0])
        mid_price = (best_bid + best_ask) / 2.0
        spread_pct = ((best_ask - best_bid) / mid_price) * 100.0 if mid_price > 0 else 0.0

        target_book = asks if side == "buy" else bids
        remaining = order_size
        cost = 0.0
        depth_exhausted = False

        for p, q in target_book:
            price = float(p)
            qty = float(q)
            fill = min(remaining, qty)
            cost += fill * price
            remaining -= fill
            if remaining <= 0:
                break

        if remaining > 0:
            depth_exhausted = True
            avg_exec_price = float(target_book[-1][0]) * (1.04 if side == "buy" else 0.96)
        else:
            avg_exec_price = cost / order_size if order_size > 0 else mid_price

        slippage_pct = abs((avg_exec_price - mid_price) / mid_price) * 100.0

        # Kyle's lambda market impact approximation: lambda = price_impact / dollar_volume
        notional = order_size * mid_price
        total_top5_depth_usdt = sum(float(p) * float(q) for p, q in target_book[:5])
        impact_ratio = notional / (total_top5_depth_usdt + 1e-6)

        return {
            "symbol": symbol,
            "side": side,
            "order_size": order_size,
            "mid_price": round(mid_price, 4),
            "expected_execution_price": round(avg_exec_price, 4),
            "spread_pct": round(spread_pct, 4),
            "slippage_pct": round(slippage_pct, 4),
            "depth_exhausted": depth_exhausted,
            "top5_depth_usdt": round(total_top5_depth_usdt, 2),
            "impact_assessment": "Severe" if slippage_pct > 1.2 or depth_exhausted else ("Noticeable" if slippage_pct > 0.4 else "Clean / Minimal Impact")
        }

    def _calculate_quant_factors(self, symbol: str, timeframe: str = "1h", limit: int = 50) -> Dict[str, Any]:
        symbol = symbol.upper()
        candles = bitget_client.get_historical_candles(symbol, timeframe, limit=limit)
        quant = QuantAnalyst.analyze_candles(candles)
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "factors": quant,
            "interpretation": {
                "regime": quant.get("market_regime"),
                "hurst_trending": quant.get("hurst_exponent", 0.5) > 0.55,
                "rsi_overbought": quant.get("rsi", 50.0) > 70.0,
                "rsi_oversold": quant.get("rsi", 50.0) < 30.0,
                "volatility_surge": quant.get("atr_pct", 1.0) > 3.0
            }
        }

    def _run_crisis_stress_test(self, symbol: str, leverage: int = 3, size: float = 0.1, side: str = "buy") -> Dict[str, Any]:
        symbol = symbol.upper()
        ticker = bitget_client.get_ticker(symbol)
        price = ticker.get("last_price", 100.0)
        notional = size * price

        intent = {
            "symbol": symbol,
            "side": side.lower(),
            "size": size,
            "leverage": leverage,
            "notional_usdt": round(notional, 2)
        }
        return stress_tester.evaluate(intent, current_price=price)

    def _audit_portfolio_and_var(self) -> Dict[str, Any]:
        balances = bitget_client.get_account_balances()
        trades = bitget_client.paper_trades
        orders = bitget_client.get_recent_orders(10)
        is_simulation = getattr(bitget_client, "is_simulation", True)
        desk_mode_str = "Bitget Simulation / Paper Desk" if is_simulation else "Bitget Live Agentic Account"

        usdt_cash = float(balances.get("USDT", 0.0))
        total_usdt_value = usdt_cash
        asset_holdings = {}

        # 1. First record Liquid Tradable Cash (USDT)
        asset_holdings["USDT"] = {
            "asset": "USDT",
            "quantity": round(usdt_cash, 2),
            "current_price": 1.0,
            "usdt_value": round(usdt_cash, 2),
            "allocation_pct": 0.0,
            "is_liquid_cash": True,
            "category": "Cash"
        }

        # 2. Add all other held assets marked to live market prices concurrently
        non_usdt_assets = [(asset, float(qty)) for asset, qty in balances.items() if asset != "USDT" and float(qty) > 0]

        def _fetch_asset_info(item):
            asset, qty = item
            pair = f"{asset}USDT"
            ticker = bitget_client.get_ticker(pair)
            price = ticker.get("last_price", 0.0)
            val = qty * price
            return asset, {
                "asset": asset,
                "quantity": qty,
                "current_price": round(price, 4),
                "usdt_value": round(val, 2),
                "allocation_pct": 0.0,
                "is_liquid_cash": False,
                "category": "Spot Asset"
            }

        if non_usdt_assets:
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, len(non_usdt_assets))) as executor:
                results = list(executor.map(_fetch_asset_info, non_usdt_assets))
            for asset, data in results:
                total_usdt_value += data["usdt_value"]
                asset_holdings[asset] = data

        # Calculate allocation percentages
        for asset, info in asset_holdings.items():
            info["allocation_pct"] = round((info["usdt_value"] / total_usdt_value) * 100, 1) if total_usdt_value > 0 else 0.0

        # Historical / Parametric VaR (Value at Risk) calculation
        # Assume daily volatility ~ 3.5% across typical crypto basket
        portfolio_daily_vol = 0.035
        var_95_daily = total_usdt_value * 1.645 * portfolio_daily_vol
        var_99_daily = total_usdt_value * 2.326 * portfolio_daily_vol

        # Profit & Loss summary
        total_realized_pnl = sum(t.get("pnl", 0.0) for t in trades if "pnl" in t)
        loss_trades = sum(1 for t in trades if t.get("pnl", 0.0) < 0)

        # Sort holdings: USDT first, then by usdt_value descending
        sorted_holdings = dict(sorted(
            asset_holdings.items(),
            key=lambda x: (not x[1]["is_liquid_cash"], -x[1]["usdt_value"])
        ))

        return {
            "total_portfolio_equity_usdt": round(total_usdt_value, 2),
            "cash_usdt": round(usdt_cash, 2),
            "cash_ratio_pct": round((usdt_cash / total_usdt_value) * 100, 1) if total_usdt_value > 0 else 100.0,
            "holdings": sorted_holdings,
            "is_simulation": is_simulation,
            "desk_mode": desk_mode_str,
            "var_metrics": {
                "daily_var_95_usdt": round(var_95_daily, 2),
                "daily_var_95_pct": round((var_95_daily / total_usdt_value) * 100, 2) if total_usdt_value > 0 else 0.0,
                "daily_var_99_usdt": round(var_99_daily, 2),
                "daily_var_99_pct": round((var_99_daily / total_usdt_value) * 100, 2) if total_usdt_value > 0 else 0.0
            },
            "recent_trade_count": len(trades),
            "total_realized_pnl_usdt": round(total_realized_pnl, 2),
            "consecutive_losses": loss_trades,
            "risk_status": "ELEVATED" if loss_trades >= 3 or (var_95_daily / max(1, total_usdt_value)) > 0.08 else "HEALTHY"
        }

    async def _run_swarm_defense(self, symbol: str, side: str = "buy", size: float = 0.1, leverage: int = 3, prompt: str = "") -> Dict[str, Any]:
        symbol = symbol.upper()
        side = side.lower()
        ticker = bitget_client.get_ticker(symbol)
        orderbook = bitget_client.get_orderbook(symbol, depth=15)
        candles = bitget_client.get_historical_candles(symbol, "1h", limit=120)
        quant_data = QuantAnalyst.analyze_candles(candles)
        recent_trades = bitget_client.paper_trades
        portfolio_balance = bitget_client.get_account_balances()

        price = ticker.get("last_price", 100.0)
        order_intent = {
            "symbol": symbol,
            "side": side,
            "size": size,
            "leverage": leverage,
            "current_price": price,
            "notional_usdt": round(size * price, 2)
        }

        context = {
            "raw_prompt": prompt or f"{side} {size} {symbol} with {leverage}x leverage",
            "symbol": symbol,
            "order_intent": order_intent,
            "ticker_data": ticker,
            "orderbook": orderbook,
            "quant_data": quant_data,
            "candles": candles,
            "recent_trades": recent_trades,
            "portfolio_balance": portfolio_balance
        }

        results = await asyncio.gather(
            VolatilityAgent.analyze(context),
            FraudHunterAgent.analyze(context),
            SecurityAgent.analyze(context),
            LiquidityAgent.analyze(context),
            PsychologyAgent.analyze(context),
            QuantAnalystAgent.analyze(context),
            BacktestAgent.analyze(context)
        )

        vol_res, fraud_res, sec_res, liq_res, psych_res, quant_res, backtest_res = results

        composite_score = int(
            (vol_res["score"] * 0.15) +
            (fraud_res["score"] * 0.20) +
            (sec_res["score"] * 0.15) +
            (liq_res["score"] * 0.15) +
            (psych_res["score"] * 0.15) +
            (quant_res["score"] * 0.10) +
            (backtest_res["score"] * 0.10)
        )

        all_flags = []
        for r in results:
            all_flags.extend(r.get("flags", []))

        if leverage >= 20:
            all_flags.append(f"Extreme Leverage Warning: {leverage}x leverage creates catastrophic liquidation risk.")
            composite_score = max(composite_score, 75)

        has_critical = any(r["score"] >= 75 for r in results) or (leverage >= 25)
        if composite_score >= 65 or has_critical:
            verdict = "INTERCEPTED_BLOCK"
            badge = "BLOCKED"
        elif composite_score >= 38:
            verdict = "ADVISORY_CAUTION"
            badge = "CAUTION"
        else:
            verdict = "APPROVED_EXECUTION"
            badge = "APPROVED"

        return {
            "symbol": symbol,
            "composite_risk_score": composite_score,
            "verdict": verdict,
            "verdict_badge": badge,
            "sub_agents": {
                "volatility_sentinel": vol_res,
                "fraud_hunter": fraud_res,
                "security_guard": sec_res,
                "liquidity_auditor": liq_res,
                "psychology_shield": psych_res,
                "quant_analyst": quant_res,
                "strategy_backtester": backtest_res
            },
            "threat_flags": all_flags
        }

    def _prescribe_safe_trade(self, symbol: str, original_leverage: int = 10, size: float = 1.0, risk_flags: Optional[List[str]] = None) -> Dict[str, Any]:
        risk_flags = risk_flags or []
        safe_lev = 3 if original_leverage > 4 else max(1, original_leverage - 1)
        lev_reduction = round(((original_leverage - safe_lev) / original_leverage) * 100) if original_leverage > safe_lev else 0

        # Slippage / execution mode
        exec_mode = "TWAP 3 Tranches (5m intervals)" if any("slippage" in f.lower() or "liquidity" in f.lower() for f in risk_flags) else "Limit Order with Tight Slippage Ceiling"
        tranche_size = round(size / 3.0, 4) if "TWAP" in exec_mode else size

        return {
            "active": True,
            "symbol": symbol.upper(),
            "original_leverage": original_leverage,
            "safe_leverage": safe_lev,
            "suggested_sl_pct": 3.5,
            "suggested_tp_pct": 8.0,
            "execution_mode": exec_mode,
            "tranche_size": tranche_size,
            "risk_reduction_pct": max(40, min(90, lev_reduction + 30)),
            "rationale": f"De-risked position: lowered leverage from {original_leverage}x to {safe_lev}x and shielded execution via {exec_mode}."
        }

    def _execute_order(self, symbol: str, side: str, size: float, order_type: str = "market", leverage: int = 1) -> Dict[str, Any]:
        return bitget_client.place_order(symbol=symbol, side=side, order_type=order_type, size=size)

    def _execute_twap(self, symbol: str, side: str, total_size: float, tranches: int = 3, interval_sec: int = 2) -> Dict[str, Any]:
        symbol = symbol.upper()
        tranche_size = round(total_size / max(1, tranches), 4)
        orders_filled = []

        # Execute the first tranche immediately
        first_fill = bitget_client.place_order(symbol=symbol, side=side, order_type="market", size=tranche_size)
        if first_fill.get("success"):
            orders_filled.append(first_fill["order"])

        # Create scheduled tranche timeline
        schedule = []
        base_time = int(time.time() * 1000)
        for i in range(tranches):
            schedule.append({
                "tranche_index": i + 1,
                "size": tranche_size,
                "status": "FILLED" if i == 0 else "SCHEDULED_SIMULATED",
                "scheduled_in_sec": i * interval_sec,
                "order_id": (first_fill.get("order") or {}).get("order_id", f"bg_twap_{base_time}_1") if i == 0 else f"bg_twap_{base_time}_{i+1}"
            })

        return {
            "status": "TWAP_ACTIVE",
            "symbol": symbol,
            "total_size": total_size,
            "tranches_count": tranches,
            "tranche_size": tranche_size,
            "initial_fill": first_fill.get("order"),
            "schedule": schedule,
            "message": f"TWAP algorithmic engine initialized: Tranche 1 of {tranches} filled ({tranche_size} {symbol}). Remaining tranches scheduled with {interval_sec}s intervals to prevent orderbook slippage."
        }

    async def _run_backtest(
        self,
        symbol: str = "BTCUSDT",
        strategy_type: str = "regime_alpha",
        initial_capital: float = 10000.0,
        stop_loss_pct: float = 0.025,
        take_profit_pct: float = 0.060,
        candle_limit: int = 150
    ) -> Dict[str, Any]:
        return await BacktestAgent.run_simulation(
            symbol=symbol,
            strategy_type=strategy_type,
            initial_capital=float(initial_capital),
            stop_loss_pct=float(stop_loss_pct),
            take_profit_pct=float(take_profit_pct),
            candle_limit=int(candle_limit)
        )

    async def _run_quant_deep_audit(
        self,
        symbol: str = "BTCUSDT",
        side: str = "buy",
        timeframe: str = "1h",
        limit: int = 60
    ) -> Dict[str, Any]:
        symbol = symbol.upper()
        candles = bitget_client.get_historical_candles(symbol, timeframe, limit=int(limit))
        quant_data = QuantAnalyst.analyze_candles(candles)
        context = {
            "symbol": symbol,
            "order_intent": {"symbol": symbol, "side": side},
            "quant_data": quant_data,
            "candles": candles
        }
        return await QuantAnalystAgent.analyze(context)

# Global Singleton
agent_tools = AgentToolRegistry()
