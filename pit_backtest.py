# -*- coding: utf-8 -*-
"""Point-in-time backtest on NSE bhavcopy (pre-registered in research_config 1.4.0).

Every listed stock is included, delisted and collapsed ones too, so there is no
survivorship bias. On each date the universe is the PIT_UNIVERSE_SIZE stocks with
the highest average daily traded value over the previous PIT_VALUE_DAYS days.
Prices are chained from CLOSE / PREVCLOSE: NSE adjusts PREVCLOSE for splits and
bonuses on the ex-date, so the chain is corporate-action adjusted.
"""
import concurrent.futures as cf
import io
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

import extended_tests as xt
import study_05_transaction_costs as s05
from research_config import (BREADTH_THRESHOLD, PIT_START, PIT_UNIVERSE_SIZE, PIT_VALUE_DAYS, PIT_T_PASS,
                             S05_NET_ALPHA_PASS, S05_WIN_RATE_PASS, REPORTS_DIR)

BHAV_DIR = Path("data/bhav")
SERIES = {"EQ", "BE", "BZ"}
UDIFF_FROM = pd.Timestamp("2024-07-08")   # NSE switched the bhavcopy format on this date
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
           "Accept": "*/*", "Referer": "https://www.nseindia.com/"}
MAX_MISSING_PCT = 2.0   # more missing days than this and the backtest refuses to run


def urls(d):
    old = "https://nsearchives.nseindia.com/content/historical/EQUITIES/%d/%s/cm%s%s%dbhav.csv.zip" % (
        d.year, d.strftime("%b").upper(), d.strftime("%d"), d.strftime("%b").upper(), d.year)
    new = "https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_%s_F_0000.csv.zip" % d.strftime("%Y%m%d")
    return [new, old] if d >= UDIFF_FROM else [old, new]


def parse(raw):
    """Either bhavcopy format -> symbol, close, prevclose, value (Rs) for EQ/BE/BZ rows."""
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        df = pd.read_csv(z.open(z.namelist()[0]))
    df.columns = [c.strip() for c in df.columns]
    if "TckrSymb" in df.columns:
        df = df.rename(columns={"TckrSymb": "symbol", "SctySrs": "series", "ClsPric": "close",
                                "PrvsClsgPric": "prevclose", "TtlTrfVal": "value"})
    else:
        df = df.rename(columns={"SYMBOL": "symbol", "SERIES": "series", "CLOSE": "close",
                                "PREVCLOSE": "prevclose", "TOTTRDVAL": "value"})
    df["series"] = df["series"].astype(str).str.strip()
    df = df[df["series"].isin(SERIES)]
    df["symbol"] = df["symbol"].astype(str).str.strip()
    # a symbol can move between EQ and BE/BZ; keep the most-traded row of the day
    df = df.sort_values("value").drop_duplicates("symbol", keep="last")
    return df[["symbol", "close", "prevclose", "value"]]


def fetch_day(d):
    out = BHAV_DIR / (d.strftime("%Y%m%d") + ".csv")
    if out.exists():
        return d, True
    for attempt in range(3):
        for url in urls(d):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=30) as r:
                    parse(r.read()).to_csv(out, index=False)
                    return d, True
            except urllib.error.HTTPError as err:
                if err.code != 404:
                    time.sleep(2 * (attempt + 1))
            except Exception:
                time.sleep(2 * (attempt + 1))
    return d, False


def download(dates, workers=4):
    BHAV_DIR.mkdir(parents=True, exist_ok=True)
    missing = []
    with cf.ThreadPoolExecutor(workers) as ex:
        for i, (d, ok) in enumerate(ex.map(fetch_day, dates), 1):
            if not ok:
                missing.append(d)
            if i % 250 == 0:
                print("  bhavcopy %d/%d (%d missing)" % (i, len(dates), len(missing)), flush=True)
    return missing


def panels(dates):
    """Wide panels on the NIFTY calendar: px, exit_px, rows, member, breadth, value."""
    frames = []
    for d in dates:
        f = BHAV_DIR / (d.strftime("%Y%m%d") + ".csv")
        if f.exists():
            frames.append(pd.read_csv(f).assign(date=d))
    long = pd.concat(frames, ignore_index=True)
    close = long.pivot(index="date", columns="symbol", values="close").reindex(dates)
    prev = long.pivot(index="date", columns="symbol", values="prevclose").reindex(dates)
    value = long.pivot(index="date", columns="symbol", values="value").reindex(dates)
    traded = close.notna() & (close > 0)
    ret = close / prev - 1
    first = traded & ~traded.cummax().shift(fill_value=False)   # listing day: no previous close to chain from
    ret = ret.where(traded & ~first & (prev > 0)).fillna(0.0)
    chain = (1 + ret).cumprod().where(traded.cummax())
    px = chain.where(traded).ffill(limit=5)
    exit_px = chain.where(traded).ffill()        # a stock that stops trading exits at its last price
    rows = traded.cumsum()
    avg_value = value.fillna(0).rolling(PIT_VALUE_DAYS, min_periods=PIT_VALUE_DAYS // 2).mean().shift(1)
    member = avg_value.rank(axis=1, ascending=False, method="first") <= PIT_UNIVERSE_SIZE
    sma = px.rolling(200, min_periods=200).mean()
    has = sma.notna() & px.notna() & member
    breadth = ((px > sma) & has).sum(axis=1) / has.sum(axis=1).replace(0, np.nan) * 100
    big_moves = int(((ret.abs() > 0.4) & traded).sum().sum())
    return px, exit_px, rows, member, breadth, big_moves, int(traded.any().sum())


def verdict_for(picks, snaps, monkey_verdict):
    picks = picks.copy()
    picks["alpha"] = picks["stock_return"] - picks["nifty_return"]
    picks = s05.add_net(picks)
    net, win, t = picks["net_alpha"].mean(), (picks["net_alpha"] > 0).mean() * 100, xt.tstat(snaps["alpha"])
    ok = net > S05_NET_ALPHA_PASS and win > S05_WIN_RATE_PASS and t >= PIT_T_PASS and monkey_verdict == "PASS"
    return ("PASS" if ok else "FAIL"), net, win, t, picks


def main():
    import historical_backtest_v3 as e
    _, nifty_data, _ = e.load_market_data()
    nifty = nifty_data["Close"]
    dates = nifty.index[nifty.index >= pd.Timestamp(PIT_START)]
    missing = download(list(dates))
    pct = 100 * len(missing) / len(dates)
    print("  bhavcopy: %d days, %d missing (%.1f%%)" % (len(dates), len(missing), pct))
    if pct > MAX_MISSING_PCT:
        raise SystemExit("[FATAL] %.1f%% of bhavcopy days missing (limit %s%%); NSE may be blocking this "
                         "machine. First missing: %s" % (pct, MAX_MISSING_PCT, [str(d.date()) for d in missing[:5]]))
    px, exit_px, rows, member, breadth, big_moves, n_symbols = panels(dates)
    nifty = nifty.reindex(dates)
    text, v, snaps, picks = xt.report("NSE bhavcopy, point-in-time universe (no survivorship bias)",
                                      px, exit_px, rows, breadth, nifty, member)
    verdict, net, win, t, picks = verdict_for(picks, snaps, v["monkey"])
    head = [
        "# Point-in-time backtest (pre-registered in research_config 1.4.0)", "",
        "**Verdict: %s**" % verdict, "",
        "| | |", "| --- | --- |",
        "| Trading days / missing | %d / %d |" % (len(dates), len(missing)),
        "| Symbols ever seen (delisted included) | %d |" % n_symbols,
        "| Daily moves beyond 40%% (should be rare if PREVCLOSE is adjusted) | %d |" % big_moves,
        "| Snapshots traded (breadth >= %s%%) | %d |" % (BREADTH_THRESHOLD, len(snaps)),
        "| Trades | %d |" % len(picks),
        "| Mean net alpha per 60 days (after Zerodha costs) | %.2f%% (PASS > %s%%) |" % (net, S05_NET_ALPHA_PASS),
        "| Trades beating NIFTY after costs | %.1f%% (PASS > %s%%) |" % (win, S05_WIN_RATE_PASS),
        "| Non-overlapping t-stat of alpha | %.2f (PASS >= %s) |" % (t, PIT_T_PASS),
        "| Random-monkey test | %s (p = %.3f) |" % (v["monkey"], v["monkey_p"]),
        "| Picks vs average eligible stock | %.2f%% per 60 days |" % snaps["selection_edge"].mean(),
        "", "Known limits: a renamed company restarts its price history (it waits 252 days to be eligible again); "
        "a stock that stops trading exits at its last traded price.", "",
    ]
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "pit_backtest.md").write_text("\n".join(head) + text, encoding="utf-8")
    (REPORTS_DIR.parent / "outputs").mkdir(parents=True, exist_ok=True)
    picks.to_csv(REPORTS_DIR.parent / "outputs" / "pit_trades.csv", index=False)
    print("\n".join(head) + text)


if __name__ == "__main__":
    main()
