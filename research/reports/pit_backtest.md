# Point-in-time backtest (pre-registered in research_config 1.4.0)

**Verdict: FAIL**

| | |
| --- | --- |
| Trading days / missing | 4129 / 1 |
| Symbols ever seen (delisted included) | 4398 |
| Unadjusted splits/bonuses neutralised (amendment 1.4.1) | 1624 |
| Daily moves beyond 40% left after that | 1511 |
| Snapshots traded (breadth >= 80.0%) | 143 |
| Trades | 715 |
| Mean net alpha per 60 days (after Zerodha costs) | 4.41% (PASS > 2.0%) |
| Trades beating NIFTY after costs | 52.7% (PASS > 55.0%) |
| Non-overlapping t-stat of alpha | 1.46 (PASS >= 2.0) |
| Random-monkey test | PASS (p = 0.000) |
| Picks vs average eligible stock | 2.50% per 60 days |

Known limits: a renamed company restarts its price history (it waits 252 days to be eligible again); a stock that stops trading exits at its last traded price.
## NSE bhavcopy, point-in-time universe (no survivorship bias)

### Random-monkey test: **PASS**
Momentum 12-1 mean gross alpha: 4.88% per 60 days over 143 snapshots. 1000 random portfolios: median 2.35%, 95th percentile 3.64%. Share of random portfolios at least as good: **p = 0.000** (PASS needs p < 0.05).

### Robustness: **PASS** (6 of 6 variants with positive selection edge)
Selection edge = picks minus the average eligible stock, per 60 days. 12-1 + breadth is the strategy; the rest are checks only.

| variant | snapshots | mean_alpha | selection_edge | t_selection |
| --- | --- | --- | --- | --- |
| 6-1 + breadth | 143 | 2.77 | 0.39 | -0.17 |
| 6-1 no filter | 764 | 1.45 | 1.34 | -0.82 |
| 9-1 + breadth | 143 | 2.93 | 0.56 | -0.04 |
| 9-1 no filter | 764 | 1.69 | 1.58 | -0.35 |
| 12-1 + breadth | 143 | 4.88 | 2.5 | 0.56 |
| 12-1 no filter | 764 | 1.98 | 1.87 | 0.81 |
