import logging
import json
import re
from typing import Dict, Any, Optional
import requests
from app.config import settings
from app.services.bitget_qwen_client import bitget_qwen_client

logger = logging.getLogger(__name__)

class OpenRouterClient:
    """
    OpenRouter AI Client tailored for Alphaind with automatic Bitget Qwen fallback.
    Generates beginner-friendly, crystal-clear conversational natural language debriefs
    and pre-trade guidance.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, fallback_client=None):
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        self.model = model or settings.OPENROUTER_MODEL
        self.base_url = settings.OPENROUTER_BASE_URL
        self.fallback_client = fallback_client or bitget_qwen_client
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://bitget.com",
            "X-Title": "Alphaind AI Trading Desk"
        }

    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 5 and not self.api_key.startswith("your_"))

    def is_fallback_configured(self) -> bool:
        return bool(self.fallback_client and self.fallback_client.is_configured())

    def get_active_provider(self) -> str:
        if self.is_configured():
            return "openrouter"
        elif self.is_fallback_configured():
            return settings.FALLBACK_MODEL_PROVIDER
        return "heuristic"

    def parse_trading_intent(self, prompt: str) -> Dict[str, Any]:
        """
        Master Orchestrator Natural Language Parser:
        Extracts structured trading parameters from natural language trader prompt using LLM,
        with an intelligent deterministic fallback.
        """
        if not self.is_configured():
            if self.fallback_client and self.fallback_client.is_configured():
                logger.info("OpenRouter not configured. Routing intent parsing to Bitget Qwen fallback.")
                fb_intent = self.fallback_client.parse_trading_intent(prompt)
                if fb_intent:
                    return fb_intent
            return self._heuristic_parse_intent(prompt)

        system_msg = (
            "You are Alphaind Master Trading Orchestrator & Co-Pilot. "
            "Analyze the trader's message and determine whether it is a trade directive / asset analysis request, "
            "or a conversational / readiness / general question. "
            "Output strictly valid JSON matching the specified schema."
        )
        user_prompt = f"""Analyze this trader message:
"{prompt}"

First determine intent:
Is this an actionable trade instruction, order directive, or asset analysis/audit (e.g. "buy $10 eth", "long sol 3x", "safe btc swing", "audit pepe", "sell 1 btc")?
Or is it a conversational greeting, readiness check, capability inquiry, or chat (e.g. "Are you ready", "hello", "hi", "what can you do", "who are you", "help")?

Extract these fields:
- is_trade: boolean. Set to true if the message is asking to trade, buy, sell, audit, scan, or analyze a specific asset or strategy. Set to false if it is a greeting, readiness check ("are you ready"), general inquiry, or conversational chat.
- symbol: string or null. If is_trade is true, the Bitget pair symbol ending in USDT (e.g. "BTCUSDT", "ETHUSDT", "SOLUSDT", "NVDAUSDT", "BGBUSDT", "DOGEUSDT"). If is_trade is false, MUST BE null (do NOT use placeholder defaults like BTCUSDT).
- side: "buy" or "sell" if is_trade is true, or null if is_trade is false.
- dollar_amount: float (fiat/USDT budget specified, e.g. 10.0 for "ten dollars", 50.0 for "$50", 1000.0 for "$1,000 worth"), or null.
- token_size: float (quantity of coin/token units specified, e.g. 0.15 for "0.15 BTC", 2.0 for "2 eth", 0.5 for "half a btc"), or null.
- leverage: integer leverage multiplier (1 for spot or unstated leverage, 2 for 2x, 5 for 5x, 10 for 10x), default 1.
- market_type: "spot" or "perp" ("spot" if leverage is 1 and no shorting/futures mentioned; "perp" if leverage > 1 or shorting/futures).
- order_type: "market" or "limit" (default "market").
- conversational_reply: string or null. If is_trade is false, provide a warm, helpful, 1-2 sentence direct response to the user's message (e.g. answering "Are you ready" with "I am completely ready! All 7 defense and quant sub-agents are online and calibrated. What coin or trade directive would you like to inspect or execute?"). If is_trade is true, set to null.
- reasoning: brief explanation of your classification and parameters.

Output strict JSON format.
Example 1 (Trade):
{{
  "is_trade": true,
  "symbol": "ETHUSDT",
  "side": "buy",
  "dollar_amount": 10.0,
  "token_size": null,
  "leverage": 1,
  "market_type": "spot",
  "order_type": "market",
  "conversational_reply": null,
  "reasoning": "Trader requested to buy $10 of ETH spot."
}}

Example 2 (Conversational / Readiness):
{{
  "is_trade": false,
  "symbol": null,
  "side": null,
  "dollar_amount": null,
  "token_size": null,
  "leverage": 1,
  "market_type": "spot",
  "order_type": "market",
  "conversational_reply": "I am fully ready! All 7 defense & quantitative sub-agents are active and calibrated. What asset would you like to trade or analyze?",
  "reasoning": "Trader asked if I am ready. No trade directive."
}}
"""
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.1,
                "response_format": {"type": "json_object"},
                "max_tokens": 700
            }
            resp = requests.post(f"{self.base_url}/chat/completions", headers=self.headers, json=payload, timeout=8)
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"].strip()
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                parsed = None
                try:
                    parsed = json.loads(content)
                except Exception:
                    s_idx = content.find("{")
                    e_idx = content.rfind("}")
                    if s_idx != -1 and e_idx != -1:
                        parsed = json.loads(content[s_idx:e_idx+1])

                if parsed and isinstance(parsed, dict):
                    is_trade = parsed.get("is_trade")
                    raw_sym = parsed.get("symbol")
                    reply = parsed.get("conversational_reply")

                    # Check if classified as non-trade or symbol is missing/falsy/placeholder
                    if (
                        is_trade is False
                        or not raw_sym
                        or str(raw_sym).upper().strip() in ("NONE", "NULL", "N/A", "NONEUSDT", "NONE/USDT", "FALSE")
                    ):
                        return {
                            "is_trade": False,
                            "symbol": None,
                            "side": None,
                            "dollar_amount": None,
                            "token_size": None,
                            "size": 0.0,
                            "leverage": 1,
                            "market_type": "spot",
                            "is_spot": True,
                            "order_type": "market",
                            "conversational_reply": reply,
                            "llm_reasoning": parsed.get("reasoning") or "Non-trade conversational interaction detected.",
                            "parser_mode": "LLM_OPENROUTER"
                        }

                    sym = str(raw_sym).upper().strip()
                    if not sym.endswith("USDT"):
                        sym = sym + "USDT"

                    side = str(parsed.get("side", "buy")).lower().strip()
                    if side not in ("buy", "sell"):
                        side = "buy"

                    dollar_amount = parsed.get("dollar_amount")
                    if dollar_amount is not None:
                        try:
                            dollar_amount = float(dollar_amount)
                            if dollar_amount <= 0:
                                dollar_amount = None
                        except (ValueError, TypeError):
                            dollar_amount = None

                    token_size = parsed.get("token_size")
                    if token_size is not None:
                        try:
                            token_size = float(token_size)
                            if token_size <= 0:
                                token_size = None
                        except (ValueError, TypeError):
                            token_size = None

                    lev = parsed.get("leverage", 1)
                    try:
                        lev = int(lev)
                    except (ValueError, TypeError):
                        lev = 1
                    lev = min(125, max(1, lev))

                    mkt_type = str(parsed.get("market_type", "spot")).lower().strip()
                    if mkt_type not in ("spot", "perp"):
                        mkt_type = "spot" if lev == 1 else "perp"
                    if lev > 1:
                        mkt_type = "perp"

                    ord_type = str(parsed.get("order_type", "market")).lower().strip()
                    if ord_type not in ("market", "limit"):
                        ord_type = "market"

                    reasoning = parsed.get("reasoning") or f"LLM Orchestrator analyzed request for {sym}."

                    return {
                        "symbol": sym,
                        "side": side,
                        "dollar_amount": dollar_amount,
                        "token_size": token_size,
                        "size": token_size if token_size is not None else 0.1,
                        "leverage": 1 if mkt_type == "spot" else lev,
                        "market_type": mkt_type,
                        "is_spot": mkt_type == "spot",
                        "order_type": ord_type,
                        "conversational_reply": None,
                        "llm_reasoning": reasoning,
                        "parser_mode": "LLM_OPENROUTER",
                        "is_trade": True
                    }
        except Exception as e:
            logger.warning(f"OpenRouter intent analysis failed ({e}). Attempting Bitget Qwen fallback...")

        # Fallback to Bitget Qwen
        if self.fallback_client and self.fallback_client.is_configured():
            logger.info("Routing intent parsing to Bitget Qwen fallback.")
            fb_intent = self.fallback_client.parse_trading_intent(prompt)
            if fb_intent:
                return fb_intent

        logger.warning("All LLMs unavailable; using intelligent heuristic fallback.")
        return self._heuristic_parse_intent(prompt)

    @classmethod
    def normalize_number_words(cls, text: str) -> str:
        """Convert natural language English number words to digits."""
        word_map = {
            "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
            "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
            "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
            "eighty": 80, "ninety": 90, "hundred": 100, "thousand": 1000,
            "half": 0.5, "quarter": 0.25
        }
        res = re.sub(r'\bhalf\s+(?:an?|of)?\s*', '0.5 ', text, flags=re.IGNORECASE)
        res = re.sub(r'\bquarter\s+(?:an?|of)?\s*', '0.25 ', res, flags=re.IGNORECASE)
        tens = ["twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
        ones = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
        for t in tens:
            for o in ones:
                val = word_map[t] + word_map[o]
                res = re.sub(rf'\b{t}[\s-]{o}\b', str(val), res, flags=re.IGNORECASE)
        for w, val in word_map.items():
            if w not in ("half", "quarter"):
                res = re.sub(rf'\b{w}\b', str(val), res, flags=re.IGNORECASE)
        return res

    def _heuristic_parse_intent(self, prompt: str) -> Dict[str, Any]:
        """Deterministic NLP intent extractor with word-number normalization."""
        # Check for conversational greeting or general question without trade actions
        clean_p = prompt.strip().lower()
        clean_words = re.sub(r'[^\w\s]', '', clean_p).strip()
        greetings = {
            "hello", "hi", "hey", "hola", "howdy", "hiya", "greetings",
            "good morning", "good evening", "good afternoon", "good day",
            "yo", "sup", "whats up", "what's up", "wassup",
            "help", "who are you", "what are you", "what can you do",
            "what is this", "what is alphaind", "how does this work",
            "how do i use this", "introduce yourself", "tell me about yourself",
            "are you ready", "ready", "status", "ping", "test"
        }
        trade_actions = {"buy", "sell", "long", "short", "leverage", "spot", "perp", "futures", "order", "margin", "swap", "trade", "scalp", "invest", "dollar", "dollars", "usd", "usdt", "worth", "$"}
        words = set(clean_words.split())
        has_trade_action = bool(words & trade_actions or any(a in clean_p for a in ["$", "usd", "usdt"]))
        
        if not has_trade_action:
            if clean_words in greetings or "ready" in clean_words or re.match(r'^(hello|hi|hey|greetings|good\s+(morning|afternoon|evening)|yo|sup|help|who\s+are\s+you|are\s+you\s+ready)[\s!?,.]*$', clean_p):
                reply = (
                    "I am completely ready! All 7 defense and quantitative sub-agents are online and calibrated. What coin or trade directive would you like to inspect or execute?"
                    if "ready" in clean_words
                    else "Hello! I'm Alphaind, your AI Trade Co-Pilot on Bitget. How can I assist you with your trading today?"
                )
                return {
                    "is_trade": False,
                    "symbol": None,
                    "side": None,
                    "dollar_amount": None,
                    "token_size": None,
                    "size": 0.0,
                    "leverage": 1,
                    "market_type": "spot",
                    "is_spot": True,
                    "order_type": "market",
                    "conversational_reply": reply,
                    "llm_reasoning": "Conversational greeting or readiness check detected.",
                    "parser_mode": "HEURISTIC_NLP"
                }

        norm_prompt = self.normalize_number_words(prompt)
        text = norm_prompt.upper()

        # Symbol extraction
        symbol = "BTCUSDT"
        pair_match = re.search(r'\b([A-Z0-9]{2,16})USDT\b', text)
        if pair_match:
            symbol = pair_match.group(1) + "USDT"
        elif any(s in text for s in ["PEPE100XINU", "HONEYPOT", "SCAMCOIN", "SAFEMOON", "ELONDOGE"]):
            for s in ["PEPE100XINU", "HONEYPOT", "SCAMCOIN", "SAFEMOON", "ELONDOGE"]:
                if s in text:
                    symbol = s + "USDT" if not s.endswith("USDT") else s
                    break
        elif "BTC" in text or "BITCOIN" in text:
            symbol = "BTCUSDT"
        elif "ETH" in text or "ETHEREUM" in text:
            symbol = "ETHUSDT"
        elif "SOL" in text or "SOLANA" in text:
            symbol = "SOLUSDT"
        elif "BGB" in text:
            symbol = "BGBUSDT"
        elif "DOGE" in text:
            symbol = "DOGEUSDT"
        elif "NVDA" in text or "NVIDIA" in text:
            symbol = "NVDAUSDT"
        elif "TSLA" in text or "TESLA" in text:
            symbol = "TSLAUSDT"
        elif "AAPL" in text or "APPLE" in text:
            symbol = "AAPLUSDT"
        elif "COINBASE" in text or bool(re.search(r'\bCOIN\b', text)):
            symbol = "COINUSDT"
        elif "SPY" in text or "S&P" in text:
            symbol = "SPYUSDT"
        elif "MSFT" in text or "MICROSOFT" in text:
            symbol = "MSFTUSDT"
        elif "XRP" in text:
            symbol = "XRPUSDT"
        elif "ADA" in text:
            symbol = "ADAUSDT"
        elif "AVAX" in text:
            symbol = "AVAXUSDT"
        elif "LINK" in text:
            symbol = "LINKUSDT"
        elif "SUI" in text:
            symbol = "SUIUSDT"
        elif "PEPE" in text:
            symbol = "PEPEUSDT"
        elif "SHIB" in text:
            symbol = "SHIBUSDT"
        else:
            susp_match = re.search(r'\b([A-Z0-9]*(?:100X|INU|SAFE|MOON|ELON|V2|HONEYPOT)[A-Z0-9]*)\b', text)
            if susp_match and len(susp_match.group(1)) >= 3:
                symbol = susp_match.group(1) + "USDT"

        # Side extraction
        side = "buy"
        if any(w in text for w in ["SHORT", "SELL", "DUMP", "BEAR"]):
            side = "sell"
        elif any(w in text for w in ["LONG", "BUY", "ACCUMULATE", "BULL"]):
            side = "buy"

        # Market Type (Spot vs Perp / Futures)
        is_spot = False
        is_perp = False
        if "SPOT" in text:
            is_spot = True
        elif any(w in text for w in ["PERP", "PERPETUAL", "FUTURES", "SWAP", "MARGIN"]):
            is_perp = True

        # Leverage extraction
        leverage = 1
        lev_match = re.search(r'(\d+)\s*[xX]', text)
        if lev_match:
            leverage = int(lev_match.group(1))
            if leverage > 1:
                is_perp = True
                is_spot = False
        else:
            lev_word_match = re.search(r'LEVERAGE\s*(\d+)', text)
            if lev_word_match:
                leverage = int(lev_word_match.group(1))
                if leverage > 1:
                    is_perp = True
                    is_spot = False
            elif is_perp:
                leverage = 3
            elif any(w in text for w in ["SHORT", "LONG"]):
                is_perp = True
                leverage = 3
            else:
                is_spot = True
                leverage = 1

        if is_spot:
            leverage = 1
            market_type = "spot"
        else:
            market_type = "perp"

        # Dollar amounts check: e.g. "$1,000", "10 DOLLARS", "100 USDT", "10 BUCKS", "TEN DOLLARS"
        dollar_amount = None
        dollar_match = re.search(r'\$\s*([\d,]+(?:\.\d+)?)|([\d,]+(?:\.\d+)?)\s*(?:USD|USDT|BUCKS|DOLLARS|BUX|WORTH)', text)
        if dollar_match:
            raw_dollar = dollar_match.group(1) or dollar_match.group(2)
            try:
                dollar_amount = float(raw_dollar.replace(',', ''))
            except (ValueError, TypeError):
                dollar_amount = None

        # Explicit token quantity
        token_size = None
        num_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:BTC|ETH|SOL|BGB|DOGE|XRP|ADA|AVAX|LINK|SUI|NVDA|TSLA|AAPL|COIN|SPY|MSFT|COINS|UNITS|SHARES|STOCKS)\b', text)
        if num_match:
            token_size = float(num_match.group(1))

        # Order Type
        order_type = "market"
        if "LIMIT" in text:
            order_type = "limit"

        reasoning = f"Heuristic NLP analysis extracted {side.upper()} order for {symbol}"
        if dollar_amount:
            reasoning += f" with budget ${dollar_amount:,.2f} USDT."
        elif token_size:
            reasoning += f" for {token_size} token units."
        else:
            reasoning += "."

        return {
            "symbol": symbol,
            "side": side,
            "dollar_amount": dollar_amount,
            "token_size": token_size,
            "size": token_size if token_size is not None else 0.1,
            "leverage": 1 if market_type == "spot" else min(125, max(1, leverage)),
            "order_type": order_type,
            "market_type": market_type,
            "is_spot": market_type == "spot",
            "llm_reasoning": reasoning,
            "parser_mode": "HEURISTIC_NLP",
            "is_trade": True
        }

    def review_pre_trade_threats(self, trade_details: Dict[str, Any], defense_report: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize 7-pillar findings into friendly, conversational natural language."""
        if not self.is_configured():
            return self._friendly_heuristic_review(trade_details, defense_report)

        is_spot = trade_details.get("is_spot") or trade_details.get("market_type") == "spot" or trade_details.get("leverage", 1) == 1
        trade_type_desc = "Spot Order (Asset Purchase, No Leverage, Zero Liquidation Risk)" if is_spot else f"Perpetual Futures ({trade_details.get('leverage', 1)}x Leverage)"

        pillars = defense_report.get("pillars", {})
        vol = pillars.get("volatility", {"score": 10, "status": "SAFE", "summary": "Price volatility within normal ranges."})
        fraud = pillars.get("scam_fraud", {"score": 5, "status": "SAFE", "summary": "Contract verified clean."})
        sec = pillars.get("security", {"score": 5, "status": "SAFE", "summary": "Ownership safe."})
        liq = pillars.get("liquidity", {"score": 10, "status": "SAFE", "summary": "Orderbook depth healthy."})
        psych = pillars.get("psychology", {"score": 10, "status": "SAFE", "summary": "Mindset disciplined."})
        quant = pillars.get("quant_analyst", {"score": 20, "status": "ACCEPTABLE", "summary": "Quantitative factors checked."})
        backtest = pillars.get("strategy_backtester", {"score": 20, "status": "ACCEPTABLE", "summary": "Empirical simulation complete."})

        overall_verdict = defense_report.get("overall_verdict", "CAUTION")
        risk_score = defense_report.get("composite_risk_score", 35)
        threat_flags = defense_report.get("threat_flags", [])

        prompt = f"""
You are Alphaind, a warm, highly intelligent, and protective AI trading co-pilot on Bitget.
A trader just entered this trade request:
- Coin: {trade_details.get('symbol')}
- Action: {trade_details.get('side', 'buy').upper()}
- Amount: {trade_details.get('size')} (~${trade_details.get('notional_usdt', 0):,.2f} USDT value)
- Trade Type: {trade_type_desc}

Our 7 specialized sub-agents just finished their scans:
1. Volatility Sentinel: Score {vol.get('score', 0)}/100 ({vol.get('status', 'N/A')}) - {vol.get('summary', '')}
2. Scam & Fraud Hunter: Score {fraud.get('score', 0)}/100 ({fraud.get('status', 'N/A')}) - {fraud.get('summary', '')}
3. Security Guard: Score {sec.get('score', 0)}/100 ({sec.get('status', 'N/A')}) - {sec.get('summary', '')}
4. Liquidity & Slippage: Score {liq.get('score', 0)}/100 ({liq.get('status', 'N/A')}) - {liq.get('summary', '')}
5. Mindset & Tilt Check: Score {psych.get('score', 0)}/100 ({psych.get('status', 'N/A')}) - {psych.get('summary', '')}
6. Statistical Factors (Quant): Score {quant.get('score', 0)}/100 ({quant.get('status', 'N/A')}) - {quant.get('summary', '')}
7. Empirical Simulation (Backtester): Score {backtest.get('score', 0)}/100 ({backtest.get('status', 'N/A')}) - {backtest.get('summary', '')} (Return: {backtest.get('metrics', {}).get('total_return_pct', 'N/A')}%, Sharpe: {backtest.get('metrics', {}).get('sharpe_ratio', 'N/A')})

Overall Risk Score: {risk_score}/100
Master Orchestrator Verdict: {overall_verdict}
Active Flags: {threat_flags}

CRITICAL RULES:
- The Master Orchestrator Verdict is "{overall_verdict}". Output "ai_verdict": "{overall_verdict}".
- If Strategy Backtester or Quantitative Analyst shows negative expectancy, negative Sharpe, or cautionary flags, YOU MUST PROMINENTLY ADDRESS THIS! Explain to the user why the historical track record is unfavorable and why breakout momentum lacks statistical edge.
- NEVER say "All clear" or "everything checked out smoothly" when the Strategy Backtester or Quant Analyst found negative expectancy or warnings!
- Explain things in clear, supportive language for a trader.

Output STRICT JSON:
{{
  "ai_verdict": "{overall_verdict}",
  "friendly_title": "Headline matching verdict and real findings",
  "conversational_explanation": "2-3 conversational paragraphs synthesizing what the 7 agents found. Explicitly discuss the empirical backtest and statistical factors alongside security and liquidity.",
  "threat_level": "LOW" | "MODERATE" | "HIGH",
  "simple_takeaways": ["Point 1 in plain English", "Point 2 in plain English", "Point 3 in plain English"]
}}
"""
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are Alphaind, a friendly and protective AI trading co-pilot. You speak in simple, clear, conversational human language. Output strictly valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
                "max_tokens": 800
            }
            if self.is_configured():
                resp = requests.post(f"{self.base_url}/chat/completions", headers=self.headers, json=payload, timeout=12)
                if resp.status_code == 200:
                    content = resp.json()["choices"][0]["message"]["content"].strip()
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0].strip()
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0].strip()
                    try:
                        return json.loads(content)
                    except Exception:
                        start = content.find("{")
                        end = content.rfind("}")
                        if start != -1 and end != -1:
                            return json.loads(content[start:end+1])
                else:
                    logger.warning(f"OpenRouter natural language synthesis returned status {resp.status_code}.")
        except Exception as e:
            logger.warning(f"OpenRouter natural language synthesis failed ({e}). Attempting Bitget Qwen fallback...")

        # Fallback to Bitget Qwen
        if self.fallback_client and self.fallback_client.is_configured():
            logger.info("Routing pre-trade threat review to Bitget Qwen fallback.")
            fb_review = self.fallback_client.review_pre_trade_threats(trade_details, defense_report)
            if fb_review:
                return fb_review

        return self._friendly_heuristic_review(trade_details, defense_report)

    def _friendly_heuristic_review(self, trade: Dict[str, Any], report: Dict[str, Any]) -> Dict[str, Any]:
        verdict = report.get("overall_verdict", "SAFE")
        score = report.get("composite_risk_score", 15)
        symbol = trade.get("symbol", "BTCUSDT").replace("USDT", "")
        side = trade.get("side", "buy").lower()
        size = trade.get("size", 0.1)
        lev = trade.get("leverage", 1)
        is_spot = trade.get("is_spot") or trade.get("market_type") == "spot" or lev == 1

        action_desc = "buy" if side == "buy" else "sell"
        trade_desc = "spot trade" if is_spot else f"{lev}x leverage"

        pillars = report.get("pillars", {})
        backtest_info = pillars.get("strategy_backtester", {})
        quant_info = pillars.get("quant_analyst", {})

        bt_metrics = backtest_info.get("metrics", {})
        bt_return = bt_metrics.get("total_return_pct", 0.0)
        bt_sharpe = bt_metrics.get("sharpe_ratio", 0.0)
        bt_status = backtest_info.get("status", "")
        has_bt_negative = bt_status == "NEGATIVE_EXPECTANCY" or bt_return < 0 or bt_sharpe < 0

        quant_metrics = quant_info.get("metrics", {})
        quant_regime = quant_metrics.get("hurst_regime", "Mean-Reverting" if "Anti-Persistent" in quant_info.get("human_status", "") else "Nominal")
        has_quant_warning = quant_info.get("score", 0) >= 40 or "Anti-Persistent" in quant_info.get("human_status", "") or quant_info.get("status") in ("WEAK_EDGE", "UNCERTAIN")

        # Incorporate rToken regime and stress test findings if present
        rtoken_info = report.get("rtoken_regime", {})
        stress_info = report.get("stress_test", {})

        if verdict in ("BLOCKED", "INTERCEPTED_BLOCK"):
            title = f"Trade Paused for Your Safety"
            if is_spot:
                explanation = (
                    f"Hey there! We had our 7 specialized sub-agents inspect your request to {action_desc} {size} {symbol} (spot order). "
                    f"We noticed serious warning signs—specifically around token security, elevated market volatility, or abnormal price action. "
                    f"To protect your capital, Alphaind has paused this order. Please review the security and risk audit below before confirming."
                )
                threat_level = "HIGH"
                takeaways = [
                    f"Spot trade paused due to elevated asset risk or market anomalies.",
                    "Review token audit and volatility flags before proceeding.",
                    "1-Click Safe Prescription available to optimize execution."
                ]
            else:
                explanation = (
                    f"Hey there! We had our 7 specialized sub-agents inspect your request to {action_desc} {size} {symbol} with {lev}x leverage. "
                    f"We noticed serious warning signs—specifically around emotional tilt, excessive leverage, or liquidity exposure. "
                    f"When using {lev}x leverage, even a tiny sudden market dip can wipe out your funds entirely. "
                    f"To protect your capital, Alphaind has paused this order. We recommend clicking 'Apply AI Safe Prescription' below to auto-adjust parameters."
                )
                threat_level = "HIGH"
                takeaways = [
                    f"High leverage ({lev}x) significantly increases liquidation danger.",
                    f"Stress test indicates high vulnerability to historical liquidity cascades.",
                    "1-Click Safe Prescription available to de-risk this position."
                ]
        elif verdict in ("CAUTION", "ADVISORY_CAUTION"):
            if has_bt_negative:
                title = f"Proceed with Caution: Unfavorable Historical Performance Detected"
                quant_text = f"In addition, our Quantitative Analyst detected an {quant_regime} regime, meaning price action is prone to mean-reverting pullbacks rather than strong follow-through. " if has_quant_warning else ""
                explanation = (
                    f"Hello! Our 7 sub-agents completed their pre-trade flight check for your plan to {action_desc} {size} {symbol} ({trade_desc}). "
                    f"While fundamental contract security, fraud auditing, and orderbook liquidity are verified clean, our Strategy Backtester issued an alert: "
                    f"recent historical simulations yielded negative expectancy ({bt_return:+.1f}% return, Sharpe {bt_sharpe:.2f}). "
                    f"{quant_text}"
                    f"Even though spot purchases carry zero liquidation risk, historical strategy performance suggests entering now carries an adverse risk-reward ratio. We recommend reviewing entry filters or using the 1-Click Safe Prescription to apply protective bracket safeguards."
                )
                threat_level = "MODERATE"
                takeaways = [
                    f"Empirical Simulation Warning: Negative expectancy ({bt_return:+.1f}% return, Sharpe {bt_sharpe:.2f}).",
                    f"Statistical Factors: {quant_regime} regime - Mean-reversion risk." if has_quant_warning else "Market price turbulence is above average.",
                    "Zero liquidation risk on spot purchase." if is_spot else "Review stop-loss buffer to protect against downside drag.",
                    "1-Click Safe Prescription available to optimize entry and protection."
                ]
            elif rtoken_info.get("is_rtoken") and not rtoken_info.get("session_info", {}).get("is_regular_market_hours"):
                title = f"Proceed with Caution: 7x24 Tokenized Equity Off-Hours"
                explanation = (
                    f"Hello! Our 7 sub-agents reviewed your plan to {action_desc} {size} {symbol} ({trade_desc}). You are trading a 7×24 Tokenized US Equity ({symbol}) outside regular NYSE hours. "
                    f"Off-hours spreads are wider ({rtoken_info['session_info'].get('spread_multiplier', 2)}x) and weekend gap risks are elevated. Review the safe prescription below to optimize execution."
                )
                threat_level = "MODERATE"
                takeaways = [
                    f"7×24 rToken Off-Hours regime detected ({rtoken_info['session_info'].get('spread_multiplier', 2)}x spread).",
                    "Zero liquidation risk (spot asset)." if is_spot else "Review the Stress Test survival buffer before confirming.",
                    "Consider applying the AI Safe Prescription to minimize slippage."
                ]
            else:
                title = f"Proceed with Caution: Advisory Flags Detected"
                explanation = (
                    f"Hello! Our 7 sub-agents reviewed your plan to {action_desc} {size} {symbol} ({trade_desc}). The trade is manageable, "
                    f"but there are cautionary flags you should know before confirming. Review the safe prescription below to optimize execution."
                )
                threat_level = "MODERATE"
                takeaways = [
                    "Market price swings or factor turbulence above average.",
                    "Zero liquidation risk (spot asset)." if is_spot else "Review the Stress Test survival buffer before confirming.",
                    "Consider applying the AI Safe Prescription to minimize slippage."
                ]
        else:
            title = f"All Clear! This Trade Looks Safe & Healthy"
            trade_subtext = "spot purchase, zero liquidation risk" if is_spot else f"{lev}x leverage"
            explanation = (
                f"Great news! Our 7 sub-agents and quant backtest layer scanned the market for your plan to {action_desc} {size} {symbol} ({trade_subtext}), "
                f"and all defense and quantitative checks passed smoothly. Price swings are steady, orderbook liquidity is deep, and empirical simulation confirmed positive expectancy. You're in great shape to execute whenever you're ready!"
            )
            threat_level = "LOW"
            takeaways = [
                f"Asset {symbol} is verified authentic with healthy orderbook depth.",
                "Zero liquidation risk on spot asset ownership." if is_spot else "Position survived all historical crisis stress test scenarios.",
                "Empirical simulation and quant factor analysis confirm positive statistical conditions."
            ]

        return {
            "ai_verdict": verdict,
            "friendly_title": title,
            "conversational_explanation": explanation,
            "threat_level": threat_level,
            "simple_takeaways": takeaways
        }

    def chat_copilot(self, query: str, context: Dict[str, Any]) -> str:
        """Friendly natural-language chat for beginners with automatic Bitget Qwen fallback."""
        if self.is_configured():
            try:
                prompt = f"""
You are Alphaind, a friendly, supportive AI trading assistant on Bitget.
The user is asking: "{query}".
Current context: {json.dumps(context)}.
Explain things simply and clearly without confusing Wall Street jargon. Keep your response under 120 words.
"""
                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are Alphaind, a beginner-friendly, protective crypto trading co-pilot."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.4,
                    "max_tokens": 300
                }
                resp = requests.post(f"{self.base_url}/chat/completions", headers=self.headers, json=payload, timeout=12)
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"].strip()
                else:
                    logger.warning(f"OpenRouter copilot chat returned status {resp.status_code}")
            except Exception as e:
                logger.error(f"OpenRouter copilot chat error: {e}. Attempting Bitget Qwen fallback...")

        # Fallback to Bitget Qwen
        if self.fallback_client and self.fallback_client.is_configured():
            logger.info("Routing copilot chat to Bitget Qwen fallback.")
            fb_reply = self.fallback_client.chat_copilot(query, context)
            if fb_reply and fb_reply.strip():
                return fb_reply.strip()

        return "Everything looks steady on the market. How can I help you plan your next trade?"

openrouter_client = OpenRouterClient()
