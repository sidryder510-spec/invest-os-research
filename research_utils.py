# -*- coding: utf-8 -*-
# =============================================================================
# INVEST OS -- RESEARCH UTILITIES
# =============================================================================
# Shared helpers used by every study. Import constants from research_config.py.
# Studies import from this module but never modify it.
#
# Protocol Version : Invest OS Research Protocol v1.1
# Module Version   : 1.0.0
# =============================================================================

import hashlib
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from research_config import (
    ENGINE_FILE, EXPECTED_ENGINE_SHA256, ENGINE_VERSION,
    PROTOCOL_VERSION, CONFIG_VERSION,
    OUTPUTS_DIR, REPORTS_DIR, METADATA_DIR, LOGS_DIR, ALL_DIRS,
)


# ---------------------------------------------------------------------------
# Directory setup
# ---------------------------------------------------------------------------

def ensure_dirs():
    for d in ALL_DIRS:
        d.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Engine verification
# ---------------------------------------------------------------------------

def verify_engine_hash(engine_path=ENGINE_FILE):
    path = Path(engine_path)
    if not path.exists():
        print("[FATAL] Engine file not found: " + engine_path)
        print("        Run from C:\\invest_os\\")
        sys.exit(1)
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != EXPECTED_ENGINE_SHA256:
        print("=" * 62)
        print("ENGINE HASH MISMATCH -- STUDY ABORTED")
        print("=" * 62)
        print("Expected : " + EXPECTED_ENGINE_SHA256)
        print("Actual   : " + actual)
        print("Engine has changed since frozen at v" + ENGINE_VERSION + ".")
        print("Resolve engine version before running any study.")
        sys.exit(1)
    return actual


def load_engine(engine_path=ENGINE_FILE):
    spec = importlib.util.spec_from_file_location("engine", engine_path)
    engine = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(engine)
    except Exception as e:
        print("[FATAL] Could not load engine: " + str(e))
        sys.exit(1)
    return engine


def verify_engine_api(engine, required_functions):
    missing = [fn for fn in required_functions if not hasattr(engine, fn)]
    if missing:
        print("[FATAL] Engine missing required API functions:")
        for fn in missing:
            print("        - " + fn + "()")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Environment snapshot
# ---------------------------------------------------------------------------

def collect_env(actual_hash):
    try:
        import yfinance as yf
        yf_ver = yf.__version__
    except Exception:
        yf_ver = "unknown"
    return {
        "engine_sha256"    : actual_hash,
        "engine_version"   : ENGINE_VERSION,
        "protocol_version" : PROTOCOL_VERSION,
        "config_version"   : CONFIG_VERSION,
        "execution_date"   : datetime.now().strftime("%Y-%m-%d"),
        "execution_time"   : datetime.now().strftime("%H:%M:%S"),
        "runtime_seconds"  : 0.0,
        "python_version"   : sys.version.split()[0],
        "pandas_version"   : pd.__version__,
        "numpy_version"    : np.__version__,
        "yfinance_version" : yf_ver,
    }


# ---------------------------------------------------------------------------
# Acceptance test runner
# ---------------------------------------------------------------------------

def run_acceptance_tests(tests_dict):
    """
    tests_dict: {name: (passed: bool, detail: str)}
    Prints results. Exits on any failure. Returns dict unchanged.
    """
    print("")
    print("  ACCEPTANCE TESTS")
    all_passed = True
    for name, (passed, detail) in tests_dict.items():
        mark = "PASS" if passed else "FAIL"
        print("    [" + mark + "]  " + name + ": " + detail)
        if not passed:
            all_passed = False
    if not all_passed:
        print("")
        print("[FATAL] Acceptance test(s) failed. Halting before analysis.")
        sys.exit(1)
    return tests_dict


# ---------------------------------------------------------------------------
# Console printing
# ---------------------------------------------------------------------------

def print_study_header(study_id, study_name):
    print("")
    print("=" * 62)
    print("INVEST OS RESEARCH PROTOCOL v" + PROTOCOL_VERSION)
    print("Study " + study_id + ": " + study_name)
    print("=" * 62)
    print("")


def print_env_block(env):
    print("DEPENDENCIES")
    short = env["engine_sha256"][:16] + "..." + env["engine_sha256"][-8:]
    print("  Engine Version:  " + env["engine_version"])
    print("  Engine SHA256:   " + short)
    print("  Config Version:  " + env["config_version"])
    print("  Protocol:        v" + env["protocol_version"])
    print("  Python:          " + env["python_version"])
    print("  pandas:          " + env["pandas_version"])
    print("  numpy:           " + env["numpy_version"])
    print("  yfinance:        " + env["yfinance_version"])
    print("  Date:            " + env["execution_date"])
    print("  Time:            " + env["execution_time"])
    print("  Runtime:         " + str(round(env["runtime_seconds"], 1)) + "s")


def print_verdict_block(verdict):
    print("")
    print("-" * 62)
    print("VERDICT: " + verdict)
    print("=" * 62)
    print("")


# ---------------------------------------------------------------------------
# Metadata JSON writer
# ---------------------------------------------------------------------------

def write_metadata(study_id, study_name, study_version,
                   summary_dict, verdict, env, acceptance_tests, artifacts):
    ensure_dirs()
    metadata = {
        "study"            : study_id,
        "study_name"       : study_name,
        "study_version"    : study_version,
        "protocol_version" : PROTOCOL_VERSION,
        "config_version"   : CONFIG_VERSION,
        "engine_version"   : ENGINE_VERSION,
        "engine_sha256"    : env["engine_sha256"],
        "execution_date"   : env["execution_date"],
        "execution_time"   : env["execution_time"],
        "runtime_seconds"  : round(env["runtime_seconds"], 2),
        "python_version"   : env["python_version"],
        "pandas_version"   : env["pandas_version"],
        "numpy_version"    : env["numpy_version"],
        "yfinance_version" : env["yfinance_version"],
        "verdict"          : verdict,
        "acceptance_tests" : {n: p for n, (p, _) in acceptance_tests.items()},
        "artifacts"        : artifacts,
        "summary"          : summary_dict,
    }
    outpath = METADATA_DIR / ("study_" + study_id + "_metadata.json")
    outpath.write_text(json.dumps(metadata, indent=2, ensure_ascii=False),
                       encoding="utf-8")
    print("  [OK] Metadata: " + str(outpath))
    return outpath


# ---------------------------------------------------------------------------
# Markdown table helpers
# ---------------------------------------------------------------------------

def md_table(headers, rows):
    sep    = "| " + " | ".join("---" for _ in headers) + " |"
    hrow   = "| " + " | ".join(str(h) for h in headers) + " |"
    drows  = ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join([hrow, sep] + drows)


def md_kv_table(pairs):
    return md_table(["Metric", "Value"], [[k, v] for k, v in pairs])


def md_test_table(acceptance_tests):
    rows = [[name, "PASS" if passed else "FAIL"]
            for name, (passed, _) in acceptance_tests.items()]
    return md_table(["Test", "Result"], rows)


# ---------------------------------------------------------------------------
# Standard report header block (used by every study)
# ---------------------------------------------------------------------------

def report_header(study_id, study_name, study_version, env):
    short = env["engine_sha256"][:16] + "..." + env["engine_sha256"][-8:]
    return "\n".join([
        "# Study " + study_id + " -- " + study_name,
        "**Protocol Version:** " + PROTOCOL_VERSION,
        "**Config Version:** " + CONFIG_VERSION,
        "**Research Engine Version:** " + ENGINE_VERSION,
        "**Engine SHA256:** `" + short + "`",
        "**Study Version:** " + study_version,
        "**Execution Date:** " + env["execution_date"],
        "",
        "---",
    ])


def report_env_table(env):
    short = env["engine_sha256"][:16] + "..." + env["engine_sha256"][-8:]
    return "## Dependencies\n" + md_kv_table([
        ("Research Engine Version", ENGINE_VERSION),
        ("Engine SHA256", "`" + short + "`"),
        ("Config Version", CONFIG_VERSION),
        ("Protocol Version", PROTOCOL_VERSION),
        ("Python Version", env["python_version"]),
        ("pandas Version", env["pandas_version"]),
        ("numpy Version", env["numpy_version"]),
        ("yfinance Version", env["yfinance_version"]),
        ("Execution Date", env["execution_date"]),
        ("Execution Time", env["execution_time"]),
        ("Runtime", str(round(env["runtime_seconds"], 1)) + " seconds"),
    ])
