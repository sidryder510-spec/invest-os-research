# Point-in-time backtest (pre-registered in research_config 1.4.0)

**Verdict: FAIL**

| | |
| --- | --- |
| Trading days / missing | 4129 / 0 |
| Symbols ever seen (delisted included) | 4398 |
| Daily moves beyond 35% neutralised as splits/bonuses/bad prints (amendment 1.4.2) | 2686 |
| Daily moves beyond 40% left after that | 0 |
| Snapshots traded (breadth >= 80.0%) | 149 |
| Trades | 745 |
| Mean net alpha per 60 days (after Zerodha costs) | 5.71% (PASS > 2.0%) |
| Trades beating NIFTY after costs | 54.0% (PASS > 55.0%) |
| Non-overlapping t-stat of alpha | 1.69 (PASS >= 2.0) |
| Random-monkey test | PASS (p = 0.000) |
| Picks vs average eligible stock | 3.41% per 60 days |

Known limits: a renamed company restarts its price history (it waits 252 days to be eligible again); a stock that stops trading exits at its last traded price.
## NSE bhavcopy, point-in-time universe (no survivorship bias)

### Random-monkey test: **PASS**
Momentum 12-1 mean gross alpha: 6.18% per 60 days over 149 snapshots. 1000 random portfolios: median 2.71%, 95th percentile 4.06%. Share of random portfolios at least as good: **p = 0.000** (PASS needs p < 0.05).

### Robustness: **PASS** (6 of 6 variants with positive selection edge)
Selection edge = picks minus the average eligible stock, per 60 days. 12-1 + breadth is the strategy; the rest are checks only.

| variant | snapshots | mean_alpha | selection_edge | t_selection |
| --- | --- | --- | --- | --- |
| 6-1 + breadth | 149 | 4.04 | 1.27 | -0.02 |
| 6-1 no filter | 764 | 3.08 | 2.7 | 0.09 |
| 9-1 + breadth | 149 | 3.19 | 0.42 | -2.28 |
| 9-1 no filter | 764 | 2.93 | 2.55 | 0.66 |
| 12-1 + breadth | 149 | 6.18 | 3.41 | 1.15 |
| 12-1 no filter | 764 | 3.66 | 3.27 | 1.7 |
