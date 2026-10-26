# Point-in-time backtest (pre-registered in research_config 1.4.0)

**Verdict: FAIL**

| | |
| --- | --- |
| Trading days / missing | 4129 / 1 |
| Symbols ever seen (delisted included) | 4398 |
| Daily moves beyond 40% (should be rare if PREVCLOSE is adjusted) | 2463 |
| Snapshots traded (breadth >= 80.0%) | 121 |
| Trades | 605 |
| Mean net alpha per 60 days (after Zerodha costs) | 5.60% (PASS > 2.0%) |
| Trades beating NIFTY after costs | 53.7% (PASS > 55.0%) |
| Non-overlapping t-stat of alpha | 0.30 (PASS >= 2.0) |
| Random-monkey test | PASS (p = 0.000) |
| Picks vs average eligible stock | 3.57% per 60 days |

Known limits: a renamed company restarts its price history (it waits 252 days to be eligible again); a stock that stops trading exits at its last traded price.
## NSE bhavcopy, point-in-time universe (no survivorship bias)

### Random-monkey test: **PASS**
Momentum 12-1 mean gross alpha: 6.07% per 60 days over 121 snapshots. 1000 random portfolios: median 2.53%, 95th percentile 4.06%. Share of random portfolios at least as good: **p = 0.000** (PASS needs p < 0.05).

### Robustness: **PASS** (6 of 6 variants with positive selection edge)
Selection edge = picks minus the average eligible stock, per 60 days. 12-1 + breadth is the strategy; the rest are checks only.

| variant | snapshots | mean_alpha | selection_edge | t_selection |
| --- | --- | --- | --- | --- |
| 6-1 + breadth | 121 | 3.46 | 0.96 | 0.51 |
| 6-1 no filter | 764 | 0.45 | 0.79 | -1.46 |
| 9-1 + breadth | 121 | 4.83 | 2.33 | -1.61 |
| 9-1 no filter | 764 | 1.38 | 1.73 | 0.06 |
| 12-1 + breadth | 121 | 6.07 | 3.57 | -0.87 |
| 12-1 no filter | 764 | 1.4 | 1.75 | 0.75 |
