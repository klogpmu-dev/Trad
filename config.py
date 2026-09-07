import os

PAPER = os.getenv("PAPER", "1") == "1"

ALPACA_KEY = os.getenv("ALPACA_KEY")
ALPACA_SECRET = os.getenv("ALPACA_SECRET")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

MODEL = "claude-sonnet-5"

WATCHLIST = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "SPY"]

MAX_POSITION_PCT = 0.40  # max fraction of equity in a single position
MAX_OPEN_POSITIONS = 2
MAX_TRADES_PER_DAY = 2

STOP_LOSS_PCT = -0.05  # per-position forced exit
TAKE_PROFIT_PCT = 0.08  # per-position forced exit
KILL_SWITCH_PCT = -0.20  # account drawdown from starting equity: liquidate + halt

# Polling at 15 min would burn 2-4% of a $50 account on inference alone
# (see HANDOFF.md sec 4). Twice daily until the measurement harness says otherwise.
POLL_SECONDS = 12 * 60 * 60

STATE_FILE = "state.json"
DECISIONS_LOG = "decisions.jsonl"
