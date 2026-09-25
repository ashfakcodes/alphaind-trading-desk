import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, model_validator

from app.services.bitget_client import bitget_client
from app.services.bitget_oauth import bitget_oauth_service
from app.services.openrouter_client import openrouter_client
from app.quant.analyst import QuantAnalyst
from app.quant.backtester import backtester
from app.agents.orchestrator import alpha_orchestrator
from app.agents.agentic_engine import autonomous_react_engine
from app.agents.swarm_deliberation import swarm_arena
from app.agents.tools import agent_tools
from app.config import settings

logger = logging.getLogger(__name__)
api_router = APIRouter(prefix="/api")

# -------------------------------------------------------------
# Request Models
# -------------------------------------------------------------

class OrchestrationPromptRequest(BaseModel):
    prompt: str = Field(..., description="Natural language trading instruction or research query")

class DirectExecuteRequest(BaseModel):
    symbol: str
    side: str
    size: float
    order_type: str = "market"
    leverage: int = 1
    market_type: Optional[str] = "spot"
    category: Optional[str] = "SPOT"

class ChatPromptRequest(BaseModel):
    query: str = Field(..., description="User question or guidance request")
    symbol: Optional[str] = Field(default="BTCUSDT")

class BacktestRequest(BaseModel):
    symbol: str = Field(default="BTCUSDT")
    strategy_type: str = Field(default="regime_alpha")
    initial_capital: float = Field(default=10000.0)
    stop_loss_pct: float = Field(default=0.025)
    take_profit_pct: float = Field(default=0.06)
    candle_limit: int = Field(default=150)

class AgenticGoalRequest(BaseModel):
    goal: str = Field(..., description="High-level autonomous objective, trade directive, or research goal")

class DebateRequest(BaseModel):
    symbol: str = Field(default="BTCUSDT", description="Target asset to debate")
    leverage: int = Field(default=3, description="Proposed leverage")
    size: float = Field(default=0.5, description="Proposed trade size")
    prompt: Optional[str] = Field(default="", description="Original user prompt or premise")

class ScannerRequest(BaseModel):
    filter_by: str = Field(default="momentum", description="Sorting criteria: 'momentum', 'alpha', 'low_volatility', 'oversold', 'high_volume'")
    top_n: int = Field(default=5, description="Number of results to return")

class TwapExecuteRequest(BaseModel):
    symbol: str
    side: str
    total_size: float
    tranches: int = 3
    interval_sec: int = 2

class BriefExportRequest(BaseModel):
    prompt: Optional[str] = None
    brief_data: Optional[Dict[str, Any]] = None

class DeskProfileUpdateRequest(BaseModel):
    max_leverage: Optional[int] = None
    max_equity_pct_per_trade: Optional[float] = None
    rtoken_weekend_leverage_cap: Optional[int] = None
    tilt_lockout_loss_streak: Optional[int] = None

class TradeReviewRequest(BaseModel):
    order_id: str
    emotion_tag: str = "DISCIPLINED"
    repeat_mistake: bool = False
    notes: Optional[str] = ""

class OAuthStartRequest(BaseModel):
    host_ip: Optional[str] = Field(default="127.0.0.1", description="Client host IP for Bitget callback")
    base_url: Optional[str] = Field(default=None, description="Optional Bitget base URL override")

class OAuthCompleteRequest(BaseModel):
    session_id: str
    data_key: str

class OAuthSyncRequest(BaseModel):
    api_key: Optional[str] = None
    apiKey: Optional[str] = None
    secret_key: Optional[str] = None
    secretKey: Optional[str] = None
    passphrase: Optional[str] = ""
    user_id: Optional[str] = ""
    userId: Optional[str] = ""
    is_simulation: Optional[bool] = False
    isSimulation: Optional[bool] = False
    account_type: Optional[str] = "Bitget Agentic Subaccount"
    accountType: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_keys(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Normalize camelCase to snake_case if snake_case is missing
            if "apiKey" in data and not data.get("api_key"):
                data["api_key"] = data["apiKey"]
            if "secretKey" in data and not data.get("secret_key"):
                data["secret_key"] = data["secretKey"]
            if "userId" in data and not data.get("user_id"):
                data["user_id"] = data["userId"]
            if "accountType" in data and not data.get("account_type"):
                data["account_type"] = data["accountType"]
            if "isSimulation" in data and "is_simulation" not in data:
                data["is_simulation"] = data["isSimulation"]
        return data

# In-memory recent briefs store
_recent_research_briefs = []

# -------------------------------------------------------------
# Alphaind Natural Language Orchestration Endpoint
# -------------------------------------------------------------

@api_router.post("/alphaind/orchestrate")
async def orchestrate_natural_language(req: OrchestrationPromptRequest):
    """
    Main Alphaind Multi-Agent Engine:
    1. Interprets natural language prompt.
    2. Runs 7 Dedicated Defense Pillars in parallel.
    3. Generates structured Research Brief & Safe Execution Prescription.
    """
    if not req.prompt or len(req.prompt.strip()) == 0:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    try:
        report = await alpha_orchestrator.process_natural_language_request(req.prompt)
        if report.get("research_brief"):
            _recent_research_briefs.insert(0, report["research_brief"])
            if len(_recent_research_briefs) > 25:
                _recent_research_briefs.pop()
        return report
    except Exception as e:
        logger.error(f"Orchestration failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/alphaind/research-brief/export")
async def export_research_brief(req: BriefExportRequest):
    """
    Export structured Research Brief to GitHub Flavored Markdown for submission packs and judges.
    """
    from app.defense.research_brief import research_brief_generator
    if req.brief_data:
        md = research_brief_generator.export_to_markdown(req.brief_data)
        return {
            "success": True,
            "markdown": md,
            "filename": f"research_brief_{req.brief_data.get('suggested_ticket', {}).get('symbol', 'desk').lower()}.md"
        }
    elif req.prompt:
        report = await alpha_orchestrator.process_natural_language_request(req.prompt)
        brief = report.get("research_brief", {})
        md = research_brief_generator.export_to_markdown(brief)
        return {
            "success": True,
            "markdown": md,
            "filename": f"research_brief_{brief.get('suggested_ticket', {}).get('symbol', 'desk').lower()}.md"
        }
    else:
        raise HTTPException(status_code=400, detail="Either prompt or brief_data must be provided.")

@api_router.post("/alphaind/execute")
def execute_approved_trade(req: DirectExecuteRequest):
    """
    Execute order on Bitget Desk once approved by human trader.
    Persists fill to paper trade ledger.
    """
    category = req.category or ("SPOT" if req.market_type == "spot" else "USDT-FUTURES")
    result = bitget_client.place_order(
        symbol=req.symbol,
        side=req.side,
        order_type=req.order_type,
        size=req.size,
        category=category,
        leverage=req.leverage
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Execution failed"))

    return {
        "status": "EXECUTED",
        "order": result["order"],
        "message": f"Alphaind dispatched order {result['order']['order_id']} to Bitget Desk."
    }

# -------------------------------------------------------------
# Desk Profile & Post-Trade Journal
# -------------------------------------------------------------

@api_router.get("/desk/profile")
def get_desk_profile():
    """Retrieve trader's personalized risk budget and behavioral rules."""
    return {
        "status": "active",
        "profile": settings.DESK_PROFILE
    }

@api_router.post("/desk/profile")
def update_desk_profile(req: DeskProfileUpdateRequest):
    """Update personalized risk profile parameters."""
    if req.max_leverage is not None:
        settings.DESK_PROFILE["max_leverage"] = max(1, min(50, req.max_leverage))
    if req.max_equity_pct_per_trade is not None:
        settings.DESK_PROFILE["max_equity_pct_per_trade"] = max(1.0, min(100.0, req.max_equity_pct_per_trade))
    if req.rtoken_weekend_leverage_cap is not None:
        settings.DESK_PROFILE["rtoken_weekend_leverage_cap"] = max(1, min(10, req.rtoken_weekend_leverage_cap))
    if req.tilt_lockout_loss_streak is not None:
        settings.DESK_PROFILE["tilt_lockout_loss_streak"] = max(1, min(10, req.tilt_lockout_loss_streak))

    return {
        "status": "updated",
        "profile": settings.DESK_PROFILE
    }

@api_router.get("/desk/journal")
def get_desk_journal():
    """Retrieve recent research briefs and paper trade fills."""
    return {
        "recent_briefs": _recent_research_briefs[:10],
        "recent_trades": bitget_client.get_recent_orders(15)
    }

@api_router.post("/desk/review")
def review_completed_trade(req: TradeReviewRequest):
    """Record post-trade review feedback and emotional state."""
    for t in bitget_client.paper_trades:
        if t.get("order_id") == req.order_id:
            t["emotion_tag"] = req.emotion_tag
            t["repeat_mistake"] = req.repeat_mistake
            t["notes"] = req.notes
            return {"status": "reviewed", "order": t}
    return {"status": "recorded", "order_id": req.order_id}

@api_router.post("/alphaind/chat")
def chat_with_copilot(req: ChatPromptRequest):
    """
    Conversational natural-language advice from Alphaind co-pilot.
    """
    sym = req.symbol or "NVDAUSDT"
    ticker = bitget_client.get_ticker(sym)
    context = {
        "symbol": sym,
        "last_price": ticker.get("last_price"),
        "change_24h": ticker.get("change_24h")
    }
    reply = openrouter_client.chat_copilot(req.query, context)
    return {
        "reply": reply,
        "symbol": sym,
        "model": settings.OPENROUTER_MODEL if openrouter_client.is_configured() else settings.BITGET_QWEN_MODEL,
        "provider": openrouter_client.get_active_provider()
    }

# -------------------------------------------------------------
# Autonomous Goal Router & Tool Execution
# -------------------------------------------------------------

@api_router.post("/alphaind/agentic")
async def execute_agentic_loop(req: AgenticGoalRequest):
    """
    Goal Router & Research Playbook Loop:
    Accepts high-level objectives, routes tools dynamically, and returns structured trace.
    """
    if not req.goal or len(req.goal.strip()) == 0:
        raise HTTPException(status_code=400, detail="Goal cannot be empty.")
    try:
        result = await autonomous_react_engine.execute_goal(req.goal)
        return result
    except Exception as e:
        logger.error(f"Goal loop failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/alphaind/debate")
async def run_swarm_debate(req: DebateRequest):
    """
    Multi-Agent Deliberation Arena:
    Convenes Bullish Strategist, Bearish Risk Sentinel, and Execution Guardian
    to debate the trade thesis.
    """
    try:
        debate = await swarm_arena.deliberate(
            symbol=req.symbol,
            requested_leverage=req.leverage,
            requested_size=req.size,
            raw_prompt=req.prompt or ""
        )
        return debate
    except Exception as e:
        logger.error(f"Swarm debate failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/alphaind/scanner")
async def run_market_scanner(req: ScannerRequest):
    """
    Autonomous Cross-Asset Watchlist Scanner:
    Ranks coins by momentum, composite alpha, Hurst exponent, or oversold RSI.
    """
    res = await agent_tools.execute_tool("tool_market_scanner", {
        "filter_by": req.filter_by,
        "top_n": req.top_n
    })
    return res.get("result", {})

@api_router.post("/alphaind/portfolio/audit")
async def audit_portfolio_risk():
    """
    Autonomous Portfolio Guardian:
    Calculates total equity, cash ratio, Value at Risk (VaR 95/99%), and margin concentration.
    """
    res = await agent_tools.execute_tool("tool_portfolio_risk_audit", {})
    return res.get("result", {})

@api_router.post("/alphaind/twap")
async def execute_twap_order(req: TwapExecuteRequest):
    """
    Algorithmic TWAP Order Dispatcher:
    Slices execution into multiple tranches and executes slices in background.
    """
    res = await agent_tools.execute_tool("tool_execute_twap", {
        "symbol": req.symbol,
        "side": req.side,
        "total_size": req.total_size,
        "tranches": req.tranches,
        "interval_sec": req.interval_sec
    })
    return res.get("result", {})

@api_router.get("/alphaind/tools")
def list_available_agent_tools():
    """List all registered callable tools available to the research workbench."""
    return {
        "count": len(agent_tools.list_tools()),
        "tools": agent_tools.list_tools()
    }

# -------------------------------------------------------------
# Market Telemetry & Watchlist
# -------------------------------------------------------------

@api_router.get("/market/watchlist")
def get_watchlist():
    watchlist_data = []
    for sym in settings.WATCHLIST:
        watchlist_data.append(bitget_client.get_ticker(sym))
    return watchlist_data

@api_router.get("/market/ticker")
def get_ticker(symbol: str = Query("NVDAUSDT")):
    return bitget_client.get_ticker(symbol)

@api_router.get("/market/orderbook")
def get_orderbook(symbol: str = Query("NVDAUSDT"), depth: int = Query(20)):
    return bitget_client.get_orderbook(symbol, depth)

@api_router.get("/quant/analysis")
def get_quant_analysis(symbol: str = Query("NVDAUSDT")):
    candles = bitget_client.get_historical_candles(symbol, "1h", 60)
    return {
        "symbol": symbol,
        "metrics": QuantAnalyst.analyze_candles(candles)
    }

# -------------------------------------------------------------
# Industrial Backtesting Endpoint
# -------------------------------------------------------------

@api_router.post("/quant/backtest")
def run_backtest_simulation(req: BacktestRequest):
    candles = bitget_client.get_historical_candles(req.symbol, "1h", req.candle_limit)
    backtester.initial_capital = req.initial_capital
    backtester.stop_loss_pct = req.stop_loss_pct
    backtester.take_profit_pct = req.take_profit_pct

    return backtester.run_backtest(
        candles=candles,
        strategy_type=req.strategy_type,
        symbol=req.symbol
    )

# -------------------------------------------------------------
# Account Status & Health
# -------------------------------------------------------------

@api_router.get("/account/status")
def get_account_status():
    return {
        "balances": bitget_client.get_account_balances(),
        "recent_orders": bitget_client.get_recent_orders(10),
        "desk_mode": "Bitget Simulation / Paper Desk" if bitget_client.is_simulation else "Bitget Live API",
        "openrouter_configured": openrouter_client.is_configured(),
        "openrouter_model": settings.OPENROUTER_MODEL,
        "fallback_configured": openrouter_client.is_fallback_configured(),
        "fallback_provider": settings.FALLBACK_MODEL_PROVIDER,
        "fallback_model": settings.BITGET_QWEN_MODEL,
        "fallback_wire_api": settings.BITGET_QWEN_WIRE_API,
        "active_provider": openrouter_client.get_active_provider(),
        "desk_profile": settings.DESK_PROFILE,
        "auth_info": bitget_client.get_auth_info()
    }

@api_router.get("/account/debug-balances")
def get_debug_balances():
    return bitget_client.debug_fetch_balances()

@api_router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "project": "Alphaind · Track 3 AI Trading Desk",
        "theme": "Execution Assistance & Decision Stress Testing",
        "architecture": "7 Rule-Based Risk Pillars + LLM Intent & Synthesis",
        "bitget_connected": True,
        "market_data_mode": "Live Bitget v2 Public REST (Cached 3s)",
        "paper_desk_mode": bitget_client.is_simulation,
        "primary_model": settings.BITGET_QWEN_MODEL,
        "openrouter_model": settings.OPENROUTER_MODEL,
        "active_provider": openrouter_client.get_active_provider(),
        "skills_status": {
            "technical_analysis": "LIVE",
            "market_depth_walker": "LIVE",
            "rtoken_regime_sentinel": "LIVE",
            "crisis_stress_tester": "CALCULATED",
            "strategy_backtester": "CALCULATED",
            "news_briefing": "SIMULATED",
            "macro_analyst": "SIMULATED"
        }
    }

# -------------------------------------------------------------
# Bitget Agentic Account OAuth Endpoints
# -------------------------------------------------------------

@api_router.post("/oauth/start")
def start_oauth(req: Optional[OAuthStartRequest] = None):
    """
    Start Bitget Agentic OAuth flow:
    Generates session keypair, starts ephemeral callback server, and returns authorize_url.
    """
    host_ip = req.host_ip if req and req.host_ip else "127.0.0.1"
    base_url = req.base_url if req and req.base_url else None
    return bitget_oauth_service.start_oauth_session(host_ip=host_ip, base_url=base_url)

@api_router.get("/oauth/session-status")
def get_oauth_session_status(session_id: str = Query(..., description="Active OAuth session ID")):
    """Poll status of an active OAuth session."""
    return bitget_oauth_service.get_session_status(session_id)

@api_router.post("/oauth/complete")
def complete_oauth(req: OAuthCompleteRequest):
    """Directly exchange dataKey if received via frontend redirect."""
    res = bitget_oauth_service.exchange_datakey_manually(req.session_id, req.data_key)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "OAuth exchange failed"))
    return res

@api_router.post("/oauth/simulate")
def simulate_oauth_grant():
    """
    Simulated Bitget Agentic OAuth grant for testing and review.
    Executes a verified RSA-2048 split-codec roundtrip.
    """
    return bitget_oauth_service.simulate_mock_oauth_grant()

@api_router.post("/oauth/sync")
def sync_oauth_credentials(req: OAuthSyncRequest):
    """
    Synchronize decrypted credentials with active Bitget desk client.
    Activates live execution and real balance telemetry.
    """
    api_key = (req.api_key or req.apiKey or "").strip()
    secret_key = (req.secret_key or req.secretKey or "").strip()
    passphrase = (req.passphrase or "").strip()
    user_id = (req.user_id or req.userId or "").strip()
    account_type = req.account_type or req.accountType or "Bitget Agentic Subaccount"
    is_sim = req.is_simulation if req.is_simulation is not None else bool(req.isSimulation)

    if not api_key or not secret_key:
        raise HTTPException(
            status_code=400,
            detail="Missing required credentials: both api_key (or apiKey) and secret_key (or secretKey) must be provided."
        )

    bitget_client.set_credentials(
        api_key=api_key,
        api_secret=secret_key,
        passphrase=passphrase,
        is_simulation=is_sim,
        user_id=user_id,
        account_type=account_type
    )
    return {
        "status": "synchronized",
        "auth": bitget_client.get_auth_info(),
        "balances": bitget_client.get_account_balances(),
        "message": "Desk credentials synchronized with authenticated Bitget Agentic Subaccount."
    }

@api_router.post("/oauth/disconnect")
def disconnect_oauth():
    """Disconnect Agentic Subaccount and revert to paper simulation."""
    bitget_client.clear_credentials()
    return {
        "status": "disconnected",
        "auth": bitget_client.get_auth_info(),
        "message": "Desk reverted to simulation / default state."
    }

@api_router.get("/oauth/status")
def get_oauth_status():
    """Query desk authentication state and masked credentials."""
    return {
        "auth": bitget_client.get_auth_info(),
        "desk_mode": "Bitget Agentic Live Subaccount" if (not bitget_client.is_simulation and bitget_client.api_key) else "Simulation Desk"
    }

class ModeSwitchRequest(BaseModel):
    mode: str = Field(..., description="'paper' or 'live'")

@api_router.post("/account/switch-mode")
def switch_account_mode(req: ModeSwitchRequest):
    """Switch desk mode between paper simulation and authenticated live execution."""
    mode = req.mode.lower().strip()
    if mode == "paper":
        bitget_client.is_simulation = True
        return {
            "mode": "paper",
            "is_simulation": True,
            "status": "Paper Simulation Active",
            "balances": bitget_client.get_account_balances(),
            "auth": bitget_client.get_auth_info()
        }
    elif mode == "live":
        if not bitget_client.api_key:
            return {
                "mode": "paper",
                "is_simulation": True,
                "status": "Credentials Required",
                "requires_auth": True,
                "message": "No Bitget credentials active. Please connect via OAuth."
            }
        bitget_client.is_simulation = False
        return {
            "mode": "live",
            "is_simulation": False,
            "status": "Bitget Live Agentic Account Active",
            "balances": bitget_client.get_account_balances(),
            "auth": bitget_client.get_auth_info()
        }
    else:
        raise HTTPException(status_code=400, detail="Invalid mode. Must be 'paper' or 'live'.")


