import pytest
import asyncio

from app.agents.quant_agent import QuantAnalystAgent
from app.agents.backtest_agent import BacktestAgent
from app.agents.tools import agent_tools
from app.agents.agentic_engine import autonomous_react_engine
from app.services.bitget_client import bitget_client
from app.quant.analyst import QuantAnalyst

@pytest.mark.asyncio
async def test_quant_analyst_agent_analysis():
    candles = bitget_client.get_historical_candles("BTCUSDT", "1h", limit=50)
    quant_data = QuantAnalyst.analyze_candles(candles)

    context = {
        "symbol": "BTCUSDT",
        "order_intent": {"symbol": "BTCUSDT", "side": "buy", "leverage": 2, "size": 0.1},
        "quant_data": quant_data,
        "candles": candles
    }

    result = await QuantAnalystAgent.analyze(context)

    assert result["agent"] == "Quantitative Analyst"
    assert "status" in result
    assert result["status"] in ("STRONG_EDGE", "MODERATE_EDGE", "UNFAVORABLE_REGIME")
    assert "metrics" in result
    assert "hurst_exponent" in result["metrics"]
    assert "composite_alpha" in result["metrics"]
    assert "market_regime" in result["metrics"]
    assert len(result["thought_trace"]) >= 2
    assert "summary" in result
    assert 0 <= result["alpha_conviction_score"] <= 100

@pytest.mark.asyncio
async def test_backtest_agent_simulation():
    candles = bitget_client.get_historical_candles("SOLUSDT", "1h", limit=100)
    context = {
        "symbol": "SOLUSDT",
        "order_intent": {"symbol": "SOLUSDT", "side": "buy", "leverage": 3, "size": 10.0},
        "strategy_type": "regime_alpha",
        "candles": candles
    }

    result = await BacktestAgent.analyze(context)

    assert result["agent"] == "Strategy Backtester"
    assert result["status"] in ("STRONG_EMPIRICAL_EDGE", "ACCEPTABLE_EDGE", "NEGATIVE_EXPECTANCY")
    assert "metrics" in result
    metrics = result["metrics"]
    assert "win_rate_pct" in metrics
    assert "sharpe_ratio" in metrics
    assert "max_drawdown_pct" in metrics
    assert "monte_carlo_worst_dd_pct" in metrics
    assert len(result["thought_trace"]) >= 2
    assert "full_report" in result

@pytest.mark.asyncio
async def test_tool_registry_has_backtest_and_quant():
    tool_names = [t["name"] for t in agent_tools.list_tools()]
    assert "tool_run_backtest" in tool_names
    assert "tool_quant_deep_audit" in tool_names

@pytest.mark.asyncio
async def test_tool_run_backtest_execution():
    res = await agent_tools.execute_tool("tool_run_backtest", {
        "symbol": "BTCUSDT",
        "strategy_type": "regime_alpha",
        "initial_capital": 10000.0,
        "stop_loss_pct": 0.025,
        "take_profit_pct": 0.060,
        "candle_limit": 80
    })
    assert res["success"] is True
    data = res["result"]
    assert data["agent"] == "Strategy Backtester"
    assert "metrics" in data
    assert data["metrics"]["total_trades"] >= 0

@pytest.mark.asyncio
async def test_tool_quant_deep_audit_execution():
    res = await agent_tools.execute_tool("tool_quant_deep_audit", {
        "symbol": "ETHUSDT",
        "side": "buy",
        "timeframe": "1h",
        "limit": 60
    })
    assert res["success"] is True
    data = res["result"]
    assert data["agent"] == "Quantitative Analyst"
    assert "alpha_conviction_score" in data
    assert "metrics" in data

@pytest.mark.asyncio
async def test_react_engine_backtest_route():
    goal = "Backtest regime alpha strategy on SOL with 3x leverage and check Monte Carlo drawdown"
    result = await autonomous_react_engine.execute_goal(goal)

    assert result["status"] == "COMPLETED"
    assert result["execution_mode"] == "AUTONOMOUS_REACT_LOOP"
    assert result["route"] == "QUANT_BACKTEST_VALIDATION"
    assert "trace" in result
    assert len(result["trace"]) >= 4

    # Verify tool calls are logged in trace
    tools_called = [t.get("tool") for t in result["trace"] if t.get("type") == "TOOL_CALL"]
    assert "tool_quant_deep_audit" in tools_called
    assert "tool_run_backtest" in tools_called

    # Verify final decision payload
    final_dec = result["final_decision"]
    assert "headline" in final_dec
    assert "performance_summary" in final_dec
    assert final_dec["performance_summary"]["symbol"] == "SOLUSDT"
