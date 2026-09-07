import risk
import config


def _state(**overrides):
    state = {"trades_today": 0, "halted": False}
    state.update(overrides)
    return state


def _account(equity=50.0):
    return {"equity": equity, "cash": equity, "buying_power": equity}


def test_off_watchlist_symbol_rejected():
    decision = {"action": "buy", "symbol": "GME", "notional": 10}
    ok, reason, sanitized = risk.approve(decision, _account(), [], _state())
    assert ok is False
    assert "watchlist" in reason
    assert sanitized is None


def test_shorting_attempt_rejected():
    decision = {"action": "sell", "symbol": "AAPL", "notional": 10}
    ok, reason, sanitized = risk.approve(decision, _account(), [], _state())
    assert ok is False
    assert "shorting" in reason
    assert sanitized is None


def test_averaging_up_rejected():
    positions = [{"symbol": "AAPL", "qty": 1, "unrealized_plpc": 0.01}]
    decision = {"action": "buy", "symbol": "AAPL", "notional": 10}
    ok, reason, sanitized = risk.approve(decision, _account(), positions, _state())
    assert ok is False
    assert "averaging" in reason
    assert sanitized is None


def test_oversized_notional_is_capped_not_rejected():
    decision = {"action": "buy", "symbol": "AAPL", "notional": 1000}
    ok, reason, sanitized = risk.approve(decision, _account(equity=50.0), [], _state())
    assert ok is True
    assert sanitized["notional"] == 50.0 * config.MAX_POSITION_PCT


def test_invalid_action_string_rejected():
    decision = {"action": "yolo", "symbol": "AAPL", "notional": 10}
    ok, reason, sanitized = risk.approve(decision, _account(), [], _state())
    assert ok is False
    assert reason == "invalid action"
    assert sanitized is None


def test_daily_trade_cap_rejected():
    decision = {"action": "buy", "symbol": "AAPL", "notional": 10}
    state = _state(trades_today=config.MAX_TRADES_PER_DAY)
    ok, reason, sanitized = risk.approve(decision, _account(), [], state)
    assert ok is False
    assert "daily" in reason
    assert sanitized is None


def test_max_open_positions_rejected():
    positions = [
        {"symbol": "AAPL", "qty": 1, "unrealized_plpc": 0.0},
        {"symbol": "MSFT", "qty": 1, "unrealized_plpc": 0.0},
    ]
    decision = {"action": "buy", "symbol": "NVDA", "notional": 10}
    ok, reason, sanitized = risk.approve(decision, _account(), positions, _state())
    assert ok is False
    assert "max open positions" in reason


def test_halted_rejects_everything_but_hold():
    state = _state(halted=True)
    ok, reason, sanitized = risk.approve(
        {"action": "buy", "symbol": "AAPL", "notional": 10}, _account(), [], state
    )
    assert ok is False

    ok, reason, sanitized = risk.approve({"action": "hold"}, _account(), [], state)
    assert ok is True


def test_valid_buy_approved():
    decision = {"action": "buy", "symbol": "AAPL", "notional": 10}
    ok, reason, sanitized = risk.approve(decision, _account(), [], _state())
    assert ok is True
    assert sanitized == {"action": "buy", "symbol": "AAPL", "notional": 10}


def test_valid_close_approved():
    positions = [{"symbol": "AAPL", "qty": 1, "unrealized_plpc": 0.02}]
    decision = {"action": "sell", "symbol": "AAPL"}
    ok, reason, sanitized = risk.approve(decision, _account(), positions, _state())
    assert ok is True
    assert sanitized == {"action": "sell", "symbol": "AAPL"}


def test_kill_switch_tripped():
    assert risk.kill_switch_tripped(39.0, 50.0) is True  # -22%
    assert risk.kill_switch_tripped(45.0, 50.0) is False  # -10%


def test_forced_exits():
    positions = [
        {"symbol": "AAPL", "unrealized_plpc": -0.06},  # stop hit
        {"symbol": "MSFT", "unrealized_plpc": 0.09},  # take-profit hit
        {"symbol": "NVDA", "unrealized_plpc": 0.02},  # neither
    ]
    assert set(risk.forced_exits(positions)) == {"AAPL", "MSFT"}
