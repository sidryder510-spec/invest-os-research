# -*- coding: utf-8 -*-
"""Forward paper trading with the frozen engine. Run weekly after NSE close.

Each run:
  1. records this week's Top-N signal from the latest close (or "no trade" when
     breadth is below the threshold), using the CURRENT Nifty 500 list, so
     there is no survivorship bias going forward;
  2. fills a signal at the close of the next trading day;
  3. closes it HOLDING_DAYS trading days later, net of Zerodha charges.
Prices are always re-read from today's adjusted series, so splits and
dividends between entry and exit do not distort returns.
Writes paper/ledger.csv, paper/weekly_log.csv and paper/SCORECARD.md, plus
paper/alert.md (not committed) when a buy or sell trigger fired this run.
`python paper_trade.py --uat` replays 2023-2024 week by week into uat/ to
show the triggers working (a functional test, not evidence of an edge).
Nothing here talks to a broker.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import historical_backtest_v3 as e
import study_05_transaction_costs as s05
from research_config import (BREADTH_THRESHOLD, HOLDING_DAYS, TOP_N, PAPER_DIR, PAPER_MIN_CLOSED_WEEKS,
                             S05_NET_ALPHA_PASS, S05_WIN_RATE_PASS)

LEDGER = PAPER_DIR / "ledger.csv"
WEEKLY = PAPER_DIR / "weekly_log.csv"
WEEKLY_COLS = ["signal_date", "breadth", "traded", "picks"]
SCORECARD = PAPER_DIR / "SCORECARD.md"
COLS = ["signal_date", "symbol", "rank", "score", "status", "entry_date", "exit_date",
        "stock_return", "nifty_return", "alpha", "cost_pct", "net_alpha"]


def read(path, cols):
    return pd.read_csv(path, dtype=str) if path.exists() else pd.DataFrame(columns=cols, dtype=str)


def step(ledger, weekly, today_index, px, exit_px, breadth, nifty, gen, new_signals=True):
    """One weekly run against data that ends at today_index[-1]. Returns updated copies."""
    ledger, weekly = ledger.copy(), weekly.copy()
    idx = today_index
    pos = {d: i for i, d in enumerate(idx.strftime("%Y-%m-%d"))}

    for i, r in ledger.iterrows():
        sig = pos.get(r["signal_date"])
        if sig is None:
            continue
        if r["status"] == "PENDING" and sig + 1 < len(idx):
            ledger.at[i, "status"], ledger.at[i, "entry_date"] = "OPEN", idx[sig + 1].strftime("%Y-%m-%d")
        if ledger.at[i, "status"] == "OPEN" and sig + 1 + HOLDING_DAYS < len(idx):
            entry, exit_ = idx[sig + 1], idx[sig + 1 + HOLDING_DAYS]
            sym = r["symbol"]
            if sym not in px or not (px.at[entry, sym] > 0 and exit_px.at[exit_, sym] > 0):
                continue   # price missing this week; retry next run rather than guess
            s = (exit_px.at[exit_, sym] / px.at[entry, sym] - 1) * 100
            n = (nifty[exit_] / nifty[entry] - 1) * 100
            cost = s05.round_trip_cost_pct(r["symbol"], s)
            ledger.loc[i, ["status", "exit_date", "stock_return", "nifty_return", "alpha", "cost_pct", "net_alpha"]] = [
                "CLOSED", exit_.strftime("%Y-%m-%d"), "%.4f" % s, "%.4f" % n, "%.4f" % (s - n), "%.4f" % cost,
                "%.4f" % (s - n - cost)]

    today = idx[-1]
    key = today.strftime("%Y-%m-%d")
    if new_signals and key not in set(weekly["signal_date"]):
        b = breadth.get(today, np.nan)
        picks = gen(today) if b >= BREADTH_THRESHOLD else []
        weekly.loc[len(weekly)] = [key, "%.1f" % b, str(bool(picks)), " ".join(p["symbol"] for p in picks)]
        for rank, p in enumerate(picks, 1):
            ledger.loc[len(ledger)] = [key, p["symbol"], str(rank), str(p["score"]), "PENDING"] + [""] * 7
    return ledger, weekly


def alerts(before, after, tag=""):
    """Plain-text BUY/SELL trigger messages for rows that changed in this run (empty if none)."""
    lines = []
    new = after.iloc[len(before):]
    for d, g in new.groupby("signal_date"):
        lines.append("%sBUY trigger %s: %s. Paper-buy at the next trading day's close; each sells %d trading days later."
                     % (tag, d, ", ".join(g["symbol"]), HOLDING_DAYS))
    old = before["status"].reindex(after.index)
    closed = after[(after["status"] == "CLOSED") & (old != "CLOSED")]
    for _, r in closed.iterrows():
        lines.append("%sSELL trigger %s: %s (bought %s) %+.1f%%, NIFTY %+.1f%%, net vs NIFTY after costs %+.1f%%."
                     % (tag, r["exit_date"], r["symbol"], r["entry_date"], float(r["stock_return"]),
                        float(r["nifty_return"]), float(r["net_alpha"])))
    return "\n".join(lines)


def scorecard(ledger, weekly):
    closed = ledger[ledger["status"] == "CLOSED"]
    net = closed["net_alpha"].astype(float)
    weeks = closed["signal_date"].nunique()
    if weeks < PAPER_MIN_CLOSED_WEEKS:
        verdict = "TOO EARLY (%d of %d closed weekly picks)" % (weeks, PAPER_MIN_CLOSED_WEEKS)
    elif net.mean() > S05_NET_ALPHA_PASS and (net > 0).mean() * 100 > S05_WIN_RATE_PASS:
        verdict = "PASS"
    else:
        verdict = "FAIL"
    last = weekly.iloc[-1] if len(weekly) else None
    lines = [
        "# Paper trading scorecard", "",
        "**Verdict: %s**" % verdict, "",
        "Rule (locked 2026-10-26): mean net alpha > %s%% per 60 days and > %s%% of trades beating NIFTY after "
        "costs, over at least %d closed weekly picks." % (S05_NET_ALPHA_PASS, S05_WIN_RATE_PASS, PAPER_MIN_CLOSED_WEEKS), "",
        "| | |", "| --- | --- |",
        "| Latest run | %s |" % (last["signal_date"] if last is not None else "-"),
        "| Latest breadth | %s%% (trades only at >= %s%%) |" % (last["breadth"] if last is not None else "-", BREADTH_THRESHOLD),
        "| Latest picks | %s |" % ((last["picks"] or "none, in cash") if last is not None else "-"),
        "| Weeks run / weeks traded | %d / %d |" % (len(weekly), (weekly["traded"] == "True").sum()),
        "| Pending / open / closed trades | %d / %d / %d |" % tuple((ledger["status"] == s).sum() for s in ("PENDING", "OPEN", "CLOSED")),
        "| Mean net alpha per 60 days | %s |" % ("%.2f%%" % net.mean() if len(net) else "-"),
        "| Trades beating NIFTY after costs | %s |" % ("%.1f%%" % ((net > 0).mean() * 100) if len(net) else "-"),
        "", "Paper only. No order is ever sent to a broker.",
    ]
    return verdict, "\n".join(lines) + "\n"


def with_held(px, exit_px, ledger, index):
    """Stocks we still hold but that left the Nifty 500 are downloaded separately, so they can be closed."""
    held = set(ledger.loc[ledger["status"].isin(["PENDING", "OPEN"]), "symbol"]) - set(px.columns)
    if not held:
        return px, exit_px
    extra = pd.DataFrame(e._download([h + ".NS" for h in sorted(held)])).reindex(index)
    extra.columns = [c[:-3] for c in extra.columns]
    return px.join(extra.ffill(limit=5)), exit_px.join(extra.ffill())


def save(out, ledger, weekly, note=""):
    out.mkdir(parents=True, exist_ok=True)
    ledger.to_csv(out / LEDGER.name, index=False)
    weekly.to_csv(out / WEEKLY.name, index=False)
    verdict, text = scorecard(ledger, weekly)
    (out / SCORECARD.name).write_text(note + text, encoding="utf-8")
    return text


def uat(start="2023-01-01", end="2024-12-31", out=Path("uat")):
    """Replay weekly runs on past data: signals from start to end, then keep running until they all close."""
    stock_data, nifty_data, st = e.load_market_data()
    gen = lambda d: e.generate_historical_candidates(d, stock_data, nifty_data, TOP_N)
    idx, nifty = nifty_data.index, nifty_data["Close"]
    ledger, weekly, log = pd.DataFrame(columns=COLS, dtype=str), pd.DataFrame(columns=WEEKLY_COLS, dtype=str), []
    first = idx.searchsorted(pd.Timestamp(start))
    for t in range(first, len(idx), 5):   # every 5th trading day, like the weekly job
        signal = idx[t] <= pd.Timestamp(end)
        if not signal and not ledger["status"].isin(["PENDING", "OPEN"]).any():
            break
        new_l, new_w = step(ledger, weekly, idx[:t + 1], st["px"], st["exit_px"], st["breadth"], nifty, gen, signal)
        msg = alerts(ledger, new_l, "[UAT] ")
        if msg:
            log.append(msg)
        ledger, weekly = new_l, new_w
    note = ("> **UAT replay, functional test only.** Weekly runs replayed over %s to %s with the live code, each "
            "seeing only data up to that Monday. Uses today's Nifty 500 list (survivorship-biased), so the numbers "
            "are NOT evidence of an edge.\n\n" % (start, end))
    text = save(out, ledger, weekly, note)
    (out / "trigger_log.md").write_text("# UAT trigger log\n\n" + "\n\n".join(log) + "\n", encoding="utf-8")
    buys = [l for m in log for l in m.splitlines() if "BUY" in l]
    sells = [l for m in log for l in m.splitlines() if "SELL" in l]
    PAPER_DIR.mkdir(parents=True, exist_ok=True)
    (PAPER_DIR / "alert.md").write_text(
        "UAT finished: %d buy triggers and %d sell triggers fired. First of each:\n\n%s\n\n%s\n\n"
        "Full log: uat/trigger_log.md. This is a test notification." % (
            len(buys), len(sells), buys[0] if buys else "-", sells[0] if sells else "-"), encoding="utf-8")
    print(text)


def main():
    if "--uat" in sys.argv:
        return uat()
    stock_data, nifty_data, st = e.load_market_data()
    gen = lambda d: e.generate_historical_candidates(d, stock_data, nifty_data, TOP_N)
    before, weekly = read(LEDGER, COLS), read(WEEKLY, WEEKLY_COLS)
    px, exit_px = with_held(st["px"], st["exit_px"], before, nifty_data.index)
    ledger, weekly = step(before, weekly, nifty_data.index, px, exit_px, st["breadth"], nifty_data["Close"], gen)
    print(save(PAPER_DIR, ledger, weekly))
    msg = alerts(before, ledger)
    if msg:
        (PAPER_DIR / "alert.md").write_text(msg + "\n\nScorecard: paper/SCORECARD.md. Paper only.", encoding="utf-8")
        print(msg)


if __name__ == "__main__":
    main()
