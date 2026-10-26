# -*- coding: utf-8 -*-
# =============================================================================
# INVEST OS -- RESEARCH CONFIG (research_config.py; the live app owns config.py)
# =============================================================================
# Single source of truth for all immutable research constants.
# Every study imports from here. Nothing is hardcoded in study files.
#
# Protocol Version : Invest OS Research Protocol v1.1
# Config Version   : 1.2.0
#
# HOW TO UPDATE:
#   If the engine changes (bug fix), update ENGINE_SHA256 and ENGINE_VERSION.
#   Increment CONFIG_VERSION when any constant changes.
#   All affected studies must be rerun after any change here.
# =============================================================================

from pathlib import Path

# ---------------------------------------------------------------------------
# Version identifiers
# ---------------------------------------------------------------------------

CONFIG_VERSION   = "1.2.0"   # 1.2.0: engine v3; 1.1.0: Study 05 cost model corrected (thresholds unchanged)
PROTOCOL_VERSION = "1.1"
ENGINE_VERSION   = "3.0.0"   # v2 engine lost; v3 rebuilt with a pre-locked 12-1 momentum score

# ---------------------------------------------------------------------------
# Engine file and locked hash
# ---------------------------------------------------------------------------

ENGINE_FILE            = "historical_backtest_v3.py"
EXPECTED_ENGINE_SHA256 = "032aa2c0bd77bac17b1e98437ee8e11c0b3b155278f0e2f024f09466fc87f27b"

# ---------------------------------------------------------------------------
# Strategy parameters (must match the frozen engine exactly)
# ---------------------------------------------------------------------------

TOP_N              = 5     # number of stocks selected per snapshot
HOLDING_DAYS       = 60    # trading days each position is held
MIN_HISTORY        = 252   # minimum trading days before a stock is eligible
BREADTH_THRESHOLD  = 80.0  # % of universe above 200-day SMA required to trade
SNAPSHOT_INTERVAL  = 5     # trading days between snapshots (weekly)

# ---------------------------------------------------------------------------
# Output directories
# ---------------------------------------------------------------------------

OUTPUTS_DIR  = Path("research/outputs")
REPORTS_DIR  = Path("research/reports")
METADATA_DIR = Path("research/metadata")
LOGS_DIR     = Path("research/logs")

ALL_DIRS = [OUTPUTS_DIR, REPORTS_DIR, METADATA_DIR, LOGS_DIR]

# ---------------------------------------------------------------------------
# Verdict thresholds (locked before any study is run)
# Study 00 -- Engine Validation
# ---------------------------------------------------------------------------

S00_MAX_CONDITIONAL_FAILURES = 2   # CONDITIONAL if <= this many non-critical failures
# FAIL if any critical check fails (duplicates, bad alpha, missing cols)

# ---------------------------------------------------------------------------
# Verdict thresholds
# Study 01 -- Eligibility Audit
# ---------------------------------------------------------------------------

S01_MAX_VIOLATIONS_CONDITIONAL = 5     # CONDITIONAL if fewer than this many violations
S01_CUTOFF_YEAR                = 2010  # violations must be before this year to be CONDITIONAL
# FAIL if: any violation after cutoff year, any at Rank 1, or >= max violations

# ---------------------------------------------------------------------------
# Verdict thresholds
# Study 02 -- Selection Concentration
# ---------------------------------------------------------------------------

S02_HHI_PASS        = 2000   # HHI below this = PASS
S02_HHI_CONDITIONAL = 3000   # HHI above this = FAIL, between = CONDITIONAL
S02_TOP1_PASS_PCT   = 25.0   # top symbol < this % of selections = PASS
S02_TOP1_FAIL_PCT   = 40.0   # top symbol > this % of selections = FAIL

# ---------------------------------------------------------------------------
# Verdict thresholds
# Study 03 -- Rank Persistence
# ---------------------------------------------------------------------------

S03_JACCARD_PASS        = 0.70   # avg Jaccard below this = PASS
S03_JACCARD_CONDITIONAL = 0.85   # above this = FAIL
S03_ZERO_TURNOVER_PASS  = 30.0   # % zero-turnover weeks below this = PASS
S03_ZERO_TURNOVER_FAIL  = 50.0   # above this = FAIL

# ---------------------------------------------------------------------------
# Verdict thresholds
# Study 04 -- Sector Concentration
# ---------------------------------------------------------------------------

S04_SECTOR_AVG_PASS = 60.0   # no single sector > this avg weight = PASS

# ---------------------------------------------------------------------------
# Verdict thresholds
# Study 05 -- Transaction Costs
# ---------------------------------------------------------------------------

S05_NET_ALPHA_PASS        = 2.0   # mean net alpha/60d above this = PASS
S05_NET_ALPHA_CONDITIONAL = 0.5   # below conditional = FAIL
S05_WIN_RATE_PASS         = 55.0  # net win rate above this = PASS
S05_WIN_RATE_FAIL         = 50.0  # below this = FAIL

# Zerodha equity-delivery (CNC) charges, applied through nse_exec.rules.charges.
# Config 1.1.0 corrected 1.0.0, which charged 0.03% brokerage (delivery is Rs 0),
# STT on the sell side only (delivery STT is 0.1% on both sides), an old exchange
# rate, and left out stamp duty and the DP charge. Verified 2026-10-26; see
# nse_exec_config.example.json "_verified" for sources.
S05_CHARGES = {
    "brokerage_per_order": 0,
    "stt_pct": 0.1,
    "exchange_txn_pct": 0.00307,
    "sebi_per_crore": 10,
    "gst_pct": 18,
    "stamp_buy_pct": 0.015,
    "dp_per_sell": 15.34,
}
S05_NOTIONAL_PER_POSITION = 100000   # Rs per position; sets the weight of the fixed DP charge
S05_SLIPPAGE_LARGECAP      = 0.001    # 0.10% each way
S05_SLIPPAGE_MIDCAP        = 0.0025   # 0.25% each way

# Symbols classified as mid-cap for slippage purposes
S05_MIDCAP_SYMBOLS = {
    "EICHERMOT", "CGPOWER", "MAZDOCK", "COCHINSHIP",
    "LODHA", "DMART", "AARTIIND", "SRF", "SHRIRAMFIN",
}

# ---------------------------------------------------------------------------
# Verdict thresholds
# Study 06 -- Walk-Forward Validation
# ---------------------------------------------------------------------------

S06_POSITIVE_WINDOWS_PASS   = 7    # out of 10 test windows
S06_OOS_ALPHA_PASS          = 1.5  # % per 60-day period
S06_OOS_ALPHA_CONDITIONAL   = 0.5  # below this = FAIL
S06_TEST_YEARS              = list(range(2015, 2025))  # 10 test years

# ---------------------------------------------------------------------------
# Required engine API (functions that must exist in the frozen engine)
# ---------------------------------------------------------------------------

REQUIRED_ENGINE_API = [
    "load_market_data",
    "get_snapshot_dates",
    "generate_historical_candidates",
]
