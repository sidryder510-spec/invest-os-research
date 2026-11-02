# PM run log (newest first)

## 2026-10-31 to 11-02: cycle 2
- Paused on 2026-10-31 by the account's weekly usage limit (reset 2026-11-01 20:00 UTC) and resumed on 2026-11-02; nothing was lost.
- Health: the paper workflow ran every weekday; data as of 2026-10-30; in cash (breadth 32.4%).
- **T1b (Trading #16): merged.** Check 1 PASS first round. Check 2: 78 tests, void check then live guards, rules.py untouched.
- **T8 (Trading #17): merged.**
  - Check 1: FAIL (an expectedFailure test that could never succeed) → PASS.
  - Check 2: merged main, resolved the README conflict, all tests pass.
  - Found: heat counts open profit (fix in T9); shares above Rs 4,800 can't be bought; sector cap 40.
- **T3 (invest-os-research #4): merged, then run (extended run 41373813677).**
  - This is **October 2026's** research idea; T7 is November's.
  - The rule was locked in a0a4f83 and unchanged since.
  - Check 1: PASS with caveats R1-R6. Check 2: 47 tests.
  - **Result: ADOPT -30% stop.** Mean net alpha 5.37 vs 5.71 (cost 0.34 < 0.5); worst trade -42.5% vs -73.6%; 8.5% of trades stopped. The baseline reproduced pit_backtest exactly.
  - The 18 picks with zeroed moves are mostly splits and bonuses.
- New backlog: T9 (fidelity + heat-from-cost), T1c (small nse_exec follow-ups). T2 now uses -30% stops.

## 2026-10-30: cycle 1
- Health: the paper workflow ran every weekday; data as of 2026-10-29; in cash (breadth 35.5%).
- **T1 SELL tickets (Trading #12): merged.**
  - Check 1 (independent reviewer): FAIL → FAIL → PASS. Fixed an "Infinity" limit that could leave a position without a stop, partial exits cancelling the whole stop, retry traps, network-unknown outcomes, ASCII checks, and a message hiding a missing stop.
  - Check 2 (PM): 69 tests pass, guard order confirmed in code, no network in tests, rules.py untouched.
  - Remaining fail-safe items moved to T1b.
- **T5 GO_LIVE.md (Trading #13): merged.**
  - Check 1: FAIL → PASS. Fixed limits that would cap the book at ~48 positions instead of 60, and manual sells leaving a live stop GTT.
  - Check 2: sources, UNVERIFIED labels, no secrets, proposals labelled.
- New backlog: T1b (bookkeeping follow-ups), T8 (config for ~60 positions).
- Next cycle: T2 bridge plus token helper, T3 stop-loss research (November's idea), T8.

## 2026-10-30: PM set up
- Owner granted standing approval up to the finish line (`pm/CHARTER.md`): finish line = paper PASS + live setup dry-run tested; at most 1 new research idea a month; weekly runs; weekly digest plus `[ACTION]` alerts.
- Backlog T1-T7 created. Paper scorecard: TOO EARLY, in cash, breadth 35.5% on 2026-10-29.
