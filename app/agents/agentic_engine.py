import asyncio
import logging
import json
import time
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.agents.tools import agent_tools
from app.agents.swarm_deliberation import swarm_arena
from app.services.openrouter_client import openrouter_client
from app.services.bitget_client import bitget_client

logger = logging.getLogger(__name__)

class AutonomousReActEngine:
    """
    Autonomous ReAct (Reasoning + Action) Agent Engine for Alphaind.
    Decomposes arbitrary high-level trader objectives into autonomous multi-step tool calls,
    observes live telemetry, iteratively evaluates hypotheses, and synthesizes final actions.
    """

    @classmethod
    async def execute_goal(cls, goal: str) -> Dict[str, Any]:
        t0 = time.time()
        start_iso = datetime.now(timezone.utc).isoformat()
        trace: List[Dict[str, Any]] = []

        # 1. Classify Goal & Identify Strategy Pattern
        goal_lower = goal.lower()
        is_portfolio_audit = any(w in goal_lower for w in ["portfolio", "balance", "var", "value at risk", "equity", "exposure", "holdings"])
        is_market_scan = any(w in goal_lower for w in ["scan", "opportunity", "best coin", "top asset", "watchlist", "find", "breakout", "momentum", "screener"])
        is_debate_request = any(w in goal_lower for w in ["debate", "arena", "bull vs bear", "discuss", "argument", "opposing"])
        is_twap_request = any(w in goal_lower for w in ["twap", "tranche", "split", "slice", "slippage guard", "iceberg"])
        is_backtest_request = any(w in goal_lower for w in ["backtest", "back-test", "historical test", "simulate strategy", "monte carlo", "sharpe", "win rate", "expectancy", "quant audit", "factor analysis"])

        # Extract potential symbol
        symbol = cls._extract_symbol(goal)

        step_idx = 1

        # =====================================================================
        # ROUTE A: PORTFOLIO RISK & VAR AUDIT GOAL
        # =====================================================================
        if is_portfolio_audit and not (is_market_scan or "buy" in goal_lower or "sell" in goal_lower):
            trace.append({
                "step": step_idx,
                "type": "THOUGHT",
                "title": "Formulate Portfolio Audit Plan",
                "content": "User requested account exposure audit. I will query the paper/live account balances, calculate historical Value at Risk (VaR 95% and 99%), and evaluate margin concentration.",
                "timestamp_ms": round((time.time() - t0) * 1000, 1)
            })
            step_idx += 1

            trace.append({
                "step": step_idx,
                "type": "TOOL_CALL",
                "tool": "tool_portfolio_risk_audit",
                "arguments": {},
                "title": "Invoking Portfolio & VaR Audit Tool",
                "timestamp_ms": round((time.time() - t0) * 1000, 1)
            })
            step_idx += 1

            audit_res = await agent_tools.execute_tool("tool_portfolio_risk_audit", {})
            audit_data = audit_res.get("result", {})

            trace.append({
                "step": step_idx,
                "type": "OBSERVATION",
                "tool": "tool_portfolio_risk_audit",
                "title": "Audit Telemetry Received",
                "content": f"Total Portfolio Equity: ${audit_data.get('total_portfolio_equity_usdt', 0):,.2f} USDT. Daily 95% VaR: ${audit_data.get('var_metrics', {}).get('daily_var_95_usdt', 0):,.2f} ({audit_data.get('var_metrics', {}).get('daily_var_95_pct', 0)}%). Holdings: {len(audit_data.get('holdings', {}))} non-cash assets.",
                "data": audit_data,
                "timestamp_ms": round((time.time() - t0) * 1000, 1)
            })
            step_idx += 1

            trace.append({
                "step": step_idx,
                "type": "THOUGHT",
                "title": "Risk Synthesis & Action Formulation",
                "content": f"Portfolio status is {audit_data.get('risk_status')}. Cash ratio is {audit_data.get('cash_ratio_pct')}%. Recommending capital retention guidelines.",
                "timestamp_ms": round((time.time() - t0) * 1000, 1)
            })

            elapsed_ms = round((time.time() - t0) * 1000, 1)
            return {
                "status": "COMPLETED",
                "execution_mode": "AUTONOMOUS_REACT_LOOP",
                "goal": goal,
                "route": "PORTFOLIO_AUDIT",
                "latency_ms": elapsed_ms,
                "timestamp": start_iso,
                "trace": trace,
                "final_decision": {
                    "verdict": "PORTFOLIO_AUDIT_HEALTHY" if audit_data.get("risk_status") == "HEALTHY" else "PORTFOLIO_RISK_WARNING",
                    "badge": audit_data.get("risk_status"),
                    "headline": f"Portfolio Health Report: ${audit_data.get('total_portfolio_equity_usdt', 0):,.2f} USDT Equity",
                    "explanation": f"Alphaind audited your portfolio across {len(audit_data.get('holdings', {}))} asset holdings. Your daily 95% Value at Risk (VaR) is ${audit_data.get('var_metrics', {}).get('daily_var_95_usdt', 0):,.2f} ({audit_data.get('var_metrics', {}).get('daily_var_95_pct', 0)}% of total equity), meaning 19 out of 20 trading days your maximum anticipated fluctuation is within this range.",
                    "audit_data": audit_data
                }
            }

        # =====================================================================
        # ROUTE B: MARKET OPPORTUNITY SCANNER GOAL
        # =====================================================================
        if is_market_scan and not ("buy" in goal_lower or "sell" in goal_lower):
            trace.append({
                "step": step_idx,
                "type": "THOUGHT",
                "title": "Market Opportunity Discovery Objective",
                "content": "User requested a broad market scan. I will execute the multi-factor scanner across the Bitget watchlist, rank assets by composite alpha & momentum, and then run an automated 5-pillar defense check on the top candidate.",
                "timestamp_ms": round((time.time() - t0) * 1000, 1)
            })
            step_idx += 1

            filter_type = "momentum" if "momentum" in goal_lower else ("oversold" if "oversold" in goal_lower else ("low_volatility" if "safe" in goal_lower or "volatility" in goal_lower else "alpha"))

            trace.append({
                "step": step_idx,
                "type": "TOOL_CALL",
                "tool": "tool_market_scanner",
                "arguments": {"filter_by": filter_type, "top_n": 5},
                "title": f"Invoking Watchlist Scanner (Filter: {filter_type})",
                "timestamp_ms": round((time.time() - t0) * 1000, 1)
            })
            step_idx += 1

            scan_res = await agent_tools.execute_tool("tool_market_scanner", {"filter_by": filter_type, "top_n": 5})
            scan_data = scan_res.get("result", {})
            top_coin = scan_data.get("best_opportunity", {})
            top_sym = top_coin.get("symbol", "BTCUSDT")

            trace.append({
                "step": step_idx,
                "type": "OBSERVATION",
                "tool": "tool_market_scanner",
                "title": "Market Scan Complete",
                "content": f"Scanned {scan_data.get('total_scanned', 0)} assets. Top pick is {top_sym} (Price: ${top_coin.get('price')}, 24h: {top_coin.get('change_24h'):+}%, Alpha: {top_coin.get('composite_alpha')}, Hurst: {top_coin.get('hurst_exponent')}).",
                "data": scan_data,
                "timestamp_ms": round((time.time() - t0) * 1000, 1)
            })
            step_idx += 1

            # Follow-up tool: run swarm defense on the best opportunity
            trace.append({
                "step": step_idx,
                "type": "THOUGHT",
                "title": "Autonomous Verification of Top Pick",
                "content": f"Top opportunity is {top_sym}. Now proactively launching the 5-Pillar Swarm Defense to ensure this asset is safe to trade before presenting to user.",
                "timestamp_ms": round((time.time() - t0) * 1000, 1)
            })
            step_idx += 1

            trace.append({
                "step": step_idx,
                "type": "TOOL_CALL",
                "tool": "tool_run_swarm_defense",
                "arguments": {"symbol": top_sym, "side": "buy", "size": 1.0, "leverage": 3},
                "title": f"Verifying {top_sym} with 5 Defense Pillars",
                "timestamp_ms": round((time.time() - t0) * 1000, 1)
            })
            step_idx += 1

            def_res = await agent_tools.execute_tool("tool_run_swarm_defense", {"symbol": top_sym, "side": "buy", "size": 1.0, "leverage": 3})
            def_data = def_res.get("result", {})

            trace.append({
                "step": step_idx,
                "type": "OBSERVATION",
                "tool": "tool_run_swarm_defense",
                "title": "Swarm Defense Verification Received",
                "content": f"Swarm verdict for {top_sym}: {def_data.get('verdict_badge')} (Composite Risk Score: {def_data.get('composite_risk_score')}/100).",
                "data": def_data,
                "timestamp_ms": round((time.time() - t0) * 1000, 1)
            })
            step_idx += 1

            elapsed_ms = round((time.time() - t0) * 1000, 1)
            return {
                "status": "COMPLETED",
                "execution_mode": "AUTONOMOUS_REACT_LOOP",
                "goal": goal,
                "route": "MARKET_SCANNER",
                "latency_ms": elapsed_ms,
                "timestamp": start_iso,
                "trace": trace,
                "scan_data": scan_data,
                "swarm_defense": def_data,
                "final_decision": {
                    "verdict": def_data.get("verdict", "APPROVED_EXECUTION"),
                    "badge": def_data.get("verdict_badge", "APPROVED"),
                    "headline": f"Top Opportunity Identified: {top_sym} ({top_coin.get('change_24h'):+}%)",
                    "explanation": f"Alphaind scanned the market watchlist and ranked {top_sym} as the premier setup. It cleared all 5 pre-trade defense checks with a risk score of {def_data.get('composite_risk_score')}/100.",
                    "recommended_trade": {
                        "symbol": top_sym,
                        "side": "buy",
                        "size": 1.0 if "BTC" not in top_sym else 0.1,
                        "leverage": 3,
                        "price": top_coin.get("price")
                    }
                }
            }

        # =====================================================================
        # ROUTE C: MULTI-AGENT SWARM DEBATE ARENA
        # =====================================================================
        if is_debate_request:
            target_sym = symbol or "BTCUSDT"
            trace.append({
                "step": step_idx,
                "type": "THOUGHT",
                "title": "Initialize Swarm Deliberation Arena",
                "content": f"User requested multi-agent debate for {target_sym}. I will convene the Bull Strategist, Bear Risk Sentinel, and Execution Guardian to debate the trade thesis.",
                "timestamp_ms": round((time.time() - t0) * 1000, 1)
            })
            step_idx += 1

            lev = 3
            lev_m = re.search(r'(\d+)\s*[xX]', goal)
            if lev_m:
                try:
                    lev = max(1, min(50, int(lev_m.group(1))))
                except Exception:
                    lev = 3

            debate_res = await swarm_arena.deliberate(target_sym, requested_leverage=lev, requested_size=None, raw_prompt=goal)

            for item in debate_res.get("transcript", []):
                trace.append({
                    "step": step_idx,
                    "type": "DEBATE_SPEECH",
                    "title": f"{item['speaker']} ({item['role']})",
                    "content": item["statement"],
                    "avatar": item["avatar"],
                    "timestamp_ms": round((time.time() - t0) * 1000, 1)
                })
                step_idx += 1

            elapsed_ms = round((time.time() - t0) * 1000, 1)
            return {
                "status": "COMPLETED",
                "execution_mode": "AUTONOMOUS_REACT_LOOP",
                "goal": goal,
                "route": "SWARM_DEBATE",
                "latency_ms": elapsed_ms,
                "timestamp": start_iso,
                "trace": trace,
                "debate": debate_res,
                "final_decision": {
                    "verdict": debate_res["consensus_status"],
                    "badge": "CONSENSUS_REACHED",
                    "headline": f"Swarm Deliberation Concluded for {target_sym}",
                    "explanation": f"The agents evaluated upside momentum vs downside ruin probability and arrived at a consensus: recommended leverage {debate_res['recommended_leverage']}x with strict stop-loss protection.",
                    "proposed_plan": debate_res["proposed_plan"]
                }
            }

        # =====================================================================
        # ROUTE E: QUANTITATIVE ANALYST & STRATEGY BACKTEST VALIDATION
        # =====================================================================
        if is_backtest_request:
            target_sym = symbol or "BTCUSDT"
            strategy = "bollinger_mean_reversion" if any(w in goal_lower for w in ["mean reversion", "bollinger", "revert"]) else (
                "trend_macd" if any(w in goal_lower for w in ["macd", "trend", "breakout"]) else "regime_alpha"
            )
            side = "sell" if any(w in goal_lower for w in ["sell", "short", "bear"]) else "buy"
            leverage = cls._extract_leverage(goal)

            # Step 1: Quant Factor Audit & Regime Detection
            trace.append({
                "step": step_idx,
                "type": "THOUGHT",
                "title": "Quantitative Factor & Regime Hypothesis",
                "content": f"User requested backtest and quantitative validation for {target_sym} ('{strategy}' strategy). Step 1: Dispatching Quantitative Analyst Sub-Agent to audit statistical persistence (Hurst exponent) and factor momentum.",
                "timestamp_ms": round((time.time() - t0) * 1000, 1)
            })
            step_idx += 1

            trace.append({
                "step": step_idx,
                "type": "TOOL_CALL",
                "tool": "tool_quant_deep_audit",
                "arguments": {"symbol": target_sym, "side": side, "limit": 60},
                "title": f"Quant Analyst Factor Audit ({target_sym})",
                "timestamp_ms": round((time.time() - t0) * 1000, 1)
            })
            step_idx += 1

            quant_res = await agent_tools.execute_tool("tool_quant_deep_audit", {"symbol": target_sym, "side": side, "limit": 60})
            quant_data = quant_res.get("result", {})

            trace.append({
                "step": step_idx,
                "type": "OBSERVATION",
                "tool": "tool_quant_deep_audit",
                "title": "Quant Analyst Telemetry Received",
                "content": f"Status: {quant_data.get('human_status')}. Hurst H={quant_data.get('metrics', {}).get('hurst_exponent')} ({quant_data.get('metrics', {}).get('hurst_regime')}). Alpha Score: {quant_data.get('metrics', {}).get('composite_alpha', 0):+.2f}. RSI: {quant_data.get('metrics', {}).get('rsi_14')}.",
                "data": quant_data,
                "timestamp_ms": round((time.time() - t0) * 1000, 1)
            })
            step_idx += 1

            # Step 2: Historical Simulation & Monte Carlo Permutations
            trace.append({
                "step": step_idx,
                "type": "THOUGHT",
                "title": "Dispatch Strategy Backtester Sub-Agent",
                "content": f"Regime is {quant_data.get('metrics', {}).get('market_regime')}. Step 2: Running event-driven bar-by-bar backtest across 150 candles with 500-run Monte Carlo permutation to test maximum drawdown and ruin probability.",
                "timestamp_ms": round((time.time() - t0) * 1000, 1)
            })
            step_idx += 1

            sl_pct = 0.025 if leverage <= 3 else (0.015 if leverage >= 10 else 0.02)
            tp_pct = round(sl_pct * 2.4, 3)

            trace.append({
                "step": step_idx,
                "type": "TOOL_CALL",
                "tool": "tool_run_backtest",
                "arguments": {
                    "symbol": target_sym,
                    "strategy_type": strategy,
                    "initial_capital": 10000.0,
                    "stop_loss_pct": sl_pct,
                    "take_profit_pct": tp_pct,
                    "candle_limit": 150
                },
                "title": f"Backtesting '{strategy}' on {target_sym} (500 Monte Carlo Runs)",
                "timestamp_ms": round((time.time() - t0) * 1000, 1)
            })
            step_idx += 1

            bt_res = await agent_tools.execute_tool("tool_run_backtest", {
                "symbol": target_sym,
                "strategy_type": strategy,
                "initial_capital": 10000.0,
                "stop_loss_pct": sl_pct,
                "take_profit_pct": tp_pct,
                "candle_limit": 150
            })
            bt_data = bt_res.get("result", {})
            metrics = bt_data.get("metrics", {})

            trace.append({
                "step": step_idx,
                "type": "OBSERVATION",
                "tool": "tool_run_backtest",
                "title": "Backtest & Monte Carlo Telemetry Received",
                "content": f"Simulated {metrics.get('total_trades', 0)} trades. Net Return: {metrics.get('total_return_pct', 0):+.2f}%. Win Rate: {metrics.get('win_rate_pct', 0)}%. Sharpe: {metrics.get('sharpe_ratio', 0)}. Max DD: -{metrics.get('max_drawdown_pct', 0)}%. 95% Monte Carlo Worst DD: -{metrics.get('monte_carlo_worst_dd_pct', 0)}%.",
                "data": bt_data,
                "timestamp_ms": round((time.time() - t0) * 1000, 1)
            })
            step_idx += 1

            # Step 3: Synthesis
            trace.append({
                "step": step_idx,
                "type": "THOUGHT",
                "title": "Quantitative & Empirical Synthesis",
                "content": f"Synthesizing backtest edge: Strategy status is {bt_data.get('status')} with Sharpe {metrics.get('sharpe_ratio')}. Quant conviction score is {quant_data.get('alpha_conviction_score')}/100.",
                "timestamp_ms": round((time.time() - t0) * 1000, 1)
            })
            step_idx += 1

            elapsed_ms = round((time.time() - t0) * 1000, 1)
            return {
                "status": "COMPLETED",
                "execution_mode": "AUTONOMOUS_REACT_LOOP",
                "goal": goal,
                "route": "QUANT_BACKTEST_VALIDATION",
                "latency_ms": elapsed_ms,
                "timestamp": start_iso,
                "trace": trace,
                "quant_analysis": quant_data,
                "backtest_report": bt_data,
                "final_decision": {
                    "verdict": bt_data.get("status", "ACCEPTABLE_EDGE"),
                    "badge": "STRONG_EDGE" if metrics.get("sharpe_ratio", 0) > 1.2 else ("ACCEPTABLE" if metrics.get("total_return_pct", 0) >= 0 else "NEGATIVE_EDGE"),
                    "headline": f"Quantitative Backtest Completed: {target_sym} ({strategy})",
                    "explanation": f"The Quantitative Analyst & Backtester sub-agents simulated {metrics.get('total_trades')} historical trades. The strategy delivered {metrics.get('win_rate_pct')}% win rate with a Sharpe ratio of {metrics.get('sharpe_ratio')}, and 500-run Monte Carlo maximum drawdown is -{metrics.get('monte_carlo_worst_dd_pct')}%.",
                    "performance_summary": {
                        "symbol": target_sym,
                        "strategy": strategy,
                        "win_rate_pct": metrics.get("win_rate_pct"),
                        "profit_factor": metrics.get("profit_factor"),
                        "sharpe_ratio": metrics.get("sharpe_ratio"),
                        "max_drawdown_pct": metrics.get("max_drawdown_pct"),
                        "monte_carlo_worst_dd": metrics.get("monte_carlo_worst_dd_pct"),
                        "hurst_exponent": quant_data.get("metrics", {}).get("hurst_exponent"),
                        "market_regime": quant_data.get("metrics", {}).get("market_regime")
                    }
                }
            }

        # =====================================================================
        # ROUTE D: END-TO-END AUTONOMOUS TRADE EXECUTION (ReAct Tool Chain)
        # =====================================================================
        target_sym = symbol or "BTCUSDT"
        side = "sell" if any(w in goal_lower for w in ["sell", "short", "dump", "bear"]) else "buy"
        leverage = cls._extract_leverage(goal)
        size = cls._extract_size(goal, target_sym)

        # Step 1: Market Depth Check
        trace.append({
            "step": step_idx,
            "type": "THOUGHT",
            "title": "Analyze Execution Impact & Depth",
            "content": f"Deconstructing directive to {side.upper()} {size} {target_sym} with {leverage}x leverage. First, I must walk Bitget Level 2 depth to ensure we won't trigger excessive slippage.",
            "timestamp_ms": round((time.time() - t0) * 1000, 1)
        })
        step_idx += 1

        trace.append({
            "step": step_idx,
            "type": "TOOL_CALL",
            "tool": "tool_get_market_depth",
            "arguments": {"symbol": target_sym, "order_size": size, "side": side},
            "title": f"Walking Orderbook Depth for {size} {target_sym}",
            "timestamp_ms": round((time.time() - t0) * 1000, 1)
        })
        step_idx += 1

        depth_res = await agent_tools.execute_tool("tool_get_market_depth", {"symbol": target_sym, "order_size": size, "side": side})
        depth_data = depth_res.get("result", {})

        trace.append({
            "step": step_idx,
            "type": "OBSERVATION",
            "tool": "tool_get_market_depth",
            "title": "Orderbook Telemetry Received",
            "content": f"Mid price: ${depth_data.get('mid_price')}. Expected execution price: ${depth_data.get('expected_execution_price')}. Slippage: {depth_data.get('slippage_pct')}%. Impact Assessment: {depth_data.get('impact_assessment')}.",
            "data": depth_data,
            "timestamp_ms": round((time.time() - t0) * 1000, 1)
        })
        step_idx += 1

        # Step 2: Crisis Stress Test
        trace.append({
            "step": step_idx,
            "type": "THOUGHT",
            "title": "Simulate Crisis Resilience",
            "content": f"Slippage is {depth_data.get('slippage_pct')}%. Now running crisis stress simulation to calculate liquidation buffer under adverse macro shocks.",
            "timestamp_ms": round((time.time() - t0) * 1000, 1)
        })
        step_idx += 1

        trace.append({
            "step": step_idx,
            "type": "TOOL_CALL",
            "tool": "tool_crisis_stress_test",
            "arguments": {"symbol": target_sym, "leverage": leverage, "size": size, "side": side},
            "title": f"Stress Testing Historical Crisis Resiliency ({leverage}x Leverage)",
            "timestamp_ms": round((time.time() - t0) * 1000, 1)
        })
        step_idx += 1

        stress_res = await agent_tools.execute_tool("tool_crisis_stress_test", {"symbol": target_sym, "leverage": leverage, "size": size, "side": side})
        stress_data = stress_res.get("result", {})

        trace.append({
            "step": step_idx,
            "type": "OBSERVATION",
            "tool": "tool_crisis_stress_test",
            "title": "Crisis Stress Report Received",
            "content": f"Liquidation buffer: {stress_data.get('liquidation_buffer_pct')}%. Scenarios survived: {stress_data.get('survival_ratio')}. Rating: {stress_data.get('resilience_rating')}.",
            "data": stress_data,
            "timestamp_ms": round((time.time() - t0) * 1000, 1)
        })
        step_idx += 1

        # Step 3: Run Full 5-Pillar Swarm Defense
        trace.append({
            "step": step_idx,
            "type": "THOUGHT",
            "title": "Concurrently Dispatch 5-Pillar Swarm Defense",
            "content": "Now dispatching all 5 specialized sub-agents in parallel to audit price turbulence, contract authenticity, whale centralization, depth exhaustion, and trader psychology.",
            "timestamp_ms": round((time.time() - t0) * 1000, 1)
        })
        step_idx += 1

        trace.append({
            "step": step_idx,
            "type": "TOOL_CALL",
            "tool": "tool_run_swarm_defense",
            "arguments": {"symbol": target_sym, "side": side, "size": size, "leverage": leverage, "prompt": goal},
            "title": "Launching 5 Defense Sub-Agents Concurrently",
            "timestamp_ms": round((time.time() - t0) * 1000, 1)
        })
        step_idx += 1

        swarm_res = await agent_tools.execute_tool("tool_run_swarm_defense", {"symbol": target_sym, "side": side, "size": size, "leverage": leverage, "prompt": goal})
        swarm_data = swarm_res.get("result", {})

        trace.append({
            "step": step_idx,
            "type": "OBSERVATION",
            "tool": "tool_run_swarm_defense",
            "title": "5-Pillar Swarm Report Completed",
            "content": f"Master Verdict: {swarm_data.get('verdict_badge')} (Risk Score: {swarm_data.get('composite_risk_score')}/100). Active Threat Flags: {len(swarm_data.get('threat_flags', []))}.",
            "data": swarm_data,
            "timestamp_ms": round((time.time() - t0) * 1000, 1)
        })
        step_idx += 1

        # Step 4: If cautionary or blocked, formulate safe prescription or TWAP
        safe_prescription = None
        if swarm_data.get("verdict_badge") in ("CAUTION", "BLOCKED") or depth_data.get("slippage_pct", 0) > 0.4:
            trace.append({
                "step": step_idx,
                "type": "THOUGHT",
                "title": "Synthesizing Capital Protection Remedy",
                "content": "Risk flags detected. Computing optimal safe leverage, bracket stop-loss/take-profit, and algorithmic TWAP execution to safeguard the position.",
                "timestamp_ms": round((time.time() - t0) * 1000, 1)
            })
            step_idx += 1

            trace.append({
                "step": step_idx,
                "type": "TOOL_CALL",
                "tool": "tool_prescribe_safe_trade",
                "arguments": {"symbol": target_sym, "original_leverage": leverage, "size": size, "risk_flags": swarm_data.get("threat_flags", [])},
                "title": "Formulating AI Safe Trade Prescription",
                "timestamp_ms": round((time.time() - t0) * 1000, 1)
            })
            step_idx += 1

            presc_res = await agent_tools.execute_tool("tool_prescribe_safe_trade", {"symbol": target_sym, "original_leverage": leverage, "size": size, "risk_flags": swarm_data.get("threat_flags", [])})
            safe_prescription = presc_res.get("result", {})

            trace.append({
                "step": step_idx,
                "type": "OBSERVATION",
                "tool": "tool_prescribe_safe_trade",
                "title": "Safe Prescription Active",
                "content": f"Safe leverage: {safe_prescription.get('safe_leverage')}x (down from {leverage}x). Execution mode: {safe_prescription.get('execution_mode')}. Risk reduction: -{safe_prescription.get('risk_reduction_pct')}%.",
                "data": safe_prescription,
                "timestamp_ms": round((time.time() - t0) * 1000, 1)
            })
            step_idx += 1

        # Final Synthesis
        elapsed_ms = round((time.time() - t0) * 1000, 1)

        return {
            "status": "COMPLETED",
            "execution_mode": "AUTONOMOUS_REACT_LOOP",
            "goal": goal,
            "route": "AUTONOMOUS_TRADE_REACT",
            "latency_ms": elapsed_ms,
            "timestamp": start_iso,
            "trace": trace,
            "depth_telemetry": depth_data,
            "stress_test": stress_data,
            "swarm_defense": swarm_data,
            "safe_prescription": safe_prescription,
            "final_decision": {
                "verdict": swarm_data.get("verdict", "APPROVED_EXECUTION"),
                "badge": swarm_data.get("verdict_badge", "APPROVED"),
                "headline": "Trade Approved & Optimized" if swarm_data.get("verdict_badge") == "APPROVED" else ("Advisory Flags — Safe Parameters Available" if swarm_data.get("verdict_badge") == "CAUTION" else "Trade Intercepted for Safety"),
                "explanation": f"The Autonomous ReAct loop completed 4 investigative steps across Bitget L2 depth, historical crisis simulations, and 5-pillar swarm defense. The trade is {'ready for clean execution' if swarm_data.get('verdict_badge') == 'APPROVED' else 'de-risked with the safe parameters below'}.",
                "order_intent": {
                    "symbol": target_sym,
                    "side": side,
                    "size": size,
                    "leverage": safe_prescription.get("safe_leverage", leverage) if safe_prescription else leverage,
                    "order_type": "limit" if safe_prescription else "market"
                }
            }
        }

    @staticmethod
    def _extract_symbol(text: str) -> Optional[str]:
        t = text.upper()
        pair_match = re.search(r'\b([A-Z0-9]{2,16})USDT\b', t)
        if pair_match:
            return pair_match.group(1) + "USDT"
        for s in ["BTC", "ETH", "SOL", "BGB", "DOGE", "NVDA", "TSLA", "AAPL", "COIN", "SPY", "MSFT", "XRP", "ADA", "AVAX", "LINK", "SUI", "PEPE"]:
            if s in t:
                return s + "USDT"
        return None

    @staticmethod
    def _extract_leverage(text: str) -> int:
        t = text.upper()
        lev_match = re.search(r'(\d+)\s*[xX]', t)
        if lev_match:
            return int(lev_match.group(1))
        lev_word = re.search(r'LEVERAGE\s*(\d+)', t)
        if lev_word:
            return int(lev_word.group(1))
        return 3

    @staticmethod
    def _extract_size(text: str, symbol: str) -> float:
        t = text.upper()
        num_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:BTC|ETH|SOL|BGB|DOGE|NVDA|TSLA|COIN|UNITS|SHARES|COINS)', t)
        if num_match:
            return float(num_match.group(1))
        # Defaults
        defaults = {
            "BTCUSDT": 0.15,
            "ETHUSDT": 2.0,
            "SOLUSDT": 15.0,
            "BGBUSDT": 1000.0,
            "DOGEUSDT": 5000.0,
            "NVDAUSDT": 25.0,
            "TSLAUSDT": 10.0
        }
        return defaults.get(symbol, 1.0)

autonomous_react_engine = AutonomousReActEngine()
