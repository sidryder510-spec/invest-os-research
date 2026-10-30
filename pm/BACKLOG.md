# PM backlog (ordered; top unblocked task first)

Each task: id, repo, goal, acceptance criteria. The PM moves finished tasks to **Done** with the PR link.

## Open

### T1. Exit tickets in nse_exec (Trading)
Goal: the order gate can build SELL tickets (60-day time exit), not only BUY tickets.
Acceptance:
- `nse_exec` plans a SELL for a held position, with exact-text approval `SELL <qty> <SYMBOL>`. Paper send works, and live send keeps the same terminal-only guard.
- The GTT stop for that position is cancelled in the same ticket flow (paper payload shown).
- Tests cover approval mismatch, a stale approval and a duplicate send for SELL.

### T2. Live bridge: paper signal → nse_exec tickets (Trading)
Goal: turn this week's paper picks and due exits into `picks.json` / `book.json` for `nse_exec plan`, so the live path uses exactly the paper strategy.
Acceptance:
- `live_bridge.py` reads `paper/ledger.csv` (synced from invest-os-research) and writes picks and exits. The entry is a limit near the last close; position size comes from `nse_exec` limits.
- An end-to-end dry run in tests: ledger → bridge → plan → approve → paper send for one BUY and one SELL.
- No code path can send live without `nse_exec`'s terminal confirmation.

### T3. Stop-loss policy as a locked research test (invest-os-research)
Goal: `nse_exec` requires a stop, but the tested strategy has none. Decide with evidence whether a catastrophe stop (e.g. -20% / -25% / -30% GTT) hurts or helps the point-in-time result.
Acceptance:
- Rules and the PASS criterion committed to `research_config.py` before the run (counts as that month's new idea).
- Report in `research/reports/`; the chosen stop documented in `STATUS.md`. If no stop passes, the live plan uses the widest tested stop as risk insurance and says so.

### T4. Make the old live app safe (Trading)
Goal: the uploaded app must never send an unapproved order if someone runs it.
Acceptance:
- `main.py` defaults to dry-run, and live needs an explicit flag plus `nse_exec`'s confirmation.
- Engine B/C market sells and GTT changes go through `nse_exec` tickets or alerts instead of `kite_manager` directly.
- Tests prove no `kite_manager.place_*` call happens without approval.

### T5. Go-live plan document (Trading)
Goal: `GO_LIVE.md`, a phone-friendly checklist of what the owner must buy or set up, with current costs and sources: Kite Connect plan, static IP (cloud VM options and monthly cost), where the job runs, the daily login flow, and starting capital and limits for phase 1.
Acceptance: every cost and rule cites a source checked during the run. Nothing is purchased.

### T6. Paper-trading health check (invest-os-research)
Goal: catch silent failures.
Acceptance: the paper workflow opens an `[ACTION]` issue if data is more than 3 trading days stale, or if the scheduled run hasn't happened for 3 weekdays (checked by the PM weekly from the Actions history).

### T7. Research idea pipeline (invest-os-research, monthly, after T3)
Goal: one new pre-registered idea per month. First candidate: fundamentals (ROE, P/E, Piotroski) built from NSE XBRL filings, dated by filing time.
Acceptance: a feasibility check first (can filings be fetched from Actions, and with what coverage), then locked rules, then the point-in-time test. Only a PASS joins paper trading.

## Blocked on the owner
- **WhatsApp alerts:** add the secrets `WHATSAPP_PHONE` and `CALLMEBOT_APIKEY` in invest-os-research (steps in the 2026-10-28 chat). GitHub issue alerts work meanwhile.

## Done
- 2026-10-26-30: research engine v3, Studies 00-06, survivorship check, monkey and robustness tests, point-in-time backtest (FAIL), paper trading (daily, alerts), UAT, Trading mirror and sync rule, WhatsApp step.
