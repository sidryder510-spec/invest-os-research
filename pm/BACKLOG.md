# PM backlog (ordered; top unblocked task first)

Each task: id, repo, goal, acceptance criteria. The PM moves finished tasks to **Done** with the PR link.

## Open

### T9. Strategy fidelity: live limits vs paper picks (invest-os-research, then Trading)
Goal: live trading through nse_exec skips picks that paper trading takes (shares above the Rs 4,800 cap, the sector cap at 40%, and heat blocks), so a paper PASS would overstate live results.
Acceptance:
- `rules.py` measures heat from cost: open risk = qty × (min(ltp, avg_price) − stop), floored at 0. `cli.plan` adds avg_price = entry to the holdings it appends. Flip Trading's `test_winners_block_new_buys_today` to expect PASS.
- A fidelity report replays every paper/point-in-time pick through `rules.check` against a simulated Rs 3 lakh book (phase-1 config, -30% stops) and reports the skip rate by reason plus the net alpha of skipped vs taken picks.
- If the skip rate is material, propose (don't adopt without a locked rule) a second paper track limited the same way as live.

### T1c. nse_exec small follow-ups (Trading, from the T1b review)
Acceptance: `void --checked-kite` also works for a SELL with an unknown outcome; the `replan` same-day BUY block ignores paper sends in live mode; `void` only applies to PASS tickets. Tests for each.

### T2. Live bridge: paper signal → nse_exec tickets (Trading; stops at entry × 0.70 per T3)
Goal: turn this week's paper picks and due exits into `picks.json` / `exits.json` / `book.json` for `nse_exec plan` / `plan-exit`, plus the daily Kite access-token helper from GO_LIVE.md, so the live path uses exactly the paper strategy.
Acceptance:
- `live_bridge.py` reads `paper/ledger.csv` (synced from invest-os-research) and writes picks and exits. The entry is a limit near the last close; position size comes from `nse_exec` limits.
- An end-to-end dry run in tests: ledger → bridge → plan → approve → paper send for one BUY and one SELL.
- No code path can send live without `nse_exec`'s terminal confirmation.

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
Goal: one new pre-registered idea per month (October 2026's was T3; this is November's). First candidate: fundamentals (ROE, P/E, Piotroski) built from NSE XBRL filings, dated by filing time.
Acceptance: a feasibility check first (can filings be fetched from Actions, and with what coverage), then locked rules, then the point-in-time test. Only a PASS joins paper trading.

## Blocked on the owner
- **WhatsApp alerts:** add the secrets `WHATSAPP_PHONE` and `CALLMEBOT_APIKEY` in invest-os-research (steps in the 2026-10-28 chat). GitHub issue alerts work meanwhile.

## Done
- 2026-11-02 PM cycle 2: **T1b** SELL bookkeeping by ticket id + void (Trading #16). **T8** phase-1 config for ~60 positions (Trading #17). **T3** stop-loss test, pre-registered (invest-os-research #4): result ADOPT -30% stop (mean net alpha 5.37 vs 5.71, worst trade -42.5% vs -73.6%).
- 2026-10-30 PM cycle 1: **T1** SELL tickets in nse_exec, merged in Trading #12 (3 review rounds, 69 tests). **T5** GO_LIVE.md go-live checklist with costs, merged in Trading #13 (2 review rounds).
- 2026-10-26-30: research engine v3, Studies 00-06, survivorship check, monkey and robustness tests, point-in-time backtest (FAIL), paper trading (daily, alerts), UAT, Trading mirror and sync rule, WhatsApp step.
