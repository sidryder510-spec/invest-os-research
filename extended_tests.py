# -*- coding: utf-8 -*-
"""Extended tests pre-registered in research_config 1.4.0: random monkey and robustness.

Works on any price panels shaped like the engine's (px, exit_px, rows, breadth),
so the point-in-time backtest (pit_backtest.py) reuses it. Does not modify or
re-score the frozen engine; the 12-1 variant here reproduces it.
"""
import numpy as np
import pandas as pd

from research_config import (BREADTH_THRESHOLD, HOLDING_DAYS, MIN_HISTORY, SNAPSHOT_INTERVAL, TOP_N,
                             MONKEY_RUNS, MONKEY_SEED, MONKEY_P_PASS,
                             ROBUST_LOOKBACKS, ROBUST_PASS_COUNT, ROBUST_FAIL_COUNT, REPORTS_DIR)

STEP = max(1, HOLDING_DAYS // SNAPSHOT_INTERVAL)   # snapshots per holding period


def forward_returns(px, exit_px):
    """% return from the close after date t to HOLDING_DAYS trading days later."""
    return (exit_px.shift(-(1 + HOLDING_DAYS)) / px.shift(-1) - 1) * 100


def snapshot_positions(n, breadth, use_breadth):
    pos = np.arange(MIN_HISTORY, n - HOLDING_DAYS - 1, SNAPSHOT_INTERVAL)
    if use_breadth:
        pos = pos[(breadth.iloc[pos] >= BREADTH_THRESHOLD).values]
    return pos


def momentum(px, lookback):
    return px.shift(21) / px.shift(lookback) - 1


def run(score, eligible, fwd, nifty_fwd, positions):
    """Per snapshot: mean of Top-N by score, mean of all eligible, NIFTY. Plus every pick's return."""
    rows, picks = [], []
    for p in positions:
        ok = eligible.iloc[p] & fwd.iloc[p].notna()
        s = score.iloc[p][ok]
        if len(s) < TOP_N:
            continue
        top = s.nlargest(TOP_N).index
        r = fwd.iloc[p]
        d = fwd.index[p]
        rows.append({"date": d, "picks": r[top].mean(), "universe": r[ok].mean(), "nifty": nifty_fwd.iloc[p],
                     "n_eligible": int(ok.sum())})
        picks += [{"date": d, "symbol": sym, "stock_return": r[sym], "nifty_return": nifty_fwd.iloc[p]} for sym in top]
    out = pd.DataFrame(rows)
    if len(out):
        out["alpha"] = out["picks"] - out["nifty"]
        out["selection_edge"] = out["picks"] - out["universe"]
    return out, pd.DataFrame(picks)


def tstat(s):
    s = s.dropna().iloc[::STEP]
    return float(s.mean() / s.std(ddof=1) * np.sqrt(len(s))) if len(s) > 2 and s.std(ddof=1) > 0 else float("nan")


def monkey(eligible, fwd, nifty_fwd, positions, actual_alpha):
    """Share of random Top-N portfolios whose mean alpha >= the strategy's (a p-value)."""
    rng = np.random.default_rng(MONKEY_SEED)
    totals, count = np.zeros(MONKEY_RUNS), 0
    for p in positions:
        ok = (eligible.iloc[p] & fwd.iloc[p].notna()).values
        r = fwd.iloc[p].values[ok]
        if len(r) < TOP_N:
            continue
        pick = np.argsort(rng.random((MONKEY_RUNS, len(r))), axis=1)[:, :TOP_N]
        totals += r[pick].mean(axis=1) - nifty_fwd.iloc[p]
        count += 1
    sims = totals / max(count, 1)
    return float((sims >= actual_alpha).mean()), sims


def eligibility(px, rows, score, member=None):
    ok = (rows >= MIN_HISTORY) & score.notna() & px.notna()
    return ok & member if member is not None else ok


def robustness(px, exit_px, rows, breadth, nifty, member=None):
    fwd, nfwd = forward_returns(px, exit_px), (nifty.shift(-(1 + HOLDING_DAYS)) / nifty.shift(-1) - 1) * 100
    out = []
    for name, lb in ROBUST_LOOKBACKS.items():
        score = momentum(px, lb)
        elig = eligibility(px, rows, score, member)
        for use_b in (True, False):
            snaps, _ = run(score, elig, fwd, nfwd, snapshot_positions(len(px), breadth, use_b))
            out.append({"variant": name + (" + breadth" if use_b else " no filter"), "snapshots": len(snaps),
                        "mean_alpha": round(snaps["alpha"].mean(), 2) if len(snaps) else None,
                        "selection_edge": round(snaps["selection_edge"].mean(), 2) if len(snaps) else None,
                        "t_selection": round(tstat(snaps["selection_edge"]), 2) if len(snaps) else None})
    table = pd.DataFrame(out)
    positive = int((table["selection_edge"] > 0).sum())
    verdict = "PASS" if positive >= ROBUST_PASS_COUNT else "FAIL" if positive <= ROBUST_FAIL_COUNT else "CONDITIONAL"
    return table, positive, verdict


def monkey_section(px, exit_px, rows, breadth, nifty, member=None):
    fwd, nfwd = forward_returns(px, exit_px), (nifty.shift(-(1 + HOLDING_DAYS)) / nifty.shift(-1) - 1) * 100
    score = momentum(px, ROBUST_LOOKBACKS["12-1"])
    elig = eligibility(px, rows, score, member)
    pos = snapshot_positions(len(px), breadth, True)
    snaps, picks = run(score, elig, fwd, nfwd, pos)
    p, sims = monkey(elig, fwd, nfwd, pos, snaps["alpha"].mean())
    verdict = "PASS" if p < MONKEY_P_PASS else "FAIL"
    return snaps, picks, p, sims, verdict


def md(df):
    return "\n".join(["| " + " | ".join(map(str, df.columns)) + " |", "|" + " --- |" * len(df.columns)] +
                     ["| " + " | ".join(map(str, r)) + " |" for r in df.astype(object).values.tolist()])


def report(title, px, exit_px, rows, breadth, nifty, member=None):
    """Both sections as markdown, plus their verdicts and the 12-1 snapshot table."""
    snaps, picks, p, sims, mv = monkey_section(px, exit_px, rows, breadth, nifty, member)
    table, positive, rv = robustness(px, exit_px, rows, breadth, nifty, member)
    lines = [
        "## %s" % title, "",
        "### Random-monkey test: **%s**" % mv,
        ("Momentum 12-1 mean gross alpha: %.2f%% per 60 days over %d snapshots. %d random portfolios: median "
         "%.2f%%, 95th percentile %.2f%%. Share of random portfolios at least as good: **p = %.3f** "
         "(PASS needs p < %s)." % (snaps["alpha"].mean(), len(snaps), len(sims), np.median(sims),
                                   np.percentile(sims, 95), p, MONKEY_P_PASS)), "",
        "### Robustness: **%s** (%d of %d variants with positive selection edge)" % (rv, positive, len(table)),
        "Selection edge = picks minus the average eligible stock, per 60 days. 12-1 + breadth is the strategy; "
        "the rest are checks only.", "",
        md(table), "",
    ]
    return "\n".join(lines), {"monkey": mv, "monkey_p": p, "robust": rv, "robust_positive": positive}, snaps, picks


def main():
    import historical_backtest_v3 as e
    _, nifty, st = e.load_market_data()
    text, verdicts, snaps, _ = report("Yahoo data (today's Nifty 500 list: survivorship-biased)",
                                      st["px"], st["exit_px"], st["rows"], st["breadth"], nifty["Close"])
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "extended_tests_yahoo.md").write_text(
        "# Extended tests (pre-registered in research_config 1.4.0)\n\n" + text, encoding="utf-8")
    print(text)
    print(verdicts)


if __name__ == "__main__":
    main()
