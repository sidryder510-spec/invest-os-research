# Study 02 -- Selection Concentration
**Protocol Version:** 1.1
**Config Version:** 1.2.0
**Research Engine Version:** 3.0.0
**Engine SHA256:** `032aa2c0bd77bac1...fc87f27b`
**Study Version:** 1.0.0
**Execution Date:** 2026-10-26

---

## Objective
Quantify how concentrated the Top-5 selections are and whether alpha depends on EICHERMOT.

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
| Execution Time | 09:48:38 |
| Runtime | 0.2 seconds |

## Acceptance Tests
| Test | Result |
| --- | --- |
| Required columns present | PASS |
| No duplicate trades | PASS |
| Row count > 0 | PASS |

## Results
| Metric | Value |
| --- | --- |
| total selections | 895 |
| unique symbols | 89 |
| hhi | 204.4 |
| gini | 0.481 |
| top1 symbol | AVANTIFEED |
| top1 share pct | 4.36 |
| mean alpha all | 19.101 |
| mean alpha without top1 | 18.421 |
| watch share pct | 0.0 |
| mean alpha without watch | 19.101 |
| max possible share pct | 20.0 |
| top1 weeks present pct | 21.79 |
| top1 alpha contribution pct | 7.76 |
| watch weeks present pct | 0.0 |
| watch alpha contribution pct | 0.0 |

### Top 10 Symbols
| symbol | selections | share_pct | mean_alpha |
| --- | --- | --- | --- |
| AVANTIFEED | 39 | 4.36 | 34.032 |
| CGPOWER | 34 | 3.8 | 35.052 |
| TITAGARH | 32 | 3.58 | 12.403 |
| CEATLTD | 30 | 3.35 | 24.715 |
| CUPID | 28 | 3.13 | -13.299 |
| PGEL | 27 | 3.02 | 32.557 |
| GVT&D | 27 | 3.02 | 27.344 |
| TTML | 26 | 2.91 | 174.397 |
| TARIL | 26 | 2.91 | 30.069 |
| JBMA | 25 | 2.79 | 47.182 |

## Alpha Without EICHERMOT
Mean alpha per 60 days falls from 19.101 to 19.101 (0.0 points) without EICHERMOT.

## Verdict Criteria (defined before results were examined)
| Verdict | Criteria |
| --- | --- |
| PASS | HHI < 2000 and top symbol < 25.0% of selections |
| CONDITIONAL | Neither PASS nor FAIL |
| FAIL | HHI > 3000 or top symbol > 40.0% |

## Verdict
**PASS**

## Protocol Warning
Each snapshot holds 5 different stocks, so no symbol can exceed 20.0% of selections and HHI cannot exceed 2000. The locked criteria above therefore cannot reach FAIL, and this verdict says little about concentration. Judge it on the informational rows instead: top1 weeks present pct (how often the stock is held) and top1 alpha contribution pct (how much of the total alpha it supplies). New thresholds for these need an owner decision and a research config version bump.

## Next Study
**Study 05 -- Transaction Costs** (Studies 03 and 04 are not implemented yet).