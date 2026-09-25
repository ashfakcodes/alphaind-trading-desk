# Bitget AI Hackathon S2 — Track 3 Submission Writeup
## Project Name: **Alphaind · AI Trading Desk**
### *Pre-Trade Research Workbench & Execution Assistant for Crypto Perps & 7×24 rTokens*

---

### Section 1: Track & Positioning

* **Selected Track:** **Track 3 — AI Trading Desk**
* **Named Sub-Theme:** **Execution Assistance** (Primary) with **Decision Stress Testing** (Deep Supporting Pillar).
* **One-Line Product Summary:**
  > Natural-language pre-trade research workbench and execution assistant for retail traders mixing crypto perps and 7×24 rTokens ($2k–$20k equity, 3–15x leverage), transforming unstructured trade ideas into institutional-grade research briefs and calibrated safe execution tickets.
* **Target User Segment:**
  * Capital base: \$2,000 – \$20,000 account equity.
  * Trade style: Active retail traders mixing high-beta crypto perps (SOL, DOGE, BTC) and tokenized 24/7 equity perps (NVDA, TSLA, AAPL, COIN, SPY) on weekends.
  * Behavioral profile: Susceptible to FOMO on breakout momentum, revenge-trading on losing streaks (martingale leverage escalation), and unaware of synthetic off-hours equity spread expansion and Monday cash open gap risks.
* **Core Philosophy:**
  > **AI researches, stress-tests, and prescribes a safe ticket; the human always decides.** Alphaind is a co-pilot, not an unconstrained autonomous black box. Every order requires explicit trader review and confirmation.

---

### Section 2: Problem & Solution

#### The Problem
Retail traders face three critical vulnerabilities when executing trades:
1. **Friction in Pre-Trade Due Diligence:** Gathering Level-2 orderbook depth, slippage estimates, statistical factor persistence, volatility regimes, and backtest expectancy across multiple disconnected screens takes minutes—leading to hasty, unvetted market orders.
2. **7×24 rToken Blindspots:** Off-hours tokenized equities (e.g. trading NVDA or TSLA on Saturday) trade on synthetic weekend liquidity pools with 2x–3x wider spreads and severe unhedged gap risk against the Monday 09:30 ET cash open. Retail traders frequently apply 5x–10x leverage on weekends without recognizing that an -8.5% cash market opening gap causes immediate liquidation.
3. **Psychological Tilt & Execution Slippage:** After loss streaks, traders aggressively increase leverage (e.g. 40x on SOL) or market-sweep thin orderbooks (e.g. 50,000 DOGE), suffering massive adverse price impact.

#### The Alphaind Solution
Alphaind replaces clunky manual forms with a unified, single-screen **Pre-Trade Research Workbench & Execution Assistant**:
1. **Natural-Language Pre-Trade Interface:** The trader enters their thesis in conversational English (e.g. *"Long 25 NVDA at 5x on Saturday"*). The LUI extracts parameters in real-time.
2. **7 Deterministic Quant & Defense Pillars:** Concurrently audits market turbulence, asset listing authenticity, contract wrapper security, L2 orderbook depth walking, trader tilt/mindset, Hurst exponent persistence ($H > 0.50$), and 500-permutation Monte Carlo ruin simulations.
3. **Structured Research Brief (3+1+1 Framework):** Generates an instant, auditable debrief consisting of **3 Sourced Findings** (`LIVE` orderbook depth, `CALCULATED` crisis shocks, `LIVE` rToken session), **1 Recommended Action**, and **1 Thing NOT To Do**, complete with a 1-click Markdown export.
4. **Side-by-Side Execution Blotter:** Shows the raw proposal next to the AI Prescribed Safe Ticket (calibrated safe leverage, exact \$ bracket stop-loss/take-profit, and algorithmic TWAP tranche execution). The trader makes the final call using the **Human Decision Trio** (*Approve Safe Prescription*, *Override with Original*, or *Reject & Pass*).

---

### Section 3: Technical Architecture & LLM/Quant Division

Alphaind enforces an honest, unyielding boundary between rule-based mathematics and language model reasoning:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       NATURAL LANGUAGE INTENT & LUI                     │
│                  Bitget Qwen 3.8 Max (Intent & Synthesis)               │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼                                       ▼
┌─────────────────────────────────┐   ┌───────────────────────────────────┐
│   7 DETERMINISTIC RISK ENGINES  │   │     DECISION STRESS TESTER        │
│    (100% Rule-Based Python)     │   │   (Historical Crash Analogues)    │
│  - L2 Orderbook Depth Walker    │   │  - Monday Cash Open Gap (-8.5%)   │
│  - Kyle's Lambda & Slippage %   │   │  - Tech Earnings Miss (-12.0%)    │
│  - Hurst Exponent & RSI Factor  │   │  - Fed Emergency 50bps (-7.5%)    │
│  - 500 Monte Carlo Ruin Fan     │   │  - COVID-19 / FTX / Luna Shocks   │
│  - 7x24 rToken Spread Multiplier│   │  - Parametric 95/99% Daily VaR    │
└────────────────┬────────────────┘   └──────────────────┬────────────────┘
                 │                                       │
                 └───────────────────┬───────────────────┘
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                 STRUCTURED PRE-TRADE RESEARCH BRIEF                     │
│    3 Sourced Findings + 1 Recommended Action + 1 Thing NOT To Do       │
│                Human Pre-Flight Risk Checklist & 1-Click .md            │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                 EXECUTION ASSISTANCE DESK BLOTTER                       │
│    Side-by-Side Ticket: Original Proposal vs. Prescribed Safe Ticket    │
│    Bracket SL/TP in Exact $ | Algorithmic Background TWAP Engine        │
│                                                                         │
│    [1. Approve Safe Ticket]   [2. Override Original]   [3. Reject/Pass] │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Why This Division Matters for S2 Judging:
* **Zero Math Hallucination:** Numerical risk scores, liquidation buffers, slippage percentages, and Monte Carlo ruin statistics are calculated deterministically by mathematical algorithms—never guessed by an LLM.
* **Language Model Strengths Utilized:** **Bitget Qwen 3.8 Max** (with OpenRouter fallback) excels at intent deconstruction, semantic entity extraction, and conversational synthesis of complex quant telemetry into clear, actionable retail language.
* **Transparent Data Provenance:** Every metric displays an honest source badge (`LIVE` Bitget REST API, `CALCULATED` 1h Klines, `SIMULATED` Monte Carlo).

---

### Section 4: 4 Pinned Canonical Demo Scenarios

The desk includes 4 canonical interactive demo scenarios accessible via top HUD buttons or URL parameters:

#### Demo 1: `NVDA Weekend 5x` (`?demo=nvda-weekend`)
* **Prompt:** `"Long 25 NVDA at 5x on Saturday"`
* **Demonstrates:**
  * **rToken Regime Detection:** Detects that US equity markets are closed; applies 2.4x off-hours spread multiplier.
  * **Monday Cash Open Gap Stress:** Runs the -8.5% equity crash analogue, warning that 5x leverage leaves an uncomfortably narrow margin buffer.
  * **Orderbook Depth Walker:** Sweeps Bitget v2 L2 orderbook for \$3,000 notional; checks slippage across book levels.
  * **Execution Prescription:** Prescribes a 2x Safe Ticket with bracket Stop-Loss at \$115.80 (-$105.00 / -3.5%) and TWAP execution.

#### Demo 2: `Tilt Revenge 40x SOL` (`?demo=tilt-revenge`)
* **Prompt:** `"Lost last 3 trades, going 40x on SOL"`
* **Demonstrates:**
  * **Psychology Shield:** Intercepts tilt keywords ("lost last 3 trades", "going 40x") and identifies martingale revenge behavior.
  * **Monte Carlo Ruin Fan:** 500 bootstrap permutations reveal extreme ruin probability (>35%).
  * **Interception Verdict:** Issues a CRITICAL CAUTION / BLOCK verdict, prescribing 3x leverage with a strict \$35 risk cap.

#### Demo 3: `DOGE Depth Shock` (`?demo=doge-depth`)
* **Prompt:** `"Market buy 50,000 DOGE vs book"`
* **Demonstrates:**
  * **Orderbook Depth Walker:** Sweeps the live Bitget L2 orderbook and flags that a single 50,000 DOGE market sweep consumes multiple levels, causing >0.45% slippage.
  * **Execution Assistant:** Proactively prescribes a 3-tranche TWAP execution schedule across 15-second intervals.

#### Demo 4: `Tech Concentration VaR` (`?demo=tech-var`)
* **Prompt:** `"Does adding 25 NVDA increase my tech concentration?"`
* **Demonstrates:**
  * **Portfolio Guardian & VaR Engine:** Audits portfolio equity, computes asset weightings, and evaluates incremental 95% Daily Value at Risk.
  * **Research Synthesis:** Generates a thesis debrief on equity correlation, NAV basis risk, and portfolio diversification.

---

### Section 5: Key Features & Deliverables

1. **Obsidian HUD Single-Screen Workspace:**
   * Live Eastern Time (ET) session clock tracking Regular, Pre-market, After-hours, and Weekend regimes.
   * Dynamic LUI parameter chips updating in real time as the trader types.
   * Multi-step animated research loading flow.
   * Weekend rToken warning banner with spread multipliers and Monday gap warnings.
2. **Structured Pre-Trade Research Brief:**
   * 3 Sourced Findings + 1 Recommended Action + 1 Thing NOT To Do.
   * Executed Skills & Telemetry Strip with `LIVE`, `CALCULATED`, and `SIMULATED` badges.
   * Human Pre-Flight Checklist with mandatory risk verification checkboxes.
   * 1-Click Markdown Brief Exporter (`.md` download) and clipboard copy.
3. **Execution Assistance Desk Blotter:**
   * Side-by-side comparison between the raw proposal and calibrated safe ticket.
   * Bracket Stop-Loss and Take-Profit in exact dollar amounts and price targets.
   * Human Decision Trio (*Approve Safe Prescription*, *Override with Original*, *Reject & Pass*).
   * Background asynchronous TWAP execution engine logging to persistent paper ledger.
4. **46 Automated Unit & Integration Tests:** 100% test coverage across all risk engines, stress scenarios, rToken regimes, and API routes.

---

### Section 6: Verification & Quickstart

```bash
# 1. Clone & Install
cd "d:/development/Bitget Hackathon Project"
pip install -r requirements.txt

# 2. Run Automated Verification (46 tests pass)
pytest -v

# 3. Launch the Trading Desk
python run.py
```
Open **`http://localhost:8000`** in your browser. Test canonical demos using the HUD buttons or deep links:
* `http://localhost:8000?demo=nvda-weekend`
* `http://localhost:8000?demo=tilt-revenge`
* `http://localhost:8000?demo=doge-depth`
* `http://localhost:8000?demo=tech-var`
