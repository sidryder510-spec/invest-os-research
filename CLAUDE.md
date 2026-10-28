# CLAUDE.md: invest-os-research (public)

Read `STATUS.md` first: it is the current truth about Invest OS.

## Owner rule: keep the private Trading repo up to date (2026-10-28)
This repo is where research and paper trading run (free Actions on a public repo). After **every** change here, in the same session, mirror it into `sidryder510-spec/Trading`:
1. In a Trading clone on a `claude/*` branch from `main`: `scripts/sync_research.sh /path/to/invest-os-research`
2. `python -m unittest discover tests` must pass there.
3. Commit, open a PR and merge it. The owner wants this end to end without asking.

Workflows are never mirrored, so no schedule or alert runs twice.

## Safety
- Paper only. Nothing here talks to a broker. No real money until `paper/SCORECARD.md` passes its locked rule.
- Pass/fail rules live in `research_config.py` and are changed only by a disclosed, versioned amendment, never to make a result pass.
