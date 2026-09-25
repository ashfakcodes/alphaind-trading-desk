import pytest
import numpy as np
from app.services.bitget_client import bitget_client
from app.services.openrouter_client import openrouter_client
from app.quant.analyst import QuantAnalyst
from app.quant.backtester import backtester
from app.defense.volatility_sentinel import VolatilitySentinel
from app.defense.fraud_detector import FraudDetector
from app.defense.security_guard import SecurityGuard
from app.defense.liquidity_auditor import LiquidityAuditor
from app.defense.psychology_shield import PsychologyShield
from app.defense.pre_trade_engine import pre_trade_engine

# -------------------------------------------------------------
# 1. Market Data & Bitget Client Tests
# -------------------------------------------------------------

def test_bitget_ticker():
    ticker = bitget_client.get_ticker("BTCUSDT")
    assert ticker["symbol"] == "BTCUSDT"
    assert ticker["last_price"] > 0
    assert ticker["bid_price"] <= ticker["ask_price"]

def test_bitget_orderbook():
    book = bitget_client.get_orderbook("BTCUSDT", depth=10)
    assert len(book["bids"]) == 10
    assert len(book["asks"]) == 10
    assert book["asks"][0][0] >= book["bids"][0][0]

def test_bitget_candles():
    candles = bitget_client.get_historical_candles("BTCUSDT", "1h", limit=50)
    assert len(candles) >= 40 and len(candles) <= 50
    assert "close" in candles[0]
    assert "high" in candles[0]

def test_paper_order_execution():
    was_sim = bitget_client.is_simulation
    bitget_client.is_simulation = True
    try:
        initial_usdt = bitget_client.paper_balance["USDT"]
        res = bitget_client.place_order("BTCUSDT", "buy", "market", 0.05)
        assert res["success"] is True
        assert res["order"]["status"] == "FILLED"
        assert bitget_client.paper_balance["USDT"] < initial_usdt
    finally:
        bitget_client.is_simulation = was_sim

# -------------------------------------------------------------
# 2. Quant Analyst & Hurst Exponent Tests
# -------------------------------------------------------------

def test_hurst_exponent():
    # Random walk
    np.random.seed(1)
    rw = np.cumsum(np.random.normal(0, 1, 100)) + 1000
    h = QuantAnalyst.calculate_hurst_exponent(rw)
    assert 0.05 <= h <= 0.95

def test_quant_analysis_features():
    candles = bitget_client.get_historical_candles("BTCUSDT", "1h", limit=60)
    q = QuantAnalyst.analyze_candles(candles)
    assert "rsi" in q
    assert "bollinger_upper" in q
    assert "bollinger_lower" in q
    assert "market_regime" in q
    assert "composite_alpha_score" in q
    assert -1.0 <= q["composite_alpha_score"] <= 1.0

# -------------------------------------------------------------
# 3. Industrial Backtester Tests
# -------------------------------------------------------------

def test_industrial_backtest_execution():
    candles = bitget_client.get_historical_candles("BTCUSDT", "1h", limit=100)
    results = backtester.run_backtest(candles, strategy_type="regime_alpha", symbol="BTCUSDT")
    assert "summary" in results
    assert "monte_carlo" in results
    assert "equity_curve" in results
    s = results["summary"]
    assert "sharpe_ratio" in s
    assert "max_drawdown_pct" in s
    assert "var_95_pct" in s
    assert s["total_trades"] >= 0

def test_monte_carlo_resampling():
    candles = bitget_client.get_historical_candles("BTCUSDT", "1h", limit=100)
    results = backtester.run_backtest(candles, strategy_type="regime_alpha")
    mc = results["monte_carlo"]
    assert "p95_worst_drawdown_pct" in mc
    assert "ruin_probability_pct" in mc
    assert mc["simulation_runs"] == 500

# -------------------------------------------------------------
# 4. Five-Pillar Pre-Trade Defense Shield Tests
# -------------------------------------------------------------

def test_volatility_sentinel_normal_vs_extreme():
    normal_q = {"annualized_volatility": 40.0, "atr_pct": 1.1, "bollinger_bandwidth": 3.5, "z_score": 0.5}
    res_normal = VolatilitySentinel.evaluate("BTCUSDT", normal_q, {})
    assert res_normal["status"] == "SAFE"

    extreme_q = {"annualized_volatility": 145.0, "atr_pct": 5.5, "bollinger_bandwidth": 18.0, "z_score": 3.2}
    res_extreme = VolatilitySentinel.evaluate("BTCUSDT", extreme_q, {})
    assert res_extreme["status"] in ("WARNING", "DANGER")
    assert res_extreme["score"] > 60

def test_fraud_detector_honeypot_ticker():
    ticker = {"change_24h": 5.0, "volume_24h": 1000000}
    book = {"bids": [[100, 1]], "asks": [[101, 1]]}
    
    # Safe known ticker
    safe_res = FraudDetector.evaluate("BTCUSDT", ticker, book)
    assert safe_res["status"] == "SAFE"

    # Suspicious spoofed / meme token
    scam_res = FraudDetector.evaluate("PEPE100XINU", {"change_24h": 65.0, "volume_24h": 10000}, book)
    assert scam_res["status"] in ("WARNING", "DANGER")
    assert scam_res["score"] > 50

def test_liquidity_auditor_slippage():
    book = {
        "bids": [[100, 0.5], [99, 1.0]],
        "asks": [[101, 0.5], [102, 1.0]]
    }
    # Huge order of 5.0 on book with only 1.5 total depth
    res = LiquidityAuditor.evaluate("TESTUSDT", "buy", 5.0, book, annualized_vol=50.0)
    assert res["score"] > 50
    assert len(res["flags"]) > 0

def test_psychology_shield_fomo_and_revenge():
    normal_q = {"current_price": 100.0, "rsi": 52.0, "z_score": 0.2}
    safe_res = PsychologyShield.evaluate("BTCUSDT", "buy", 0.1, 3, normal_q, [])
    assert safe_res["status"] == "SAFE"

    # Extreme FOMO buying at top + revenge streak
    fomo_q = {"current_price": 100.0, "rsi": 82.0, "z_score": 2.8}
    bad_trades = [
        {"pnl": -50, "size": 0.1, "entry_price": 100},
        {"pnl": -120, "size": 0.1, "entry_price": 100},
        {"pnl": -80, "size": 0.1, "entry_price": 100}
    ]
    tilt_res = PsychologyShield.evaluate("BTCUSDT", "buy", 2.0, 35, fomo_q, bad_trades)
    assert tilt_res["status"] in ("WARNING", "DANGER")
    assert tilt_res["tilt_detected"] is True
    assert "REVENGE_TRADING" in tilt_res["tilt_factors"] or "FOMO_CHASING" in tilt_res["tilt_factors"]

def test_pre_trade_flight_check_master_coordinator():
    order_req = {"symbol": "BTCUSDT", "side": "buy", "size": 0.1, "leverage": 3, "order_type": "market"}
    ticker = bitget_client.get_ticker("BTCUSDT")
    book = bitget_client.get_orderbook("BTCUSDT", 20)
    candles = bitget_client.get_historical_candles("BTCUSDT", "1h", 40)
    quant = QuantAnalyst.analyze_candles(candles)

    report = pre_trade_engine.execute_pre_trade_flight_check(
        order_request=order_req,
        ticker_data=ticker,
        orderbook=book,
        quant_data=quant,
        recent_trades=[],
        portfolio_equity=50000.0
    )

    assert "composite_risk_score" in report
    assert report["overall_verdict"] in ("SAFE", "CAUTION", "BLOCKED")
    assert "pillars" in report
    assert len(report["pillars"]) == 5
    assert "ai_review" in report
