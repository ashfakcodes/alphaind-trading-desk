import pytest
from fastapi.testclient import TestClient

from run import app
from app.agents.tools import agent_tools
from app.agents.swarm_deliberation import swarm_arena
from app.agents.orchestrator import AlphaOrchestrator

client = TestClient(app)

@pytest.mark.asyncio
async def test_debate_swarm_btc_derisking():
    """Test Swarm Deliberation derisks high-leverage BTC request and computes bracket plan."""
    debate = await swarm_arena.deliberate(
        symbol="BTCUSDT",
        requested_leverage=10,
        requested_size=0.1
    )
    assert debate["symbol"] == "BTCUSDT"
    assert debate["original_leverage"] == 10
    assert debate["recommended_leverage"] <= 3  # Execution Guardian must cap high leverage
    assert "transcript" in debate
    assert len(debate["transcript"]) == 4

    plan = debate["proposed_plan"]
    assert plan["symbol"] == "BTCUSDT"
    assert plan["action"] == "BUY"
    assert plan["leverage"] <= 3
    assert plan["target_tp"] > plan["current_price"]
    assert plan["stop_loss"] < plan["current_price"]
    assert "liquidation_buffer" in plan
    assert plan["notional_usdt"] > 0

@pytest.mark.asyncio
async def test_debate_swarm_unleveraged_spot():
    """Test Swarm Deliberation handles 1x/spot leverage cleanly without 0.00 liquidation artifacts."""
    debate = await swarm_arena.deliberate(
        symbol="NVDAUSDT",
        requested_leverage=1,
        requested_size=10.0
    )
    assert debate["symbol"] == "NVDAUSDT"
    assert debate["recommended_leverage"] == 1
    
    # Bear speech should handle 1x gracefully
    bear_speech = next(s["statement"] for s in debate["transcript"] if "Risk Sentinel" in s["speaker"])
    assert "$0.00" not in bear_speech
    assert "Unleveraged structure protects from liquidation" in bear_speech

@pytest.mark.asyncio
async def test_debate_swarm_default_sizing():
    """Test Swarm Deliberation dynamically uses coin-appropriate default sizes when unspecified."""
    debate_sol = await swarm_arena.deliberate(
        symbol="SOLUSDT",
        requested_leverage=3,
        requested_size=None
    )
    assert debate_sol["proposed_plan"]["size"] == 10.0  # DEFAULT_SIZES for SOL

    debate_btc = await swarm_arena.deliberate(
        symbol="BTCUSDT",
        requested_leverage=2,
        requested_size=None
    )
    assert debate_btc["proposed_plan"]["size"] == 0.1  # DEFAULT_SIZES for BTC

@pytest.mark.asyncio
async def test_tool_swarm_debate_registered_and_executable():
    """Test tool_swarm_debate is properly registered in agent_tools and can be called via tool loop."""
    tools = agent_tools.list_tools()
    tool_names = [t["name"] for t in tools]
    assert "tool_swarm_debate" in tool_names

    res = await agent_tools.execute_tool("tool_swarm_debate", {
        "symbol": "ETHUSDT",
        "leverage": 5,
        "size": 1.0,
        "prompt": "Evaluate ETH breakout viability"
    })
    assert res["success"] is True
    data = res["result"]
    assert data["symbol"] == "ETHUSDT"
    assert "transcript" in data
    assert len(data["transcript"]) == 4
    assert data["consensus_status"] in ["CONSENSUS_RECONCILED", "CONDITIONAL_APPROVAL", "CONDITIONAL_APPROVAL_DERISKED"]

def test_debate_api_endpoint():
    """Test POST /api/alphaind/debate returns 200 with full consensus structure."""
    response = client.post("/api/alphaind/debate", json={
        "symbol": "SOLUSDT",
        "leverage": 5,
        "size": 10.0,
        "prompt": "Test arena deliberation"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "SOLUSDT"
    assert "transcript" in data
    assert len(data["transcript"]) == 4
    assert "consensus_status" in data
    assert "proposed_plan" in data
    assert "latency_ms" in data
    assert data["latency_ms"] > 0

@pytest.mark.asyncio
async def test_orchestrator_nl_debate_routing():
    """Test AlphaOrchestrator routes natural language debate queries to the Swarm Arena."""
    result = await AlphaOrchestrator.process_natural_language_request("debate BTC at 5x")
    assert "debate" in result
    debate = result["debate"]
    assert debate["symbol"] == "BTCUSDT"
    assert "transcript" in debate
    assert len(debate["transcript"]) == 4
    assert "research_brief" in result
    assert result["orchestrator"]["parsed_intent"]["is_debate"] is True

@pytest.mark.asyncio
async def test_orchestrator_trade_thesis_triggers_debate():
    """Test that when a trader sends a trade thesis via Research Thesis, the Swarm Arena debates it."""
    thesis = "Long 25 NVDA at 5x on Saturday"
    result = await AlphaOrchestrator.process_natural_language_request(thesis)
    assert "debate" in result
    debate = result["debate"]
    assert debate["symbol"] == "NVDAUSDT"
    assert "transcript" in debate
    assert len(debate["transcript"]) == 4
    assert debate["raw_prompt"] == thesis
    assert "proposed_plan" in debate
    # Verify Conductor intro explicitly references the user's thesis
    conductor_speech = next(s["statement"] for s in debate["transcript"] if "AlphaConductor" in s["speaker"])
    assert thesis in conductor_speech
