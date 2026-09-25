# Alphaind · AI Trading Desk
### *Pre-Trade Research Workbench & Execution Assistant for Crypto Perps & 7×24 Tokenized Equities*

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python Version" />
  <img src="https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Bitget-v2%20REST%20%26%20OAuth-00F0FF?style=for-the-badge&logo=bitcoin&logoColor=black" alt="Bitget v2" />
  <img src="https://img.shields.io/badge/LLM_Engine-OpenRouter_%7C_Bitget_Qwen_Fallback-8A2BE2?style=for-the-badge" alt="LLM Engine" />
  <img src="https://img.shields.io/badge/Orderbook-Level--2_Depth_Walker-FF6B6B?style=for-the-badge" alt="Orderbook Depth Walker" />
  <img src="https://img.shields.io/badge/Automated_Tests-73%20Passed-10B981?style=for-the-badge&logo=pytest&logoColor=white" alt="Pytest 73 Passed" />
  <img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License MIT" />
</p>

---

## 🎯 Executive Summary & Core Thesis

**Alphaind** is a high-performance, natural-language **pre-trade research workbench and execution assistant** engineered specifically for active traders navigating both high-beta crypto perpetuals (`BTC`, `ETH`, `SOL`, `DOGE`) and around-the-clock tokenized US equity perpetuals (`NVDA`, `TSLA`, `AAPL`, `COIN`, `SPY`, `MSFT`).

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              THE CORE PROBLEM                               │
│  7×24 Tokenized Equities (rTokens) trade around the clock, even when US     │
│  cash equity markets close on weekends. This creates severe off-hours       │
│  spread expansion (2.4x–3.5x), synthetic pool fragmentation, and extreme    │
│  unhedged Monday Cash Open Gap risk (-8.5%). Meanwhile, retail traders      │
│  suffer from FOMO, emotional revenge trading on loss streaks, and hasty     │
│  market orders that sweep thin Level-2 books with massive slippage.         │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           THE ALPHAIND SOLUTION                             │
│  A single-screen research desk where natural language trade ideas are       │
│  audited by 7 deterministic quant/defense engines, stress-tested against    │
│  historical crash analogues, and synthesized into a structured 3+1+1        │
│  research brief paired with a calibrated safe execution ticket.             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Core Operating Philosophy
> **"AI researches, stress-tests, and prescribes a safe ticket; the human always decides."**  
> Alphaind is an institutional co-pilot, not an unconstrained black-box bot. Every execution requires sovereign human confirmation. Zero automated orders are dispatched without explicit trader review.

### Target User Profile
* **Account Capital Base:** \$2,000 – \$20,000 equity.
* **Target Leverage Range:** 3x – 15x.
* **Trading Frequency & Assets:** Active intraday and swing traders transitioning between volatile crypto perps and 7×24 synthetic equity rTokens during off-market hours and weekends.
* **Behavioral Vulnerabilities Addressed:** Emotional revenge trading after loss streaks (martingale sizing escalation), unhedged weekend equity gap liquidation, and naive market-order sweeps into thin orderbooks.

---

## ✨ Key System Capabilities

| Capability | Technical Implementation | Trader Benefit |
| :--- | :--- | :--- |
| **Natural-Language LUI Command Bar** | Real-time semantic parsing and entity extraction via LLM with automatic Bitget Qwen fallback failover | Formless, instantaneous trade auditing from plain English prompts. |
| **7 Rule-Based Risk & Quant Pillars** | 100% deterministic Python rule engines for math, volatility, fraud, and security | Zero LLM math hallucinations; rock-solid numerical gating. |
| **7×24 rToken Off-Hours Sentinel** | Live America/New_York (ET) session clock detecting Pre-market, Regular, After-hours, and Weekend regimes | Dynamic 2.4x–3.5x spread expansion warnings and Monday open gap alerts. |
| **Decision Stress Testing Engine** | 4 Equity/rToken crisis analogues and 4 Crypto black swan shock scenarios | Immediate visibility into portfolio liquidation buffers under extreme tail events. |
| **500-Run Monte Carlo Ruin Fan** | Non-parametric bootstrap return permutation simulator | Quantifies tail drawdown and ruin probability at the 95th percentile. |
| **Level-2 Orderbook Depth Walker** | Live Bitget v2 REST orderbook bid/ask sweep (up to 50 levels) | Computes Kyle's lambda, price impact, and slippage before order dispatch. |
| **Structured 3+1+1 Research Brief** | 3 Sourced Findings, 1 Recommended Action, 1 Thing NOT To Do, plus Human Pre-Flight Checklist | Clear, auditable research brief with 1-click Markdown export. |
| **Execution Assistance Desk Blotter** | Side-by-side comparison (Raw Proposal vs. Calibrated Safe Ticket) | Enforces safe leverage caps, exact \$ risk brackets, and algorithmic TWAP routing. |
| **Sovereign Human Decision Trio** | Three explicit execution options (*Approve Safe*, *Override Original*, *Reject & Pass*) | Total trader sovereignty with persistent paper trade ledger logging. |
| **Bitget Agentic OAuth Subaccount** | Ephemeral RSA-2048 split-codec handshake with public key encryption | Secure, 1-click credential sync with zero UI popups. |

---

## ⚡ 90-Second Quickstart

### Prerequisites
* **Python 3.11, 3.12, or 3.13**
* **Git**
* *(Optional)* **Docker & Docker Compose**

### Running Locally
```bash
# 1. Clone repository
git clone https://github.com/your-org/alphaind-trading-desk.git
cd alphaind-trading-desk

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch Desk
python run.py
```
> Open **`http://localhost:8000`** in your browser.

---

### Running via Docker Compose
```bash
docker compose up -d --build
```
* **Trading Desk UI:** `http://localhost:3000`
* **Backend REST API & OpenAPI Docs:** `http://localhost:8000/docs`
* **Backend REST API & OpenAPI Docs:** `http://localhost:8000/docs`

---

## 🚀 4 Interactive Canonical Demo Scenarios

The desk includes 4 canonical interactive demo scenarios accessible via top HUD buttons or direct URL query parameters:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       CANONICAL DEMO MATRIX                                             │
├────────────────────┬────────────────────────────────────────────────────┬───────────────────────────────┤
│ Demo Name          │ Prompt Query                                       │ Primary Risk Audit Triggered  │
├────────────────────┼────────────────────────────────────────────────────┼───────────────────────────────┤
│ NVDA Weekend 5x    │ "Long 25 NVDA at 5x on Saturday"                   │ 7×24 rToken Off-Hours Sentinel│
│ Tilt Revenge 40x   │ "Lost last 3 trades, going 40x on SOL"             │ Psychology Shield & MC Ruin   │
│ DOGE Depth Shock   │ "Market buy 50,000 DOGE vs book"                   │ L2 Depth Walker & TWAP Router │
│ Tech Concentration │ "Does adding 25 NVDA increase tech concentration?" │ Portfolio 95% Daily VaR Audit │
└────────────────────┴────────────────────────────────────────────────────┴───────────────────────────────┘
```

### 1. `NVDA Weekend 5x` ([`?demo=nvda-weekend`](http://localhost:8000?demo=nvda-weekend))
* **Prompt:** `"Long 25 NVDA at 5x on Saturday"`
* **What Executes:**
  * **rToken Regime Sentinel:** Detects US equity cash market is closed; triggers a **2.4x off-hours spread multiplier alert** and a **Monday Cash Open gap warning**.
  * **Level-2 Depth Walker:** Sweeps the Bitget v2 orderbook for 25 units (~$3,000 notional) and checks depth liquidity.
  * **Crisis Stress Tester:** Simulates a **Monday Cash Open Gap (-8.5% shock)**; flags that 5x leverage leaves an uncomfortably narrow 3.5% liquidation buffer.
  * **Execution Assistant:** Prescribes a **2x Safe Weekend Ticket** with bracket Stop-Loss at \$115.80 (-$105.00 / -3.5%) and automated TWAP routing.
  * **Human Decision Trio:** Trader evaluates the side-by-side comparison and chooses *Approve Safe Prescription*, *Override with Original*, or *Reject & Pass*.

### 2. `Tilt Revenge 40x SOL` ([`?demo=tilt-revenge`](http://localhost:8000?demo=tilt-revenge))
* **Prompt:** `"Lost last 3 trades, going 40x on SOL"`
* **What Executes:**
  * **Psychology Shield:** Intercepts tilt keywords (`"lost last 3 trades"`, `"going 40x"`) and identifies a dangerous martingale leverage escalation pattern.
  * **Monte Carlo Ruin Fan:** 500 bootstrap permutations reveal an extreme tail ruin probability (>35% probability of >50% drawdown).
  * **Interception Verdict:** Issues a `CRITICAL CAUTION / BLOCKED` verdict, prescribing **3x safe leverage** with a strict **\$35 max risk cap** and a mandatory cooling-off reminder.

### 3. `DOGE Depth Shock` ([`?demo=doge-depth`](http://localhost:8000?demo=doge-depth))
* **Prompt:** `"Market buy 50,000 DOGE vs book"`
* **What Executes:**
  * **Orderbook Depth Walker:** Walks Bitget v2 L2 bids and asks; detects that a single market sweep of 50,000 DOGE exhausts top price levels, causing estimated slippage > 0.45%.
  * **Execution Assistant:** Proactively prescribes a **3-tranche TWAP execution schedule** at 15-second intervals to minimize market impact.

### 4. `Tech Concentration VaR` ([`?demo=tech-var`](http://localhost:8000?demo=tech-var))
* **Prompt:** `"Does adding 25 NVDA increase my tech concentration?"`
* **What Executes:**
  * **Portfolio Guardian & VaR Engine:** Audits spot & futures portfolio equity, calculates multi-asset weightings, and evaluates incremental parametric **95% Daily Value at Risk (VaR)**.
  * **Conversational Research Brief:** Delivers an institutional-grade thesis briefing on tech correlation, NAV basis risk, and portfolio diversification.

---

## 🔬 System Architecture & LLM/Quant Division

Alphaind enforces an unyielding, honest separation of concerns between natural language intelligence and deterministic mathematics:

```
                                 TRADER NATURAL LANGUAGE PROMPT
                                ("Long 25 NVDA at 5x on Saturday")
                                                │
                                                ▼
                     ┌─────────────────────────────────────────────────────┐
                     │          NATURAL LANGUAGE LUI COMMAND BAR           │
                     │   - Real-Time Parameter & Entity Extraction         │
                     │   - Dual LLM: Qwen 3.8 Max + Claude 3.5 Sonnet      │
                     └──────────────────────────┬──────────────────────────┘
                                                │
                 ┌──────────────────────────────┴──────────────────────────────┐
                 ▼                                                             ▼
┌─────────────────────────────────────────────┐ ┌─────────────────────────────────────────────┐
│     7 DETERMINISTIC DEFENSE & QUANT PILLARS │ │        DECISION STRESS TESTING ENGINE       │
│            (100% Rule-Based Python)         │ │         (Historical Crisis Analogues)       │
│                                             │ │                                             │
│ 1. Volatility Sentinel (ATR & Parkinson)    │ │ - Monday Cash Open Gap (-8.5%)              │
│ 2. Fraud Hunter (Catalog & Spoof Check)     │ │ - Tech Earnings Miss (-12.0%)               │
│ 3. Security Guard (Wrapper & Mint Rights)   │ │ - Fed Emergency 50bps Cut (-7.5%)           │
│ 4. Liquidity Auditor (L2 Depth Walker)      │ │ - Crypto Black Swans (COVID/FTX/Luna)       │
│ 5. Psychology Shield (Tilt & Martingale)    │ │ - 500-Run Monte Carlo Tail Ruin Simulator   │
│ 6. Quantitative Analyst (Hurst & RSI)       │ │ - Parametric 95/99% Daily Portfolio VaR     │
│ 7. Strategy Backtester (Fee/Slippage Sim)   │ │ - 7×24 rToken Off-Hours Spread Multiplier   │
└──────────────────────┬──────────────────────┘ └──────────────────────┬──────────────────────┘
                       │                                               │
                       └───────────────────────┬───────────────────────┘
                                               │
                                               ▼
                     ┌─────────────────────────────────────────────────────┐
                     │          STRUCTURED 3+1+1 RESEARCH BRIEF            │
                     │  - 3 Sourced Findings ([LIVE], [CALC], [SIM])       │
                     │  - 1 Recommended Action (Calibrated Safe Ticket)    │
                     │  - 1 Thing NOT To Do (Antipattern Warning)          │
                     │  - Human Pre-Flight Risk Checklist                  │
                     │  - 1-Click Markdown Export (.md)                    │
                     └──────────────────────────┬──────────────────────────┘
                                                │
                                                ▼
                     ┌─────────────────────────────────────────────────────┐
                     │          EXECUTION ASSISTANCE DESK BLOTTER          │
                     │  - Side-by-Side: Raw Proposal vs. Safe Prescription │
                     │  - Exact Dollar Bracket Stop-Loss & Take-Profit     │
                     │  - Algorithmic Background TWAP Execution Router     │
                     │                                                     │
                     │  [ 1. Approve Safe ] [ 2. Override ] [ 3. Pass ]    │
                     └─────────────────────────────────────────────────────┘
```

### Zero-Math-Hallucination & Single-Active-LLM Architecture
* **Zero Math Generated by LLMs:** Numerical risk scores, liquidation buffers, slippage percentages, Kyle's lambda, Monte Carlo ruin probabilities, and bracket price targets are **100% computed by deterministic Python algorithms**.
* **Single Active LLM with Auto-Failover:** Only **one LLM operates at any given time**. Requests first route through **OpenRouter** (Claude 3.5 Sonnet / configured model). If OpenRouter is unavailable, unconfigured, or encounters API rate limits / network timeouts, the desk seamlessly fails over to **Bitget Qwen 3.8 Max** as high-availability secondary provider. If both external APIs are unreachable, the desk gracefully downgrades to deterministic regex/heuristic intent parsing without breaking.
* **Transparent Data Provenance:** Every metric in the UI and exported research briefs displays an honest provenance badge (`LIVE`, `CALCULATED`, or `SIMULATED`).

---

## 🛡️ The 7 Deterministic Defense & Quant Pillars

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 THE 7 DEFENSE & QUANT PILLARS                                    │
├─────────────────────────┬────────────────────────────────────────────────────────┬───────────────┤
│ Pillar                  │ Algorithmic Logic & Measurement Method                 │ Provenance    │
├─────────────────────────┼────────────────────────────────────────────────────────┼───────────────┤
│ 1. Volatility Sentinel  │ Real-time ATR surge scanner, Parkinson high-low ratio, │ [CALCULATED]  │
│                         │ and market turbulence index ($Z > 2.50$ alert).        │               │
├─────────────────────────┼────────────────────────────────────────────────────────┼───────────────┤
│ 2. Fraud Hunter         │ Validates token symbols against official Bitget spot & │ [LIVE]        │
│                         │ rToken catalog; intercepts unverified spoofed tickers. │               │
├─────────────────────────┼────────────────────────────────────────────────────────┼───────────────┤
│ 3. Security Guard       │ Audits rToken synthetic wrapper structure, custodian   │ [LIVE]        │
│                         │ asset-backing proof, and token mint/burn permissions.  │               │
├─────────────────────────┼────────────────────────────────────────────────────────┼───────────────┤
│ 4. Liquidity Auditor    │ Real-time Level-2 orderbook depth walker (50 levels);  │ [LIVE]        │
│                         │ computes Kyle's lambda, spread %, and sweep slippage.  │               │
├─────────────────────────┼────────────────────────────────────────────────────────┼───────────────┤
│ 5. Psychology Shield    │ Natural language sentiment parser + loss-streak ledger │ [CALCULATED]  │
│                         │ interceptor; blocks martingale leverage escalation.    │               │
├─────────────────────────┼────────────────────────────────────────────────────────┼───────────────┤
│ 6. Quantitative Analyst │ Computes Hurst Exponent ($H > 0.50$ trending vs mean   │ [CALCULATED]  │
│                         │ reverting), RSI-14, and momentum alpha score.          │               │
├─────────────────────────┼────────────────────────────────────────────────────────┼───────────────┤
│ 7. Strategy Backtester  │ Event-driven bar-by-bar backtester (0.06% taker fee &  │ [CALCULATED]  │
│                         │ slippage) + 500-permutation bootstrap Monte Carlo fan. │ [SIMULATED]   │
└─────────────────────────┴────────────────────────────────────────────────────────┴───────────────┘
```

---

## ⚡ Decision Stress Testing & Crisis Shock Matrix

Alphaind evaluates every trade idea against historical market dislocations and tail-risk shocks tailored per asset class:

### Equity & rToken Crisis Analogues
* **Monday Cash Open Gap ($-8.5\%$):** Simulates unhedged synthetic positions encountering cash market weekend event gaps at 09:30 ET Monday.
* **Tech Earnings Miss ($-12.0\%$):** Models high-beta semiconductor/mega-cap earnings shock and implied volatility crush.
* **Fed Emergency 50bps Rate Cut ($-7.5\%$):** Simulates intraday macro policy liquidity turbulence and cross-asset correlation breakdowns.
* **Global Risk-Off Deleveraging ($-15.0\%$):** Simulates broad multi-asset margin liquidation cascade.

### Crypto Black Swan Analogues
* **COVID-19 Liquidity Shock ($-33.5\%$):** March 2020 cross-market cascade.
* **FTX Solvency Collapse ($-24.5\%$):** November 2022 counterparty failure shock.
* **Luna Death Spiral ($-52.0\%$):** May 2022 algorithmic de-pegging collapse.
* **Flash Crash Sweeper ($-15.0\%$):** Derivative cascade orderbook wipeout.

### 500-Run Monte Carlo Tail Ruin Simulator
The simulator performs **500 non-parametric bootstrap return permutations** across historical candle distributions, computing:
* **Worst Drawdown Distribution:** 50th, 90th, and 95th percentile worst-case drawdowns.
* **Ruin Probability:** Chance of account equity falling $> 50\%$ over a 30-trade sequence.
* **Resilience Score:** Deterministic 0–100 score indicating trade survival capacity.

---

## 📋 Structured 3+1+1 Pre-Trade Research Brief

Every analyzed trade generates an institutional-grade research debrief following our **3+1+1 framework**:

```markdown
# PRE-TRADE RESEARCH BRIEF: LONG 25 NVDA @ 5x [WEEKEND SESSION]

### 📊 3 SOURCED FINDINGS
1. [LIVE] Level-2 Orderbook Depth: 25 units (~$3,025 notional) requires sweeping 2 bid/ask levels on Bitget v2, incurring ~0.08% estimated slippage.
2. [CALCULATED] Crisis Stress Shock: A -8.5% Monday Cash Open Gap results in a -$1,285.62 equity drawdown (-42.5%), narrowing liquidation buffer to < 3.5%.
3. [LIVE] 7×24 rToken Regime Sentinel: US equity cash market is CLOSED. Off-hours spread multiplier is 2.4x; synthetic liquidity pool depth is 45% of regular hours.

### 🎯 1 RECOMMENDED ACTION (CALIBRATED SAFE TICKET)
* Reduce leverage from 5x to 2x.
* Place Bracket Stop-Loss at $115.80 (-$105.00 / -3.5%) and Take-Profit at $130.20 (+$243.00 / +8.1%).
* Route execution via 3-tranche TWAP across 15-second intervals.

### 🚫 1 THING NOT TO DO
* DO NOT execute unconstrained market orders with > 2x leverage on synthetic rTokens during weekend hours.

### 🛡️ HUMAN PRE-FLIGHT RISK CHECKLIST
- [ ] Confirmed 2.4x off-hours spread expansion accepted.
- [ ] Confirmed Monday 09:30 ET cash market opening gap risk acknowledged.
- [ ] Confirmed exact dollar risk ($105.00) is within daily risk budget.
```

> **1-Click Markdown Export:** Traders can export and download the complete brief as a `.md` document or copy it to the clipboard directly from the HUD.

---

## 📊 Telemetry Transparency & Data Provenance Matrix

Alphaind adheres to rigorous data integrity standards. Every telemetry point carries an honest data provenance badge:

| Metric / Telemetry Field | Badge | Upstream Source | Update Frequency / Method |
| :--- | :---: | :--- | :--- |
| **Current Price & 24h Ticker** | `LIVE` | Bitget Public v2 REST (`/api/v2/spot/market/tickers`) | Real-time with 3-second in-memory TTL cache |
| **Level-2 Orderbook Depth** | `LIVE` | Bitget Public v2 REST (`/api/v2/spot/market/orderbook`) | Real-time bids/asks depth walk up to 50 levels |
| **Market Session Clock** | `LIVE` | System Clock (`America/New_York` ET) | Sub-second evaluation of trading sessions |
| **Token Listing Authenticity** | `LIVE` | Bitget Spot & rToken Catalog Cache | Verified against official exchange symbol registry |
| **Hurst Exponent ($H$) & RSI** | `CALCULATED` | Bitget 1-Hour Candles (`/api/v2/spot/market/candles`) | Deterministic mathematical calculation |
| **Historical Crisis Shocks** | `CALCULATED` | Parametric Asset Stress Engine | Deterministic shock matrix (-8.5% to -52.0%) |
| **Backtest Expectancy & Sharpe** | `CALCULATED` | Historical Candle Backtest Engine | Bar-by-bar sim with 0.06% taker fees & slippage |
| **500-Run Tail Ruin Drawdown** | `SIMULATED` | 500-Permutation Bootstrap Simulator | Non-parametric return reshuffling for 95% worst DD |
| **Natural Language Synthesis** | `LIVE` | Dual LLM (`Qwen 3.8 Max` / `Claude 3.5 Sonnet`) | Intent deconstruction & conversational debriefing |

---

## ⚙️ Configuration & Environment Variables

Create a `.env` file in the project root based on `.env.example`:

```env
# Server Configuration
PORT=8000
CORS_ORIGINS=*

# Bitget Public Market Data & Simulation Mode
BITGET_IS_SIMULATION=true

# Primary LLM Engine (OpenRouter)
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# High-Availability Fallback LLM Engine (Bitget Qwen 3.8 Max)
BITGET_QWEN_API_KEY=your_bitget_qwen_api_key_here
BITGET_QWEN_MODEL=qwen3.8-max
BITGET_QWEN_BASE_URL=https://hackathon.bitgetops.com/v1
BITGET_QWEN_WIRE_API=responses

# Bitget Authenticated Live Subaccount (Optional / Configured via OAuth)
BITGET_API_KEY=
BITGET_API_SECRET=
BITGET_API_PASSPHRASE=
```

---

## 🌐 Production Cloud Deployment Guide

Alphaind is built with a decoupled architecture ready for immediate deployment on modern cloud platforms:

```
┌────────────────────────────────────────────────────────┐
│                   FRONTEND SERVICE                     │
│  Host: Vercel / Netlify (https://alphaind.vercel.app)  │
│  - Static SPA (HTML5, CSS3, Vanilla ES6+ JavaScript)   │
│  - Dynamic API Base URL resolution (config.js)         │
│  - Zero UI Popups/Modals — 100% Background Routing     │
└──────────────────────────┬─────────────────────────────┘
                           │ HTTPS / REST (CORS enabled)
                           ▼
┌────────────────────────────────────────────────────────┐
│                    BACKEND SERVICE                     │
│  Host: Render / Fly.io / Railway / Docker              │
│  - FastAPI + Uvicorn ASGI Server                       │
│  - 7 Risk & Defense Pillars + Multi-Agent Orchestrator │
│  - Live Bitget v2 REST Market Data (Cached 3s)         │
│  - Health Check Probes (/health & /api/health)         │
└────────────────────────────────────────────────────────┘
```

### Deploying Backend to Render
1. Push the repository to GitHub.
2. Go to [Render Dashboard](https://dashboard.render.com) → **New +** → **Blueprint** (detects `render.yaml`).
3. Set environment variables (`BITGET_IS_SIMULATION=true`, `BITGET_QWEN_API_KEY`, etc.).
4. Click **Create Web Service** to receive your public endpoint (e.g. `https://alphaind-backend.onrender.com`).

### Deploying Frontend to Vercel
1. Import the repository into [Vercel Dashboard](https://vercel.com/new).
2. Set **Root Directory** to `frontend`.
3. Add Environment Variable: `VITE_API_URL=https://alphaind-backend.onrender.com`.
4. Click **Deploy**.

> **Dynamic API Endpoint Override:** You can deep-link to any backend instance by passing `?api=https://your-backend.com` in the URL.

---

## 📡 REST API Reference

### Core Desk Endpoints

#### `POST /api/alphaind/orchestrate`
Main multi-agent research and risk audit pipeline.
* **Request:**
  ```json
  {
    "prompt": "Long 25 NVDA at 5x on Saturday"
  }
  ```
* **Response:**
  ```json
  {
    "orchestrator": {
      "status": "COMPLETED",
      "verdict": "ADVISORY_CAUTION",
      "parsed_intent": {
        "symbol": "NVDAUSDT",
        "side": "buy",
        "size": 25.0,
        "leverage": 5,
        "is_rtoken": true
      }
    },
    "sub_agents": {
      "volatility_sentinel": { "status": "SAFE", "score": 15 },
      "liquidity_auditor": { "status": "SAFE", "slippage_pct": 0.08 },
      "psychology_shield": { "status": "SAFE", "score": 5 }
    },
    "stress_testing": {
      "resilience_score": 55,
      "monday_gap_drawdown_pct": -42.5,
      "monte_carlo_worst_dd_pct": -38.2
    },
    "research_brief": { ... },
    "suggested_ticket": {
      "symbol": "NVDAUSDT",
      "side": "buy",
      "safe_leverage": 2,
      "bracket_stop_loss": 115.80,
      "bracket_take_profit": 130.20,
      "dollar_risk": 105.00
    }
  }
  ```

#### `POST /api/alphaind/research-brief/export`
Exports a structured research brief to formatted GitHub Flavored Markdown.

#### `POST /api/alphaind/execute`
Dispatches a confirmed trade ticket to the Bitget Desk (persists to paper ledger in simulation mode).

#### `POST /api/alphaind/agentic`
Goal router executing high-level autonomous research and risk discovery directives.

#### `POST /api/alphaind/debate`
Multi-agent deliberation arena convening Bullish Strategist, Bearish Risk Sentinel, and Execution Guardian.

#### `POST /api/alphaind/scanner`
Cross-asset watchlist scanner ranking pairs by momentum, composite alpha, or Hurst exponent.

#### `GET /api/market/orderbook?symbol=NVDAUSDT&depth=20`
Fetches live Level-2 orderbook depth directly from Bitget v2 REST.

#### `POST /api/quant/backtest`
Executes an event-driven backtest with realistic fees, slippage, and 500 Monte Carlo bootstrap permutations.

#### `GET /health` & `GET /api/health`
System health probe returning live Bitget API connectivity and model status.

---

## 🧪 Automated Testing & Verification

Alphaind includes a comprehensive automated test suite covering all risk pillars, stress scenarios, session regimes, cryptographic split-codecs, and API routes:

```bash
# Run the entire test suite (73 tests)
pytest -v

# Run specific domain test suites
pytest tests/test_desk_core.py            # Core market data, Hurst & risk engines
pytest tests/test_alphaind_agents.py      # Orchestrator & parallel agent swarms
pytest tests/test_bitget_oauth.py         # RSA-2048 split-codec & OAuth sessions
pytest tests/test_agentic_power.py        # Autonomous goal router & tool suite
pytest tests/test_debate_swarm.py         # Multi-agent bull/bear deliberation
pytest tests/test_quant_backtest_agents.py # Backtester & Monte Carlo simulator
pytest tests/test_s2_features.py          # rToken regime sentinel & stress tester
```

```
============================== 73 passed in 100% ==============================
```

---

## 📁 Repository Directory Structure

```
├── app/
│   ├── agents/
│   │   ├── orchestrator.py        # Master Swarm Orchestrator & Briefing Engine
│   │   ├── tools.py               # 11 Callable Quant & Execution Tools
│   │   ├── agentic_engine.py      # Autonomous Goal Router & ReAct Engine
│   │   └── swarm_deliberation.py  # Bull vs. Bear Deliberation Arena
│   ├── defense/
│   │   ├── research_brief.py      # Structured 3+1+1 Research Brief Generator & Exporter
│   │   ├── rtoken_regime.py       # 7×24 rToken Session Clock & Spread Multipliers
│   │   ├── psychology.py          # Tilt, revenge-trading, and sentiment interceptor
│   │   ├── volatility.py          # ATR surge & Parkinson volatility scanner
│   │   ├── fraud_detector.py      # Asset authenticity & catalog verification
│   │   ├── contract_auditor.py    # Wrapper structure & contract permissions
│   │   └── liquidity_auditor.py   # L2 Depth Walker & Kyle's Lambda slippage auditor
│   ├── quant/
│   │   ├── stress_tester.py       # 4-Scenario Crisis Stress & Resilience Engine
│   │   ├── factor_engine.py       # Hurst exponent, RSI, ATR, and momentum alpha
│   │   ├── backtester.py          # Event-driven backtester & 500-run Monte Carlo
│   │   └── portfolio_var.py       # Portfolio equity & Parametric 95/99% Daily VaR
│   ├── services/
│   │   ├── bitget_client.py       # Bitget v2 REST client with caching & paper ledger
│   │   ├── bitget_oauth.py        # RSA-2048 split-codec Agentic Subaccount OAuth
│   │   ├── bitget_qwen_client.py  # Bitget Qwen 3.8 Max client (/responses wire API)
│   │   ├── openrouter_client.py   # OpenRouter Claude 3.5 Sonnet client
│   │   ├── twap_executor.py       # Background algorithmic TWAP execution engine
│   │   └── bitget_signal.py       # Real technical indicator calculations
│   ├── static/
│   │   ├── index.html             # Obsidian HUD Single-Screen Workspace
│   │   ├── css/styles.css         # Institutional glassmorphic dark theme
│   │   └── js/app.js              # UI controller, ET clock, LUI tracker & blotter
│   ├── api/
│   │   └── routes.py              # FastAPI REST endpoints & export routes
│   ├── config.py                  # Desk profile & asset defaults
│   └── main.py                    # FastAPI application entry point
├── frontend/                      # Standalone static SPA for Vercel/Netlify
│   ├── index.html                 # Obsidian HUD SPA
│   ├── css/                       # Modular CSS stylesheets
│   ├── js/                        # Modular ES6 JavaScript controllers
│   └── vercel.json                # Vercel deployment configuration
├── backend/                       # Dedicated backend deployment manifests
│   ├── Dockerfile                 # Production backend container
│   ├── render.yaml                # Render deployment blueprint
│   └── fly.toml                   # Fly.io deployment manifest
├── tests/                         # 73 automated unit and integration tests
├── requirements.txt               # Python package dependencies
├── docker-compose.yml             # Multi-container orchestration
├── run.py                         # One-click startup runner
├── DEPLOYMENT.md                  # Comprehensive Cloud Deployment Guide
└── README.md                      # Desk documentation & quickstart
```

---

## ⚖️ License & Risk Disclaimer

**Alphaind** is released under the **MIT License**.

> [!WARNING]
> **Financial Risk Disclaimer:** Trading cryptocurrencies, perpetual futures, and leveraged synthetic equity tokens (rTokens) carries substantial risk of financial loss. Leverage can work against you as well as for you. Alphaind operates by default in paper simulation mode. Always practice disciplined risk management and never risk capital you cannot afford to lose.
