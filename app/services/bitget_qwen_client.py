import logging
import json
import re
from typing import Dict, Any, Optional
import requests
from app.config import settings

logger = logging.getLogger(__name__)

class BitgetQwenClient:
    """
    Dedicated LLM Client for Bitget Qwen (qwen3.8-max).
    Provides high-availability secondary LLM capabilities for Alphaind, supporting
    both OpenAI-style Responses API (wire_api="responses") and Chat Completions API (wire_api="chat").
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        wire_api: Optional[str] = None
    ):
        self.api_key = api_key or settings.BITGET_QWEN_API_KEY
        self.model = model or settings.BITGET_QWEN_MODEL
        self.base_url = (base_url or settings.BITGET_QWEN_BASE_URL).rstrip("/")
        self.wire_api = (wire_api or settings.BITGET_QWEN_WIRE_API).lower().strip()
        self.provider_name = settings.BITGET_QWEN_NAME
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def is_configured(self) -> bool:
        """Check if Bitget Qwen API key is present and configured."""
        return bool(self.api_key and len(self.api_key) > 5 and not self.api_key.startswith("your_"))

    def call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 800,
        timeout: int = 30
    ) -> Optional[str]:
        """
        Execute an LLM request to the Bitget Qwen provider.
        Supports wire_api='responses' (/responses) with automatic fallback to /chat/completions.
        """
        if not self.is_configured():
            return None

        # 1. Primary path based on wire_api configuration
        if self.wire_api == "responses":
            text = self._call_responses_api(system_prompt, user_prompt, temperature, timeout)
            if text:
                return text
            # Fallback to chat completions if responses endpoint fails
            logger.warning("Bitget Qwen /responses endpoint did not return text; falling back to /chat/completions")
            return self._call_chat_api(system_prompt, user_prompt, temperature, max_tokens, timeout)
        else:
            text = self._call_chat_api(system_prompt, user_prompt, temperature, max_tokens, timeout)
            if text:
                return text
            logger.warning("Bitget Qwen /chat/completions endpoint did not return text; falling back to /responses")
            return self._call_responses_api(system_prompt, user_prompt, temperature, timeout)

    def _call_responses_api(self, system_prompt: str, user_prompt: str, temperature: float, timeout: int) -> Optional[str]:
        """Call the Bitget Ops /responses API endpoint."""
        url = f"{self.base_url}/responses"
        payload = {
            "model": self.model,
            "instructions": system_prompt,
            "input": user_prompt,
            "temperature": temperature
        }
        try:
            resp = requests.post(url, headers=self.headers, json=payload, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                extracted_text = ""
                for item in data.get("output", []):
                    if item.get("type") == "message":
                        for part in item.get("content", []):
                            if part.get("type") == "output_text":
                                extracted_text += part.get("text", "")
                if extracted_text.strip():
                    return extracted_text.strip()
            else:
                logger.warning(f"Bitget Qwen /responses returned status {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            logger.warning(f"Bitget Qwen /responses call failed: {e}")
        return None

    def _call_chat_api(self, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int, timeout: int) -> Optional[str]:
        """Call standard OpenAI-compatible /chat/completions endpoint."""
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        try:
            resp = requests.post(url, headers=self.headers, json=payload, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices and "message" in choices[0]:
                    content = choices[0]["message"].get("content", "")
                    if content.strip():
                        return content.strip()
            else:
                logger.warning(f"Bitget Qwen /chat/completions returned status {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            logger.warning(f"Bitget Qwen /chat/completions call failed: {e}")
        return None

    def parse_trading_intent(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Extract structured trading parameters from plain English using Bitget Qwen."""
        if not self.is_configured():
            return None

        system_msg = (
            "You are Alphaind Master Trading Orchestrator & Co-Pilot powered by Bitget Qwen. "
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
        raw_text = self.call_llm(system_msg, user_prompt, temperature=0.1, timeout=30)
        if not raw_text:
            return None

        content = raw_text.strip()
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
                try:
                    parsed = json.loads(content[s_idx:e_idx+1])
                except Exception:
                    pass

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
                    "parser_mode": "LLM_BITGET_QWEN"
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

            reasoning = parsed.get("reasoning") or f"Bitget Qwen Fallback Orchestrator analyzed request for {sym}."

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
                "parser_mode": "LLM_BITGET_QWEN",
                "is_trade": True
            }

        return None

    def review_pre_trade_threats(self, trade_details: Dict[str, Any], defense_report: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Synthesize 7-agent pre-trade defense report via Bitget Qwen."""
        if not self.is_configured():
            return None

        pillars = defense_report.get("pillars", {})
        vol = pillars.get("volatility_sentinel", {})
        fraud = pillars.get("scam_detector", {})
        sec = pillars.get("contract_security", {})
        liq = pillars.get("liquidity_auditor", {})
        psych = pillars.get("psychology_shield", {})
        quant = pillars.get("quant_analyst", {})
        backtest = pillars.get("strategy_backtester", {})

        overall_verdict = defense_report.get("overall_verdict", "SAFE")
        risk_score = defense_report.get("composite_risk_score", 0)
        threat_flags = defense_report.get("threat_flags", [])

        is_spot = trade_details.get("is_spot") or trade_details.get("market_type") == "spot" or trade_details.get("leverage", 1) == 1
        lev = trade_details.get("leverage", 1)
        trade_type_desc = "Spot Order (1x, No Liquidation Risk)" if is_spot else f"Perpetual Futures ({lev}x Leverage)"

        prompt = f"""
You are Alphaind, a warm, highly intelligent, and protective AI trading co-pilot on Bitget (powered by Qwen 3.8 Max).
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
7. Empirical Simulation (Backtester): Score {backtest.get('score', 0)}/100 ({backtest.get('status', 'N/A')}) - {backtest.get('summary', '')}

Overall Risk Score: {risk_score}/100
Master Orchestrator Verdict: {overall_verdict}
Active Flags: {threat_flags}

Output STRICT JSON:
{{
  "ai_verdict": "{overall_verdict}",
  "friendly_title": "Headline matching verdict and real findings",
  "conversational_explanation": "2-3 conversational paragraphs synthesizing what the 7 agents found.",
  "threat_level": "LOW" | "MODERATE" | "HIGH",
  "simple_takeaways": ["Point 1 in plain English", "Point 2 in plain English", "Point 3 in plain English"]
}}
"""
        system_msg = "You are Alphaind, a friendly and protective AI trading co-pilot powered by Bitget Qwen. Output strictly valid JSON."
        raw_text = self.call_llm(system_msg, prompt, temperature=0.2, timeout=30)
        if not raw_text:
            return None

        content = raw_text.strip()
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
                try:
                    return json.loads(content[start:end+1])
                except Exception:
                    pass
        return None

    def chat_copilot(self, query: str, context: Dict[str, Any]) -> Optional[str]:
        """Friendly natural-language chat response via Bitget Qwen."""
        if not self.is_configured():
            return None

        prompt = f"""
You are Alphaind, a friendly, supportive AI trading assistant on Bitget powered by Bitget Qwen.
The user is asking: "{query}".
Current context: {json.dumps(context)}.
Explain things simply and clearly without confusing Wall Street jargon. Keep your response under 120 words.
"""
        system_msg = "You are Alphaind, a beginner-friendly, protective crypto trading co-pilot."
        return self.call_llm(system_msg, prompt, temperature=0.4, max_tokens=300, timeout=30)

bitget_qwen_client = BitgetQwenClient()
