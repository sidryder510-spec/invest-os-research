# Extended tests (pre-registered in research_config 1.4.0)

## Yahoo data (today's Nifty 500 list: survivorship-biased)

### Random-monkey test: **PASS**
Momentum 12-1 mean gross alpha: 19.23% per 60 days over 183 snapshots. 1000 random portfolios: median 6.15%, 95th percentile 7.33%. Share of random portfolios at least as good: **p = 0.000** (PASS needs p < 0.05).

### Robustness: **PASS** (6 of 6 variants with positive selection edge)
Selection edge = picks minus the average eligible stock, per 60 days. 12-1 + breadth is the strategy; the rest are checks only.

| variant | snapshots | mean_alpha | selection_edge | t_selection |
| --- | --- | --- | --- | --- |
| 6-1 + breadth | 183 | 17.02 | 10.88 | 2.45 |
| 6-1 no filter | 764 | 9.97 | 6.57 | 2.97 |
| 9-1 + breadth | 183 | 16.36 | 10.22 | 2.39 |
| 9-1 no filter | 764 | 10.19 | 6.8 | 3.62 |
| 12-1 + breadth | 183 | 19.23 | 13.09 | 2.0 |
| 12-1 no filter | 764 | 10.28 | 6.88 | 3.6 |
