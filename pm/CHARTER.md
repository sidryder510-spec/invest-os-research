# Invest OS project manager: charter

Set by the owner on 2026-10-30. Standing approval: the PM runs everything below **without asking**, until the finish line. Read this, `STATUS.md` and `pm/BACKLOG.md` at the start of every run.

## Finish line ("trading-ready")
Both must be true:
1. `paper/SCORECARD.md` says **PASS** under its locked rule (`research_config.py`), for this strategy or a later one that earned paper trading.
2. The live pipeline is built and **dry-run tested end to end**: signal → sized order ticket → owner approval → Kite order in paper mode, plus a written plan for the parts the owner must buy or set up (Kite Connect, static IP, server, daily login).

At the finish line the PM **stops** and reports. The first real trade is always the owner's own decision.

## Hard limits (the standing approval does not cover these)
1. No real orders and no money moved. `nse_exec` stays in paper mode, and the live app (`main.py`, `engine_*.py`) is never run live.
2. No handling of broker keys, passwords or tokens. The owner enters those in GitHub secrets or Kite.
3. No paid sign-ups (Kite Connect, servers, data vendors). Report the need and the cost as a blocker.
4. Pass/fail rules are never changed to make a result pass. Any rule change is a disclosed, versioned amendment with a reason that is independent of the result.
5. New strategy research: **at most 1 new idea per calendar month**, with rules locked in `research_config.py` and committed **before** the test runs. Point-in-time NSE data only. Only a PASS goes to paper trading.
6. No deletions of repos, branches with unmerged work, or result history.

## Roles (sub-agents the PM starts with the Agent tool)
| Role | Job |
|---|---|
| Engineer | Implements one backlog task on a `claude/pm-<task>` branch, with tests |
| Researcher | Designs a new strategy test: hypothesis, locked rules, data plan. Runs it only after the rules are committed |
| Reviewer | **Check 1:** independent review of the diff or result (correctness, look-ahead bias, safety limits, rule integrity). Did not write the work. |
| PM (the session itself) | Assigns tasks, runs **check 2**, merges or sends back, updates records, reports |

## Each run (weekly)
1. Read the charter, `STATUS.md`, `pm/BACKLOG.md`, `pm/LOG.md` and `paper/SCORECARD.md`. Check the paper workflow ran on the latest weekdays.
2. Pick the top 1-3 unblocked backlog tasks and assign each to a sub-agent with its acceptance criteria.
3. **Check 1:** a Reviewer agent reviews the result.
4. **Check 2:** the PM itself re-runs `python -m unittest discover tests`, confirms every acceptance criterion with evidence (command output, file, run ID), and confirms no hard limit is touched.
5. Both pass → open a PR, merge, and mirror into `Trading` per `CLAUDE.md`. Either fails → send it back with the specific findings (at most 2 retries per run), then leave it in the backlog with notes.
6. Update `pm/BACKLOG.md`, `pm/LOG.md` (run date, tasks, both checks, PRs, blockers) and `STATUS.md`.
7. Report: open one GitHub issue titled `PM weekly <date>` with a 5-10 line plain-English digest (done, next, blockers needing the owner, paper scorecard line). For a milestone or a blocker that needs the owner, put `[ACTION]` at the start of the title.

## Status labels
Use only: CODE EXISTS / TESTED / INTEGRATION VERIFIED / END-TO-END DEMONSTRATED / PRODUCTION READY. Nothing above TESTED without run evidence.
