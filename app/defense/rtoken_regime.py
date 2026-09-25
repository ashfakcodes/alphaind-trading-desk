import datetime
from zoneinfo import ZoneInfo
from typing import Dict, Any

class RTokenRegimeDetector:
    """
    7x24 Tokenized US Equities (rToken) & Market-Hours Regime Sentinel.
    Evaluates whether an asset is a tokenized US equity (NVDA, TSLA, AAPL, COIN, SPY, etc.)
    and detects the current US market trading session to compute off-hours liquidity penalties,
    spread multipliers, and weekend macro gap risk.
    """

    SUPPORTED_RTOKENS = {
        "NVDAUSDT": {"name": "NVIDIA Corp (rToken)", "ticker": "NVDA", "nav_baseline": 138.50},
        "TSLAUSDT": {"name": "Tesla Inc (rToken)", "ticker": "TSLA", "nav_baseline": 242.00},
        "AAPLUSDT": {"name": "Apple Inc (rToken)", "ticker": "AAPL", "nav_baseline": 228.00},
        "COINUSDT": {"name": "Coinbase Global (rToken)", "ticker": "COIN", "nav_baseline": 315.00},
        "SPYUSDT":  {"name": "S&P 500 ETF (rToken)", "ticker": "SPY", "nav_baseline": 585.00},
        "MSFTUSDT": {"name": "Microsoft Corp (rToken)", "ticker": "MSFT", "nav_baseline": 420.00}
    }

    @classmethod
    def is_rtoken(cls, symbol: str) -> bool:
        sym = symbol.upper()
        return sym in cls.SUPPORTED_RTOKENS or any(t in sym for t in ["NVDA", "TSLA", "AAPL", "COIN", "SPY", "MSFT"])

    @classmethod
    def get_market_session(cls) -> Dict[str, Any]:
        """Compute live US Stock Market session in Eastern Time."""
        try:
            now_est = datetime.datetime.now(ZoneInfo("America/New_York"))
        except Exception:
            # Fallback for systems without tzdata: UTC - 4 hours (EDT approx)
            now_utc = datetime.datetime.now(datetime.timezone.utc)
            now_est = now_utc - datetime.timedelta(hours=4)

        weekday = now_est.weekday()  # 0=Mon, 4=Fri, 5=Sat, 6=Sun
        hour = now_est.hour
        minute = now_est.minute
        time_minutes = hour * 60 + minute

        # Market times in minutes from midnight
        mkt_open = 9 * 60 + 30   # 09:30 EST
        mkt_close = 16 * 60       # 16:00 EST
        pre_mkt_open = 4 * 60     # 04:00 EST
        after_mkt_close = 20 * 60 # 20:00 EST

        if weekday in (5, 6) or (weekday == 4 and time_minutes >= after_mkt_close) or (weekday == 0 and time_minutes < pre_mkt_open):
            session = "WEEKEND_CLOSED"
            session_name = "Weekend Market Closure (7×24 rToken Active)"
            is_regular = False
            spread_mult = 2.8
            gap_risk = "HIGH"
            advisory = "US traditional exchanges are closed until Monday 09:30 EST. 7×24 rToken trades on-chain with wider spreads and weekend macro gap risk."
        elif time_minutes < pre_mkt_open:
            session = "OVERNIGHT_CLOSED"
            session_name = "Overnight Window (7×24 rToken Active)"
            is_regular = False
            spread_mult = 2.2
            gap_risk = "MODERATE"
            advisory = "Overnight off-hours: spreads are wider than regular session. Orderbook depth is reduced."
        elif time_minutes < mkt_open:
            session = "PRE_MARKET"
            session_name = "US Pre-Market Session"
            is_regular = False
            spread_mult = 1.6
            gap_risk = "MODERATE"
            advisory = "US Pre-market active. Spreads tightening as institutional liquidity enters."
        elif time_minutes <= mkt_close:
            session = "REGULAR_HOURS"
            session_name = "Regular US Trading Session (NYSE/NASDAQ OPEN)"
            is_regular = True
            spread_mult = 1.0
            gap_risk = "LOW"
            advisory = "Primary US equity markets are open. Deep institutional liquidity and minimal slippage."
        else:
            session = "AFTER_HOURS"
            session_name = "US After-Hours Session"
            is_regular = False
            spread_mult = 1.8
            gap_risk = "MODERATE"
            advisory = "After-hours session active. Watch out for earnings releases and post-market volatility."

        return {
            "session": session,
            "session_name": session_name,
            "is_regular_market_hours": is_regular,
            "eastern_time": now_est.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "spread_multiplier": spread_mult,
            "weekend_gap_risk": gap_risk,
            "advisory": advisory
        }

    @classmethod
    def audit_rtoken_trade(cls, symbol: str, leverage: int, size: float) -> Dict[str, Any]:
        symbol = symbol.upper()
        is_rk = cls.is_rtoken(symbol)
        session_info = cls.get_market_session()

        if not is_rk:
            return {
                "is_rtoken": False,
                "asset_class": "CRYPTO_ASSET",
                "session_info": session_info
            }

        rk_info = cls.SUPPORTED_RTOKENS.get(symbol, {
            "name": f"{symbol.replace('USDT', '')} (rToken)",
            "ticker": symbol.replace('USDT', ''),
            "nav_baseline": 150.0
        })

        flags = []
        is_off_hours = not session_info["is_regular_market_hours"]

        if is_off_hours:
            flags.append(f"7×24 rToken Off-Hours Window: Spreads are ~{session_info['spread_multiplier']}x wider than NYSE regular hours.")
            if session_info["session"] == "WEEKEND_CLOSED":
                flags.append("Weekend Gap Risk: Holding unhedged leveraged positions over the weekend exposes trade to Sunday night / Monday opening gaps.")

        if leverage > 5 and is_off_hours:
            flags.append(f"High Leverage ({leverage}x) in Off-Hours: Vulnerable to sudden orderbook slippage sweeps.")

        # Max safe leverage prescription
        if session_info["session"] == "WEEKEND_CLOSED":
            suggested_max_leverage = 2
        elif session_info["session"] == "OVERNIGHT_CLOSED":
            suggested_max_leverage = 2
        elif session_info["session"] in ("PRE_MARKET", "AFTER_HOURS"):
            suggested_max_leverage = 3
        else:
            suggested_max_leverage = 5

        # Approximate NAV premium / discount estimation (S2 thesis language)
        nav_base = rk_info.get("nav_baseline", 150.0)
        nav_deviation_pct = 0.28 if is_off_hours else 0.05
        nav_note = f"Estimated rToken tracking basis: ~{nav_deviation_pct:+.2f}% vs underlying cash NAV (${nav_base:.2f})."

        comparison_note = (
            f"US cash {rk_info['ticker']} is closed; on-chain {symbol} still trades 7×24 — "
            f"beware gap risk into Monday 09:30 ET open."
            if is_off_hours
            else f"US cash {rk_info['ticker']} and on-chain {symbol} are in full continuous alignment."
        )

        weekend_banner_required = is_off_hours and leverage > suggested_max_leverage
        risk_score = 45 if is_off_hours and leverage > suggested_max_leverage else (25 if is_off_hours else 10)

        return {
            "is_rtoken": True,
            "asset_class": "TOKENIZED_US_EQUITY",
            "token_info": rk_info,
            "session_info": session_info,
            "spread_multiplier": session_info["spread_multiplier"],
            "suggested_max_leverage": suggested_max_leverage,
            "nav_note": nav_note,
            "comparison_note": comparison_note,
            "weekend_banner_required": weekend_banner_required,
            "risk_score": risk_score,
            "flags": flags,
            "human_summary": f"{rk_info['name']} under {session_info['session_name']} (Spread mult: {session_info['spread_multiplier']}x, Max Safe Lev: {suggested_max_leverage}x)"
        }

rtoken_regime_detector = RTokenRegimeDetector()

