# Stop-loss test (pre-registered in research_config 1.5.0)

**Decision: ADOPT -30% stop: within 0.5 points of the no-stop mean and a smaller worst loss.**

Point-in-time data, 4133 trading days (0 missing). Stops on daily closes, exit at the next close; Study 05 Zerodha costs. Rule: the widest stop whose mean net alpha is at most 0.5 points per 60 days below no-stop AND whose worst trade (lowest net return) is better. The strategy's point-in-time FAIL stands whatever this shows.

| variant | trades | mean_net_alpha | median_net_alpha | win_rate_pct | worst_trade_net_return | stopped_pct | t_nonoverlap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| no stop | 745 | 5.71 | 1.74 | 54.0 | -73.61 | 0.0 | 1.69 |
| -20% stop | 745 | 4.92 | 0.86 | 51.7 | -33.68 | 20.5 | 1.95 |
| -25% stop | 745 | 5.17 | 1.48 | 53.0 | -37.98 | 13.8 | 1.66 |
| -30% stop | 745 | 5.37 | 1.6 | 53.4 | -42.45 | 8.5 | 1.68 |

**Disclosure.** The baseline's per-trade results (worst -73.6%, ENERGYDEV 2016) were already public in research/outputs/pit_trades.csv when this rule was locked, so the worst-trade test was nearly predetermined; the mean-alpha test is what decides.

**Biases (they point in different directions, so this is a close-data estimate, not a GTT simulation).**
- Closes miss intraday dips that would fire a real GTT, so stop-outs are understated and the mean flatters the stop.
- On a steady slide a GTT sells near the trigger, while the test sells at the next close, usually lower, so worst losses look worse than live (against the stop).
- On lower-circuit (limit-down) days no sell can fill, but the test still sells at the next close, which flatters the stop's worst trade.
- Crash protection beyond a 35% single-day move is NOT measured: amendment 1.4.2 zeroes those moves for the baseline and every stop alike.

Picks with a zeroed >35% daily move inside their holding window: **18**: RSSOFTWARE (2014-10-28), RSSOFTWARE (2014-11-20), JINDWORLD (2017-11-03), GPIL (2021-08-03), GPIL (2021-08-10), GPIL (2021-08-17), GPIL (2021-09-01), GPIL (2021-09-08), GPIL (2021-09-16), NEWGEN (2023-12-20), NEWGEN (2023-12-28), INOXWIND (2024-02-26), INOXWIND (2024-03-04), INOXWIND (2024-04-04), INOXWIND (2024-04-12), INOXWIND (2024-04-29), PCJEWELLER (2024-09-23), PCJEWELLER (2024-09-30)

t is the non-overlapping t-stat of gross alpha, as in pit_backtest.
