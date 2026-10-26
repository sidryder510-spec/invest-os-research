# -*- coding: utf-8 -*-
"""Informational: how much of the alpha is survivorship, how much is stock picking?

The universe is today's Nifty 500, so even a random pick from it beats NIFTY in
hindsight. For every trade, compare it with the equal-weighted average of ALL
eligible stocks in that same universe over the same entry-exit window:
  universe_edge  = universe average - NIFTY   (what knowing today's list is worth)
  selection_edge = stock - universe average    (what the momentum score added)
Not part of any verdict. Needs the engine's market cache (run after the dump).
"""
import numpy as np
import pandas as pd

import historical_backtest_v3 as e
from research_config import HOLDING_DAYS, MIN_HISTORY, SNAPSHOT_INTERVAL, REPORTS_DIR


def decompose(dump, st, nifty_index):
    rows = []
    for snap, grp in dump.groupby("date"):
        i = nifty_index.get_loc(pd.Timestamp(snap))
        entry, exit_ = nifty_index[i + 1], nifty_index[i + 1 + HOLDING_DAYS]
        ok = (st["rows"].loc[pd.Timestamp(snap)] >= MIN_HISTORY) & st["px"].loc[entry].notna()
        rets = (st["exit_px"].loc[exit_, ok] / st["px"].loc[entry, ok] - 1) * 100
        uni = float(rets.mean())
        rows.append({"date": snap, "stocks": float(grp["stock_return"].mean()),
                     "universe": uni, "nifty": float(grp["nifty_return"].iloc[0])})
    d = pd.DataFrame(rows)
    d["universe_edge"] = d["universe"] - d["nifty"]
    d["selection_edge"] = d["stocks"] - d["universe"]
    return d


def tstat(s):
    s = s.iloc[::max(1, HOLDING_DAYS // SNAPSHOT_INTERVAL)]   # non-overlapping holds
    return len(s), float(s.mean() / s.std(ddof=1) * np.sqrt(len(s))) if len(s) > 2 else float("nan")


def main():
    _, nifty, st = e.load_market_data()
    dump = pd.read_csv("trade_dump.csv")
    d = decompose(dump, st, nifty.index)
    lines = ["# Survivorship check (informational)", "",
             "Per snapshot, gross %, 60-day hold. Universe = equal-weight average of every eligible stock "
             "in today's Nifty 500 list over the same window.", "",
             "| Part | Mean % per 60d | Non-overlapping t-stat (n) |", "| --- | --- | --- |"]
    d["alpha"] = d["stocks"] - d["nifty"]   # = universe_edge + selection_edge
    for col, label in [("alpha", "Top-5 picks vs NIFTY (total gross alpha)"),
                       ("universe_edge", "Universe average vs NIFTY (survivorship + small/mid-cap tilt)"),
                       ("selection_edge", "Picks vs universe average (what the momentum score added)")]:
        n, t = tstat(d[col])
        lines.append("| %s | %.2f | %.2f (%d) |" % (label, d[col].mean(), t, n))
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "survivorship_check.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    d.to_csv(REPORTS_DIR.parent / "outputs" / "survivorship_check.csv", index=False)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
