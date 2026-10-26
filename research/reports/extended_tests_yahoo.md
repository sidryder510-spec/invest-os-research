# Extended tests (pre-registered in research_config 1.4.0)

## Yahoo data (today's Nifty 500 list: survivorship-biased)

### Random-monkey test: **PASS**
Momentum 12-1 mean gross alpha: 19.10% per 60 days over 179 snapshots. 1000 random portfolios: median 6.04%, 95th percentile 7.37%. Share of random portfolios at least as good: **p = 0.000** (PASS needs p < 0.05).

### Robustness: **PASS** (6 of 6 variants with positive selection edge)
Selection edge = picks minus the average eligible stock, per 60 days. 12-1 + breadth is the strategy; the rest are checks only.

| variant | snapshots | mean_alpha | selection_edge | t_selection |
| --- | --- | --- | --- | --- |
| 6-1 + breadth | 179 | 16.4 | 10.3 | 1.53 |
| 6-1 no filter | 764 | 9.92 | 6.52 | 2.91 |
| 9-1 + breadth | 179 | 16.05 | 9.94 | 1.08 |
| 9-1 no filter | 764 | 10.13 | 6.73 | 3.56 |
| 12-1 + breadth | 179 | 19.1 | 13.0 | 1.19 |
| 12-1 no filter | 764 | 10.15 | 6.75 | 3.56 |
