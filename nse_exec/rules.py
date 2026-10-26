"""Pure rules for NSE cash-equity (CNC) orders: ticks, charges, sizing, risk check.

No I/O here. Everything takes plain dicts/numbers so Invest OS can call it directly.
"""
from decimal import Decimal as D, ROUND_CEILING, ROUND_FLOOR

# NSE cash tick sizes by price (revision effective 15 Apr 2025).
# shortcut: NSE sets the tick from the previous month-end close, not the live price;
# a stock sitting on a band edge can be off by one band. Kite rejects a bad tick, so it fails safe.
TICKS = [(D(250), D("0.01")), (D(1000), D("0.05")), (D(5000), D("0.10")),
         (D(10000), D("0.50")), (D(20000), D("1.00")), (None, D("5.00"))]


def tick_for(price):
    price = D(str(price))
    for limit, tick in TICKS:
        if limit is None or price < limit:
            return tick


def to_tick(price, rounding):
    """Round a price onto its tick: ROUND_CEILING for buys, ROUND_FLOOR for stops."""
    price = D(str(price))
    tick = tick_for(price)
    return (price / tick).to_integral_value(rounding) * tick


def charges(side, qty, price, rates):
    """Statutory + Zerodha charges in rupees for one CNC leg. `rates` comes from config."""
    value = D(qty) * D(str(price))
    pct = lambda key: value * D(str(rates[key])) / 100
    exch = pct("exchange_txn_pct")
    sebi = value * D(str(rates["sebi_per_crore"])) / D(10**7)
    brokerage = D(str(rates["brokerage_per_order"]))
    total = pct("stt_pct") + exch + sebi + brokerage
    total += (exch + sebi + brokerage) * D(str(rates["gst_pct"])) / 100
    if side == "BUY":
        total += pct("stamp_buy_pct")
    else:
        total += D(str(rates["dp_per_sell"]))
    return total


def loss_at_stop(qty, entry, stop, rates):
    """Rupees lost if bought at entry and sold at stop, charges included."""
    return D(qty) * (D(str(entry)) - D(str(stop))) + charges("BUY", qty, entry, rates) + charges("SELL", qty, stop, rates)


def check(pick, book, cfg):
    """Size one pick and run every limit. Returns a ticket dict with status PASS or BLOCK.

    pick: {symbol, entry, stop, sector, price_band_pct?}
    book: {cash, holdings: [{symbol, qty, ltp, stop, sector}]}
    """
    sym = str(pick.get("symbol", "")).upper().strip()
    capital = D(str(cfg["capital"]))
    rates = cfg["charges"]
    ticket = {"symbol": sym, "status": "BLOCK", "reasons": []}
    block = lambda why: ticket["reasons"].append(why) or ticket

    if not sym or not sym.replace("-", "").replace("&", "").isalnum():
        return block("bad symbol %r" % sym)
    if sym in {s.upper() for s in cfg.get("blocked", [])}:
        return block("%s is on the blocked list" % sym)
    try:
        entry = to_tick(pick["entry"], ROUND_CEILING)
        stop = to_tick(pick["stop"], ROUND_FLOOR)
    except (KeyError, ArithmeticError, ValueError, TypeError):
        return block("entry and stop are both required numbers")
    if entry <= 0 or stop <= 0 or stop >= entry:
        return block("stop %s must be above 0 and below entry %s" % (stop, entry))
    ticket.update(entry=str(entry), stop=str(stop))

    holdings = book.get("holdings", [])
    if any(h["symbol"].upper() == sym for h in holdings):
        return block("already holding %s; adding to a position is not allowed" % sym)
    if len(holdings) >= cfg["max_positions"]:
        return block("already at max_positions (%d)" % cfg["max_positions"])
    band = pick.get("price_band_pct")
    if band is not None and D(str(band)) < D(str(cfg["min_price_band_pct"])):
        return block("price band %s%% is below %s%%: circuit-lock risk, the stop may not fill"
                     % (band, cfg["min_price_band_pct"]))

    max_loss = D(str(cfg["max_loss_per_trade"]))
    if loss_at_stop(1, entry, stop, rates) > max_loss:
        return block("one share loses %.2f at the stop, over max_loss_per_trade %s; stop is too far"
                     % (loss_at_stop(1, entry, stop, rates), max_loss))

    # Each limit gives a max qty; the smallest one decides.
    value = lambda h: D(h["qty"]) * D(str(h["ltp"]))
    open_risk = sum((max(D(0), D(h["qty"]) * (D(str(h["ltp"])) - D(str(h["stop"])))) for h in holdings), D(0))
    sector = str(pick.get("sector", "")).strip() or "UNKNOWN"
    sector_value = sum((value(h) for h in holdings if h.get("sector") == sector), D(0))
    spendable = D(str(book["cash"])) - D(str(cfg["cash_buffer"]))
    per_share_risk = entry - stop
    limits = {
        "max_loss_per_trade": max_loss / per_share_risk,
        "max_position_pct": capital * D(str(cfg["max_position_pct"])) / 100 / entry,
        "max_sector_pct": (capital * D(str(cfg["max_sector_pct"])) / 100 - sector_value) / entry,
        "max_heat_pct": (capital * D(str(cfg["max_heat_pct"])) / 100 - open_risk) / per_share_risk,
        "cash_after_buffer": spendable / entry,
    }
    limits = {k: max(0, int(v)) for k, v in limits.items()}
    decider = min(limits, key=limits.get)
    qty = limits[decider]
    # Charges come on top of the price, so step down until loss and cash both fit.
    while qty > 0 and (loss_at_stop(qty, entry, stop, rates) > max_loss
                       or D(qty) * entry + charges("BUY", qty, entry, rates) > spendable):
        qty -= 1
    if qty == 0:
        return block("no whole share fits: %s leaves no room" % decider)

    loss = loss_at_stop(qty, entry, stop, rates)
    ticket.update(status="PASS", qty=qty, decided_by=decider, sector=sector,
                  value=str((qty * entry).quantize(D("0.01"))),
                  max_loss_at_stop=str(loss.quantize(D("0.01"))),
                  buy_charges=str(charges("BUY", qty, entry, rates).quantize(D("0.01"))))
    return ticket
