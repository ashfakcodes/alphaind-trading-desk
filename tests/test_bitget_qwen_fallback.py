import pytest
import requests
from unittest.mock import patch, MagicMock
from app.config import settings
from app.services.bitget_qwen_client import bitget_qwen_client, BitgetQwenClient
from app.services.openrouter_client import openrouter_client, OpenRouterClient

def test_config_loaded_from_toml():
    """Verify DeskConfig correctly ingested settings from config.toml."""
    assert settings.FALLBACK_MODEL_PROVIDER == "bitget-qwen"
    assert settings.BITGET_QWEN_MODEL == "qwen3.8-max"
    assert settings.BITGET_QWEN_NAME == "Bitget Qwen"
    assert settings.BITGET_QWEN_BASE_URL == "https://hackathon.bitgetops.com/v1"
    assert settings.BITGET_QWEN_WIRE_API == "responses"
    assert settings.BITGET_QWEN_ENV_KEY == "BITGET_QWEN_API_KEY"

def test_bitget_qwen_client_is_configured():
    """Verify bitget_qwen_client recognizes active API credentials."""
    assert bitget_qwen_client.is_configured() is True
    assert bitget_qwen_client.model == "qwen3.8-max"
    assert bitget_qwen_client.wire_api == "responses"

def test_openrouter_client_fallback_status():
    """Verify openrouter_client detects the fallback client as active."""
    assert openrouter_client.is_fallback_configured() is True
    assert openrouter_client.get_active_provider() in ("openrouter", "bitget-qwen")

def test_bitget_qwen_responses_api_intent_parsing():
    """Verify bitget_qwen_client parses natural language trading intents via /responses."""
    client = BitgetQwenClient()
    intent = client.parse_trading_intent("buy 50 dollars worth of SOL with 3x leverage")
    assert intent is not None
    assert intent["symbol"] == "SOLUSDT"
    assert intent["side"] == "buy"
    assert intent["dollar_amount"] == 50.0
    assert intent["leverage"] == 3
    assert intent["market_type"] == "perp"
    assert intent["parser_mode"] == "LLM_BITGET_QWEN"

def test_bitget_qwen_threat_synthesis():
    """Verify bitget_qwen_client pre-trade threat review generation."""
    client = BitgetQwenClient()
    trade_details = {
        "symbol": "BTCUSDT",
        "side": "buy",
        "size": 0.1,
        "notional_usdt": 8500.0,
        "is_spot": True,
        "leverage": 1
    }
    defense_report = {
        "overall_verdict": "SAFE",
        "composite_risk_score": 10,
        "threat_flags": [],
        "pillars": {
            "volatility_sentinel": {"score": 5, "status": "LOW_VOLATILITY", "summary": "Calm market."},
            "scam_detector": {"score": 0, "status": "CLEAN", "summary": "Verified contract."},
            "contract_security": {"score": 0, "status": "CLEAN", "summary": "Standard spot pair."},
            "liquidity_auditor": {"score": 10, "status": "HIGH_LIQUIDITY", "summary": "Deep book."},
            "psychology_shield": {"score": 0, "status": "RATIONAL", "summary": "Normal trading."},
            "quant_analyst": {"score": 15, "status": "POSITIVE_ALPHA", "summary": "Trend persistent."},
            "strategy_backtester": {"score": 10, "status": "PROFITABLE", "summary": "Historical Sharpe 1.8"}
        }
    }
    review = client.review_pre_trade_threats(trade_details, defense_report)
    assert review is not None
    assert "ai_verdict" in review
    assert "friendly_title" in review
    assert "conversational_explanation" in review

def test_openrouter_failover_to_bitget_qwen():
    """Verify that when OpenRouter fails, OpenRouterClient automatically fails over to Bitget Qwen."""
    # Create client where OpenRouter API key is forced invalid or simulated failure
    test_client = OpenRouterClient(api_key="sk-or-v1-simulated-invalid-key")

    orig_post = requests.post
    with patch("requests.post") as mock_post:
        # Mock OpenRouter request failing with HTTP 500 / 401
        def side_effect(url, **kwargs):
            if "openrouter.ai" in url:
                mock_resp = MagicMock()
                mock_resp.status_code = 500
                mock_resp.text = "Internal Server Error"
                return mock_resp
            # Passthrough to real post for Bitget Qwen
            return orig_post(url, **kwargs)

        mock_post.side_effect = side_effect

        # Call parse_trading_intent on OpenRouterClient
        intent = test_client.parse_trading_intent("buy 25 dollars of BTC on spot")

        # Must have fallen back to Bitget Qwen
        assert intent is not None
        assert intent["symbol"] == "BTCUSDT"
        assert intent["side"] == "buy"
        assert intent["dollar_amount"] == 25.0
        assert intent["parser_mode"] == "LLM_BITGET_QWEN"

def test_cascade_to_deterministic_heuristic_when_all_fail():
    """Verify graceful downgrade to deterministic heuristics when both providers fail."""
    test_client = OpenRouterClient(api_key="invalid", fallback_client=BitgetQwenClient(api_key="invalid"))

    with patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 503
        mock_resp.text = "Service Unavailable"
        mock_post.return_value = mock_resp

        # Should still safely return parsed intent using heuristic rules
        intent = test_client.parse_trading_intent("short 2 ETH with 10x leverage")
        assert intent is not None
        assert intent["symbol"] == "ETHUSDT"
        assert intent["side"] == "sell"
        assert intent["leverage"] == 10
        assert intent["market_type"] == "perp"
