import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from app.api.routes import api_router
from app.config import settings

# Initialize FastAPI App
app = FastAPI(
    title="Alphaind - AI Trading Desk",
    description="Pre-Trade Research Workbench & Execution Assistant for Crypto Perps & 7x24 rTokens",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router)

@app.get("/health")
def root_health():
    """Cloud platform health check endpoint."""
    return {
        "status": "healthy",
        "service": "Alphaind - AI Trading Desk Backend",
        "version": "1.0.0",
        "simulation": settings.BITGET_IS_SIMULATION,
        "primary_model": settings.BITGET_QWEN_MODEL
    }

# Mount Frontend Static Assets
static_dir = Path(__file__).resolve().parent / "frontend"

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    src_dir = static_dir / "src"
    if src_dir.exists():
        app.mount("/src", StaticFiles(directory=str(src_dir)), name="src")
    css_dir = static_dir / "css"
    if css_dir.exists():
        app.mount("/css", StaticFiles(directory=str(css_dir)), name="css")
    js_dir = static_dir / "js"
    if js_dir.exists():
        app.mount("/js", StaticFiles(directory=str(js_dir)), name="js")

from fastapi.responses import FileResponse, HTMLResponse
from typing import Optional

def _check_and_handle_oauth_callback(dataKey: Optional[str] = None, data_key: Optional[str] = None, session_id: Optional[str] = None):
    key = (dataKey or data_key or "").strip()
    if key:
        from app.services.bitget_oauth import bitget_oauth_service
        success, html, _ = bitget_oauth_service.handle_callback_sync(key, session_id=session_id)
        return HTMLResponse(content=html, status_code=200)
    return None

@app.get("/")
@app.get("/landing")
@app.get("/landing.html")
def serve_ui(dataKey: Optional[str] = None, data_key: Optional[str] = None, session_id: Optional[str] = None):
    cb_resp = _check_and_handle_oauth_callback(dataKey, data_key, session_id)
    if cb_resp:
        return cb_resp

    landing_file = static_dir / "landing.html"
    if landing_file.exists():
        return FileResponse(landing_file)
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "message": "Alphaind - AI Trading Desk API is active. Open /docs for Swagger interactive endpoints.",
        "version": "1.0.0",
        "health": "/health",
        "api_health": "/api/health"
    }

@app.get("/callback")
@app.get("/oauth/callback")
def serve_oauth_callback(dataKey: Optional[str] = None, data_key: Optional[str] = None, session_id: Optional[str] = None):
    cb_resp = _check_and_handle_oauth_callback(dataKey, data_key, session_id)
    if cb_resp:
        return cb_resp
    from app.services.bitget_oauth import render_oauth_success_html
    return HTMLResponse(content=render_oauth_success_html(error="No dataKey provided in callback URL."), status_code=400)

@app.get("/desk")
@app.get("/desk.html")
def serve_desk(dataKey: Optional[str] = None, data_key: Optional[str] = None, session_id: Optional[str] = None):
    cb_resp = _check_and_handle_oauth_callback(dataKey, data_key, session_id)
    if cb_resp:
        return cb_resp

    desk_file = static_dir / "desk.html"
    if desk_file.exists():
        return FileResponse(desk_file)
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Trading Desk page not found"}

@app.get("/auth")
@app.get("/auth.html")
def serve_auth(dataKey: Optional[str] = None, data_key: Optional[str] = None, session_id: Optional[str] = None):
    cb_resp = _check_and_handle_oauth_callback(dataKey, data_key, session_id)
    if cb_resp:
        return cb_resp

    auth_file = static_dir / "auth.html"
    if auth_file.exists():
        return FileResponse(auth_file)
    landing_file = static_dir / "landing.html"
    if landing_file.exists():
        return FileResponse(landing_file)
    return {"message": "Auth page not found"}

if __name__ == "__main__":
    print(f"[*] Launching Alphaind - AI Trading Desk on http://{settings.HOST}:{settings.PORT}")
    print(f"[*] Primary LLM (OpenRouter): {settings.OPENROUTER_MODEL}")
    print(f"[*] Fallback LLM ({settings.BITGET_QWEN_NAME}): {settings.BITGET_QWEN_MODEL} via {settings.BITGET_QWEN_WIRE_API} ({settings.BITGET_QWEN_BASE_URL})")
    print(f"[*] Mode: {'Bitget Simulation Paper Desk' if settings.BITGET_IS_SIMULATION else 'Bitget Live'}")
    uvicorn.run("run:app", host=settings.HOST, port=settings.PORT, reload=True)
