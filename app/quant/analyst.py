import math
from typing import Dict, List, Any, Tuple
import numpy as np
import pandas as pd

class QuantAnalyst:
    """
    Industrial-grade Quantitative Analysis Engine for Bitget Trading Desk.
    Computes statistical factors, regime detection, Hurst exponent, and volatility modeling.
    """

    @staticmethod
    def calculate_hurst_exponent(prices: np.ndarray, max_lags: int = 20) -> float:
        """
        Calculate Hurst Exponent (H) via Rescaled Range (R/S) analysis.
        H < 0.5: Mean-reverting / anti-persistent
        H = 0.5: Random walk (geometric brownian motion)
        H > 0.5: Trending / persistent series
        """
        if len(prices) < max_lags * 2:
            return 0.50

        lags = range(2, max_lags)
        tau = [np.std(np.subtract(prices[lag:], prices[:-lag])) for lag in lags]
        
        # Filter out zero variance
        valid_indices = [i for i, t in enumerate(tau) if t > 1e-8]
        if len(valid_indices) < 3:
            return 0.50

        log_lags = [np.log(lags[i]) for i in valid_indices]
        log_tau = [np.log(tau[i]) for i in valid_indices]

        # Linear regression slope = Hurst exponent
        poly = np.polyfit(log_lags, log_tau, 1)
        h = float(poly[0])
        return round(float(np.clip(h, 0.05, 0.95)), 3)

    @classmethod
    def analyze_candles(cls, candles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate full quantitative feature matrix from candle series.
        """
        if not candles or len(candles) < 20:
            return cls._empty_quant_metrics()

        df = pd.DataFrame(candles)
        df["close"] = df["close"].astype(float)
        df["open"] = df["open"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        df["volume"] = df["volume"].astype(float)

        close = df["close"]
        high = df["high"]
        low = df["low"]

        # 1. Moving Averages
        sma_20 = close.rolling(window=20).mean()
        sma_50 = close.rolling(window=50).mean() if len(df) >= 50 else sma_20
        std_20 = close.rolling(window=20).std()

        # 2. Bollinger Bands
        upper_bb = sma_20 + (2.0 * std_20)
        lower_bb = sma_20 - (2.0 * std_20)
        curr_close = float(close.iloc[-1])
        curr_sma20 = float(sma_20.iloc[-1])
        curr_upper = float(upper_bb.iloc[-1])
        curr_lower = float(lower_bb.iloc[-1])
        curr_std = float(std_20.iloc[-1]) if std_20.iloc[-1] > 0 else 1.0

        bb_pct_b = (curr_close - curr_lower) / (curr_upper - curr_lower) if (curr_upper - curr_lower) > 0 else 0.5
        bb_bandwidth = ((curr_upper - curr_lower) / curr_sma20) * 100 if curr_sma20 > 0 else 0.0
        z_score = (curr_close - curr_sma20) / curr_std

        # 3. RSI (Relative Strength Index - 14)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss.replace(0, 1e-9))
        rsi_series = 100 - (100 / (1 + rs))
        curr_rsi = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else 50.0

        # 4. MACD (12, 26, 9)
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        macd = ema_12 - ema_26
        macd_signal = macd.ewm(span=9, adjust=False).mean()
        macd_hist = macd - macd_signal

        curr_macd = float(macd.iloc[-1])
        curr_signal = float(macd_signal.iloc[-1])
        curr_hist = float(macd_hist.iloc[-1])

        # 5. Average True Range (ATR 14)
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr_14 = tr.rolling(window=14).mean()
        curr_atr = float(atr_14.iloc[-1]) if not pd.isna(atr_14.iloc[-1]) else float(high.iloc[-1] - low.iloc[-1])
        atr_pct = (curr_atr / curr_close) * 100

        # 6. Realized Volatility & Parkinson Volatility
        returns = close.pct_change().dropna()
        realized_vol_daily = float(returns.std())
        annualized_vol = realized_vol_daily * math.sqrt(365 * 24) * 100  # for hourly data

        # Parkinson Volatility (High/Low estimator - more efficient than close-to-close)
        safe_low = np.maximum(low, 1e-9)
        safe_high = np.maximum(high, safe_low)
        hl_ratio = np.log(safe_high / safe_low) ** 2
        mean_hl = hl_ratio.rolling(window=20).mean().iloc[-1]
        if pd.isna(mean_hl) or mean_hl < 0:
            parkinson_vol = annualized_vol
        else:
            parkinson_vol = math.sqrt(max(0.0, (1.0 / (4.0 * math.log(2))) * mean_hl)) * math.sqrt(365 * 24) * 100

        # 7. Hurst Exponent
        hurst = cls.calculate_hurst_exponent(close.values[-60:] if len(close) >= 60 else close.values)

        # 8. Market Regime Classification
        regime = cls._classify_regime(curr_close, curr_sma20, float(sma_50.iloc[-1]), hurst, annualized_vol, bb_bandwidth)

        # 9. Composite Alpha Score (-1.0 to +1.0)
        alpha_score = cls._compute_alpha_score(curr_rsi, curr_hist, z_score, hurst, regime)

        return {
            "current_price": round(curr_close, 2),
            "sma_20": round(curr_sma20, 2),
            "sma_50": round(float(sma_50.iloc[-1]), 2),
            "bollinger_upper": round(curr_upper, 2),
            "bollinger_lower": round(curr_lower, 2),
            "bollinger_pct_b": round(bb_pct_b, 3),
            "bollinger_bandwidth": round(bb_bandwidth, 2),
            "z_score": round(z_score, 2),
            "rsi": round(curr_rsi, 1),
            "macd": round(curr_macd, 3),
            "macd_signal": round(curr_signal, 3),
            "macd_hist": round(curr_hist, 3),
            "atr": round(curr_atr, 2),
            "atr_pct": round(atr_pct, 2),
            "annualized_volatility": round(annualized_vol, 1),
            "parkinson_volatility": round(parkinson_vol, 1),
            "hurst_exponent": hurst,
            "market_regime": regime,
            "composite_alpha_score": round(alpha_score, 2),
            "recommended_stance": "STRONG BUY" if alpha_score > 0.5 else ("BUY" if alpha_score > 0.15 else ("STRONG SELL" if alpha_score < -0.5 else ("SELL" if alpha_score < -0.15 else "NEUTRAL")))
        }

    @staticmethod
    def _classify_regime(price: float, sma20: float, sma50: float, hurst: float, vol: float, bandwidth: float) -> str:
        """Classify dynamic quantitative regime."""
        if vol > 80.0 or bandwidth > 12.0:
            return "High Volatility Breakout/Shock"
        elif hurst > 0.56:
            if price > sma20 and sma20 > sma50:
                return "Strong Trend Persistence (Bullish)"
            elif price < sma20 and sma20 < sma50:
                return "Strong Trend Persistence (Bearish)"
            else:
                return "Trending Momentum"
        elif hurst < 0.46:
            return "Mean-Reverting Range-Bound"
        else:
            return "Neutral Brownian Walk"

    @staticmethod
    def _compute_alpha_score(rsi: float, macd_hist: float, z: float, hurst: float, regime: str) -> float:
        """Compute institutional alpha score from -1.0 to +1.0."""
        score = 0.0

        if "Mean-Reverting" in regime or hurst < 0.48:
            # Mean-reversion signals
            if z < -1.8 or rsi < 32:
                score += 0.65
            elif z > 1.8 or rsi > 68:
                score -= 0.65
            else:
                score -= (z * 0.2)
        else:
            # Trend-following signals
            if macd_hist > 0:
                score += 0.35
            else:
                score -= 0.35

            if rsi > 52 and rsi < 70:
                score += 0.30
            elif rsi < 48 and rsi > 30:
                score -= 0.30

        return float(np.clip(score, -1.0, 1.0))

    @staticmethod
    def _empty_quant_metrics() -> Dict[str, Any]:
        return {
            "current_price": 0.0,
            "rsi": 50.0,
            "macd": 0.0,
            "macd_signal": 0.0,
            "macd_hist": 0.0,
            "z_score": 0.0,
            "atr": 0.0,
            "atr_pct": 0.0,
            "annualized_volatility": 0.0,
            "parkinson_volatility": 0.0,
            "hurst_exponent": 0.50,
            "market_regime": "Neutral Brownian Walk",
            "composite_alpha_score": 0.0,
            "recommended_stance": "NEUTRAL"
        }
