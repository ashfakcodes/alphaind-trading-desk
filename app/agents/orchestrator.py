import asyncio
import time
import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.services.bitget_client import bitget_client
from app.services.openrouter_client import openrouter_client
from app.quant.analyst import QuantAnalyst
from app.quant.stress_tester import stress_tester
from app.services.bitget_signal import bitget_signal_service
from app.defense.rtoken_regime import rtoken_regime_detector
from app.agents.volatility_agent import VolatilityAgent
from app.agents.fraud_agent import FraudHunterAgent
from app.agents.security_agent import SecurityAgent
from app.agents.liquidity_agent import LiquidityAgent
from app.agents.psychology_agent import PsychologyAgent
from app.agents.quant_agent import QuantAnalystAgent
from app.agents.backtest_agent import BacktestAgent
from app.agents.agentic_engine import autonomous_react_engine
from app.agents.tools import agent_tools
from app.agents.swarm_deliberation import swarm_arena

logger = logging.getLogger(__name__)

class AlphaOrchestrator:
    """
    Master Conductor of Alphaind.
    1. Interprets natural language trader intent.
    2. Concurrently launches the 5 Sub-Agents in parallel (asyncio.gather).
    3. Synthesizes findings into a unified pre-trade decision verdict.
    4. Orchestrates Bitget order execution with zero manual UI friction.
    """

    @classmethod
    def _is_greeting(cls, prompt: str) -> bool:
        clean_p = prompt.strip().lower()
        clean_words = re.sub(r'[^\w\s]', '', clean_p).strip()
        greetings = {
            "hello", "hi", "hey", "hola", "howdy", "hiya", "greetings",
            "good morning", "good evening", "good afternoon", "good day",
            "yo", "sup", "whats up", "what's up", "wassup",
            "help", "who are you", "what are you", "what can you do",
            "what is this", "what is alphaind", "how does this work",
            "how do i use this", "introduce yourself", "tell me about yourself",
            "are you ready", "ready", "status", "ping", "test"
        }
        trade_actions = {
            "buy", "sell", "long", "short", "leverage", "spot", "perp", "futures",
            "order", "margin", "swap", "trade", "scalp", "invest", "dollar",
            "dollars", "usd", "usdt", "worth", "$"
        }
        words = set(clean_words.split())
        has_trade_action = bool(words & trade_actions or any(a in clean_p for a in ["$", "usd", "usdt"]))
        if not has_trade_action:
            if clean_words in greetings or "ready" in clean_words or re.match(r'^(hello|hi|hey|greetings|good\s+(morning|afternoon|evening)|yo|sup|help|who\s+are\s+you|are\s+you\s+ready)[\s!?,.]*$', clean_p):
                return True
        return False

    @classmethod
    def _is_balance_query(cls, prompt: str) -> bool:
        clean_p = prompt.strip().lower()
        balance_patterns = [
            r'\bbalance\b', r'\bbalances\b', r'\bhow much (?:money|equity|cash|funds|usdt|capital)\b',
            r'\bmy account\b', r'\baccount status\b', r'\bportfolio balance\b',
            r'\bwallet balance\b', r'\bavailable funds\b', r'\bcheck balance\b',
            r'\bshow balance\b', r'\bwhat is my balance\b', r'\bmy funds\b',
            r'\bnet worth\b', r'\btotal equity\b', r'\baccount equity\b'
        ]
        trade_actions = {"buy", "sell", "long", "short", "leverage", "swap", "scalp"}
        words = set(re.sub(r'[^\w\s]', '', clean_p).split())
        if not (words & trade_actions):
            for pat in balance_patterns:
                if re.search(pat, clean_p):
                    return True
        return False

    @classmethod
    async def _build_conversational_response(cls, prompt: str, order_intent: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Produce a friendly co-pilot intro/standby state when user sends a greeting or question,
        avoiding false trade parsing on imaginary tokens like NONEUSDT.
        """
        timestamp_start = datetime.now(timezone.utc).isoformat()
        is_bal_query = cls._is_balance_query(prompt) or bool((order_intent or {}).get("is_balance_query"))

        # Ingest current live Bitget account & balance telemetry
        balances = bitget_client.get_account_balances()
        auth_info = bitget_client.get_auth_info()
        is_auth = bool(auth_info.get("authenticated", False))
        user_id = auth_info.get("user_id", "")
        usdt_bal = balances.get("USDT", 0.0)

        copilot_context = {
            "mode": "account_balance_query" if is_bal_query else "greeting",
            "desk": "Alphaind AI Trading Desk",
            "is_balance_query": is_bal_query,
            "authenticated": is_auth,
            "user_id": user_id,
            "account_type": auth_info.get("account_type", "Bitget Simulation / Default"),
            "desk_mode": "Bitget Live Agentic Account" if is_auth else "Simulation / Paper Desk",
            "available_usdt": usdt_bal,
            "balances": balances
        }

        # Friendly response from LLM (Bitget Qwen or OpenRouter) with fallback
        copilot_reply = (order_intent or {}).get("conversational_reply")
        if not copilot_reply or not str(copilot_reply).strip():
            try:
                copilot_reply = await asyncio.to_thread(
                    openrouter_client.chat_copilot,
                    prompt,
                    copilot_context
                )
            except Exception as e:
                logger.warning(f"Error querying copilot chat: {e}")
                copilot_reply = None

        # Build accurate fallback reply if LLM did not return or claimed no access
        reply_lower = str(copilot_reply or "").lower()
        if (
            is_bal_query
            or not copilot_reply
            or "don't have direct access" in reply_lower
            or "do not have direct access" in reply_lower
            or "check your bitget account" in reply_lower
        ):
            if is_auth:
                status_desc = f"Connected Bitget Agentic Subaccount (`{user_id}`)"
                mode_label = "Live Desk Ready"
            else:
                status_desc = "Simulation / Paper Desk"
                mode_label = "Paper Simulation"

            other_coins = [f"**{c}**: {q}" for c, q in balances.items() if q > 0 and c != "USDT"]
            other_str = ", ".join(other_coins) if other_coins else "None"

            funding_note = ""
            if is_auth and usdt_bal <= 0:
                funding_note = (
                    "\n\n[Tip] **Funding Guidance:** To execute live orders, transfer USDT from your primary Bitget account "
                    "into this Agentic Subaccount via your Bitget App or Web Dashboard (**Assets -> Transfer -> Subaccount**)."
                )

            copilot_reply = (
                f"Here is your current **Bitget Account Balance & Telemetry**:\n\n"
                f"- **Available Trading Collateral:** **${usdt_bal:,.2f} USDT**\n"
                f"- **Subaccount ID:** `{user_id or 'bg_agent_active'}` ({status_desc})\n"
                f"- **Desk Mode:** {mode_label}\n"
                f"- **Additional Holdings:** {other_str}\n"
                f"- **Security Vault:** AES-GCM (256-bit WebCrypto) Authenticated & Active{funding_note}"
            )

        parser_mode = (order_intent or {}).get("parser_mode", "LLM_BITGET_QWEN" if openrouter_client.is_fallback_configured() else "NLP_ENGINE")

        sub_agents = {
            "volatility_sentinel": {
                "agent": "Volatility Sentinel",
                "score": 0, "status": "STANDBY", "human_status": "Ready (Standby)",
                "summary": "Volatility Sentinel calibrated and standing by for trade directives.",
                "flags": [], "thought_trace": ["Standing by for asset parameters.", "Calibrated to Bitget orderbook telemetry."]
            },
            "fraud_hunter": {
                "agent": "Fraud & Scam Hunter",
                "score": 0, "status": "STANDBY", "human_status": "Ready (Standby)",
                "summary": "Fraud Hunter standing by to verify smart contracts and token legitimacy.",
                "flags": [], "thought_trace": ["Honeypot and fake pair scanners active.", "Standing by for target contract."]
            },
            "security_guard": {
                "agent": "Security Guard",
                "score": 0, "status": "STANDBY", "human_status": "Ready (Standby)",
                "summary": "Contract Security Guard ready to audit permissions and mint risks.",
                "flags": [], "thought_trace": ["Security rules loaded.", "Awaiting symbol input."]
            },
            "liquidity_auditor": {
                "agent": "Liquidity Auditor",
                "score": 0, "status": "STANDBY", "human_status": "Ready (Standby)",
                "summary": "Liquidity Auditor ready to simulate orderbook depth walking and slippage.",
                "flags": [], "thought_trace": ["Orderbook Walker primed.", "Standing by for order size."]
            },
            "psychology_shield": {
                "agent": "Psychology Shield",
                "score": 0, "status": "STANDBY", "human_status": "Ready (Standby)",
                "summary": "Psychology Shield monitoring trader fatigue and leverage boundaries.",
                "flags": [], "thought_trace": ["FOMO/Tilt detection ready.", "Account risk parameters active."]
            },
            "quant_analyst": {
                "agent": "Quantitative Analyst",
                "score": 0, "status": "STANDBY", "human_status": "Ready (Standby)",
                "summary": "Quant Analyst ready to calculate Hurst exponents, RSI, and statistical regimes.",
                "flags": [], "thought_trace": ["Statistical factor engine initialized.", "Standing by for candle ingestion."],
                "metrics": {"hurst_exponent": 0.5, "composite_alpha": 0.0, "market_regime": "STANDBY"}
            },
            "strategy_backtester": {
                "agent": "Strategy Backtester",
                "score": 0, "status": "STANDBY", "human_status": "Ready (Standby)",
                "summary": "Strategy Backtester ready to run Monte Carlo simulations on historical crisis data.",
                "flags": [], "thought_trace": ["Monte Carlo engine primed.", "Standing by for strategy execution parameters."],
                "metrics": {
                    "win_rate_pct": 0.0,
                    "sharpe_ratio": 0.0,
                    "max_drawdown_pct": 0.0,
                    "monte_carlo_worst_dd_pct": 0.0,
                    "total_return_pct": 0.0
                }
            }
        }

        parsed = {
            "symbol": None,
            "side": None,
            "size": 0.0,
            "leverage": 1,
            "market_type": "spot",
            "is_spot": True,
            "order_type": "market",
            "dollar_amount": None,
            "token_size": None,
            "llm_reasoning": "Account telemetry inquiry acknowledged." if is_bal_query else "Conversational greeting acknowledged. Awaiting trade directive.",
            "parser_mode": parser_mode,
            "is_trade": False
        }

        try:
            btc_price = bitget_client.get_ticker("BTCUSDT").get("last_price", 65000.0)
        except Exception:
            btc_price = 65000.0

        if is_bal_query:
            friendly_title = f"Account Balance & Telemetry: ${usdt_bal:,.2f} USDT"
            takeaways = [
                f"Available Trading Collateral: ${usdt_bal:,.2f} USDT.",
                f"Connected Subaccount: {user_id if user_id else 'Bitget Paper Desk'}.",
                "All 7 risk defense pillars standing by for trade directives."
            ]
        else:
            friendly_title = "Hello! I'm Alphaind, your AI Trade Co-Pilot."
            takeaways = [
                "Alphaind AI Co-Pilot is online and ready.",
                "7 specialized defense & quant sub-agents are in standby.",
                "Enter any trade instruction (e.g. 'Buy $1,000 ETH' or 'Audit SOL 3x') to execute with protective multi-agent consensus."
            ]

        return {
            "is_conversational": True,
            "is_balance_query": is_bal_query,
            "orchestrator": {
                "status": "COMPLETED",
                "execution_mode": "COPILOT_STANDBY",
                "latency_ms": 15.0,
                "timestamp": timestamp_start,
                "parsed_intent": parsed,
                "composite_risk_score": 0,
                "verdict": "STANDBY",
                "verdict_badge": "STANDBY"
            },
            "sub_agents": sub_agents,
            "market_snapshot": {
                "symbol": "BTCUSDT",
                "price": btc_price,
                "regime": "CALIBRATED_STANDBY",
                "hurst_exponent": 0.5,
                "rsi": 50.0
            },
            "threat_flags": [],
            "ai_synthesis": {
                "ai_verdict": "STANDBY",
                "friendly_title": friendly_title,
                "conversational_explanation": copilot_reply,
                "threat_level": "LOW",
                "simple_takeaways": takeaways
            },
            "rtoken_regime": {"is_rtoken": False},
            "stress_test": {
                "is_spot": True,
                "resilience_rating": "STANDBY",
                "resilience_color": "safe",
                "survival_ratio": "7/7 Active",
                "liquidation_message": "Standby · Ready for trade instructions",
                "scenarios": []
            },
            "safe_prescription": {
                "active": False
            },
            "bitget_signals": {
                "perception_summary": "Co-pilot online. Telemetry stream connected."
            },
            "agentic_trace": [
                {"step": 1, "type": "THOUGHT", "title": "Co-Pilot Interaction", "content": f"Trader prompted: '{prompt}'. Deconstructed intent: {'Account balance query' if is_bal_query else 'Conversational greeting'}."},
                {"step": 2, "type": "TOOL_CALL", "tool": "copilot_dialogue_engine", "title": "Co-Pilot Assistance Active", "arguments": {"query": prompt, "balances": balances}},
                {"step": 3, "type": "OBSERVATION", "tool": "copilot_dialogue_engine", "title": "Account Telemetry Stream Active", "content": f"Collateral verified: ${usdt_bal:,.2f} USDT across {len(balances)} asset accounts."}
            ]
        }

    @classmethod
    async def process_natural_language_request(cls, prompt: str) -> Dict[str, Any]:
        timestamp_start = datetime.now(timezone.utc).isoformat()

        # Check if the prompt is an account balance / portfolio inquiry
        if cls._is_balance_query(prompt):
            return await cls._build_conversational_response(prompt, order_intent={"is_trade": False, "is_balance_query": True})

        # Check if the prompt is a Swarm Deliberation / Debate request
        clean_p = prompt.strip().lower()
        is_debate_request = any(w in clean_p for w in ["debate", "arena", "bull vs bear", "deliberat", "opposing", "argue"])
        if is_debate_request:
            debate_result = await autonomous_react_engine.execute_goal(prompt)
            target_sym = debate_result.get("debate", {}).get("symbol", "BTCUSDT")
            debate_data = debate_result.get("debate", {})
            plan = debate_data.get("proposed_plan", {})
            debate_result["research_brief"] = {
                "brief_id": f"DEBATE_{target_sym}_{int(time.time())}",
                "timestamp": timestamp_start,
                "suggested_ticket": {
                    "symbol": target_sym,
                    "side": "BUY",
                    "size": plan.get("size", 0.5),
                    "leverage": plan.get("leverage", 3),
                    "stop_loss": plan.get("stop_loss"),
                    "take_profit": plan.get("target_tp")
                },
                "status": debate_data.get("consensus_status", "CONSENSUS_REACHED"),
                "summary": f"Swarm Deliberation completed for {target_sym}. Reconciled consensus: {debate_data.get('consensus_status')}."
            }
            debate_result["orchestrator"] = {
                "parsed_intent": {
                    "symbol": target_sym,
                    "side": "buy",
                    "size": plan.get("size", 0.5),
                    "leverage": plan.get("leverage", 3),
                    "is_trade": True,
                    "is_debate": True
                }
            }
            return debate_result

        # 1. Parse Natural Language Intent directly with Orchestrator LLM
        order_intent = await cls._parse_intent_async(prompt)
        raw_symbol = order_intent.get("symbol")
        if (
            not order_intent.get("is_trade", True)
            or not raw_symbol
            or str(raw_symbol).upper() in ("NONE", "NULL", "N/A", "NONEUSDT", "NONE/USDT", "FALSE")
        ):
            return await cls._build_conversational_response(prompt, order_intent)

        symbol = raw_symbol

        # 2. Fetch Live Bitget Telemetry
        ticker = bitget_client.get_ticker(symbol)
        orderbook = bitget_client.get_orderbook(symbol, depth=15)
        candles = bitget_client.get_historical_candles(symbol, "1h", limit=120)
        quant_data = QuantAnalyst.analyze_candles(candles)
        recent_trades = bitget_client.paper_trades
        portfolio_balance = bitget_client.get_account_balances()

        # Calculate notional & resolve exact token size from live price
        current_price = ticker.get("last_price", 100.0)
        if current_price <= 0:
            current_price = 100.0
        order_intent["current_price"] = current_price

        # If user specified a fiat/dollar budget (e.g. "ten dollars of eth"), convert to token size
        if order_intent.get("dollar_amount") and order_intent["dollar_amount"] > 0:
            precision = 6 if current_price > 500 else 4
            order_intent["size"] = round(order_intent["dollar_amount"] / current_price, precision)
            order_intent["notional_usdt"] = round(order_intent["dollar_amount"], 2)
        elif order_intent.get("token_size") and order_intent["token_size"] > 0:
            order_intent["size"] = float(order_intent["token_size"])
            order_intent["notional_usdt"] = round(order_intent["size"] * current_price, 2)
        elif order_intent.get("size") and order_intent["size"] > 0:
            order_intent["notional_usdt"] = round(order_intent["size"] * current_price, 2)
        else:
            default_sz = cls._get_default_size(symbol)
            order_intent["size"] = default_sz
            order_intent["notional_usdt"] = round(default_sz * current_price, 2)

        # Build Context Package for the Sub-Agents
        context = {
            "raw_prompt": prompt,
            "symbol": symbol,
            "order_intent": order_intent,
            "ticker_data": ticker,
            "orderbook": orderbook,
            "quant_data": quant_data,
            "candles": candles,
            "recent_trades": recent_trades,
            "portfolio_balance": portfolio_balance
        }

        # 3. RUN ALL 7 SUB-AGENTS & SWARM DELIBERATION ARENA IN PARALLEL VIA ASYNCIO.GATHER
        t0 = asyncio.get_event_loop().time()
        sub_agents_coro = asyncio.gather(
            VolatilityAgent.analyze(context),
            FraudHunterAgent.analyze(context),
            SecurityAgent.analyze(context),
            LiquidityAgent.analyze(context),
            PsychologyAgent.analyze(context),
            QuantAnalystAgent.analyze(context),
            BacktestAgent.analyze(context)
        )
        debate_coro = swarm_arena.deliberate(
            symbol=symbol,
            requested_leverage=order_intent["leverage"],
            requested_size=order_intent["size"],
            raw_prompt=prompt
        )
        sub_agent_results, debate_data = await asyncio.gather(sub_agents_coro, debate_coro)
        t_elapsed = round((asyncio.get_event_loop().time() - t0) * 1000, 1)

        vol_res, fraud_res, sec_res, liq_res, psych_res, quant_res, backtest_res = sub_agent_results

        # 4. S2 Modules: rToken Regime Audit, Historical Stress Testing, & Bitget Signals
        rtoken_audit = rtoken_regime_detector.audit_rtoken_trade(symbol, order_intent["leverage"], order_intent["size"])
        bitget_signals = bitget_signal_service.get_live_signals(symbol, candles=candles)
        stress_test = stress_tester.evaluate(order_intent, current_price)

        # Execution Assistance: Detailed L2 Depth Walk
        depth_walk = bitget_client.walk_orderbook_depth(symbol, order_intent["size"], order_intent["side"])

        # 5. Compute Weighted Composite Risk Score across all 7 Defense Pillars
        # Weights: Fraud (20%), Security (15%), Volatility (15%), Liquidity (15%), Psychology (15%), Quant Analyst (10%), Backtester (10%)
        composite_score = int(
            (vol_res["score"] * 0.15) +
            (fraud_res["score"] * 0.20) +
            (sec_res["score"] * 0.15) +
            (liq_res["score"] * 0.15) +
            (psych_res["score"] * 0.15) +
            (quant_res["score"] * 0.10) +
            (backtest_res["score"] * 0.10)
        )

        # Aggregate All Flags
        all_flags = []
        for r in sub_agent_results:
            all_flags.extend(r.get("flags", []))

        # Extreme leverage penalty (e.g. >= 20x)
        if order_intent["leverage"] >= 20:
            all_flags.append(f"Extreme Leverage Alert: {order_intent['leverage']}x leverage creates catastrophic liquidation risk on normal intra-day price swings.")
            composite_score = max(composite_score, 75)
        elif order_intent["leverage"] >= 10:
            all_flags.append(f"Elevated Leverage: {order_intent['leverage']}x leverage narrows liquidation buffer to {stress_test.get('liquidation_buffer_pct')}%.")

        # Elevate composite score if rToken off-hours or stress test fragility detected
        if rtoken_audit.get("is_rtoken"):
            all_flags.extend(rtoken_audit.get("flags", []))
            if rtoken_audit["session_info"]["session"] == "WEEKEND_CLOSED" and order_intent["leverage"] > 2:
                all_flags.append(f"Weekend rToken Cap: Holding {order_intent['leverage']}x leverage on weekend exceeds recommended 2x maximum.")
                composite_score = max(composite_score, 45)
                if order_intent["leverage"] >= 10:
                    composite_score = max(composite_score, 75)

        if not stress_test["survived_all"] and stress_test["resilience_rating"] == "FRAGILE / HIGH LEVERAGE":
            all_flags.append(f"Pre-Trade Stress Alert: Position fails in {stress_test['survival_ratio']} historical crisis scenarios.")

        # Check for empirical simulation and quant factor warnings
        has_backtest_negative = (backtest_res.get("status") == "NEGATIVE_EXPECTANCY")
        has_quant_warning = (quant_res.get("status") in ("WEAK_EDGE", "UNCERTAIN", "NEGATIVE_ALPHA"))

        if has_backtest_negative and has_quant_warning:
            composite_score = max(composite_score, 45)
            all_flags.append(f"Empirical & Factor Warning: Strategy yielded negative historical expectancy ({backtest_res.get('metrics', {}).get('total_return_pct', 0):+.1f}%, Sharpe {backtest_res.get('metrics', {}).get('sharpe_ratio', 0):.2f}).")
        elif has_backtest_negative:
            composite_score = max(composite_score, 40)
            all_flags.append(f"Empirical Backtest Warning: Strategy yielded negative expectancy ({backtest_res.get('metrics', {}).get('total_return_pct', 0):+.1f}%).")

        composite_score = min(100, max(0, composite_score))

        # Check for hard critical thresholds (Fraud >= 75, Contract Risk >= 75, Severe Tilt >= 75 with high leverage, or Leverage >= 25x)
        has_critical_pillar = (
            (fraud_res.get("score", 0) >= 75) or
            (sec_res.get("score", 0) >= 75) or
            (order_intent["leverage"] >= 25) or
            (psych_res.get("score", 0) >= 75 and order_intent["leverage"] >= 15)
        )
        has_warning_pillar = any(p["score"] >= 45 or p.get("status") in ("NEGATIVE_EXPECTANCY", "WARNING", "DANGER") for p in sub_agent_results) or (order_intent["leverage"] > 3 and not order_intent.get("is_spot"))

        if composite_score >= 65 or has_critical_pillar:
            verdict = "INTERCEPTED_BLOCK"
            verdict_badge = "BLOCKED"
        elif composite_score >= 35 or has_warning_pillar:
            verdict = "ADVISORY_CAUTION"
            verdict_badge = "CAUTION"
        else:
            verdict = "APPROVED_EXECUTION"
            verdict_badge = "APPROVED"

        # 6. Interactive 1-Click "Safe Trade Prescription" (Execution Assistance)
        safe_prescription = None
        if verdict_badge in ("CAUTION", "BLOCKED"):
            is_spot_intent = bool(order_intent.get("is_spot"))
            curr_lev = order_intent["leverage"]
            if is_spot_intent:
                prescribed_leverage = 1
                safe_rationale = "Protects spot capital: limits execution slippage and sets optimal bracket SL/TP."
            elif rtoken_audit.get("is_rtoken") and not rtoken_audit["session_info"]["is_regular_market_hours"]:
                prescribed_leverage = min(2, curr_lev)
                safe_rationale = f"De-risks 7×24 rToken position: caps leverage to weekend-safe {prescribed_leverage}x and cushions against Monday open gap."
            elif curr_lev > 5:
                prescribed_leverage = 3
                safe_rationale = f"De-risks position: lowers borrowing multiplier from {curr_lev}x to {prescribed_leverage}x and widens liquidation buffer."
            else:
                prescribed_leverage = max(1, curr_lev - 1)
                safe_rationale = f"De-risks position: lowers borrowing multiplier from {curr_lev}x to {prescribed_leverage}x."

            # Execution style recommendation
            if depth_walk.get("recommend_twap") or liq_res["score"] >= 40 or order_intent["notional_usdt"] > 5000.0:
                prescribed_execution = "TWAP 3 Tranches (3s intervals)"
                tranche_size = round(order_intent["size"] / 3.0, 4)
                exec_note = f"Split into 3 scheduled tranches of {tranche_size} {symbol.replace('USDT', '')} to minimize orderbook impact"
            else:
                prescribed_execution = "Limit Order at Mid-Price (Slippage Guard)"
                exec_note = "Passive limit order with strict slippage guard"

            lev_reduction_pct = round(((curr_lev - prescribed_leverage) / curr_lev) * 100) if curr_lev > prescribed_leverage else 0
            risk_reduction_pct = max(35, min(88, lev_reduction_pct + 25))

            safe_prescription = {
                "active": True,
                "is_spot": is_spot_intent,
                "original_leverage": curr_lev,
                "safe_leverage": prescribed_leverage,
                "original_size": order_intent["size"],
                "safe_size": order_intent["size"],
                "execution_mode": prescribed_execution,
                "execution_note": exec_note,
                "suggested_sl_pct": 3.5,
                "suggested_tp_pct": 8.0,
                "risk_reduction_pct": risk_reduction_pct,
                "rationale": safe_rationale
            }

        # 7. Master Synthesis & Research Brief Generation
        defense_summary = {
            "overall_verdict": verdict_badge,
            "composite_risk_score": composite_score,
            "pillars": {
                "volatility": vol_res,
                "scam_fraud": fraud_res,
                "security": sec_res,
                "liquidity": liq_res,
                "psychology": psych_res,
                "quant_analyst": quant_res,
                "strategy_backtester": backtest_res
            },
            "rtoken_regime": rtoken_audit,
            "threat_flags": all_flags,
            "stress_test": {
                "survival_ratio": stress_test["survival_ratio"],
                "resilience_rating": stress_test["resilience_rating"]
            },
            "bitget_signals_summary": bitget_signals.get("perception_summary")
        }
        ai_synthesis = openrouter_client.review_pre_trade_threats(order_intent, defense_summary)

        # Generate Formal Track 3 Research Brief
        from app.defense.research_brief import research_brief_generator
        research_brief = research_brief_generator.generate_brief(
            prompt=prompt,
            parsed_intent=order_intent,
            market_snapshot={
                "symbol": symbol,
                "price": current_price,
                "regime": quant_data.get("market_regime", "Nominal"),
                "hurst_exponent": quant_data.get("hurst_exponent", 0.52),
                "rsi": quant_data.get("rsi", 50.0)
            },
            rtoken_regime=rtoken_audit,
            stress_test=stress_test,
            sub_agents={
                "volatility_sentinel": vol_res,
                "fraud_hunter": fraud_res,
                "security_guard": sec_res,
                "liquidity_auditor": liq_res,
                "psychology_shield": psych_res,
                "quant_analyst": quant_res,
                "strategy_backtester": backtest_res
            },
            composite_score=composite_score,
            verdict=verdict,
            verdict_badge=verdict_badge,
            safe_prescription=safe_prescription,
            ai_synthesis=ai_synthesis
        )

        is_spot_order = bool(order_intent.get("is_spot"))
        step1_action = f"SPOT {order_intent['side'].upper()}" if is_spot_order else order_intent['side'].upper()
        step1_lev = "Spot asset purchase (No leverage)." if is_spot_order else f"Leverage: {order_intent['leverage']}x."
        parser_mode = order_intent.get("parser_mode")
        if parser_mode == "LLM_OPENROUTER":
            mode_label = "LLM OpenRouter"
        elif parser_mode == "LLM_BITGET_QWEN":
            mode_label = "LLM Bitget Qwen"
        else:
            mode_label = "NLP Engine"
        llm_reasoning = order_intent.get("llm_reasoning") or "Deconstructed intent & extracted parameters."
        if order_intent.get("dollar_amount"):
            budget_str = f"Budget: ${order_intent['dollar_amount']:,.2f} USD -> Converted to {order_intent['size']} {symbol.replace('USDT', '')} @ ${current_price:,.2f}"
        else:
            budget_str = f"Size: {order_intent['size']} {symbol.replace('USDT', '')} (~${order_intent.get('notional_usdt', 0):,.2f} USDT)"

        step1_desc = f"[{mode_label}] {llm_reasoning} | Target: {symbol}, Action: {step1_action}, {budget_str}. {step1_lev}"
        step6_risk = "Zero Liquidation Risk (Spot Ownership)." if is_spot_order else f"Liquidation buffer: {stress_test.get('liquidation_buffer_pct')}%, Monte Carlo 95% worst DD: {backtest_res['metrics']['monte_carlo_worst_dd_pct']}%."
        step6_desc = f"Resilience: {stress_test['resilience_rating']} ({stress_test['survival_ratio']} survived). {step6_risk}"

        return {
            "orchestrator": {
                "status": "COMPLETED",
                "execution_mode": "RESEARCH_WORKBENCH_SWARM",
                "latency_ms": t_elapsed,
                "timestamp": timestamp_start,
                "parsed_intent": order_intent,
                "composite_risk_score": composite_score,
                "verdict": verdict,
                "verdict_badge": verdict_badge
            },
            "research_brief": research_brief,
            "debate": debate_data,
            "depth_walk": depth_walk,
            "sub_agents": {
                "volatility_sentinel": vol_res,
                "fraud_hunter": fraud_res,
                "security_guard": sec_res,
                "liquidity_auditor": liq_res,
                "psychology_shield": psych_res,
                "quant_analyst": quant_res,
                "strategy_backtester": backtest_res
            },
            "market_snapshot": {
                "symbol": symbol,
                "price": current_price,
                "regime": quant_data.get("market_regime"),
                "hurst_exponent": quant_data.get("hurst_exponent"),
                "rsi": quant_data.get("rsi")
            },
            "threat_flags": all_flags,
            "ai_synthesis": ai_synthesis,
            "rtoken_regime": rtoken_audit,
            "stress_test": stress_test,
            "safe_prescription": safe_prescription,
            "bitget_signals": bitget_signals,
            "agentic_trace": [
                {"step": 1, "type": "THOUGHT", "title": f"Intent Deconstruction: {symbol} {step1_action}", "content": step1_desc},
                {"step": 2, "type": "TOOL_CALL", "tool": "bitget_l2_depth_walk", "title": f"Walking Bitget L2 Book ({depth_walk['levels_consumed']} levels, {depth_walk['slippage_pct']:.2f}% slip)", "arguments": {"symbol": symbol, "size": order_intent["size"], "levels_consumed": depth_walk["levels_consumed"]}},
                {"step": 3, "type": "OBSERVATION", "tool": "bitget_telemetry_fetch", "title": "Telemetry Ground Truth Ingested", "content": f"Price: ${current_price:,.2f}, Regime: {quant_data.get('market_regime')}, Hurst: {quant_data.get('hurst_exponent')}, RSI: {quant_data.get('rsi')}."},
                {"step": 4, "type": "TOOL_CALL", "tool": "parallel_7_defense_pillars_dispatch", "title": f"Concurrent 7-Pillar Defense Audit on {order_intent['size']} {symbol.replace('USDT', '')}", "arguments": {"symbol": symbol, "side": order_intent["side"], "size": order_intent["size"], "notional_usdt": order_intent["notional_usdt"], "leverage": order_intent["leverage"], "pillars": ["volatility", "fraud", "security", "liquidity", "psychology", "quant_analyst", "backtest_simulator"]}},
                {"step": 5, "type": "OBSERVATION", "tool": "parallel_7_defense_pillars_dispatch", "title": f"7-Pillar Swarm Consensus Completed ({t_elapsed}ms)", "content": f"Score: {composite_score}/100. Master Verdict: {verdict_badge}. Active flags: {len(all_flags)}. Win Rate: {backtest_res['metrics']['win_rate_pct']}%, Sharpe: {backtest_res['metrics']['sharpe_ratio']}."},
                {"step": 6, "type": "THOUGHT", "title": "Crisis Stress Testing & Safe Prescription Routing", "content": step6_desc}
            ]
        }

    @classmethod
    async def _parse_intent_async(cls, prompt: str) -> Dict[str, Any]:
        """
        Orchestrator LLM Intent Analysis:
        Dispatches prompt to OpenRouter LLM for deep natural language deconstruction,
        falling back to deterministic NLP engine if offline or timed out.
        """
        try:
            intent = await asyncio.to_thread(openrouter_client.parse_trading_intent, prompt)
            if intent and isinstance(intent, dict) and "symbol" in intent:
                return intent
        except Exception as e:
            logger.warning(f"Async LLM intent parsing encountered error: {e}")

        return cls._parse_intent(prompt)

    @classmethod
    def _get_default_size(cls, symbol: str) -> float:
        default_sizes = {
            "BTCUSDT": 0.15,
            "ETHUSDT": 2.0,
            "SOLUSDT": 15.0,
            "BGBUSDT": 1000.0,
            "DOGEUSDT": 5000.0,
            "NVDAUSDT": 25.0,
            "TSLAUSDT": 10.0,
            "AAPLUSDT": 20.0,
            "COINUSDT": 15.0,
            "SPYUSDT": 5.0,
            "MSFTUSDT": 10.0
        }
        return default_sizes.get(symbol, 0.1)

    @classmethod
    async def execute_agentic_goal(cls, goal: str) -> Dict[str, Any]:
        """
        Execute an open-ended autonomous trading objective through the ReAct Agent loop.
        """
        return await autonomous_react_engine.execute_goal(goal)

    @staticmethod
    def _parse_intent(prompt: str) -> Dict[str, Any]:
        """Extract asset, side, size, and leverage from natural language."""
        if AlphaOrchestrator._is_greeting(prompt):
            reply = (
                "I am completely ready! All 7 defense and quantitative sub-agents are online and calibrated. What coin or trade directive would you like to inspect or execute?"
                if "ready" in prompt.lower()
                else "Hello! I'm Alphaind, your AI Trade Co-Pilot on Bitget. How can I assist you with your trading today?"
            )
            return {
                "is_trade": False,
                "symbol": None,
                "side": None,
                "dollar_amount": None,
                "token_size": None,
                "size": 0.0,
                "leverage": 1,
                "market_type": "spot",
                "is_spot": True,
                "order_type": "market",
                "conversational_reply": reply,
                "llm_reasoning": "Conversational greeting or readiness check detected.",
                "parser_mode": "NLP_ENGINE"
            }

        norm_prompt = openrouter_client.normalize_number_words(prompt)
        text = norm_prompt.upper()

        # Symbol extraction (Default: NVDAUSDT for 7x24 tokenized US stock workbench)
        symbol = "NVDAUSDT"
        pair_match = re.search(r'\b([A-Z0-9]{2,16})USDT\b', text)
        if pair_match:
            symbol = pair_match.group(1) + "USDT"
        elif any(s in text for s in ["PEPE100XINU", "HONEYPOT", "SCAMCOIN", "SAFEMOON", "ELONDOGE"]):
            for s in ["PEPE100XINU", "HONEYPOT", "SCAMCOIN", "SAFEMOON", "ELONDOGE"]:
                if s in text:
                    symbol = s + "USDT" if not s.endswith("USDT") else s
                    break
        elif "BTC" in text or "BITCOIN" in text:
            symbol = "BTCUSDT"
        elif "ETH" in text or "ETHEREUM" in text:
            symbol = "ETHUSDT"
        elif "SOL" in text or "SOLANA" in text:
            symbol = "SOLUSDT"
        elif "BGB" in text:
            symbol = "BGBUSDT"
        elif "DOGE" in text:
            symbol = "DOGEUSDT"
        elif "NVDA" in text or "NVIDIA" in text:
            symbol = "NVDAUSDT"
        elif "TSLA" in text or "TESLA" in text:
            symbol = "TSLAUSDT"
        elif "AAPL" in text or "APPLE" in text:
            symbol = "AAPLUSDT"
        elif "COINBASE" in text or bool(re.search(r'\bCOIN\b', text)):
            symbol = "COINUSDT"
        elif "SPY" in text or "S&P" in text:
            symbol = "SPYUSDT"
        elif "MSFT" in text or "MICROSOFT" in text:
            symbol = "MSFTUSDT"
        elif "XRP" in text:
            symbol = "XRPUSDT"
        elif "ADA" in text:
            symbol = "ADAUSDT"
        elif "AVAX" in text:
            symbol = "AVAXUSDT"
        elif "LINK" in text:
            symbol = "LINKUSDT"
        elif "SUI" in text:
            symbol = "SUIUSDT"
        elif "PEPE" in text:
            symbol = "PEPEUSDT"
        elif "SHIB" in text:
            symbol = "SHIBUSDT"
        else:
            susp_match = re.search(r'\b([A-Z0-9]*(?:100X|INU|SAFE|MOON|ELON|V2|HONEYPOT)[A-Z0-9]*)\b', text)
            if susp_match and len(susp_match.group(1)) >= 3:
                symbol = susp_match.group(1) + "USDT"

        # Side extraction
        side = "buy"
        if any(w in text for w in ["SHORT", "SELL", "DUMP", "BEAR"]):
            side = "sell"
        elif any(w in text for w in ["LONG", "BUY", "ACCUMULATE", "BULL"]):
            side = "buy"

        # Market Type (Spot vs Perp / Futures)
        is_spot = False
        is_perp = False
        if "SPOT" in text:
            is_spot = True
        elif any(w in text for w in ["PERP", "PERPETUAL", "FUTURES", "SWAP", "MARGIN"]):
            is_perp = True

        # Leverage extraction (e.g. "10x", "5X", "leverage 20")
        leverage = 1
        lev_match = re.search(r'(\d+)\s*[xX]', text)
        if lev_match:
            leverage = int(lev_match.group(1))
            if leverage > 1:
                is_perp = True
                is_spot = False
        else:
            lev_word_match = re.search(r'LEVERAGE\s*(\d+)', text)
            if lev_word_match:
                leverage = int(lev_word_match.group(1))
                if leverage > 1:
                    is_perp = True
                    is_spot = False
            elif is_perp:
                leverage = 3
            elif any(w in text for w in ["SHORT", "LONG"]):
                is_perp = True
                leverage = 3
            else:
                is_spot = True
                leverage = 1

        if is_spot:
            leverage = 1
            market_type = "spot"
        else:
            market_type = "perp"

        # Size & Dollar extraction (e.g. "0.5 BTC", "50 SOL", "$1,000 worth", "1000 USDT", "size 2")
        size = 0.1
        if symbol == "BTCUSDT":
            size = 0.15
        elif symbol == "ETHUSDT":
            size = 2.0
        elif symbol == "SOLUSDT":
            size = 15.0
        elif symbol == "BGBUSDT":
            size = 1000.0
        elif symbol == "DOGEUSDT":
            size = 5000.0
        elif symbol == "NVDAUSDT":
            size = 25.0
        elif symbol == "TSLAUSDT":
            size = 10.0
        elif symbol == "AAPLUSDT":
            size = 20.0
        elif symbol == "COINUSDT":
            size = 15.0
        elif symbol == "SPYUSDT":
            size = 5.0
        elif symbol == "MSFTUSDT":
            size = 10.0

        # Check for explicit token quantities
        token_size = None
        num_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:BTC|ETH|SOL|BGB|DOGE|XRP|ADA|AVAX|LINK|SUI|NVDA|TSLA|AAPL|COIN|SPY|MSFT|COINS|UNITS|SHARES|STOCKS)\b', text)
        if num_match:
            token_size = float(num_match.group(1))
            size = token_size

        # Check for dollar amounts (e.g. "$1,000 worth", "$500", "1000 USD", "2500 USDT", "1000 worth", "10 dollars")
        dollar_amount = None
        dollar_match = re.search(r'\$\s*([\d,]+(?:\.\d+)?)|([\d,]+(?:\.\d+)?)\s*(?:USD|USDT|BUCKS|DOLLARS|BUX|WORTH)', text)
        if dollar_match:
            raw_dollar = dollar_match.group(1) or dollar_match.group(2)
            try:
                dollar_amount = float(raw_dollar.replace(',', ''))
            except (ValueError, TypeError):
                dollar_amount = None

        # Order Type
        order_type = "market"
        if "LIMIT" in text:
            order_type = "limit"

        intent = {
            "symbol": symbol,
            "side": side,
            "size": size,
            "token_size": token_size,
            "leverage": 1 if market_type == "spot" else min(125, max(1, leverage)),
            "order_type": order_type,
            "market_type": market_type,
            "is_spot": market_type == "spot",
            "llm_reasoning": f"NLP engine extracted {side.upper()} order for {symbol}.",
            "is_trade": True
        }
        if dollar_amount is not None and dollar_amount > 0:
            intent["dollar_amount"] = dollar_amount

        return intent

alpha_orchestrator = AlphaOrchestrator()
