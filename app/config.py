import os
from pathlib import Path
from dotenv import load_dotenv
import tomllib

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env if present
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

# Load config.toml if present
toml_config = {}
toml_path = BASE_DIR / "config.toml"
if toml_path.exists():
    try:
        with open(toml_path, "rb") as f:
            toml_config = tomllib.load(f)
    except Exception:
        pass

class DeskConfig:
    # Project Base Directory
    BASE_DIR: Path = BASE_DIR

    # OpenRouter API Configuration
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

    # Fallback LLM API: Bitget Qwen Configuration
    _bitget_qwen_toml = toml_config.get("model_providers", {}).get("bitget-qwen", {})
    FALLBACK_MODEL_PROVIDER: str = os.getenv("FALLBACK_MODEL_PROVIDER", toml_config.get("model_provider", "bitget-qwen"))
    BITGET_QWEN_NAME: str = _bitget_qwen_toml.get("name", "Bitget Qwen")
    BITGET_QWEN_MODEL: str = os.getenv("BITGET_QWEN_MODEL", toml_config.get("model", "qwen3.8-max"))
    BITGET_QWEN_BASE_URL: str = os.getenv("BITGET_QWEN_BASE_URL", _bitget_qwen_toml.get("base_url", "https://hackathon.bitgetops.com/v1"))
    BITGET_QWEN_ENV_KEY: str = _bitget_qwen_toml.get("env_key", "BITGET_QWEN_API_KEY")
    BITGET_QWEN_WIRE_API: str = os.getenv("BITGET_QWEN_WIRE_API", _bitget_qwen_toml.get("wire_api", "responses"))
    BITGET_QWEN_API_KEY: str = os.getenv("BITGET_QWEN_API_KEY", "")

    # Bitget API Credentials
    BITGET_API_KEY: str = os.getenv("BITGET_API_KEY", "")
    BITGET_API_SECRET: str = os.getenv("BITGET_API_SECRET", "")
    BITGET_API_PASSPHRASE: str = os.getenv("BITGET_API_PASSPHRASE", "")
    BITGET_IS_SIMULATION: bool = os.getenv("BITGET_IS_SIMULATION", "true").lower() in ("true", "1", "yes")

    # Bitget Base URLs
    BITGET_REST_URL: str = "https://api.bitget.com"
    BITGET_SIMULATION_URL: str = "https://api.bitget.com"

    # Server Settings
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")

    # CORS Settings
    _cors_env: str = os.getenv("CORS_ORIGINS", "*")
    CORS_ORIGINS: list = ["*"] if _cors_env.strip() == "*" else [o.strip() for o in _cors_env.split(",") if o.strip()]

    # Risk & Pre-Trade Defense Thresholds
    MAX_SLIPPAGE_TOLERANCE_PCT: float = float(os.getenv("MAX_SLIPPAGE_TOLERANCE_PCT", "1.5"))
    MAX_LEVERAGE: int = int(os.getenv("MAX_LEVERAGE", "10"))
    MAX_DRAWDOWN_LIMIT_PCT: float = float(os.getenv("MAX_DRAWDOWN_LIMIT_PCT", "10.0"))
    FOMO_SURGE_THRESHOLD_PCT: float = float(os.getenv("FOMO_SURGE_THRESHOLD_PCT", "3.5"))
    REVENGE_TRADING_LOSS_STREAK: int = int(os.getenv("REVENGE_TRADING_LOSS_STREAK", "3"))

    # Trader Desk Profile (Personalized Risk Budget & Behavioral Rules)
    DESK_PROFILE = {
        "user_segment": "$2k–$20k retail trader (3–15x leverage, 7×24 rToken & crypto mix)",
        "max_leverage": int(os.getenv("PROFILE_MAX_LEVERAGE", "10")),
        "max_equity_pct_per_trade": float(os.getenv("PROFILE_MAX_EQUITY_PCT", "25.0")),
        "rtoken_weekend_leverage_cap": int(os.getenv("PROFILE_RTOKEN_WEEKEND_CAP", "2")),
        "tilt_lockout_loss_streak": int(os.getenv("PROFILE_TILT_STREAK", "3")),
        "tilt_lockout_hours": float(os.getenv("PROFILE_TILT_HOURS", "2.0")),
        "theme": "Execution Assistance",
        "supporting_theme": "Decision Stress Testing"
    }

    # Default trading pairs to monitor (7x24 Tokenized US Equities First, Crypto Secondary Sleeve)
    WATCHLIST = [
        "NVDAUSDT",    # 7x24 Tokenized US Stock (NVIDIA)
        "TSLAUSDT",    # 7x24 Tokenized US Stock (Tesla)
        "AAPLUSDT",    # 7x24 Tokenized US Stock (Apple)
        "COINUSDT",    # 7x24 Tokenized US Stock (Coinbase)
        "SPYUSDT",     # 7x24 Tokenized US ETF (S&P 500)
        "MSFTUSDT",    # 7x24 Tokenized US Stock (Microsoft)
        "BTCUSDT",     # Crypto hedge sleeve
        "ETHUSDT",     # Crypto hedge sleeve
        "SOLUSDT",     # High-beta crypto
        "BGBUSDT",     # Bitget native token
        "DOGEUSDT"     # Meme volatility
    ]

    # Model Provider Options (Primary: Bitget Qwen qwen3.8-max, Backup: OpenRouter)
    QWEN_MODEL_NAME: str = os.getenv("QWEN_MODEL_NAME", "qwen3.8-max")
    BITGET_OPS_BASE_URL: str = os.getenv("BITGET_OPS_BASE_URL", "https://hackathon.bitgetops.com/v1")
    MARKET_CACHE_TTL_SEC: float = 3.0

settings = DeskConfig()
