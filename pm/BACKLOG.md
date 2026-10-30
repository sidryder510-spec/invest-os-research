# PM backlog (ordered; top unblocked task first)

Each task: id, repo, goal, acceptance criteria. The PM moves finished tasks to **Done** with the PR link.

## Open

### T1b. SELL-ticket bookkeeping follow-ups (Trading, from the T1 review)
Goal: close the fail-safe gaps the reviewer left open on #12.
Acceptance:
- A paper SELL doesn't block real exits (skip `sent == "paper"` when the config is live, or keep paper and live ticket stores separate).
- "Being sold" is ordered by ticket id instead of date, which fixes a same-day re-buy that can't be exited and a planned-earlier SELL that's wrongly ignored.
- An explicit `void --id N` for unsent tickets, logged, so the owner can clear a wrong approval or an unknown BUY after checking Kite (no hand-editing tickets.json).
- Tests for each.

### T8. Position config for ~60 holdings (Trading)
Goal: weekly Top-5 with 60-day holds means about 60 open positions. Make `nse_exec_config.example.json` match GO_LIVE.md section 6 (max_positions 60, max_position_pct 1.6, max_heat_pct 20, cash_buffer), and check that `rules.py` sizing behaves with them.
Acceptance: a test plans 60 positions on Rs 3 lakh without the cash or heat caps blocking early. If `rules.py` (mirrored from invest-os-research) needs changes, make them in invest-os-research and sync.


### T2. Live bridge: paper signal → nse_exec tickets (Trading)
Goal: turn this week's paper picks and due exits into `picks.json` / `exits.json` / `book.json` for `nse_exec plan` / `plan-exit`, plus the daily Kite access-token helper from GO_LIVE.md, so the live path uses exactly the paper strategy.
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


### T6. Paper-trading health check (invest-os-research)
Goal: catch silent failures.
Acceptance: the paper workflow opens an `[ACTION]` issue if data is more than 3 trading days stale, or if the scheduled run hasn't happened for 3 weekdays (checked by the PM weekly from the Actions history).

### T7. Research idea pipeline (invest-os-research, monthly, after T3)
Goal: one new pre-registered idea per month. First candidate: fundamentals (ROE, P/E, Piotroski) built from NSE XBRL filings, dated by filing time.
Acceptance: a feasibility check first (can filings be fetched from Actions, and with what coverage), then locked rules, then the point-in-time test. Only a PASS joins paper trading.

## Blocked on the owner
- **WhatsApp alerts:** add the secrets `WHATSAPP_PHONE` and `CALLMEBOT_APIKEY` in invest-os-research (steps in the 2026-10-28 chat). GitHub issue alerts work meanwhile.

## Done
- 2026-10-30 PM cycle 1: **T1** SELL tickets in nse_exec, merged in Trading #12 (3 review rounds, 69 tests). **T5** GO_LIVE.md go-live checklist with costs, merged in Trading #13 (2 review rounds).
- 2026-10-26-30: research engine v3, Studies 00-06, survivorship check, monkey and robustness tests, point-in-time backtest (FAIL), paper trading (daily, alerts), UAT, Trading mirror and sync rule, WhatsApp step.
