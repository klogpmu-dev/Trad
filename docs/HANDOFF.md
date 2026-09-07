# LLM Trading Agent — Project Handoff

Context doc for continuing this work in Claude Code. Written 2026-09-07.

---

## 1. What this is

A personal experiment: can an LLM-driven agent trade profitably? Started as
"give an agent $50 and let it trade for a week." The scope changed once the
economics were worked out (see §4). Not a work project.

**Current state:** working paper-trading agent, tested risk gate, not yet run
live. Next build is a measurement harness, not more trading logic.

---

## 2. Venue decision (settled — don't relitigate)

| Venue | Verdict |
|---|---|
| **US equities via Alpaca** | **Chosen.** Commission-free, fractional, $1 min funding, free paper API on identical endpoints, non-US residents supported. |
| Crypto (Binance) | Rejected as primary. Fits technically (24/7, tiny sizes) but 0.1%/side fees dominate a $50 account, and SAMA prohibits Saudi banks from processing crypto transactions, so funding likely fails. |
| Forex | Rejected. Only "works" at this size with leverage. |

**Binance is still a possible secondary venue** for the multi-venue experiment.
If added: spot-trading-only API key, **withdrawals disabled**, IP whitelist.
Handle per-pair `stepSize` and `MIN_NOTIONAL` (~$5) rounding or orders reject.
Widen stops to 10–15% — the 5% equity stop gets shredded by crypto vol.

---

## 3. Architecture (built, tested)

Files: `config.py`, `broker.py`, `risk.py`, `brain.py`, `main.py`, `benchmark.py`

**Core invariant — do not break this:**

```
forced exits (deterministic) -> kill switch -> brain -> risk gate -> execute
```

The model is consulted third and obeyed last. `brain.py` can only *propose*
JSON. `risk.py` decides what reaches `broker.py`. Separation of reasoning from
execution privilege.

### Module contracts

- **`broker.py`** — only module that touches the market. Wraps alpaca-py.
  `account()`, `positions()`, `market_open()`, `snapshot(symbols)`,
  `buy_notional(sym, $)`, `close(sym)`. Swap this file to change venue;
  nothing else should need to change.
- **`risk.py`** — pure functions, no network, no model. `approve()` returns
  `(ok, reason, sanitized_decision)`. Rejection is the default; every path to
  `True` is explicit. Also `kill_switch_tripped()` and `forced_exits()`.
- **`brain.py`** — Claude call, strict JSON out. **Any exception returns HOLD.**
  Never fail open into a trade.
- **`main.py`** — loop + JSONL decision log (`decisions.jsonl`) + `state.json`
  (starting equity, daily trade count, halted flag).
- **`benchmark.py`** — agent return vs SPY over the same window.

### Risk limits (`config.py`)

40% max per position · 2 max open positions · 2 trades/day · −5% stop /
+8% take-profit · −20% kill switch (liquidates + halts permanently;
delete `state.json` to reset) · long only, no shorting, no averaging up ·
8-symbol liquid watchlist.

**Risk gate is unit-tested** against: off-watchlist symbol, shorting attempt,
averaging up, oversized notional (correctly capped), invalid action string,
daily cap. All rejected. Keep these tests when refactoring.

---

## 4. Why the goal changed — read before "improving returns"

**One week on $50 cannot produce a meaningful result.**

- Portfolio 1-week sigma ≈ 2%. Expected range $48–$52. A great week is +$2.
- **Inference cost exceeds expected P&L.** Polling every 15 min ≈ 130 Claude
  calls/week ≈ $1–2 = 2–4% of capital. The agent must beat SPY by 2–4pp just
  to pay for its own thinking. → `POLL_SECONDS` should go to twice daily.
- At 2% weekly vol you cannot separate skill from noise. Whatever number
  appears on Friday is a coin flip that will feel like signal.

**Evidence base:**
- StockBench: most LLM agents beat buy-and-hold over 4 months — but the
  baseline returned 0.4% and agents ~2%. Weak benchmark, single window.
- Agent Market Arena: **scaffold matters more than model backbone.** Most
  public projects tune the variable shown to matter least.
- TrustTrade: identical market conditions → divergent decisions → wide
  return variance. **A single run is not a measurement.**
- Retail base rates: 70–90% lose money; ~15% of day traders survive 3 years.
- Reddit/blog "success stories" are unusable — pure survivorship bias, and
  search results for this topic are saturated with Gumroad/Substack funnels.

---

## 5. Next build (the actual project)

**Measure calibration, not returns.** `brain.py` already emits a `confidence`
field that nothing currently reads.

Why this is the right target:
- Works on **decisions, not trades** — ~130 decisions/week vs ~5 trades.
  Real sample size.
- Runs on **paper**, so capital constraint disappears; run variants in
  parallel at zero marginal cost.
- Produces your own denominator instead of trusting anyone's anecdote.

### To build

1. **Experiment runner** — N variants against one shared market feed:
   - full agent
   - price-only ablation (no news/context)
   - **random null model** behind the identical risk gate, matched trade count
   - buy-and-hold SPY
2. **Calibration analyzer** — reliability curve: when it says 0.8 confidence,
   is it right 80% of the time?
3. **Decision-consistency score** — same input 5×, measure divergence
   (directly tests the TrustTrade finding).
4. **Cost-adjusted returns** — subtract inference spend. Nobody publishes
   this, which is why the field looks more profitable than it is.

`risk.py` and `broker.py` need no changes for any of this.

**Success criterion:** not "did it make money" but "is the confidence signal
calibrated, and does the full agent beat the random null?" If it can't beat
coin-flipping behind the same risk gate, that's the finding.

---

## 6. Setup

```bash
pip install -r requirements.txt   # alpaca-py, anthropic
export ALPACA_KEY=... ALPACA_SECRET=... ANTHROPIC_API_KEY=...
export PAPER=1                    # 0 = live money
python main.py
python benchmark.py               # end of run
```

Paper keys from app.alpaca.markets work immediately, no funding needed.
Model string: `claude-sonnet-5`.

---

## 7. Working preferences

Brief and direct. Ask rather than assume. Lean, testable controls over
comprehensive ones. Don't pad with documentation that wasn't asked for.
