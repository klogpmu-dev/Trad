"""Only module that touches the market. Swap this file to change venue;
nothing else should need to change.
"""

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest, StockBarsRequest
from alpaca.data.timeframe import TimeFrame

import config

_trading = TradingClient(config.ALPACA_KEY, config.ALPACA_SECRET, paper=config.PAPER)
_data = StockHistoricalDataClient(config.ALPACA_KEY, config.ALPACA_SECRET)


def account():
    a = _trading.get_account()
    return {
        "equity": float(a.equity),
        "cash": float(a.cash),
        "buying_power": float(a.buying_power),
    }


def positions():
    out = []
    for p in _trading.get_all_positions():
        out.append(
            {
                "symbol": p.symbol,
                "qty": float(p.qty),
                "market_value": float(p.market_value),
                "unrealized_plpc": float(p.unrealized_plpc),
            }
        )
    return out


def market_open():
    return bool(_trading.get_clock().is_open)


def snapshot(symbols):
    req = StockLatestQuoteRequest(symbol_or_symbols=symbols)
    quotes = _data.get_stock_latest_quote(req)
    return {
        sym: {"bid": float(q.bid_price), "ask": float(q.ask_price)}
        for sym, q in quotes.items()
    }


def bars(symbol, start, end):
    req = StockBarsRequest(
        symbol_or_symbols=symbol, timeframe=TimeFrame.Day, start=start, end=end
    )
    resp = _data.get_stock_bars(req)
    return [{"t": b.timestamp, "close": float(b.close)} for b in resp[symbol]]


def buy_notional(symbol, dollars):
    order = MarketOrderRequest(
        symbol=symbol,
        notional=round(dollars, 2),
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY,
    )
    return _trading.submit_order(order)


def close(symbol):
    return _trading.close_position(symbol)
