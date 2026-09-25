# Alphaind - AI Trading Desk · Cloud Deployment Guide

This guide details the streamlined deployment of **Alphaind - AI Trading Desk** with **Frontend on Vercel** and **Backend on Render**.

```
┌────────────────────────────────────────────────────────┐
│                   FRONTEND SERVICE                     │
│  Host: Vercel (https://alphaind.vercel.app)            │
│  - Static SPA (HTML5, CSS3, Vanilla ES6+ JS)           │
│  - Dynamic API Base URL resolution (config.js)         │
│  - Zero UI Popups/Modals — 100% Background Routing     │
└──────────────────────────┬─────────────────────────────┘
                           │ HTTPS / REST (CORS enabled)
                           ▼
┌────────────────────────────────────────────────────────┐
│                    BACKEND SERVICE                     │
│  Host: Render (https://alphaind-backend.onrender.com)  │
│  - FastAPI + Uvicorn ASGI Server                       │
│  - Single Active LLM with Auto-Failover (OpenRouter -> Qwen) │
│  - Live Bitget v2 REST Market Data (Cached 3s)         │
│  - Health Check Probes (/health & /api/health)         │
└────────────────────────────────────────────────────────┘
```

---

## 🚀 Step 1: Deploy Backend to Render

1. Ensure your repository is pushed to GitHub: [`https://github.com/ashfakcodes/alphaind-trading-desk`](https://github.com/ashfakcodes/alphaind-trading-desk).
2. Go to the [Render Dashboard](https://dashboard.render.com).
3. Click **New +** → **Blueprint** and select `alphaind-trading-desk` (it will automatically detect `render.yaml`).
   * *Alternatively:* Click **New +** → **Web Service** → Connect `ashfakcodes/alphaind-trading-desk`:
     * **Name**: `alphaind-backend`
     * **Environment**: `Python 3`
     * **Build Command**: `pip install -r requirements.txt`
     * **Start Command**: `uvicorn run:app --host 0.0.0.0 --port $PORT`
     * **Health Check Path**: `/health`
4. Under **Environment Variables**, configure:
   ```env
   CORS_ORIGINS=*
   BITGET_IS_SIMULATION=true
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
   BITGET_QWEN_API_KEY=your_bitget_qwen_api_key_here
   BITGET_QWEN_MODEL=qwen3.8-max
   BITGET_QWEN_BASE_URL=https://hackathon.bitgetops.com/v1
   BITGET_QWEN_WIRE_API=responses
   ```
5. Click **Create Web Service**. Once built, copy your public backend URL:
   `https://alphaind-backend.onrender.com`

---

## ⚡ Step 2: Deploy Frontend to Vercel

1. Go to [Vercel Dashboard](https://vercel.com/new).
2. Import `https://github.com/ashfakcodes/alphaind-trading-desk`.
3. In **Project Configuration**:
   * **Framework Preset**: `Other`
   * **Root Directory**: `frontend`
   * **Build Command**: *(Leave blank)*
   * **Output Directory**: *(Leave blank / `.`)*
4. Under **Environment Variables**, add:
   * **Key**: `VITE_API_URL` (or set `window.API_BASE_URL` in `config.js`)
   * **Value**: `https://alphaind-backend.onrender.com`
5. Click **Deploy**.
6. Your trading desk is live at `https://alphaind.vercel.app`!

---

## 🔄 How the Connection Works (Zero-UI)

* **Production (Vercel → Render)**: The frontend automatically reads `VITE_API_URL` or `window.API_BASE_URL` and routes all API requests directly to your Render backend with CORS enabled.
* **Local Development**: When running locally (e.g. `localhost:3000`), the frontend automatically connects to `http://localhost:8000` without any manual configuration.
* **Shareable Deep-Links**: You can pass `?api=https://alphaind-backend.onrender.com` in the URL to override the backend endpoint dynamically for testing.

---

## 💻 Local Running
To launch the desk locally with the full UI and API active:
```bash
python run.py
```
> Access the desk at `http://localhost:8000`.
