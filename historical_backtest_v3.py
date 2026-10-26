# -*- coding: utf-8 -*-
# =============================================================================
# INVEST OS -- RESEARCH ENGINE v3.0.0 (frozen; hash-locked in research_config.py)
# =============================================================================
# Rebuilt 2026-10-26 because the v2 engine was lost. Score locked before any
# result was seen: 12-1 momentum = close 21 trading days ago / close 252
# trading days ago - 1. Everything else comes from research_config.py:
# Top-N by score, weekly snapshots, MIN_HISTORY eligibility, trade only when
# >= BREADTH_THRESHOLD % of the universe is above its 200-day SMA, hold
# HOLDING_DAYS trading days.
#
# Entry is the close of the trading day AFTER the snapshot, so the score never
# sees the entry price. Prices: Yahoo Finance, split/dividend adjusted.
#
# Known bias: the universe is TODAY's Nifty 500 list applied to the past
# (survivorship). Stocks that fell out or were delisted are missing, which
# flatters results. Point-in-time constituents are not freely available.
# =============================================================================

import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

from research_config import TOP_N, HOLDING_DAYS, MIN_HISTORY, BREADTH_THRESHOLD, SNAPSHOT_INTERVAL

UNIVERSE_URL  = "https://niftyindices.com/IndexConstituent/ind_nifty500list.csv"
UNIVERSE_FILE = Path("data/universe_nifty500.csv")
CACHE_FILE    = Path("data/market_cache.csv.gz")
NIFTY         = "^NSEI"
START         = "2010-01-01"
SMA_DAYS      = 200
MIN_BREADTH_STOCKS = 50   # breadth from fewer stocks is noise; no trading before then

_state = {}   # panels built by load_market_data, reused by the other API calls


def load_universe():
    if not UNIVERSE_FILE.exists():
        req = urllib.request.Request(UNIVERSE_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        UNIVERSE_FILE.parent.mkdir(parents=True, exist_ok=True)
        UNIVERSE_FILE.write_bytes(data)
    return sorted(pd.read_csv(UNIVERSE_FILE)["Symbol"].astype(str).str.strip().unique())


def _download(tickers):
    import yfinance as yf
    closes = {}
    for i in range(0, len(tickers), 50):
        chunk = tickers[i:i + 50]
        for attempt in range(3):
            try:
                df = yf.download(chunk, start=START, auto_adjust=True, progress=False,
                                 threads=True, group_by="ticker")
                break
            except Exception as e:
                print("  [WARN] download retry %d: %s" % (attempt + 1, e))
                time.sleep(15 * (attempt + 1))
        else:
            continue
        for t in chunk:
            try:
                s = df[t]["Close"].dropna()
            except KeyError:
                continue
            if len(s):
                closes[t] = s
    return closes


def load_market_data():
    """Returns (stock_data {symbol: DataFrame[Close]}, nifty_data DataFrame[Close], panel)."""
    if CACHE_FILE.exists():
        closes = pd.read_csv(CACHE_FILE, index_col=0, parse_dates=True)
    else:
        symbols = load_universe()
        closes = pd.DataFrame(_download([s + ".NS" for s in symbols] + [NIFTY]))
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        closes.to_csv(CACHE_FILE)
    if NIFTY not in closes:
        raise RuntimeError("NIFTY (^NSEI) history did not download")
    closes = closes.sort_index()
    nifty = closes[NIFTY].dropna()
    raw = closes.drop(columns=[NIFTY]).reindex(nifty.index)   # NIFTY trading days are the calendar
    raw.columns = [c[:-3] if c.endswith(".NS") else c for c in raw.columns]

    px = raw.ffill(limit=5)   # bridge short suspensions/holiday mismatches, not long gaps
    sma = px.rolling(SMA_DAYS, min_periods=SMA_DAYS).mean()
    has_sma = sma.notna() & px.notna()
    breadth = ((px > sma) & has_sma).sum(axis=1) / has_sma.sum(axis=1).replace(0, np.nan) * 100
    breadth[has_sma.sum(axis=1) < MIN_BREADTH_STOCKS] = np.nan
    _state.update(
        px=px,
        exit_px=raw.ffill(),   # a stock that stops trading exits at its last price
        rows=raw.notna().cumsum(),
        score=px.shift(21) / px.shift(252) - 1,
        breadth=breadth,
    )
    stock_data = {s: raw[[s]].dropna().rename(columns={s: "Close"}) for s in raw.columns}
    stock_data = {s: df for s, df in stock_data.items() if not df.empty}
    return stock_data, nifty.to_frame("Close"), _state


def _require_state():
    if not _state:
        raise RuntimeError("call load_market_data() first")
    return _state


def get_snapshot_dates(nifty_data):
    """Weekly dates on which the strategy trades: breadth passes and a full holding window follows."""
    st = _require_state()
    idx = nifty_data.index
    last = len(idx) - HOLDING_DAYS - 2          # entry next day + full hold must fit
    dates = idx[MIN_HISTORY:last + 1:SNAPSHOT_INTERVAL]
    ok = st["breadth"].reindex(dates) >= BREADTH_THRESHOLD
    return list(dates[ok.values])


def generate_historical_candidates(snapshot, stock_data, nifty_data, top_n=TOP_N):
    st = _require_state()
    snap = pd.Timestamp(snapshot)
    if not st["breadth"].get(snap, np.nan) >= BREADTH_THRESHOLD:
        return []
    score = st["score"].loc[snap]
    eligible = (st["rows"].loc[snap] >= MIN_HISTORY) & score.notna() & st["px"].loc[snap].notna()
    ranked = score[eligible].sort_values(ascending=False).head(top_n)
    return [{"symbol": s, "score": round(float(v), 6)} for s, v in ranked.items()]


def export_trade_dump(path="trade_dump.csv"):
    stock_data, nifty_data, st = load_market_data()
    idx = nifty_data.index
    nifty = nifty_data["Close"]
    rows = []
    for snap in get_snapshot_dates(nifty_data):
        i = idx.get_loc(snap)
        entry, exit_ = idx[i + 1], idx[i + 1 + HOLDING_DAYS]
        n_ret = (nifty[exit_] / nifty[entry] - 1) * 100
        for rank, c in enumerate(generate_historical_candidates(snap, stock_data, nifty_data), 1):
            p0, p1 = st["px"].at[entry, c["symbol"]], st["exit_px"].at[exit_, c["symbol"]]
            if not (p0 > 0 and p1 > 0):
                continue
            s_ret = (p1 / p0 - 1) * 100
            rows.append({"date": snap.strftime("%Y-%m-%d"), "symbol": c["symbol"], "rank": rank,
                         "score": c["score"], "stock_return": round(s_ret, 4),
                         "nifty_return": round(n_ret, 4), "alpha": round(s_ret - n_ret, 4)})
    df = pd.DataFrame(rows, columns=["date", "symbol", "rank", "score", "stock_return", "nifty_return", "alpha"])
    df.to_csv(path, index=False)
    print("  [OK] %s: %d trades over %d snapshots" % (path, len(df), df["date"].nunique()))
    return df
