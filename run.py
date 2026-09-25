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

# Mount Static Files (if local monolithic mode is active)
static_dir = Path(__file__).resolve().parent / "frontend"
if not static_dir.exists():
    static_dir = Path(__file__).resolve().parent / "app" / "static"

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

@app.get("/")
@app.get("/landing")
@app.get("/landing.html")
def serve_ui():
    landing_file = static_dir / "landing.html"
    if landing_file.exists():
        return FileResponse(landing_file)
    desk_file = static_dir / "index.html"
    if desk_file.exists():
        return FileResponse(desk_file)
    return {
        "message": "Alphaind - AI Trading Desk API is active. Open /docs for Swagger interactive endpoints.",
        "version": "1.0.0",
        "health": "/health",
        "api_health": "/api/health"
    }

@app.get("/desk")
@app.get("/desk.html")
@app.get("/index.html")
def serve_desk():
    desk_file = static_dir / "index.html"
    if desk_file.exists():
        return FileResponse(desk_file)
    return {"message": "Trading Desk page not found"}

@app.get("/auth")
@app.get("/auth.html")
def serve_auth():
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
