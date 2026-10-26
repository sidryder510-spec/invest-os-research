# -*- coding: utf-8 -*-
# =============================================================================
# INVEST OS -- STUDY 01: ELIGIBILITY AUDIT
# =============================================================================
# Protocol Version : Invest OS Research Protocol v1.1
# Study Version    : 1.0.0
#
# Research Question:
#   Was every stock only selected into the Top 5 portfolio after accumulating
#   at least 252 trading days of price history at the snapshot date?
#
# Method:
#   Uses engine load_market_data(), get_snapshot_dates(), and
#   generate_historical_candidates() directly.
#   Does NOT use trade_dump.csv (audit is independent of the export).
# =============================================================================

import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import research_utils as ru
from research_config import (
    TOP_N, MIN_HISTORY, REQUIRED_ENGINE_API,
    OUTPUTS_DIR, REPORTS_DIR, METADATA_DIR,
    S01_MAX_VIOLATIONS_CONDITIONAL, S01_CUTOFF_YEAR,
)

# =============================================================================
# Constants
# =============================================================================

STUDY_ID      = "01"
STUDY_NAME    = "Eligibility Audit"
STUDY_VERSION = "1.0.0"

OUTPUT_CSV    = OUTPUTS_DIR  / "study_01_output.csv"
OUTPUT_REPORT = REPORTS_DIR  / "study_01_report.md"
OUTPUT_META   = METADATA_DIR / "study_01_metadata.json"


# =============================================================================
# Core audit logic
# =============================================================================

def rows_at_snapshot(stock_df, snapshot_date):
    if stock_df is None or stock_df.empty:
        return 0
    try:
        return int((stock_df.index <= pd.Timestamp(snapshot_date)).sum())
    except Exception:
        return 0


def run_audit(engine):
    print("  Loading market data...")
    stock_data, nifty_data, _ = engine.load_market_data()
    all_symbols = sorted(stock_data.keys())
    print("  Universe: " + str(len(all_symbols)) + " symbols")

    print("  Generating snapshots...")
    snapshots = engine.get_snapshot_dates(nifty_data)
    total = len(snapshots)
    print("  Snapshots: " + str(total))

    records = []
    for i, snap in enumerate(snapshots, 1):
        if i == 1 or i % 100 == 0 or i == total:
            print("  Snapshot " + str(i) + "/" + str(total) + " (" + str(snap.date()) + ")")

        try:
            candidates = engine.generate_historical_candidates(
                snap, stock_data, nifty_data, TOP_N
            )
        except Exception as e:
            print("  [WARN] " + str(snap.date()) + " failed: " + str(e))
            candidates = []

        selected = {c["symbol"]: idx + 1 for idx, c in enumerate(candidates)}

        for sym in all_symbols:
            rows = rows_at_snapshot(stock_data.get(sym), snap)
            records.append({
                "snapshot_date" : snap.date(),
                "symbol"        : sym,
                "rows_available": rows,
                "eligible"      : rows >= MIN_HISTORY,
                "was_selected"  : sym in selected,
                "selected_rank" : selected.get(sym, pd.NA),
            })

    df = pd.DataFrame(records)
    df["snapshot_date"]  = pd.to_datetime(df["snapshot_date"])
    df["rows_available"] = df["rows_available"].astype(int)
    df["eligible"]       = df["eligible"].astype(bool)
    df["was_selected"]   = df["was_selected"].astype(bool)
    return df


# =============================================================================
# Acceptance tests
# =============================================================================

def build_tests(df, csv_path):
    tests = {}

    tests["CSV exported"] = (
        Path(csv_path).exists(),
        str(csv_path) + " found" if Path(csv_path).exists() else "File missing"
    )

    tests["Row count > 0"] = (
        len(df) > 0, str(len(df)) + " rows"
    )

    dupes = int(df.duplicated(subset=["snapshot_date", "symbol"]).sum())
    tests["No duplicate snapshot/symbol rows"] = (
        dupes == 0, "0 duplicates" if dupes == 0 else str(dupes) + " found"
    )

    counts = df.groupby("snapshot_date")["symbol"].count()
    uniform = counts.nunique() == 1
    tests["Consistent symbol count per snapshot"] = (
        uniform,
        str(counts.iloc[0]) + " symbols/snapshot" if uniform
        else "min=" + str(counts.min()) + " max=" + str(counts.max())
    )

    sel_ranks = df.loc[df["was_selected"], "selected_rank"].dropna().astype(int)
    valid = bool(sel_ranks.between(1, TOP_N).all()) if len(sel_ranks) > 0 else True
    tests["selected_rank in [1," + str(TOP_N) + "] or NA"] = (
        valid, "All valid" if valid else "Invalid values found"
    )

    r1 = int(df.loc[df["was_selected"], "selected_rank"].isna().sum())
    r2 = int(df.loc[~df["was_selected"], "selected_rank"].notna().sum())
    ok = (r1 == 0) and (r2 == 0)
    tests["was_selected and selected_rank consistent"] = (
        ok, "Consistent" if ok
        else str(r1) + " selected/no-rank; " + str(r2) + " not-selected/has-rank"
    )

    required = {"snapshot_date", "symbol", "rows_available",
                "eligible", "was_selected", "selected_rank"}
    missing  = required - set(df.columns)
    tests["Required columns present"] = (
        len(missing) == 0,
        "All present" if not missing else "Missing: " + str(missing)
    )

    return tests


# =============================================================================
# Summary and verdict
# =============================================================================

def compute_summary(df):
    viols = df[df["was_selected"] & ~df["eligible"]].copy()
    syms  = sorted(df.loc[df["was_selected"], "symbol"].unique())

    first_elig    = {}
    viol_per_sym  = {}
    for sym in syms:
        elig = df[(df["symbol"] == sym) & df["eligible"]]
        first_elig[sym]   = str(elig["snapshot_date"].min().date()) if len(elig) else "Never"
        viol_per_sym[sym] = int((viols["symbol"] == sym).sum())

    return {
        "total_snapshots"         : int(df["snapshot_date"].nunique()),
        "total_observations"      : int(len(df)),
        "eligible_observations"   : int(df["eligible"].sum()),
        "ineligible_observations" : int((~df["eligible"]).sum()),
        "total_selections"        : int(df["was_selected"].sum()),
        "violations"              : int(len(viols)),
        "violation_rows"          : viols,
        "first_eligible"          : first_elig,
        "viol_per_sym"            : viol_per_sym,
        "selected_symbols"        : syms,
    }


def determine_verdict(summary):
    n = summary["violations"]
    if n == 0:
        return "PASS"
    vdf      = summary["violation_rows"]
    pre_cut  = (vdf["snapshot_date"].dt.year < S01_CUTOFF_YEAR).all()
    no_rank1 = (vdf["selected_rank"].astype(str) != "1").all()
    if n < S01_MAX_VIOLATIONS_CONDITIONAL and pre_cut and no_rank1:
        return "CONDITIONAL"
    return "FAIL"


# =============================================================================
# Report
# =============================================================================

def write_report(summary, verdict, env, tests):
    ru.ensure_dirs()
    n = summary["violations"]

    if verdict == "PASS":
        conclusion   = ("Zero violations across " + str(summary["total_snapshots"]) +
                        " snapshots and " + str(summary["total_observations"]) +
                        " observations. Every Top-" + str(TOP_N) + " selection had >= " +
                        str(MIN_HISTORY) + " days of history. Engine eligibility is correct.")
        vtext        = "**PASS** -- Zero selection violations."
        model_impact = "NO -- Engine behaviour confirmed correct."
        rec          = "Proceed to Study 02 -- Selection Concentration."
    elif verdict == "CONDITIONAL":
        conclusion   = (str(n) + " violation(s) found, all before " + str(S01_CUTOFF_YEAR) +
                        " and none at Rank 1. Post-" + str(S01_CUTOFF_YEAR) + " results are unlikely affected.")
        vtext        = "**CONDITIONAL** -- " + str(n) + " pre-" + str(S01_CUTOFF_YEAR) + " violation(s), none at Rank 1."
        model_impact = "CONDITIONAL -- Pre-" + str(S01_CUTOFF_YEAR) + " violations require impact assessment."
        rec          = ("Confirm pre-" + str(S01_CUTOFF_YEAR) +
                        " violations do not affect alpha, then proceed to Study 02.")
    else:
        conclusion   = (str(n) + " violation(s) breach FAIL criteria. "
                        "Engine requires correction before research can continue.")
        vtext        = "**FAIL** -- " + str(n) + " critical violation(s)."
        model_impact = "YES -- Engine correction required."
        rec          = ("Fix eligibility guard in " + ru.ENGINE_FILE +
                        ", increment version, recompute SHA256, rerun Study 01.")

    # First eligibility table
    elig_rows = [
        [sym, summary["first_eligible"][sym], str(summary["viol_per_sym"].get(sym, 0))]
        for sym in summary["selected_symbols"]
    ]
    elig_table = ru.md_table(
        ["Symbol", "First Eligible Date", "Selections Before Eligible"], elig_rows
    )

    # Violation table
    if summary["violations"] > 0:
        vrows = [[str(r["snapshot_date"].date()), str(r["symbol"]),
                  str(r["selected_rank"]), str(r["rows_available"])]
                 for _, r in summary["violation_rows"].iterrows()]
        viol_section = ("### Violation Detail\n" +
                        ru.md_table(["Snapshot Date", "Symbol", "Rank", "Rows"], vrows))
    else:
        viol_section = "### Violation Detail\nNo violations found."

    kv = [
        ("Total snapshots audited",          str(summary["total_snapshots"])),
        ("Total stock-snapshot combinations", str(summary["total_observations"])),
        ("Eligible combinations",             str(summary["eligible_observations"])),
        ("Ineligible combinations",           str(summary["ineligible_observations"])),
        ("Total selections audited",          str(summary["total_selections"])),
        ("Selection violations",              str(summary["violations"])),
    ]

    lines = [
        ru.report_header(STUDY_ID, STUDY_NAME, STUDY_VERSION, env),
        "",
        "## Objective",
        ("Verify that no stock was selected into the Top " + str(TOP_N) +
         " portfolio before accumulating " + str(MIN_HISTORY) +
         " trading days of price history at the snapshot date."),
        "",
        ru.report_env_table(env),
        "",
        "## Method",
        ("Market data loaded via engine `load_market_data()`. "
         "Snapshots via `get_snapshot_dates()`. "
         "Top-" + str(TOP_N) + " selections reconstructed via `generate_historical_candidates()`. "
         "Independent of `trade_dump.csv`. "
         "Eligibility: rows_available >= " + str(MIN_HISTORY) + ". "
         "Violation: was_selected AND NOT eligible."),
        "",
        "## Acceptance Tests",
        ru.md_test_table(tests),
        "",
        "## Results",
        ru.md_kv_table(kv),
        "",
        "### First Eligibility Dates",
        elig_table,
        "",
        viol_section,
        "",
        "## Conclusion",
        conclusion,
        "",
        "## Verdict Criteria (defined before results were examined)",
        ru.md_table(
            ["Verdict", "Criteria"],
            [
                ["PASS",        "Zero violations across full history"],
                ["CONDITIONAL", ("< " + str(S01_MAX_VIOLATIONS_CONDITIONAL) +
                                 " violations, all before " + str(S01_CUTOFF_YEAR) +
                                 ", none at Rank 1")],
                ["FAIL",        ("Any violation after " + str(S01_CUTOFF_YEAR) +
                                 ", any at Rank 1, or >= " +
                                 str(S01_MAX_VIOLATIONS_CONDITIONAL) + " total")],
            ]
        ),
        "",
        "## Verdict",
        vtext,
        "",
        "## Research Impact",
        ru.md_table(
            ["Question", "Answer"],
            [
                ["Does this change the model?", model_impact],
                ["Does this change production?", "NO -- Production system is separate."],
                ["Does this require rerunning previous studies?", "NO -- This is Study 01."],
            ]
        ),
        "",
        "## Recommendation",
        rec,
        "",
        "## Next Study",
        "**Study 02 -- Selection Concentration:** Uses `trade_dump.csv` directly.",
        "Quantifies concentration (HHI, Gini) and computes alpha with/without EICHERMOT.",
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

    print("Step 2 -- Loading engine...")
    engine = ru.load_engine()
    ru.verify_engine_api(engine, REQUIRED_ENGINE_API)
    print("  [OK] Engine loaded and API verified")

    env = ru.collect_env(actual_hash)

    print("Step 3 -- Running eligibility audit (takes several minutes)...")
    df = run_audit(engine)
    print("  [OK] " + str(len(df)) + " observations")

    print("Step 4 -- Exporting CSV...")
    df.to_csv(str(OUTPUT_CSV), index=False)
    print("  [OK] CSV: " + str(OUTPUT_CSV))

    print("Step 5 -- Running acceptance tests...")
    tests = build_tests(df, OUTPUT_CSV)
    ru.run_acceptance_tests(tests)
    print("  [OK] All tests passed")

    print("Step 6 -- Computing summary and verdict...")
    summary = compute_summary(df)
    verdict = determine_verdict(summary)
    print("  [OK] Verdict: " + verdict)

    env["runtime_seconds"] = time.time() - start

    print("Step 7 -- Writing reports...")
    write_report(summary, verdict, env, tests)

    meta_summary = {k: str(v) for k, v in summary.items() if k not in ("violation_rows",)}
    ru.write_metadata(
        STUDY_ID, STUDY_NAME, STUDY_VERSION,
        meta_summary, verdict, env, tests,
        [str(OUTPUT_CSV), str(OUTPUT_REPORT), str(OUTPUT_META)]
    )

    # Console summary
    print("")
    print("=" * 62)
    print("INVEST OS -- STUDY 01 ELIGIBILITY AUDIT")
    print("=" * 62)
    ru.print_env_block(env)
    print("")
    print("-" * 62)
    print("RESULTS")
    print("  Total snapshots:    " + str(summary["total_snapshots"]))
    print("  Total observations: " + str(summary["total_observations"]))
    print("  Eligible combos:    " + str(summary["eligible_observations"]))
    print("  Ineligible combos:  " + str(summary["ineligible_observations"]))
    print("  Total selections:   " + str(summary["total_selections"]))
    print("  Violations:         " + str(summary["violations"]))
    print("")
    print("FIRST ELIGIBILITY DATES")
    for sym in summary["selected_symbols"]:
        print("  " + sym.ljust(20) + " " + summary["first_eligible"][sym])
    if summary["violations"] > 0:
        print("")
        print("VIOLATIONS")
        print("  " + "Snapshot".ljust(14) + "Symbol".ljust(18) + "Rank".ljust(6) + "Rows")
        for _, row in summary["violation_rows"].iterrows():
            print("  " + str(row["snapshot_date"].date()).ljust(14) +
                  str(row["symbol"]).ljust(18) +
                  str(row["selected_rank"]).ljust(6) +
                  str(row["rows_available"]))
    ru.print_verdict_block(verdict)

    print("Study 01 complete. Runtime: " + str(round(env["runtime_seconds"], 1)) + "s")
    print("Artifacts:")
    print("  " + str(OUTPUT_CSV))
    print("  " + str(OUTPUT_REPORT))
    print("  " + str(OUTPUT_META))
    print("")


if __name__ == "__main__":
    main()
