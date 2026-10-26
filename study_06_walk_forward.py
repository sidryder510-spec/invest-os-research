# -*- coding: utf-8 -*-
# =============================================================================
# INVEST OS -- STUDY 06: WALK-FORWARD VALIDATION
# =============================================================================
# Protocol Version : Invest OS Research Protocol v1.1
# Study Version    : 1.0.0
#
# Research Question:
#   Is the after-cost alpha consistent year by year, or does it come from a
#   few good years?
#
# Method: trade_dump.csv with Study 05's net alpha. One test window per year
# in S06_TEST_YEARS (by snapshot date). The engine's parameters are frozen,
# so nothing is refit per window: this measures stability across years.
# It is not true out-of-sample if the parameters were chosen while looking
# at this history; only forward paper trading from the freeze date is.
# =============================================================================

import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import research_utils as ru
import study_05_transaction_costs as s05
from research_config import (
    OUTPUTS_DIR, REPORTS_DIR, METADATA_DIR,
    S06_POSITIVE_WINDOWS_PASS, S06_OOS_ALPHA_PASS, S06_OOS_ALPHA_CONDITIONAL, S06_TEST_YEARS,
)

STUDY_ID      = "06"
STUDY_NAME    = "Walk-Forward Validation"
STUDY_VERSION = "1.0.0"

OUTPUT_CSV    = OUTPUTS_DIR  / "study_06_output.csv"
OUTPUT_REPORT = REPORTS_DIR  / "study_06_report.md"
OUTPUT_META   = METADATA_DIR / "study_06_metadata.json"


def windows(df):
    rows = []
    for year in S06_TEST_YEARS:
        w = df[df["date"].dt.year == year]
        rows.append({
            "year": year,
            "trades": int(len(w)),
            "mean_gross_alpha": round(float(w["alpha"].mean()), 3) if len(w) else None,
            "mean_net_alpha": round(float(w["net_alpha"].mean()), 3) if len(w) else None,
            "net_win_rate_pct": round(float((w["net_alpha"] > 0).mean() * 100), 2) if len(w) else None,
        })
    return pd.DataFrame(rows)


def summarise(table):
    net = table["mean_net_alpha"].dropna()
    return {
        "test_windows": int(len(table)),
        "windows_with_data": int(len(net)),
        "positive_windows": int((net > 0).sum()),
        "mean_oos_net_alpha": round(float(net.mean()), 3) if len(net) else float("nan"),
        "worst_window": int(table.loc[table["mean_net_alpha"].idxmin(), "year"]) if len(net) else None,
        "worst_window_net_alpha": round(float(net.min()), 3) if len(net) else None,
    }


def determine_verdict(s):
    if s["positive_windows"] >= S06_POSITIVE_WINDOWS_PASS and s["mean_oos_net_alpha"] >= S06_OOS_ALPHA_PASS:
        return "PASS"
    if s["mean_oos_net_alpha"] < S06_OOS_ALPHA_CONDITIONAL:
        return "FAIL"
    return "CONDITIONAL"


def write_report(table, s, verdict, env, tests):
    lines = [
        ru.report_header(STUDY_ID, STUDY_NAME, STUDY_VERSION, env), "",
        "## Objective",
        "Check that after-cost alpha holds up across " + str(len(S06_TEST_YEARS)) + " yearly test windows.", "",
        ru.report_env_table(env), "",
        "## Method",
        ("Net alpha per trade comes from Study 05. Each window is one calendar year of snapshots. "
         "A year with no trades (breadth filter kept the strategy in cash) counts as not positive. "
         "The engine is frozen, so no parameters are refit. This tests stability, not true "
         "out-of-sample performance: if the parameters were chosen while looking at these years, "
         "only forward paper trading from the freeze date is truly out of sample."), "",
        "## Acceptance Tests", ru.md_test_table(tests), "",
        "## Windows", ru.md_table(list(table.columns), table.astype(object).values.tolist()), "",
        "## Results", ru.md_kv_table([(k.replace("_", " "), str(v)) for k, v in s.items()]), "",
        "## Verdict Criteria (defined before results were examined)",
        ru.md_table(["Verdict", "Criteria"], [
            ["PASS", ">= " + str(S06_POSITIVE_WINDOWS_PASS) + " of " + str(len(S06_TEST_YEARS)) +
                     " windows positive and mean net alpha >= " + str(S06_OOS_ALPHA_PASS) + "% per 60d"],
            ["CONDITIONAL", "Neither PASS nor FAIL"],
            ["FAIL", "Mean net alpha < " + str(S06_OOS_ALPHA_CONDITIONAL) + "% per 60d"],
        ]), "",
        "## Verdict", "**" + verdict + "**", "",
        "## Next Step",
        "If PASS: paper trade through `nse_exec` from the freeze date before any live order.",
    ]
    OUTPUT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print("  [OK] Report: " + str(OUTPUT_REPORT))


def main():
    start = time.time()
    ru.ensure_dirs()
    ru.print_study_header(STUDY_ID, STUDY_NAME)
    env, df, tests = s05.load_checked()
    table = windows(df)
    s = summarise(table)
    verdict = determine_verdict(s)
    env["runtime_seconds"] = time.time() - start
    table.to_csv(str(OUTPUT_CSV), index=False)
    write_report(table, s, verdict, env, tests)
    ru.write_metadata(STUDY_ID, STUDY_NAME, STUDY_VERSION, {k: str(v) for k, v in s.items()},
                      verdict, env, tests, [str(OUTPUT_CSV), str(OUTPUT_REPORT), str(OUTPUT_META)])
    ru.print_env_block(env)
    print(table.to_string(index=False))
    ru.print_verdict_block(verdict)


if __name__ == "__main__":
    main()
