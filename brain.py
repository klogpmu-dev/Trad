"""The only module allowed to call the model. Proposes; never executes.

Any exception here returns HOLD. Never fail open into a trade.
"""

import json

from anthropic import Anthropic

import config

_client = Anthropic(api_key=config.ANTHROPIC_API_KEY) if config.ANTHROPIC_API_KEY else None

HOLD = {
    "action": "hold",
    "symbol": None,
    "notional": 0,
    "confidence": 0.0,
    "reasoning": "fallback: brain error or no output",
}

SYSTEM_PROMPT = """You are a trading decision agent for a small US-equities paper account.

Rules (hard constraints, not suggestions):
- Long only. Never propose shorting.
- Never propose adding to a position you already hold (no averaging up).
- Only propose symbols from the given watchlist.
- At most one action per call.

Respond with ONLY a JSON object, no prose, no markdown fences:
{"action": "buy" | "sell" | "hold", "symbol": "<TICKER or null>", "notional": <dollar amount or 0>, "confidence": <0.0-1.0>, "reasoning": "<one sentence>"}

"sell" means closing a position you currently hold. "buy" opens a new position.
"""


def _build_prompt(market_snapshot, account_state, positions, watchlist):
    return json.dumps(
        {
            "watchlist": watchlist,
            "market_snapshot": market_snapshot,
            "account": account_state,
            "open_positions": positions,
        }
    )


def decide(market_snapshot, account_state, positions, watchlist):
    if _client is None:
        return dict(HOLD)

    try:
        resp = _client.messages.create(
            model=config.MODEL,
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": _build_prompt(
                        market_snapshot, account_state, positions, watchlist
                    ),
                }
            ],
        )
        text = resp.content[0].text
        decision = json.loads(text)
        if not isinstance(decision, dict) or "action" not in decision:
            return dict(HOLD)
        return decision
    except Exception:
        return dict(HOLD)
