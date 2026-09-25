import pytest
import asyncio
from fastapi.testclient import TestClient

from run import app
from app.agents.tools import agent_tools
from app.agents.agentic_engine import autonomous_react_engine
from app.agents.swarm_deliberation import swarm_arena

client = TestClient(app)

# -------------------------------------------------------------
# 1. Tool Registry Tests
# -------------------------------------------------------------

def test_tool_registry_registration():
    tools = agent_tools.list_tools()
    tool_names = [t["name"] for t in tools]
    assert len(tools) >= 9
    assert "tool_market_scanner" in tool_names
    assert "tool_get_market_depth" in tool_names
    assert "tool_quant_analytics" in tool_names
    assert "tool_crisis_stress_test" in tool_names
    assert "tool_portfolio_risk_audit" in tool_names
    assert "tool_run_swarm_defense" in tool_names
    assert "tool_prescribe_safe_trade" in tool_names
    assert "tool_execute_order" in tool_names
    assert "tool_execute_twap" in tool_names

@pytest.mark.asyncio
async def test_tool_market_scanner_execution():
    res = await agent_tools.execute_tool("tool_market_scanner", {"filter_by": "momentum", "top_n": 4})
    assert res["success"] is True
    data = res["result"]
    assert "top_candidates" in data
    assert len(data["top_candidates"]) <= 4
    assert "best_opportunity" in data
    assert data["best_opportunity"]["symbol"] in [c["symbol"] for c in data["top_candidates"]]

@pytest.mark.asyncio
async def test_tool_market_depth_and_impact():
    res = await agent_tools.execute_tool("tool_get_market_depth", {"symbol": "BTCUSDT", "order_size": 0.5, "side": "buy"})
    assert res["success"] is True
    data = res["result"]
    assert data["symbol"] == "BTCUSDT"
    assert data["mid_price"] > 0
    assert "slippage_pct" in data
    assert "spread_pct" in data
    assert "impact_assessment" in data

@pytest.mark.asyncio
async def test_tool_portfolio_risk_audit():
    res = await agent_tools.execute_tool("tool_portfolio_risk_audit", {})
    assert res["success"] is True
    data = res["result"]
    assert "total_portfolio_equity_usdt" in data
    assert data["total_portfolio_equity_usdt"] > 0
    assert "var_metrics" in data
    assert "daily_var_95_usdt" in data["var_metrics"]
    assert "daily_var_99_usdt" in data["var_metrics"]
    assert "risk_status" in data

@pytest.mark.asyncio
async def test_tool_swarm_defense_execution():
    res = await agent_tools.execute_tool("tool_run_swarm_defense", {
        "symbol": "BTCUSDT",
        "side": "buy",
        "size": 0.1,
        "leverage": 3,
        "prompt": "Safe swing trade on BTC"
    })
    assert res["success"] is True
    data = res["result"]
    assert data["verdict"] in ("APPROVED_EXECUTION", "ADVISORY_CAUTION", "INTERCEPTED_BLOCK")
    assert "sub_agents" in data
    assert len(data["sub_agents"]) == 7
    assert "quant_analyst" in data["sub_agents"]
    assert "strategy_backtester" in data["sub_agents"]

@pytest.mark.asyncio
async def test_tool_twap_execution():
    res = await agent_tools.execute_tool("tool_execute_twap", {
        "symbol": "SOLUSDT",
        "side": "buy",
        "total_size": 3.0,
        "tranches": 3,
        "interval_sec": 1
    })
    assert res["success"] is True
    data = res["result"]
    assert data["status"] == "TWAP_ACTIVE"
    assert data["tranches_count"] == 3
    assert len(data["schedule"]) == 3
    assert data["schedule"][0]["status"] == "FILLED"

# -------------------------------------------------------------
# 2. Multi-Agent Swarm Deliberation Arena Tests
# -------------------------------------------------------------

@pytest.mark.asyncio
async def test_swarm_deliberation_arena():
    debate = await swarm_arena.deliberate(symbol="SOLUSDT", requested_leverage=10, requested_size=20.0)
    assert debate["symbol"] == "SOLUSDT"
    assert "transcript" in debate
    assert len(debate["transcript"]) == 4

    speakers = [s["speaker"] for s in debate["transcript"]]
    assert any("AlphaConductor" in sp for sp in speakers)
    assert any("Alpha Strategist" in sp for sp in speakers)
    assert any("Risk Sentinel" in sp for sp in speakers)
    assert any("Execution Guardian" in sp for sp in speakers)

    assert "consensus_status" in debate
    assert debate["recommended_leverage"] <= debate["original_leverage"]
    assert "proposed_plan" in debate

# -------------------------------------------------------------
# 3. Autonomous ReAct Agent Loop Tests
# -------------------------------------------------------------

@pytest.mark.asyncio
async def test_react_engine_trade_goal():
    goal = "I want to buy 15 SOL with 5x leverage at market price"
    result = await autonomous_react_engine.execute_goal(goal)

    assert result["status"] == "COMPLETED"
    assert result["execution_mode"] == "AUTONOMOUS_REACT_LOOP"
    assert result["route"] == "AUTONOMOUS_TRADE_REACT"
    assert "trace" in result
    assert len(result["trace"]) >= 4

    # Check that trace has THOUGHT, TOOL_CALL, and OBSERVATION steps
    step_types = [s["type"] for s in result["trace"]]
    assert "THOUGHT" in step_types
    assert "TOOL_CALL" in step_types
    assert "OBSERVATION" in step_types
    assert "final_decision" in result

@pytest.mark.asyncio
async def test_react_engine_market_scan_goal():
    goal = "Scan the market for the top momentum asset on Bitget"
    result = await autonomous_react_engine.execute_goal(goal)

    assert result["status"] == "COMPLETED"
    assert result["route"] == "MARKET_SCANNER"
    assert "scan_data" in result
    assert "swarm_defense" in result
    assert len(result["trace"]) >= 3

@pytest.mark.asyncio
async def test_react_engine_portfolio_audit_goal():
    goal = "Audit my portfolio risk and calculate my daily Value at Risk"
    result = await autonomous_react_engine.execute_goal(goal)

    assert result["status"] == "COMPLETED"
    assert result["route"] == "PORTFOLIO_AUDIT"
    assert "final_decision" in result
    assert "audit_data" in result["final_decision"]
    assert len(result["trace"]) >= 3

# -------------------------------------------------------------
# 4. FastAPI Endpoints Integration Tests
# -------------------------------------------------------------

def test_api_agentic_loop_endpoint():
    resp = client.post("/api/alphaind/agentic", json={"goal": "Scan the market for high alpha coins"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "COMPLETED"
    assert "trace" in data

def test_api_debate_endpoint():
    resp = client.post("/api/alphaind/debate", json={"symbol": "BTCUSDT", "leverage": 4, "size": 0.2})
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "BTCUSDT"
    assert "transcript" in data
    assert "consensus_status" in data

def test_api_scanner_endpoint():
    resp = client.post("/api/alphaind/scanner", json={"filter_by": "momentum", "top_n": 3})
    assert resp.status_code == 200
    data = resp.json()
    assert "top_candidates" in data
    assert len(data["top_candidates"]) <= 3

def test_api_portfolio_audit_endpoint():
    resp = client.post("/api/alphaind/portfolio/audit")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_portfolio_equity_usdt" in data
    assert "var_metrics" in data

def test_api_twap_endpoint():
    resp = client.post("/api/alphaind/twap", json={
        "symbol": "BTCUSDT",
        "side": "buy",
        "total_size": 0.3,
        "tranches": 3,
        "interval_sec": 1
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "TWAP_ACTIVE"
    assert len(data["schedule"]) == 3

def test_api_tools_list_endpoint():
    resp = client.get("/api/alphaind/tools")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 9
    assert len(data["tools"]) >= 9
