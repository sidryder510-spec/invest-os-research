# -*- coding: utf-8 -*-
"""Stop-loss test (pre-registered in research_config 1.5.0, before any result).

Same point-in-time picks as pit_backtest (12-1 + breadth, Top 5, weekly, next-day
close entry, 60-day hold), re-run with a stop at each of STOP_LEVELS and with no
stop. Reads the bhavcopy files pit_backtest already downloaded; never downloads.
"""
import numpy as np
import pandas as pd

import extended_tests as xt
import pit_backtest as pit
import study_05_transaction_costs as s05
from research_config import (HOLDING_DAYS, PIT_START, REPORTS_DIR, ROBUST_LOOKBACKS,
                             STOP_INSURANCE_LEVEL, STOP_LEVELS, STOP_MAX_ALPHA_COST)


def stop_return(closes, stop):
    """closes[0] = entry close, closes[-1] = scheduled exit close. Returns (% return, stopped).

    If close_t <= entry * (1 - stop) on a day t before the last, sell at close t + 1.
    """
    entry = closes[0]
    if stop is not None:
        level = entry * (1 - stop)
        for t in range(1, len(closes) - 1):
            if closes[t] <= level:     # decided on closes[: t + 1] only
                return (closes[t + 1] / entry - 1) * 100, True
    return (closes[-1] / entry - 1) * 100, False


def baseline_picks(px, exit_px, rows, breadth, nifty, member=None):
    """The 12-1 + breadth picks, built exactly as extended_tests.monkey_section (without the monkey)."""
    fwd = xt.forward_returns(px, exit_px)
    nfwd = (nifty.shift(-(1 + HOLDING_DAYS)) / nifty.shift(-1) - 1) * 100
    score = xt.momentum(px, ROBUST_LOOKBACKS["12-1"])
    _, picks = xt.run(score, xt.eligibility(px, rows, score, member), fwd, nfwd,
                      xt.snapshot_positions(len(px), breadth, True))
    return picks


def apply_stop(picks, px, exit_px, stop):
    """Picks with stock_return replaced by the stopped return, plus costs and alpha."""
    loc = px.index.get_indexer(picks["date"])
    cols = px.columns.get_indexer(picks["symbol"])
    ex = exit_px.reindex(columns=px.columns).to_numpy()
    out = [stop_return(np.r_[px.iat[p + 1, c], ex[p + 2:p + 2 + HOLDING_DAYS, c]], stop)
           for p, c in zip(loc, cols)]
    picks = picks.assign(stock_return=[r for r, _ in out], stopped=[s for _, s in out])
    picks["alpha"] = picks["stock_return"] - picks["nifty_return"]
    return s05.add_net(picks)


def summary(name, picks):
    """Unrounded; the report rounds for display only."""
    per_snap = picks.groupby("date")["alpha"].mean().sort_index()
    return {"variant": name, "trades": len(picks),
            "mean_net_alpha": picks["net_alpha"].mean(),
            "median_net_alpha": picks["net_alpha"].median(),
            "win_rate_pct": (picks["net_alpha"] > 0).mean() * 100,
            "worst_trade_net_return": picks["net_return"].min(),
            "stopped_pct": picks["stopped"].mean() * 100,
            "t_nonoverlap": xt.tstat(per_snap)}


def zeroed_in_window(picks, px, ca):
    """(date, symbol) of picks with a >35% daily move zeroed (amendment 1.4.2) inside the holding window."""
    loc = px.index.get_indexer(picks["date"])
    m = ca.reindex(index=px.index, columns=px.columns, fill_value=False).to_numpy()
    cols = px.columns.get_indexer(picks["symbol"])
    return [(d, sym) for d, sym, p, c in zip(picks["date"], picks["symbol"], loc, cols)
            if m[p + 2:p + 2 + HOLDING_DAYS, c].any()]


def decide(table):
    """Locked rule (config 1.5.0). table: summary rows, first the baseline, then one per stop level."""
    base = table[0]
    ok = [s for s, row in zip(STOP_LEVELS, table[1:])
          if row["mean_net_alpha"] >= base["mean_net_alpha"] - STOP_MAX_ALPHA_COST
          and row["worst_trade_net_return"] > base["worst_trade_net_return"]]
    if ok:
        s = max(ok)
        return s, "ADOPT -%d%% stop: within %.1f points of the no-stop mean and a smaller worst loss." % (
            s * 100, STOP_MAX_ALPHA_COST)
    cost = base["mean_net_alpha"] - table[1 + STOP_LEVELS.index(STOP_INSURANCE_LEVEL)]["mean_net_alpha"]
    return STOP_INSURANCE_LEVEL, ("NO STOP QUALIFIES. Live plan uses -%d%% purely as disaster insurance, "
                                  "not as an edge. Its cost against no stop: %.2f points of mean net alpha "
                                  "per 60 days." % (STOP_INSURANCE_LEVEL * 100, cost))


def run_all(px, exit_px, rows, breadth, nifty, member=None):
    picks = baseline_picks(px, exit_px, rows, breadth, nifty, member)
    variants = [("no stop", None)] + [("-%d%% stop" % (s * 100), s) for s in STOP_LEVELS]
    table = [summary(name, apply_stop(picks, px, exit_px, s)) for name, s in variants]
    return table, decide(table), picks


def display(table):
    return pd.DataFrame(table).round({"mean_net_alpha": 2, "median_net_alpha": 2, "win_rate_pct": 1,
                                      "worst_trade_net_return": 2, "stopped_pct": 1, "t_nonoverlap": 2})


def main():
    import historical_backtest_v3 as e
    _, nifty_data, _ = e.load_market_data()
    nifty = nifty_data["Close"]
    dates = nifty.index[nifty.index >= pd.Timestamp(PIT_START)]
    missing = [d for d in dates if not (pit.BHAV_DIR / (d.strftime("%Y%m%d") + ".csv")).exists()]
    pct = 100 * len(missing) / len(dates)
    if pct > pit.MAX_MISSING_PCT:
        raise SystemExit("[FATAL] %.1f%% of bhavcopy days missing; run pit_backtest.py first." % pct)
    px, exit_px, rows, member, breadth, *_, ca = pit.panels(dates, with_ca=True)
    table, (level, text), picks = run_all(px, exit_px, rows, breadth, nifty.reindex(dates), member)
    zeroed = zeroed_in_window(picks, px, ca)
    lines = ["# Stop-loss test (pre-registered in research_config 1.5.0)", "",
             "**Decision: %s**" % text, "",
             "Point-in-time data, %d trading days (%d missing). Stops on daily closes, exit at the next close; "
             "Study 05 Zerodha costs. Rule: the widest stop whose mean net alpha is at most %.1f points per 60 "
             "days below no-stop AND whose worst trade (lowest net return) is better. The strategy's "
             "point-in-time FAIL stands whatever this shows." % (len(dates), len(missing), STOP_MAX_ALPHA_COST), "",
             xt.md(display(table)), "",
             "**Disclosure.** The baseline's per-trade results (worst -73.6%, ENERGYDEV 2016) were already public "
             "in research/outputs/pit_trades.csv when this rule was locked, so the worst-trade test was nearly "
             "predetermined; the mean-alpha test is what decides.", "",
             "**Biases (they point in different directions, so this is a close-data estimate, not a GTT "
             "simulation).**",
             "- Closes miss intraday dips that would fire a real GTT, so stop-outs are understated and the mean "
             "flatters the stop.",
             "- On a steady slide a GTT sells near the trigger, while the test sells at the next close, usually "
             "lower, so worst losses look worse than live (against the stop).",
             "- On lower-circuit (limit-down) days no sell can fill, but the test still sells at the next close, "
             "which flatters the stop's worst trade.",
             "- Crash protection beyond a 35% single-day move is NOT measured: amendment 1.4.2 zeroes those "
             "moves for the baseline and every stop alike.", "",
             "Picks with a zeroed >35%% daily move inside their holding window: **%d**%s" % (
                 len(zeroed), (": " + ", ".join("%s (%s)" % (sym, pd.Timestamp(d).date()) for d, sym in zeroed))
                 if zeroed else "."), "",
             "t is the non-overlapping t-stat of gross alpha, as in pit_backtest.", ""]
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "stop_test.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
