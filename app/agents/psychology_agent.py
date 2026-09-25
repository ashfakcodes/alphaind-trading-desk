import asyncio
from typing import Dict, Any, List

class PsychologyAgent:
    """
    Dedicated Sub-Agent 5: Trader Mindset & Tilt Protection.
    Protects beginners from trading out of anger, FOMO, or revenge after a loss.
    """
    AGENT_NAME = "Psychology Shield"
    HUMAN_TITLE = "Mindset & Risk Check"
    ROLE = "FOMO, Revenge Trading & Emotional Guard"

    @classmethod
    async def analyze(cls, context: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(0.05)

        order = context.get("order_intent", {})
        side = order.get("side", "buy").lower()
        size = float(order.get("size", 0.1))
        leverage = int(order.get("leverage", 1))
        prompt_text = context.get("raw_prompt", "").lower()
        recent_trades = context.get("recent_trades", [])
        quant = context.get("quant_data", {})

        rsi = quant.get("rsi", 50.0)
        z_score = quant.get("z_score", 0.0)

        risk_score = 10
        flags: List[str] = []
        thought_trace: List[str] = [
            "Checking if your trade is based on a calm plan or driven by FOMO / frustration.",
            f"Checking your leverage ({leverage}x): How quickly could a minor dip liquidate you?"
        ]

        # Emotion keywords
        tilt_words = ["angry", "revenge", "make it back", "all in", "pump it", "fomo", "fast", "immediately", "fuck", "loss"]
        found_tilt = [w for w in tilt_words if w in prompt_text]
        if found_tilt:
            risk_score += 45
            flags.append("Emotional trading detected: Trading out of frustration or greed leads to fast losses.")
            thought_trace.append(f"Caution: Found emotional trigger words: {', '.join(found_tilt)}.")

        if leverage >= 20:
            risk_score += 45
            flags.append(f"Dangerous leverage multiplier ({leverage}x): A tiny 3%-5% dip will erase your entire trade.")
            thought_trace.append(f"Excessive leverage warning: {leverage}x provides virtually zero breathing room.")
        elif leverage > 7:
            risk_score += 20
            flags.append(f"Elevated leverage ({leverage}x): Higher risk of liquidation during brief dips.")

        if side == "buy" and (rsi > 75.0 or z_score > 2.5):
            risk_score += 30
            flags.append("FOMO Alert: You are buying right after a huge rally. High chance of buying at the top.")
            thought_trace.append("Buying at overbought peak: Favorable risk-reward has passed.")

        # Loss streaks
        recent_closed = [t for t in recent_trades if "pnl" in t][-5:]
        losses = sum(1 for t in recent_closed if t["pnl"] < 0)
        if losses >= 3:
            risk_score += 35
            flags.append("Revenge trading warning: You've experienced multiple recent losses. Take a break.")
            thought_trace.append("Trader is coming off multiple losses. High risk of revenge doubling down.")

        risk_score = min(100, risk_score)
        status = "SAFE" if risk_score < 35 else ("WARNING" if risk_score < 70 else "DANGER")

        if status == "SAFE":
            plain_summary = "Disciplined & Calm: Reasonable leverage and no emotional chasing detected."
            human_status = "Calm & Disciplined"
        elif status == "WARNING":
            plain_summary = "Caution: Elevated leverage or buying late in a price rally."
            human_status = "Elevated Risk"
        else:
            plain_summary = "EMOTIONAL DANGER: High FOMO or excessive leverage will likely lead to fast liquidation."
            human_status = "Tilt Alert"

        return {
            "agent": cls.AGENT_NAME,
            "role": cls.ROLE,
            "status": status,
            "human_status": human_status,
            "score": risk_score,
            "metrics": {
                "leverage_level": f"{leverage}x (" + ("Safe" if leverage <= 5 else ("Moderate" if leverage <= 10 else "High Risk")) + ")",
                "emotional_urgency": "Low" if not found_tilt else "High",
                "loss_streak": f"{losses} recent losses"
            },
            "flags": flags,
            "thought_trace": thought_trace,
            "summary": plain_summary
        }
