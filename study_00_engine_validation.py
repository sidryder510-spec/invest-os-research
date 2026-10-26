# -*- coding: utf-8 -*-
# =============================================================================
# INVEST OS -- STUDY 00: ENGINE VALIDATION
# =============================================================================
# Protocol Version : Invest OS Research Protocol v1.1
# Study Version    : 1.0.0
#
# Research Question:
#   Is the research engine internally consistent and suitable as the
#   foundation for all subsequent studies?
#
# Validates (does NOT rerun backtest -- uses trade_dump.csv):
#   - Engine SHA256 matches locked hash
#   - Required API functions exist
#   - trade_dump.csv has no duplicate rows
#   - Exactly TOP_N stocks per snapshot
#   - Sequential ranks per snapshot
#   - No null returns or alpha values
#   - alpha == stock_return - nifty_return (within tolerance)
#   - Weekly snapshot spacing (4-15 calendar days)
#   - Engine snapshot count matches dump snapshot count
#
# Runtime: < 2 minutes
# =============================================================================

import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import research_utils as ru
from research_config import (
    TOP_N, REQUIRED_ENGINE_API,
    OUTPUTS_DIR, REPORTS_DIR, METADATA_DIR,
    S00_MAX_CONDITIONAL_FAILURES,
)

# =============================================================================
# Constants
# =============================================================================

STUDY_ID      = "00"
STUDY_NAME    = "Engine Validation"
STUDY_VERSION = "1.0.0"
TRADE_DUMP    = "trade_dump.csv"

OUTPUT_CSV    = OUTPUTS_DIR  / "study_00_output.csv"
OUTPUT_REPORT = REPORTS_DIR  / "study_00_report.md"
OUTPUT_META   = METADATA_DIR / "study_00_metadata.json"

CRITICAL_CHECKS = [
    "Required columns present",
    "No duplicate trades",
    "alpha == stock_return - nifty_return",
]


# =============================================================================
# Validation functions
# =============================================================================

def load_trade_dump():
    df = pd.read_csv(TRADE_DUMP)
    df["date"] = pd.to_datetime(df["date"], dayfirst=False, errors="coerce")
    return df


def chk_required_cols(df):
    required = {"date", "symbol", "rank", "score",
                "stock_return", "nifty_return", "alpha"}
    missing  = required - set(df.columns)
    ok = len(missing) == 0
    return ok, "All present" if ok else "Missing: " + str(missing)


def chk_no_duplicates(df):
    n = int(df.duplicated(subset=["date", "symbol"]).sum())
    return n == 0, "0 duplicates" if n == 0 else str(n) + " duplicates"


def chk_top_n(df):
    counts = df.groupby("date")["symbol"].count()
    bad = int((counts != TOP_N).sum())
    return (bad == 0,
            "All snapshots have " + str(TOP_N) + " stocks" if bad == 0
            else str(bad) + " snapshots deviate (min=" + str(int(counts.min())) +
                 " max=" + str(int(counts.max())) + ")")


def chk_sequential_ranks(df):
    def ok(grp):
        return sorted(grp["rank"].tolist()) == list(range(1, len(grp) + 1))
    bad = int((~df.groupby("date").apply(ok)).sum())
    return bad == 0, ("All ranks sequential" if bad == 0
                      else str(bad) + " snapshots have non-sequential ranks")


def chk_no_nulls(df):
    cols = ["stock_return", "nifty_return", "alpha"]
    nulls = {c: int(df[c].isna().sum()) for c in cols}
    total = sum(nulls.values())
    return (total == 0,
            "0 nulls" if total == 0
            else "  ".join(c + "=" + str(n) for c, n in nulls.items() if n > 0))


def chk_alpha_consistency(df, tol=0.02):
    diff = (df["alpha"] - (df["stock_return"] - df["nifty_return"])).abs()
    bad  = int((diff > tol).sum())
    return (bad == 0,
            "Consistent (max diff=" + str(round(float(diff.max()), 4)) + ")" if bad == 0
            else str(bad) + " rows inconsistent (max=" + str(round(float(diff.max()), 4)) + ")")


def chk_snapshot_spacing(df):
    snaps = sorted(df["date"].dropna().unique())
    if len(snaps) < 2:
        return True, "Only 1 snapshot"
    gaps = [(pd.Timestamp(b) - pd.Timestamp(a)).days
            for a, b in zip(snaps, snaps[1:])]
    bad = sum(1 for g in gaps if g < 4 or g > 15)
    mn, mx = min(gaps), max(gaps)
    return (bad == 0,
            "OK (min=" + str(mn) + "d max=" + str(mx) + "d)" if bad == 0
            else str(bad) + " irregular gaps (min=" + str(mn) + "d max=" + str(mx) + "d)")


def chk_engine_vs_dump(engine, df):
    try:
        stock_data, nifty_data, _ = engine.load_market_data()
        engine_snaps = engine.get_snapshot_dates(nifty_data)
        n_eng  = len(engine_snaps)
        n_dump = df["date"].nunique()
        match  = abs(n_eng - n_dump) <= 5
        return (match,
                "Engine=" + str(n_eng) + " Dump=" + str(n_dump) +
                (" (OK)" if match else " (MISMATCH -- diff=" + str(abs(n_eng - n_dump)) + ")"),
                n_eng, n_dump)
    except Exception as e:
        return False, "Error: " + str(e), 0, df["date"].nunique()


# =============================================================================
# Verdict
# =============================================================================

def determine_verdict(checks):
    any_critical_fail = any(
        not checks[k]["passed"] for k in CRITICAL_CHECKS if k in checks
    )
    n_failed = sum(1 for v in checks.values() if not v["passed"])
    if n_failed == 0:
        return "PASS"
    if any_critical_fail or n_failed > S00_MAX_CONDITIONAL_FAILURES:
        return "FAIL"
    return "CONDITIONAL"


# =============================================================================
# Report
# =============================================================================

def write_report(checks, summary, verdict, env):
    ru.ensure_dirs()
    n_passed = summary["checks_passed"]
    n_failed = summary["checks_failed"]

    if verdict == "PASS":
        conclusion     = ("All " + str(n_passed) + " engine validation checks passed. "
                          "The research engine is internally consistent and suitable "
                          "as the foundation for Studies 01 through 06.")
        verdict_text   = "**PASS** -- All checks passed."
        recommendation = "Proceed to Study 01 -- Eligibility Audit."
        model_impact   = "NO -- Engine validated as-is."
    elif verdict == "CONDITIONAL":
        conclusion     = (str(n_failed) + " non-critical warning(s). "
                          "Engine is usable but flagged items should be reviewed.")
        verdict_text   = "**CONDITIONAL** -- " + str(n_failed) + " non-critical warning(s)."
        recommendation = "Review warnings. Proceed to Study 01 with noted caveats."
        model_impact   = "CONDITIONAL -- Review flagged items."
    else:
        conclusion     = (str(n_failed) + " critical check(s) failed. "
                          "Engine has structural problems. "
                          "No subsequent study should be trusted until resolved.")
        verdict_text   = "**FAIL** -- " + str(n_failed) + " critical check(s) failed."
        recommendation = "Fix failing checks, then rerun Study 00."
        model_impact   = "YES -- Engine requires correction."

    results_rows = [[name, "PASS" if v["passed"] else "FAIL", v["detail"]]
                    for name, v in checks.items()]
    results_table = ru.md_table(["Check", "Result", "Detail"], results_rows)

    summary_rows = [
        ("Total checks run",     str(summary["total_checks"])),
        ("Checks passed",        str(summary["checks_passed"])),
        ("Checks failed",        str(summary["checks_failed"])),
        ("Engine snapshots",     str(summary["engine_snapshots"])),
        ("Dump snapshots",       str(summary["dump_snapshots"])),
        ("Total trades",         str(summary["total_trades"])),
    ]

    lines = [
        ru.report_header(STUDY_ID, STUDY_NAME, STUDY_VERSION, env),
        "",
        "## Objective",
        "Validate the frozen research engine before any study results are produced.",
        "If this study fails, no subsequent study result can be trusted.",
        "",
        ru.report_env_table(env),
        "",
        "## Validation Results",
        results_table,
        "",
        "## Summary",
        ru.md_kv_table(summary_rows),
        "",
        "## Conclusion",
        conclusion,
        "",
        "## Verdict Criteria (defined before results were examined)",
        ru.md_table(
            ["Verdict", "Criteria"],
            [
                ["PASS",        "All checks pass"],
                ["CONDITIONAL", "<= " + str(S00_MAX_CONDITIONAL_FAILURES) + " non-critical failures"],
                ["FAIL",        "Any critical check fails or > " +
                                str(S00_MAX_CONDITIONAL_FAILURES) + " failures"],
            ]
        ),
        "",
        "## Verdict",
        verdict_text,
        "",
        "## Research Impact",
        ru.md_table(
            ["Question", "Answer"],
            [
                ["Does this change the model?", model_impact],
                ["Does this change production?", "NO -- Production system is separate."],
                ["Does this require rerunning previous studies?", "NO -- This is Study 00."],
            ]
        ),
        "",
        "## Recommendation",
        recommendation,
        "",
        "## Next Study",
        "**Study 01 -- Eligibility Audit:** Verifies that every stock was only",
        "selected after accumulating 252 trading days of price history.",
    ]

    OUTPUT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print("  [OK] Report: " + str(OUTPUT_REPORT))


# =============================================================================
# Main
# =============================================================================

def main():
    start = time.time()
    ru.ensure_dirs()
    ru.print_study_header(STUDY_ID, STUDY_NAME)

    print("Step 1 -- Verifying engine hash...")
    actual_hash = ru.verify_engine_hash()
    print("  [OK] Hash verified")

    print("Step 2 -- Loading engine and verifying API...")
    engine = ru.load_engine()
    ru.verify_engine_api(engine, REQUIRED_ENGINE_API)
    print("  [OK] Engine loaded")

    env = ru.collect_env(actual_hash)

    print("Step 3 -- Loading trade_dump.csv...")
    if not Path(TRADE_DUMP).exists():
        print("[FATAL] trade_dump.csv not found in " + str(Path.cwd()))
        sys.exit(1)
    df = load_trade_dump()
    print("  [OK] " + str(len(df)) + " rows loaded")

    print("Step 4 -- Running validation checks...")
    checks = {}

    ok, det = chk_required_cols(df)
    checks["Required columns present"] = {"passed": ok, "detail": det}

    ok, det = chk_no_duplicates(df)
    checks["No duplicate trades"] = {"passed": ok, "detail": det}

    ok, det = chk_top_n(df)
    checks["Exactly Top-" + str(TOP_N) + " per snapshot"] = {"passed": ok, "detail": det}

    ok, det = chk_sequential_ranks(df)
    checks["Sequential ranks per snapshot"] = {"passed": ok, "detail": det}

    ok, det = chk_no_nulls(df)
    checks["No null returns or alpha"] = {"passed": ok, "detail": det}

    ok, det = chk_alpha_consistency(df)
    checks["alpha == stock_return - nifty_return"] = {"passed": ok, "detail": det}

    ok, det = chk_snapshot_spacing(df)
    checks["Weekly snapshot spacing"] = {"passed": ok, "detail": det}

    print("  Comparing engine snapshot count (downloads data -- may take a minute)...")
    ok, det, n_eng, n_dump = chk_engine_vs_dump(engine, df)
    checks["Engine vs dump snapshot count"] = {"passed": ok, "detail": det}

    # Acceptance tests
    acceptance = {k: (v["passed"], v["detail"]) for k, v in checks.items()}
    ru.run_acceptance_tests(acceptance)

    n_passed = sum(1 for v in checks.values() if v["passed"])
    n_failed = len(checks) - n_passed
    verdict  = determine_verdict(checks)

    summary = {
        "total_checks"    : str(len(checks)),
        "checks_passed"   : str(n_passed),
        "checks_failed"   : str(n_failed),
        "engine_snapshots": str(n_eng),
        "dump_snapshots"  : str(n_dump),
        "total_trades"    : str(len(df)),
    }

    env["runtime_seconds"] = time.time() - start

    print("Step 5 -- Writing artifacts...")
    results_df = pd.DataFrame([
        {"check": k, "passed": v["passed"], "detail": v["detail"]}
        for k, v in checks.items()
    ])
    results_df.to_csv(str(OUTPUT_CSV), index=False)
    print("  [OK] CSV: " + str(OUTPUT_CSV))

    write_report(checks, summary, verdict, env)
    ru.write_metadata(
        STUDY_ID, STUDY_NAME, STUDY_VERSION,
        summary, verdict, env, acceptance,
        [str(OUTPUT_CSV), str(OUTPUT_REPORT), str(OUTPUT_META)]
    )

    # Console summary
    print("")
    print("=" * 62)
    print("INVEST OS -- STUDY 00 ENGINE VALIDATION")
    print("=" * 62)
    ru.print_env_block(env)
    print("")
    print("-" * 62)
    print("CHECKS")
    for name, v in checks.items():
        mark = "PASS" if v["passed"] else "FAIL"
        print("  [" + mark + "]  " + name)
        print("         " + str(v["detail"]))
    print("")
    print("  Passed: " + str(n_passed) + " / " + str(len(checks)))
    ru.print_verdict_block(verdict)

    print("Study 00 complete. Runtime: " + str(round(env["runtime_seconds"], 1)) + "s")
    print("Artifacts:")
    print("  " + str(OUTPUT_CSV))
    print("  " + str(OUTPUT_REPORT))
    print("  " + str(OUTPUT_META))
    print("")


if __name__ == "__main__":
    main()
