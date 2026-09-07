"""Pure decision gate. No network, no model calls.

approve() is the only path a proposed trade can take to reach broker.py.
Rejection is the default; every path to True is explicit.
"""

import config

VALID_ACTIONS = {"buy", "sell", "hold"}


def kill_switch_tripped(current_equity, starting_equity):
    if starting_equity <= 0:
        return False
    drawdown = (current_equity - starting_equity) / starting_equity
    return drawdown <= config.KILL_SWITCH_PCT


def forced_exits(positions):
    """Deterministic stop-loss / take-profit exits, evaluated before the model runs."""
    symbols = []
    for p in positions:
        plpc = p.get("unrealized_plpc", 0.0)
        if plpc <= config.STOP_LOSS_PCT or plpc >= config.TAKE_PROFIT_PCT:
            symbols.append(p["symbol"])
    return symbols


def _hold():
    return True, "hold", {"action": "hold"}


def approve(decision, account, positions, state):
    """Returns (ok: bool, reason: str, sanitized_decision: dict | None)."""
    action = decision.get("action") if isinstance(decision, dict) else None

    if action not in VALID_ACTIONS:
        return False, "invalid action", None

    if action == "hold":
        return _hold()

    if state.get("halted"):
        return False, "halted by kill switch", None

    if state.get("trades_today", 0) >= config.MAX_TRADES_PER_DAY:
        return False, "daily trade cap reached", None

    symbol = decision.get("symbol")
    held_symbols = {p["symbol"] for p in positions}

    if action == "sell":
        if symbol not in held_symbols:
            return False, "no long position to close (shorting not allowed)", None
        return True, "close", {"action": "sell", "symbol": symbol}

    # action == "buy"
    if symbol not in config.WATCHLIST:
        return False, "symbol not on watchlist", None

    if symbol in held_symbols:
        return False, "averaging up not allowed", None

    if len(positions) >= config.MAX_OPEN_POSITIONS:
        return False, "max open positions reached", None

    requested_notional = decision.get("notional", 0)
    if not isinstance(requested_notional, (int, float)) or requested_notional <= 0:
        return False, "invalid notional", None

    equity = account.get("equity", 0)
    cap = equity * config.MAX_POSITION_PCT
    sanitized_notional = min(requested_notional, cap)

    return True, "buy", {"action": "buy", "symbol": symbol, "notional": sanitized_notional}
