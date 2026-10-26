# -*- coding: utf-8 -*-
# =============================================================================
# INVEST OS -- STUDY 02: SELECTION CONCENTRATION
# =============================================================================
# Protocol Version : Invest OS Research Protocol v1.1
# Study Version    : 1.0.0
#
# Research Question:
#   Does a single stock (EICHERMOT) dominate the Top-5 selections, and does the
#   strategy's alpha survive without it?
#
# Method: trade_dump.csv only. HHI and Gini of selection counts, top symbol's
# share of all selections, mean alpha with and without the top symbol and
# without EICHERMOT.
# =============================================================================

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import research_utils as ru
import study_00_engine_validation as s00
from research_config import (
    OUTPUTS_DIR, REPORTS_DIR, METADATA_DIR,
    S02_HHI_PASS, S02_HHI_CONDITIONAL, S02_TOP1_PASS_PCT, S02_TOP1_FAIL_PCT,
)

STUDY_ID      = "02"
STUDY_NAME    = "Selection Concentration"
STUDY_VERSION = "1.0.0"
WATCH_SYMBOL  = "EICHERMOT"

OUTPUT_CSV    = OUTPUTS_DIR  / "study_02_output.csv"
OUTPUT_REPORT = REPORTS_DIR  / "study_02_report.md"
OUTPUT_META   = METADATA_DIR / "study_02_metadata.json"


def gini(counts):
    x = np.sort(np.asarray(counts, dtype=float))
    n = len(x)
    if n == 0 or x.sum() == 0:
        return 0.0
    return float((2 * np.arange(1, n + 1) - n - 1).dot(x) / (n * x.sum()))


def analyse(df):
    counts = df["symbol"].value_counts()
    share = counts / counts.sum() * 100
    table = pd.DataFrame({
        "symbol": counts.index,
        "selections": counts.values,
        "share_pct": share.round(2).values,
        "mean_alpha": df.groupby("symbol")["alpha"].mean().reindex(counts.index).round(3).values,
    })
    top1 = counts.index[0]
    alpha_wo = lambda sym: float(df.loc[df["symbol"] != sym, "alpha"].mean())
    weeks_with = lambda sym: df.loc[df["symbol"] == sym, "date"].nunique() / df["date"].nunique() * 100
    alpha_part = lambda sym: df.loc[df["symbol"] == sym, "alpha"].sum() / df["alpha"].sum() * 100
    summary = {
        "total_selections": int(len(df)),
        "unique_symbols": int(len(counts)),
        "hhi": round(float((share ** 2).sum()), 1),
        "gini": round(gini(counts.values), 3),
        "top1_symbol": top1,
        "top1_share_pct": round(float(share.iloc[0]), 2),
        "mean_alpha_all": round(float(df["alpha"].mean()), 3),
        "mean_alpha_without_top1": round(alpha_wo(top1), 3),
        "watch_share_pct": round(float(share.get(WATCH_SYMBOL, 0.0)), 2),
        "mean_alpha_without_watch": round(alpha_wo(WATCH_SYMBOL), 3),
        # Informational: the locked share/HHI tests cannot fail (see report), these can.
        "max_possible_share_pct": round(100 / df.groupby("date")["symbol"].count().max(), 2),
        "top1_weeks_present_pct": round(float(weeks_with(top1)), 2),
        "top1_alpha_contribution_pct": round(float(alpha_part(top1)), 2),
        "watch_weeks_present_pct": round(float(weeks_with(WATCH_SYMBOL)), 2),
        "watch_alpha_contribution_pct": round(float(alpha_part(WATCH_SYMBOL)), 2),
    }
    return table, summary


def determine_verdict(s):
    if s["hhi"] < S02_HHI_PASS and s["top1_share_pct"] < S02_TOP1_PASS_PCT:
        return "PASS"
    if s["hhi"] > S02_HHI_CONDITIONAL or s["top1_share_pct"] > S02_TOP1_FAIL_PCT:
        return "FAIL"
    return "CONDITIONAL"


def write_report(table, s, verdict, env, tests):
    drop = s["mean_alpha_all"] - s["mean_alpha_without_watch"]
    lines = [
        ru.report_header(STUDY_ID, STUDY_NAME, STUDY_VERSION, env), "",
        "## Objective",
        "Quantify how concentrated the Top-5 selections are and whether alpha depends on " + WATCH_SYMBOL + ".", "",
        ru.report_env_table(env), "",
        "## Acceptance Tests", ru.md_test_table(tests), "",
        "## Results",
        ru.md_kv_table([(k.replace("_", " "), str(v)) for k, v in s.items()]), "",
        "### Top 10 Symbols",
        ru.md_table(list(table.columns), table.head(10).astype(object).values.tolist()), "",
        "## Alpha Without " + WATCH_SYMBOL,
        ("Mean alpha per 60 days falls from " + str(s["mean_alpha_all"]) + " to " +
         str(s["mean_alpha_without_watch"]) + " (" + str(round(drop, 3)) + " points) without " +
         WATCH_SYMBOL + "."), "",
        "## Verdict Criteria (defined before results were examined)",
        ru.md_table(["Verdict", "Criteria"], [
            ["PASS", "HHI < " + str(S02_HHI_PASS) + " and top symbol < " + str(S02_TOP1_PASS_PCT) + "% of selections"],
            ["CONDITIONAL", "Neither PASS nor FAIL"],
            ["FAIL", "HHI > " + str(S02_HHI_CONDITIONAL) + " or top symbol > " + str(S02_TOP1_FAIL_PCT) + "%"],
        ]), "",
        "## Verdict", "**" + verdict + "**", "",
        "## Protocol Warning",
        ("Each snapshot holds " + str(round(100 / s["max_possible_share_pct"])) + " different stocks, so no "
         "symbol can exceed " + str(s["max_possible_share_pct"]) + "% of selections and HHI cannot exceed " +
         str(round(s["max_possible_share_pct"] * 100)) + ". The locked criteria above therefore cannot reach "
         "FAIL, and this verdict says little about concentration. Judge it on the informational rows instead: "
         "top1 weeks present pct (how often the stock is held) and top1 alpha contribution pct (how much of "
         "the total alpha it supplies). New thresholds for these need an owner decision and a research config version bump."), "",
        "## Next Study",
        "**Study 05 -- Transaction Costs** (Studies 03 and 04 are not implemented yet).",
    ]
    OUTPUT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print("  [OK] Report: " + str(OUTPUT_REPORT))


def main():
    start = time.time()
    ru.ensure_dirs()
    ru.print_study_header(STUDY_ID, STUDY_NAME)
    env = ru.collect_env(ru.verify_engine_hash())
    if not Path(s00.TRADE_DUMP).exists():
        print("[FATAL] trade_dump.csv not found in " + str(Path.cwd()))
        sys.exit(1)
    df = s00.load_trade_dump()
    tests = ru.run_acceptance_tests({
        "Required columns present": s00.chk_required_cols(df),
        "No duplicate trades": s00.chk_no_duplicates(df),
        "Row count > 0": (len(df) > 0, str(len(df)) + " rows"),
    })
    table, s = analyse(df)
    verdict = determine_verdict(s)
    env["runtime_seconds"] = time.time() - start
    table.to_csv(str(OUTPUT_CSV), index=False)
    write_report(table, s, verdict, env, tests)
    ru.write_metadata(STUDY_ID, STUDY_NAME, STUDY_VERSION, {k: str(v) for k, v in s.items()},
                      verdict, env, tests, [str(OUTPUT_CSV), str(OUTPUT_REPORT), str(OUTPUT_META)])
    ru.print_env_block(env)
    for k, v in s.items():
        print("  " + k.ljust(26) + str(v))
    ru.print_verdict_block(verdict)


if __name__ == "__main__":
    main()
