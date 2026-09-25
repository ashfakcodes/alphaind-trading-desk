import pytest
import asyncio
from app.agents.orchestrator import alpha_orchestrator
from app.agents.volatility_agent import VolatilityAgent
from app.agents.fraud_agent import FraudHunterAgent
from app.agents.security_agent import SecurityAgent
from app.agents.liquidity_agent import LiquidityAgent
from app.agents.psychology_agent import PsychologyAgent

@pytest.mark.asyncio
async def test_orchestrator_intent_parsing():
    intent1 = alpha_orchestrator._parse_intent("I want to long 50 SOL with 5x leverage")
    assert intent1["symbol"] == "SOLUSDT"
    assert intent1["side"] == "buy"
    assert intent1["size"] == 50.0
    assert intent1["leverage"] == 5

    intent2 = alpha_orchestrator._parse_intent("Sell 2.5 ETH with 10x leverage limit order")
    assert intent2["symbol"] == "ETHUSDT"
    assert intent2["side"] == "sell"
    assert intent2["size"] == 2.5
    assert intent2["leverage"] == 10
    assert intent2["order_type"] == "limit"

@pytest.mark.asyncio
async def test_sub_agents_parallel_execution():
    context = {
        "raw_prompt": "Conservative swing long on 0.1 BTC with 2x leverage",
        "symbol": "BTCUSDT",
        "order_intent": {"symbol": "BTCUSDT", "side": "buy", "size": 0.1, "leverage": 2, "notional_usdt": 9245.0},
        "ticker_data": {"last_price": 92450.0, "change_24h": 1.5, "volume_24h": 1200000000},
        "orderbook": {"bids": [[92440, 1.5]], "asks": [[92460, 1.5]]},
        "quant_data": {"annualized_volatility": 42.0, "atr_pct": 1.1, "bollinger_bandwidth": 3.5, "z_score": 0.2, "rsi": 52.0},
        "recent_trades": [],
        "portfolio_balance": {"USDT": 50000.0}
    }

    t0 = asyncio.get_event_loop().time()
    results = await asyncio.gather(
        VolatilityAgent.analyze(context),
        FraudHunterAgent.analyze(context),
        SecurityAgent.analyze(context),
        LiquidityAgent.analyze(context),
        PsychologyAgent.analyze(context)
    )
    elapsed = asyncio.get_event_loop().time() - t0

    assert len(results) == 5
    # All 5 ran concurrently in parallel
    assert elapsed < 0.5  # sub-second parallel execution

    vol, fraud, sec, liq, psych = results
    assert vol["agent"] == "Volatility Sentinel"
    assert fraud["agent"] == "Fraud & Scam Hunter"
    assert sec["agent"] == "Security Guard"
    assert liq["agent"] == "Liquidity Auditor"
    assert psych["agent"] == "Psychology Shield"

    assert all(r["status"] == "SAFE" for r in results)

@pytest.mark.asyncio
async def test_orchestrator_full_workflow_safe():
    prompt = "Conservative swing long on 0.15 BTC with 3x leverage"
    res = await alpha_orchestrator.process_natural_language_request(prompt)

    assert res["orchestrator"]["status"] == "COMPLETED"
    assert res["orchestrator"]["verdict"] in ("APPROVED_EXECUTION", "ADVISORY_CAUTION")
    assert "sub_agents" in res
    assert len(res["sub_agents"]) == 7
    assert "quant_analyst" in res["sub_agents"]
    assert "strategy_backtester" in res["sub_agents"]
    assert "ai_synthesis" in res

@pytest.mark.asyncio
async def test_orchestrator_tilt_interception():
    # Prompt explicitly indicating emotional tilt & revenge trading
    prompt = "I lost my last 3 trades, I am angry and want to 50x all-in leverage on SOL right now!"
    res = await alpha_orchestrator.process_natural_language_request(prompt)

    # Psychology agent must trigger high alert
    psych = res["sub_agents"]["psychology_shield"]
    assert psych["score"] > 50
    assert psych["status"] in ("WARNING", "DANGER")
    # Overall verdict should be blocked or cautionary
    assert res["orchestrator"]["verdict"] in ("INTERCEPTED_BLOCK", "ADVISORY_CAUTION")

@pytest.mark.asyncio
async def test_dollar_amount_and_meme_ticker_parsing():
    intent_dollar = alpha_orchestrator._parse_intent("I want to buy $1,000 worth of Bitcoin with 2x leverage at market price")
    assert intent_dollar["symbol"] == "BTCUSDT"
    assert intent_dollar["side"] == "buy"
    assert intent_dollar["leverage"] == 2
    assert intent_dollar.get("dollar_amount") == 1000.0

    intent_meme = alpha_orchestrator._parse_intent("Audit PEPE100XINU before buying")
    assert "PEPE100XINU" in intent_meme["symbol"]

@pytest.mark.asyncio
async def test_ten_dollars_of_eth_orchestrator_flow():
    prompt = "i want to buy ten dollars of eth"
    
    # 1. Test synchronous intent parsing
    intent = alpha_orchestrator._parse_intent(prompt)
    assert intent["symbol"] == "ETHUSDT"
    assert intent["side"] == "buy"
    assert intent["dollar_amount"] == 10.0
    assert intent["is_spot"] is True
    assert intent["leverage"] == 1

    # 2. Test full orchestrator processing & conversion
    res = await alpha_orchestrator.process_natural_language_request(prompt)
    orch = res["orchestrator"]
    parsed = orch["parsed_intent"]

    assert parsed["symbol"] == "ETHUSDT"
    assert parsed["dollar_amount"] == 10.0
    assert parsed["notional_usdt"] == 10.0
    # Crucial: size must NOT be the hardcoded default 2.0 ETH!
    assert parsed["size"] < 0.1
    assert parsed["size"] > 0.001
    assert parsed["is_spot"] is True

    # 3. Check that trace documents LLM Orchestrator analysis & conversion
    trace = res["agentic_trace"]
    assert len(trace) >= 6
    assert "ETHUSDT" in trace[0]["title"]
    assert "$10.00" in trace[0]["content"]
    assert trace[3]["tool"] in ("parallel_7_defense_pillars_dispatch", "parallel_7_pillar_swarm_dispatch")
    assert trace[3]["arguments"]["notional_usdt"] == 10.0
    assert trace[3]["arguments"]["size"] == parsed["size"]

@pytest.mark.asyncio
async def test_natural_language_word_number_parsing():
    intent_sol = alpha_orchestrator._parse_intent("buy twenty five dollars of solana")
    assert intent_sol["symbol"] == "SOLUSDT"
    assert intent_sol["dollar_amount"] == 25.0
    assert intent_sol["side"] == "buy"

    intent_half = alpha_orchestrator._parse_intent("sell half an eth")
    assert intent_half["symbol"] == "ETHUSDT"
    assert intent_half["side"] == "sell"
    assert intent_half["token_size"] == 0.5
    assert intent_half["size"] == 0.5


@pytest.mark.asyncio
async def test_doge_recognized_as_safe_major_coin():
    context = {
        "raw_prompt": "Buy 5000 DOGE with 2x leverage",
        "symbol": "DOGEUSDT",
        "order_intent": {"symbol": "DOGEUSDT", "side": "buy", "size": 5000.0, "notional_usdt": 1400.0}
    }
    sec_res = await SecurityAgent.analyze(context)
    assert sec_res["status"] == "SAFE"
    assert "DOGEUSDT" in SecurityAgent.MAJOR_COINS

@pytest.mark.asyncio
async def test_orchestrator_sol_50x_trade_setup_dispatches_to_quant_and_backtest():
    prompt = "i want to open a long position on sol with 50x leverage worth of $500"
    res = await alpha_orchestrator.process_natural_language_request(prompt)

    intent = res["orchestrator"]["parsed_intent"]
    assert intent["symbol"] == "SOLUSDT"
    assert intent["side"] == "buy"
    assert intent["leverage"] == 50
    assert intent["dollar_amount"] == 500.0

    # Verify all 7 sub-agents executed
    sub_agents = res["sub_agents"]
    assert len(sub_agents) == 7
    assert "quant_analyst" in sub_agents
    assert "strategy_backtester" in sub_agents

    # Verify Quant Analyst telemetry
    quant = sub_agents["quant_analyst"]
    assert quant["agent"] == "Quantitative Analyst"
    assert "hurst_exponent" in quant["metrics"]
    assert "composite_alpha" in quant["metrics"]
    assert len(quant["thought_trace"]) > 0

    # Verify Strategy Backtester simulation
    backtest = sub_agents["strategy_backtester"]
    assert backtest["agent"] == "Strategy Backtester"
    assert "win_rate_pct" in backtest["metrics"]
    assert "sharpe_ratio" in backtest["metrics"]
    assert "monte_carlo_worst_dd_pct" in backtest["metrics"]
    assert len(backtest["thought_trace"]) > 0

    # Verify 50x leverage is blocked or flagged for extreme risk with safe prescription
    assert res["orchestrator"]["verdict"] in ("INTERCEPTED_BLOCK", "ADVISORY_CAUTION")
    assert res["safe_prescription"] is not None
    assert res["safe_prescription"]["safe_leverage"] <= 3

@pytest.mark.asyncio
async def test_greeting_handled_as_copilot_chat():
    # 1. Test greeting recognition logic
    assert alpha_orchestrator._is_greeting("hello") is True
    assert alpha_orchestrator._is_greeting("hi!") is True
    assert alpha_orchestrator._is_greeting("who are you") is True
    assert alpha_orchestrator._is_greeting("help") is True
    assert alpha_orchestrator._is_greeting("buy 1 btc") is False
    assert alpha_orchestrator._is_greeting("Hello, buy $500 of BTC") is False

    # 2. Test intent parsing for greeting
    intent = alpha_orchestrator._parse_intent("hello")
    assert intent["is_trade"] is False
    assert intent["symbol"] is None

    # 3. Test full orchestrator processing for greeting
    res = await alpha_orchestrator.process_natural_language_request("hello")
    assert res.get("is_conversational") is True
    assert res["orchestrator"]["verdict_badge"] == "STANDBY"
    assert res["orchestrator"]["status"] == "COMPLETED"
    assert res["orchestrator"]["execution_mode"] == "COPILOT_STANDBY"
    assert res["orchestrator"]["parsed_intent"]["symbol"] is None
    assert res["orchestrator"]["parsed_intent"]["is_trade"] is False

    # Ensure fake NONEUSDT token was NEVER created
    assert "NONEUSDT" not in str(res)
    assert res["safe_prescription"]["active"] is False

    # Sub-agents should be in clean STANDBY state
    assert len(res["sub_agents"]) == 7
    for name, agent in res["sub_agents"].items():
        assert agent["score"] == 0
        assert agent["status"] == "STANDBY"

@pytest.mark.asyncio
async def test_are_you_ready_readiness_and_capability_queries():
    # Prompt: "Are you ready"
    res = await alpha_orchestrator.process_natural_language_request("Are you ready")
    assert res.get("is_conversational") is True
    assert res["orchestrator"]["verdict_badge"] == "STANDBY"
    assert res["orchestrator"]["parsed_intent"]["is_trade"] is False
    assert res["orchestrator"]["parsed_intent"]["symbol"] is None
    assert "NONEUSDT" not in str(res)
    # Check conversational response headline and text
    assert "ready" in res["ai_synthesis"]["conversational_explanation"].lower() or "ready" in res["ai_synthesis"]["friendly_title"].lower() or "alphaind" in res["ai_synthesis"]["conversational_explanation"].lower()
    assert res["safe_prescription"]["active"] is False

    # Prompt: "what can you do"
    res_cap = await alpha_orchestrator.process_natural_language_request("what can you do")
    assert res_cap.get("is_conversational") is True
    assert res_cap["orchestrator"]["verdict_badge"] == "STANDBY"
    assert res_cap["orchestrator"]["parsed_intent"]["is_trade"] is False
    assert res_cap["orchestrator"]["parsed_intent"]["symbol"] is None


