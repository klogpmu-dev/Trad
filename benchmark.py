"""Agent return vs SPY buy-and-hold over the same window. Run at end of a session."""

import json
from datetime import datetime

import config
import broker


def _load_starting_equity():
    with open(config.STATE_FILE) as f:
        return json.load(f)["starting_equity"]


def _first_decision_ts():
    with open(config.DECISIONS_LOG) as f:
        first_line = f.readline()
    return json.loads(first_line)["ts"]


def _spy_return_since(start_ts):
    start_date = datetime.fromtimestamp(start_ts).date()
    end_date = datetime.now().date()
    day_bars = broker.bars("SPY", start_date, end_date)
    if len(day_bars) < 2:
        return None
    return (day_bars[-1]["close"] - day_bars[0]["close"]) / day_bars[0]["close"]


def main():
    starting_equity = _load_starting_equity()
    acct = broker.account()
    agent_return = (acct["equity"] - starting_equity) / starting_equity

    spy_return = _spy_return_since(_first_decision_ts())

    print(f"Agent return: {agent_return:+.2%}")
    if spy_return is not None:
        print(f"SPY return:   {spy_return:+.2%}")
        print(f"Alpha:        {agent_return - spy_return:+.2%}")
    else:
        print("SPY return:   unavailable (not enough bars in window)")


if __name__ == "__main__":
    main()
