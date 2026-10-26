# -*- coding: utf-8 -*-
# =============================================================================
# INVEST OS -- STUDY 05: TRANSACTION COSTS
# =============================================================================
# Protocol Version : Invest OS Research Protocol v1.1
# Study Version    : 1.0.0
#
# Research Question:
#   Does the strategy still beat NIFTY after Zerodha delivery charges and
#   slippage on every round trip?
#
# Method: trade_dump.csv only. Each row is one 60-day round trip of
# S05_NOTIONAL_PER_POSITION rupees. Charges come from nse_exec.rules.charges
# (the same code that sizes live orders), slippage from config.
#   net_return = stock_return - round-trip cost %
#   net_alpha  = net_return - nifty_return
#   win        = net_alpha > 0 (beat NIFTY after costs)
# =============================================================================

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import research_utils as ru
import study_00_engine_validation as s00
from nse_exec.rules import charges
from research_config import (
    HOLDING_DAYS, SNAPSHOT_INTERVAL,
    OUTPUTS_DIR, REPORTS_DIR, METADATA_DIR,
    S05_NET_ALPHA_PASS, S05_NET_ALPHA_CONDITIONAL, S05_WIN_RATE_PASS, S05_WIN_RATE_FAIL,
    S05_CHARGES, S05_NOTIONAL_PER_POSITION,
    S05_SLIPPAGE_LARGECAP, S05_SLIPPAGE_MIDCAP, S05_MIDCAP_SYMBOLS,
)

STUDY_ID      = "05"
STUDY_NAME    = "Transaction Costs"
STUDY_VERSION = "1.0.0"

OUTPUT_CSV    = OUTPUTS_DIR  / "study_05_output.csv"
OUTPUT_REPORT = REPORTS_DIR  / "study_05_report.md"
OUTPUT_META   = METADATA_DIR / "study_05_metadata.json"


def round_trip_cost_pct(symbol, stock_return_pct):
    """Charges on the buy and the sell, plus slippage both ways, as % of the buy value."""
    n = S05_NOTIONAL_PER_POSITION
    sell_value = n * (1 + stock_return_pct / 100)
    fees = charges("BUY", 1, n, S05_CHARGES) + charges("SELL", 1, max(sell_value, 0.01), S05_CHARGES)
    slip = S05_SLIPPAGE_MIDCAP if symbol in S05_MIDCAP_SYMBOLS else S05_SLIPPAGE_LARGECAP
    return float(fees) / n * 100 + 2 * slip * 100


def add_net(df):
    df = df.copy()
    df["cost_pct"] = [round_trip_cost_pct(s, r) for s, r in zip(df["symbol"], df["stock_return"])]
    df["net_return"] = df["stock_return"] - df["cost_pct"]
    df["net_alpha"] = df["net_return"] - df["nifty_return"]
    return df


def non_overlapping_tstat(df, col="net_alpha"):
    """Informational. Weekly snapshots with 60-day holds overlap ~12x, so per-row stats
    overstate certainty; keep every k-th snapshot so holding periods do not overlap."""
    k = max(1, HOLDING_DAYS // SNAPSHOT_INTERVAL)
    per_snap = df.groupby("date")[col].mean().sort_index().iloc[::k]
    n = len(per_snap)
    if n < 3 or per_snap.std(ddof=1) == 0:
        return n, float("nan")
    return n, float(per_snap.mean() / per_snap.std(ddof=1) * np.sqrt(n))


def summarise(df):
    n_periods, t = non_overlapping_tstat(df)
    return {
        "trades": int(len(df)),
        "mean_gross_alpha": round(float(df["alpha"].mean()), 3),
        "mean_cost_pct": round(float(df["cost_pct"].mean()), 3),
        "mean_net_alpha": round(float(df["net_alpha"].mean()), 3),
        "median_net_alpha": round(float(df["net_alpha"].median()), 3),
        "net_win_rate_pct": round(float((df["net_alpha"] > 0).mean() * 100), 2),
        "mean_net_win": round(float(df.loc[df["net_alpha"] > 0, "net_alpha"].mean()), 3),
        "mean_net_loss": round(float(df.loc[df["net_alpha"] <= 0, "net_alpha"].mean()), 3),
        "non_overlapping_periods": n_periods,
        "non_overlapping_t_stat": round(t, 2),
    }


def determine_verdict(s):
    if s["mean_net_alpha"] > S05_NET_ALPHA_PASS and s["net_win_rate_pct"] > S05_WIN_RATE_PASS:
        return "PASS"
    if s["mean_net_alpha"] < S05_NET_ALPHA_CONDITIONAL or s["net_win_rate_pct"] < S05_WIN_RATE_FAIL:
        return "FAIL"
    return "CONDITIONAL"


def write_report(s, verdict, env, tests):
    lines = [
        ru.report_header(STUDY_ID, STUDY_NAME, STUDY_VERSION, env), "",
        "## Objective",
        "Measure alpha after Zerodha equity-delivery charges and slippage on every round trip.", "",
        ru.report_env_table(env), "",
        "## Method",
        ("Each trade is a Rs " + str(S05_NOTIONAL_PER_POSITION) + " round trip. Charges: STT, exchange, SEBI, "
         "GST, stamp duty and DP via `nse_exec.rules.charges` with `S05_CHARGES`. Slippage: " +
         str(S05_SLIPPAGE_LARGECAP * 100) + "% (large cap) or " + str(S05_SLIPPAGE_MIDCAP * 100) +
         "% (mid cap) each way. A win means beating NIFTY after costs. The NIFTY leg carries no cost, "
         "which makes this slightly conservative. Tax is not included."), "",
        "## Acceptance Tests", ru.md_test_table(tests), "",
        "## Results", ru.md_kv_table([(k.replace("_", " "), str(v)) for k, v in s.items()]), "",
        ("The t-stat uses one snapshot every " + str(HOLDING_DAYS // SNAPSHOT_INTERVAL) +
         " weeks so holding periods do not overlap. It is informational, not part of the verdict; "
         "below about 2 the edge cannot be told apart from luck."), "",
        "## Verdict Criteria (defined before results were examined)",
        ru.md_table(["Verdict", "Criteria"], [
            ["PASS", "Mean net alpha > " + str(S05_NET_ALPHA_PASS) + "% per 60d and net win rate > " + str(S05_WIN_RATE_PASS) + "%"],
            ["CONDITIONAL", "Neither PASS nor FAIL"],
            ["FAIL", "Mean net alpha < " + str(S05_NET_ALPHA_CONDITIONAL) + "% or net win rate < " + str(S05_WIN_RATE_FAIL) + "%"],
        ]), "",
        "## Verdict", "**" + verdict + "**", "",
        "## Next Study", "**Study 06 -- Walk-Forward Validation** (uses this study's net alpha).",
    ]
    OUTPUT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print("  [OK] Report: " + str(OUTPUT_REPORT))


def load_checked():
    """Shared by Studies 05 and 06: verified engine, loaded dump, acceptance tests."""
    env = ru.collect_env(ru.verify_engine_hash())
    if not Path(s00.TRADE_DUMP).exists():
        print("[FATAL] trade_dump.csv not found in " + str(Path.cwd()))
        sys.exit(1)
    df = s00.load_trade_dump()
    tests = ru.run_acceptance_tests({
        "Required columns present": s00.chk_required_cols(df),
        "No duplicate trades": s00.chk_no_duplicates(df),
        "No null returns or alpha": s00.chk_no_nulls(df),
        "No unparseable dates": (bool(df["date"].notna().all()), str(int(df["date"].isna().sum())) + " bad"),
        "Row count > 0": (len(df) > 0, str(len(df)) + " rows"),
    })
    return env, add_net(df), tests


def main():
    start = time.time()
    ru.ensure_dirs()
    ru.print_study_header(STUDY_ID, STUDY_NAME)
    env, df, tests = load_checked()
    s = summarise(df)
    verdict = determine_verdict(s)
    env["runtime_seconds"] = time.time() - start
    df.to_csv(str(OUTPUT_CSV), index=False)
    write_report(s, verdict, env, tests)
    ru.write_metadata(STUDY_ID, STUDY_NAME, STUDY_VERSION, {k: str(v) for k, v in s.items()},
                      verdict, env, tests, [str(OUTPUT_CSV), str(OUTPUT_REPORT), str(OUTPUT_META)])
    ru.print_env_block(env)
    for k, v in s.items():
        print("  " + k.ljust(26) + str(v))
    ru.print_verdict_block(verdict)


if __name__ == "__main__":
    main()
