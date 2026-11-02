# -*- coding: utf-8 -*-
# =============================================================================
# INVEST OS -- RESEARCH CONFIG (research_config.py; the live app owns config.py)
# =============================================================================
# Single source of truth for all immutable research constants.
# Every study imports from here. Nothing is hardcoded in study files.
#
# Protocol Version : Invest OS Research Protocol v1.1
# Config Version   : 1.5.0
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

CONFIG_VERSION   = "1.5.0"   # 1.5.0: stop-loss test pre-registered; 1.4.2: any >35% day neutralised; 1.4.1: PIT corporate-action fix (after first run); 1.4.0: extended tests pre-registered; 1.3.0: paper-trading rule; 1.2.0: engine v3; 1.1.0: Study 05 cost model corrected (thresholds unchanged)
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

# ---------------------------------------------------------------------------
# Forward paper trading (locked 2026-10-26, before the first live signal)
# Verdict: PASS if mean net alpha > S05_NET_ALPHA_PASS and net win rate >
# S05_WIN_RATE_PASS over at least PAPER_MIN_CLOSED_WEEKS closed weekly picks.
# Until then the verdict is "TOO EARLY". Nothing here places a real order.
# ---------------------------------------------------------------------------

PAPER_MIN_CLOSED_WEEKS = 26
PAPER_DIR              = Path("paper")

# ---------------------------------------------------------------------------
# Extended tests (pre-registered 2026-10-26, before any of them was run)
#
# 1. Random-monkey test: on the same snapshots, MONKEY_RUNS portfolios of
#    TOP_N random eligible stocks (seed MONKEY_SEED). PASS if momentum's mean
#    gross alpha beats at least (1 - MONKEY_P_PASS) of them.
# 2. Robustness: lookbacks 6-1, 9-1, 12-1 months, each with and without the
#    breadth filter (6 variants). Measure: selection edge = picks minus the
#    equal-weight average of eligible stocks. PASS if >= ROBUST_PASS_COUNT
#    variants are positive, FAIL if <= ROBUST_FAIL_COUNT, else CONDITIONAL.
#    12-1 stays the strategy whatever this shows; nothing is re-chosen.
# 3. Point-in-time backtest: NSE bhavcopy (every listed stock, delisted ones
#    included; EQ/BE/BZ series). Universe on each date = PIT_UNIVERSE_SIZE
#    stocks with the highest average daily traded value over the previous
#    PIT_VALUE_DAYS trading days. Prices chained from CLOSE / PREVCLOSE (NSE
#    adjusts PREVCLOSE for corporate actions). Same engine rules otherwise.
#    PASS if mean net alpha > S05_NET_ALPHA_PASS, net win rate >
#    S05_WIN_RATE_PASS, non-overlapping t-stat >= PIT_T_PASS and the monkey
#    test on this data passes. Otherwise FAIL.
# ---------------------------------------------------------------------------

MONKEY_RUNS        = 1000
MONKEY_SEED        = 2026
MONKEY_P_PASS      = 0.05
ROBUST_LOOKBACKS   = {"6-1": 126, "9-1": 189, "12-1": 252}
ROBUST_PASS_COUNT  = 5
ROBUST_FAIL_COUNT  = 3
PIT_UNIVERSE_SIZE  = 500
PIT_VALUE_DAYS     = 126
PIT_START          = "2010-01-01"
PIT_T_PASS         = 2.0

# Amendment 1.4.1 (2026-10-26, AFTER the first point-in-time run; pass rules unchanged):
# NSE's PREVCLOSE is NOT always adjusted for splits/bonuses (INOXWIND 3:1 bonus
# showed as -77%; 2,463 daily moves beyond 40%). A daily move beyond
# PIT_CA_MIN_MOVE whose price ratio is within PIT_CA_TOL of a standard
# split/bonus ratio is treated as a corporate action (0% that day).
#
# Amendment 1.4.2 (after the second run; pass rules unchanged): the ratio match
# missed bonuses/splits on days the stock also moved (INOXWIND -77%, PCJEWELLER
# -90%, GPIL -80% remained; 1,511 moves beyond 40% left). EQ-series stocks are
# capped at 20% a day and F&O stocks almost never move 35%, so ANY daily move
# beyond PIT_MAX_DAILY_MOVE is treated as a corporate action or data error (0%
# that day). Cost: a rare real crash beyond 35% (e.g. Yes Bank, Mar 2020) is
# erased too. Owner-facing commitment: the next run's result is the verdict; no
# further data amendments without a specific, evidenced error.
PIT_MAX_DAILY_MOVE = 0.35

# ---------------------------------------------------------------------------
# Stop-loss test (pre-registered 2026-10-31, written BEFORE any stop result was
# computed; backlog T3; this month's one new research idea). Adds rules only:
# no existing pass/fail rule changes, and the 12-1 strategy's point-in-time
# FAIL stands whatever this test shows. A stop that improves the numbers does
# not make the strategy pass; that would need its own locked test.
#
# Why: the live order gate (nse_exec) puts a stop-loss GTT on every buy, but
# the tested strategy has no stop. This test says which stop the live plan uses.
#
# Data and picks: exactly the point-in-time backtest of 1.4.0-1.4.2 (pit_backtest
# panels, 12-1 + breadth, Top 5, weekly, entry at the next day's close, 60-day
# hold). Variants: no stop (baseline) and stops at STOP_LEVELS below entry.
#
# Mechanics (daily closes): entry E = close on the entry day. On each later day
# t of the hold, if close_t <= E * (1 - s), sell at the close of day t + 1; the
# decision on day t uses only closes up to t. A trigger on the last day of the
# hold changes nothing (that close is the scheduled exit). The money then sits
# in cash at 0% until the 60 days end; the benchmark stays NIFTY over the full
# 60 days, so a stopped trade's alpha = its stopped return - NIFTY's 60-day return.
#
# Bias of using closes: a real GTT triggers intraday on the last traded price
# (bhavcopy has no reliable intraday path for this). (1) It fires more often:
# intraday dips that recover by the close trigger a GTT but not this test, so
# the test UNDERSTATES whipsaw stop-outs and its mean net alpha is biased IN
# FAVOUR of the stop. (2) On a steady slide a GTT sells near the trigger, while
# the test sells at the next day's close, usually lower, so the test's worst
# losses are biased AGAINST the stop. Gaps through the trigger hurt both alike.
# Also, amendment 1.4.2 zeroes any daily move beyond 35%, so a real one-day
# crash of that size is invisible to the baseline and to every stop.
#
# Costs: Zerodha CNC charges via nse_exec.rules.charges plus slippage, exactly as
# Study 05 (study_05_transaction_costs.add_net), charged on the actual exit value.
#
# Primary metric: mean net alpha per trade per 60 days (the S05/PIT metric).
# Reported too: trades, median net alpha, net win rate, worst trade (lowest net
# return), share of trades stopped out, non-overlapping t-stat of gross alpha
# (as in pit_backtest).
#
# DECISION RULE: adopt the widest stop in STOP_LEVELS whose mean net alpha is
# not below the baseline's by more than STOP_MAX_ALPHA_COST percentage points
# per 60 days AND whose worst trade (lowest net return) is strictly better than
# the baseline's. If none qualifies, the live plan uses STOP_INSURANCE_LEVEL
# purely as disaster insurance, recorded as such (not as an edge).
#
# Why X = 0.5 points: it is the insurance premium we accept, about 9% of the
# failed baseline's +5.7 points per 60 days (about 2 points a year at ~4 holding
# periods), and the same size as Study 05's CONDITIONAL floor. The stop is there
# to cap a disaster, so paying a little mean is acceptable; paying more would eat
# a large part of an edge that already failed to clear 2 points net.
# Why "widest": it stops out least, stays closest to the tested strategy, and
# choosing the best-scoring of three stops would be picking on noise.
# ---------------------------------------------------------------------------

STOP_LEVELS          = (0.20, 0.25, 0.30)   # fraction below entry
STOP_MAX_ALPHA_COST  = 0.5                  # X: max mean net alpha given up, points per 60 days
STOP_INSURANCE_LEVEL = 0.30                 # fallback when no stop qualifies: the widest tested
