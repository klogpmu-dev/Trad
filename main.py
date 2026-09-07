"""Loop that enforces the core invariant:

forced exits (deterministic) -> kill switch -> brain -> risk gate -> execute

The model is consulted third and obeyed last.
"""

import json
import os
import time
from datetime import date

import config
import broker
import risk
import brain


def load_state():
    if os.path.exists(config.STATE_FILE):
        with open(config.STATE_FILE) as f:
            return json.load(f)
    acct = broker.account()
    return {
        "starting_equity": acct["equity"],
        "trade_date": None,
        "trades_today": 0,
        "halted": False,
    }


def save_state(state):
    with open(config.STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def log_decision(record):
    record["ts"] = time.time()
    with open(config.DECISIONS_LOG, "a") as f:
        f.write(json.dumps(record) + "\n")


def _reset_daily_counter(state):
    today = str(date.today())
    if state.get("trade_date") != today:
        state["trade_date"] = today
        state["trades_today"] = 0


def run_once(state):
    _reset_daily_counter(state)

    if state.get("halted"):
        log_decision({"event": "halted", "note": "kill switch previously tripped"})
        return state

    acct = broker.account()
    pos = broker.positions()

    # 1. forced exits (deterministic, no model involved)
    for symbol in risk.forced_exits(pos):
        broker.close(symbol)
        log_decision({"event": "forced_exit", "symbol": symbol})
    if risk.forced_exits(pos):
        pos = broker.positions()

    # 2. kill switch
    if risk.kill_switch_tripped(acct["equity"], state["starting_equity"]):
        for p in pos:
            broker.close(p["symbol"])
        state["halted"] = True
        log_decision({"event": "kill_switch", "equity": acct["equity"]})
        save_state(state)
        return state

    if not broker.market_open():
        log_decision({"event": "market_closed"})
        return state

    # 3. brain proposes
    snap = broker.snapshot(config.WATCHLIST)
    decision = brain.decide(snap, acct, pos, config.WATCHLIST)

    # 4. risk gate decides
    ok, reason, sanitized = risk.approve(decision, acct, pos, state)

    log_decision(
        {
            "event": "decision",
            "proposed": decision,
            "approved": ok,
            "reason": reason,
            "executed": sanitized if ok else None,
        }
    )

    # 5. execute
    if ok and sanitized["action"] == "buy":
        broker.buy_notional(sanitized["symbol"], sanitized["notional"])
        state["trades_today"] += 1
    elif ok and sanitized["action"] == "sell":
        broker.close(sanitized["symbol"])
        state["trades_today"] += 1

    save_state(state)
    return state


def main():
    state = load_state()
    save_state(state)
    while True:
        state = run_once(state)
        if state.get("halted"):
            break
        time.sleep(config.POLL_SECONDS)


if __name__ == "__main__":
    main()
