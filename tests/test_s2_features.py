import pytest
from app.agents.orchestrator import alpha_orchestrator
from app.quant.stress_tester import stress_tester
from app.services.bitget_signal import bitget_signal_service
from app.defense.rtoken_regime import rtoken_regime_detector

@pytest.mark.asyncio
async def test_rtoken_intent_parsing_and_regime():
    # Test rToken intent parsing
    intent_nvda = alpha_orchestrator._parse_intent("I want to buy 25 NVDA with 5x leverage")
    assert intent_nvda["symbol"] == "NVDAUSDT"
    assert intent_nvda["side"] == "buy"
    assert intent_nvda["size"] == 25.0
    assert intent_nvda["leverage"] == 5

    intent_tsla = alpha_orchestrator._parse_intent("Short 10 TSLA with 3x leverage")
    assert intent_tsla["symbol"] == "TSLAUSDT"
    assert intent_tsla["side"] == "sell"
    assert intent_tsla["size"] == 10.0

    # Test rToken regime detector
    assert rtoken_regime_detector.is_rtoken("NVDAUSDT")
    assert rtoken_regime_detector.is_rtoken("TSLAUSDT")
    assert not rtoken_regime_detector.is_rtoken("BTCUSDT")

    audit = rtoken_regime_detector.audit_rtoken_trade("NVDAUSDT", leverage=5, size=25.0)
    assert audit["is_rtoken"] is True
    assert "session_info" in audit
    assert "spread_multiplier" in audit
    assert audit["session_info"]["session"] in ("REGULAR_HOURS", "PRE_MARKET", "AFTER_HOURS", "WEEKEND_CLOSED", "OVERNIGHT_CLOSED")

def test_stress_tester_scenarios():
    intent = {
        "symbol": "BTCUSDT",
        "side": "buy",
        "size": 0.5,
        "leverage": 10,
        "notional_usdt": 46225.0
    }
    result = stress_tester.evaluate(intent, current_price=92450.0)

    assert result["symbol"] == "BTCUSDT"
    assert result["leverage"] == 10
    assert len(result["scenarios"]) == 4

    # 10x leverage has 9% liquidation buffer -> should fail COVID (-33.5%) and FTX (-24.5%)
    assert result["liquidation_buffer_pct"] == 9.0
    assert result["resilience_rating"] == "FRAGILE / HIGH LEVERAGE"
    assert not result["survived_all"]

    # Conservative 2x leverage should survive scenarios
    intent_safe = {
        "symbol": "BTCUSDT",
        "side": "buy",
        "size": 0.1,
        "leverage": 2,
        "notional_usdt": 9245.0
    }
    result_safe = stress_tester.evaluate(intent_safe, current_price=92450.0)
    assert result_safe["liquidation_buffer_pct"] == 45.0
    assert result_safe["survived_all"] is True
    assert result_safe["resilience_rating"] == "HIGHLY RESILIENT"

def test_bitget_signal_perception_layer():
    signals = bitget_signal_service.get_live_signals("NVDAUSDT")
    assert "skills" in signals
    skills = signals["skills"]

    assert "sentiment_analyst" in skills
    assert "fear_and_greed" in skills["sentiment_analyst"]
    assert "long_short_ratio" in skills["sentiment_analyst"]

    assert "macro_analyst" in skills
    assert "dxy_index" in skills["macro_analyst"]
    assert "macro_regime" in skills["macro_analyst"]

    assert "market_intel" in skills
    assert "etf_net_inflows_24h" in skills["market_intel"]

    assert "technical_analysis" in skills
    assert "rsi" in skills["technical_analysis"]

    assert "news_briefing" in skills
    assert "catalysts" in skills["news_briefing"]

@pytest.mark.asyncio
async def test_full_orchestration_with_rtoken_and_prescription():
    # Prompt with high leverage rToken trade
    prompt = "I want to buy 25 NVDA with 15x leverage on Saturday"
    res = await alpha_orchestrator.process_natural_language_request(prompt)

    assert res["orchestrator"]["status"] == "COMPLETED"
    assert "rtoken_regime" in res
    assert res["rtoken_regime"]["is_rtoken"] is True
    assert "stress_test" in res
    assert "safe_prescription" in res

    # High leverage should trigger safe prescription
    prescription = res["safe_prescription"]
    assert prescription is not None
    assert prescription["active"] is True
    assert prescription["safe_leverage"] < prescription["original_leverage"]
    assert "TWAP" in prescription["execution_mode"] or "Slippage" in prescription["execution_mode"]
    assert prescription["risk_reduction_pct"] > 0
