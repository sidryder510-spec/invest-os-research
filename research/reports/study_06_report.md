# Study 06 -- Walk-Forward Validation
**Protocol Version:** 1.1
**Config Version:** 1.2.0
**Research Engine Version:** 3.0.0
**Engine SHA256:** `032aa2c0bd77bac1...fc87f27b`
**Study Version:** 1.0.0
**Execution Date:** 2026-10-26

---

## Objective
Check that after-cost alpha holds up across 10 yearly test windows.

## Dependencies
| Metric | Value |
| --- | --- |
| Research Engine Version | 3.0.0 |
| Engine SHA256 | `032aa2c0bd77bac1...fc87f27b` |
| Config Version | 1.2.0 |
| Protocol Version | 1.1 |
| Python Version | 3.12.15 |
| pandas Version | 3.1.0 |
| numpy Version | 2.5.4 |
| yfinance Version | 1.7.0 |
| Execution Date | 2026-10-26 |
| Execution Time | 09:40:10 |
| Runtime | 0.3 seconds |

## Method
Net alpha per trade comes from Study 05. Each window is one calendar year of snapshots. A year with no trades (breadth filter kept the strategy in cash) counts as not positive. The engine is frozen, so no parameters are refit. This tests stability, not true out-of-sample performance: if the parameters were chosen while looking at these years, only forward paper trading from the freeze date is truly out of sample.

## Acceptance Tests
| Test | Result |
| --- | --- |
| Required columns present | PASS |
| No duplicate trades | PASS |
| No null returns or alpha | PASS |
| No unparseable dates | PASS |
| Row count > 0 | PASS |

## Windows
| year | trades | mean_gross_alpha | mean_net_alpha | net_win_rate_pct |
| --- | --- | --- | --- | --- |
| 2015 | 5 | 18.706 | 18.242 | 100.0 |
| 2016 | 55 | 1.227 | 0.792 | 47.27 |
| 2017 | 80 | 18.902 | 18.44 | 62.5 |
| 2018 | 20 | -7.443 | -7.87 | 30.0 |
| 2019 | 0 | nan | nan | nan |
| 2020 | 35 | 26.6 | 26.097 | 62.86 |
| 2021 | 215 | 34.117 | 33.595 | 68.37 |
| 2022 | 0 | nan | nan | nan |
| 2023 | 125 | 16.619 | 16.127 | 70.4 |
| 2024 | 160 | 4.083 | 3.612 | 43.12 |

## Results
| Metric | Value |
| --- | --- |
| test windows | 10 |
| windows with data | 8 |
| positive windows | 7 |
| mean oos net alpha | 13.629 |
| worst window | 2018 |
| worst window net alpha | -7.87 |

## Verdict Criteria (defined before results were examined)
| Verdict | Criteria |
| --- | --- |
| PASS | >= 7 of 10 windows positive and mean net alpha >= 1.5% per 60d |
| CONDITIONAL | Neither PASS nor FAIL |
| FAIL | Mean net alpha < 0.5% per 60d |

## Verdict
**PASS**

## Next Step
If PASS: paper trade through `nse_exec` from the freeze date before any live order.