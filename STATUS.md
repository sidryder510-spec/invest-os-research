# Invest OS: current status (read this first)

This is the shared record between Claude Code and the owner's Claude chat. If anything here disagrees with older chat summaries, this file wins. Last updated 2026-10-28 (WhatsApp alerts added).

## Verdict
**No real money.** The 12-1 momentum strategy **failed** its pre-registered point-in-time test. Forward paper trading is running to collect honest evidence.

## What exists
| Piece | Where | Status |
|---|---|---|
| Research engine v3 (12-1 momentum, Top 5, weekly, 60-day hold, 80% breadth filter) | `historical_backtest_v3.py`, hash-locked in `research_config.py` | Frozen. v2 was lost; v2 numbers (4,345 trades, 14 symbols, 7.63% alpha) no longer apply. |
| Studies 00, 01, 02, 05, 06 | `study_*.py`, reports in `research/reports/` | Run on Yahoo data (today's Nifty 500 list): 00 CONDITIONAL, others PASS, but survivorship-biased. |
| Survivorship check | `research/reports/survivorship_check.md` | About 6 of the 19% per 60 days came from using today's list. |
| Random-monkey + robustness + point-in-time backtest | `extended_tests.py`, `pit_backtest.py`, rules locked in config 1.4.0 | **Point-in-time: FAIL.** Net alpha +5.7% per 60d (needs > 2), win rate 54.0% (needs > 55), t-stat 1.69 (needs >= 2). Beats random picks (p < 0.001). Data amendments 1.4.1/1.4.2 (unadjusted splits/bonuses) are disclosed; no further data changes without an evidenced error. |
| Forward paper trading | `paper_trade.py`, `.github/workflows/paper.yml`, `paper/SCORECARD.md` | Runs weekdays after NSE close. Picks on the first trading day of each week; sells reported the same evening. Buy/sell alerts arrive as GitHub issues, and on WhatsApp via CallMeBot once the owner adds the secrets WHATSAPP_PHONE and CALLMEBOT_APIKEY. Pass rule (config 1.3.0): > 2% net alpha and > 55% win rate over >= 26 closed weekly picks. |
| UAT | `uat/`, `.github/workflows/uat.yml` | Passed 2026-10-26: 59 buy and 295 sell triggers replayed (2023-24), and the phone alert arrived. Functional test only. |
| Order gate (sizing, sector/heat caps, two approvals, Kite) | private `Trading` repo, `nse_exec/` | Built and tested, never used live. |
| Live app (engines A-E) | private `Trading` repo | **Never buys:** its buy functions are never called and the screener was never written. Its sells fire with no approval. Do not run live. |

## Decided, don't reopen without new evidence
- No intraday or day-trading skill packs, and no AI placing live orders.
- No tweaking the strategy to pass after seeing results; a new idea needs its own locked test.
- Monte Carlo drawdown study (a "Study 07"): only if paper trading passes, as the last check before real money.
- Savings meanwhile: Nifty index fund SIP.

## Project manager
A weekly PM session (charter `pm/CHARTER.md`, backlog `pm/BACKLOG.md`, log `pm/LOG.md`) works through the backlog with double-checked sub-agents and reports through a `PM weekly <date>` GitHub issue. It stops at the finish line: paper PASS plus a live setup that has been dry-run tested.

## Next decision point
When `paper/SCORECARD.md` reaches 26 closed weekly picks. Expect months: the strategy is in cash while breadth < 80% (31.4% on 2026-10-26).
