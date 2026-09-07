# Trad

A personal experiment: can an LLM-driven agent trade profitably? Paper-trading
agent on US equities via Alpaca, Claude as the decision model. See
[`docs/HANDOFF.md`](docs/HANDOFF.md) for full context, venue rationale, and
the reasoning behind the current scope.

## Status

Working paper-trading agent with a unit-tested risk gate. Not yet run live.

## Core invariant

```
forced exits (deterministic) -> kill switch -> brain -> risk gate -> execute
```

The model (`brain.py`) can only *propose* a JSON decision. `risk.py` decides
what actually reaches `broker.py`. Reasoning is separated from execution
privilege.

- **`broker.py`** — only module that touches the market (wraps `alpaca-py`).
  Swap this file to change venue; nothing else should need to change.
- **`risk.py`** — pure functions, no network, no model call. Rejection is the
  default; every path to approval is explicit.
- **`brain.py`** — the Claude call. Strict JSON out. Any exception returns
  HOLD — never fails open into a trade.
- **`main.py`** — the loop: JSONL decision log (`decisions.jsonl`) + state
  file (`state.json`) tracking starting equity, daily trade count, halted flag.
- **`benchmark.py`** — agent return vs. SPY buy-and-hold over the same window.

## Risk limits (`config.py`)

- 40% max equity per position, 2 max open positions, 2 trades/day
- −5% stop-loss / +8% take-profit per position (forced, deterministic)
- −20% account kill switch: liquidates everything and halts permanently
  (delete `state.json` to reset)
- Long only — no shorting, no averaging up
- 8-symbol liquid watchlist (`config.WATCHLIST`)

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in keys, then `export $(cat .env | xargs)` or use direnv
python main.py
python benchmark.py    # after a run
```

Paper keys from app.alpaca.markets work immediately, no funding needed.
Set `PAPER=0` only when you mean to trade real money.

## Tests

```bash
pytest
```

`tests/test_risk.py` covers the cases the risk gate must reject: off-watchlist
symbol, shorting attempt, averaging up, oversized notional (capped, not
rejected), invalid action string, daily cap, max open positions, and kill
switch / halted state. Keep these passing when refactoring `risk.py`.

## Next up

Not built yet: an experiment runner comparing the full agent against a
price-only ablation and a random null model (same risk gate, matched trade
count) behind SPY buy-and-hold, plus a calibration analyzer for the
`confidence` field `brain.py` already emits. Details in
[`docs/HANDOFF.md`](docs/HANDOFF.md#5-next-build-the-actual-project).
