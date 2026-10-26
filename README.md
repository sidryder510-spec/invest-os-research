# Invest OS research studies

These follow Research Protocol v1.1: each study has its verdict thresholds locked in `research_config.py`, checks the frozen engine's hash (`historical_backtest_v3.py`: 12-1 momentum, locked before any result; the v2 engine was lost), and writes a CSV, a report and a metadata JSON under `research/`.

| Study | File | Needs | Status |
|---|---|---|---|
| 00 Engine validation | `study_00_engine_validation.py` | engine + `trade_dump.csv` | TESTED on synthetic market |
| 01 Eligibility audit | `study_01_eligibility.py` | engine (downloads data) | TESTED on synthetic market |
| 02 Selection concentration | `study_02_concentration.py` | `trade_dump.csv` | TESTED on synthetic data |
| 03 Rank persistence | not built | `trade_dump.csv` | not built |
| 04 Sector concentration | not built | sector map (not in the dump) | not built |
| 05 Transaction costs | `study_05_transaction_costs.py` | `trade_dump.csv` | TESTED on synthetic data |
| 06 Walk-forward | `study_06_walk_forward.py` | `trade_dump.csv` | TESTED on synthetic data |

## Run
Build the dump, then run the studies:
```
python -c "import historical_backtest_v3 as e; e.export_trade_dump()"
```
```
python study_00_engine_validation.py
python study_01_eligibility.py
python study_02_concentration.py
python study_05_transaction_costs.py
python study_06_walk_forward.py
```
Run them in order (or let GitHub run everything: Actions tab -> research -> Run workflow). A study is only as trustworthy as the ones before it. Offline tests: `python -m unittest discover tests`.

## Known limits
- **Study 02's locked criteria cannot fail.** Every snapshot holds 5 different stocks, so no symbol can exceed 20% of selections and HHI cannot exceed 2,000. The report flags this. Judge concentration on its informational rows instead: weeks present % and alpha contribution %. New thresholds need an owner decision and a research config version bump.
- **Study 05 costs.** These are Zerodha delivery charges at Rs 1 lakh per position (config 1.1.0 corrected the 1.0.0 cost model). Income tax is not included. The NIFTY leg is treated as cost-free.
- **Study 06 tests stability, not true out-of-sample performance.** The engine is frozen and nothing is refit. If its parameters were chosen while looking at 2015-2024, only forward paper trading from the freeze date counts as out of sample.
- **Overlapping holds.** Weekly snapshots with 60-day holds overlap about 12 times. Study 05 reports a t-stat on non-overlapping periods; below about 2, the edge can't be told apart from luck.
- **Survivorship.** Engine v3 uses today's Nifty 500 list for all past dates. Stocks that dropped out or were delisted are missing, which flatters every result. Point-in-time constituents are not freely available.
- **Breadth filter.** The strategy trades only when at least 80% of the universe is above its 200-day average. Expect long stretches in cash.
