# Study 05 -- Transaction Costs
**Protocol Version:** 1.1
**Config Version:** 1.2.0
**Research Engine Version:** 3.0.0
**Engine SHA256:** `032aa2c0bd77bac1...fc87f27b`
**Study Version:** 1.0.0
**Execution Date:** 2026-10-26

---

## Objective
Measure alpha after Zerodha equity-delivery charges and slippage on every round trip.

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
| Runtime | 0.3 seconds |

## Method
Each trade is a Rs 100000 round trip. Charges: STT, exchange, SEBI, GST, stamp duty and DP via `nse_exec.rules.charges` with `S05_CHARGES`. Slippage: 0.1% (large cap) or 0.25% (mid cap) each way. A win means beating NIFTY after costs. The NIFTY leg carries no cost, which makes this slightly conservative. Tax is not included.

## Acceptance Tests
| Test | Result |
| --- | --- |
| Required columns present | PASS |
| No duplicate trades | PASS |
| No null returns or alpha | PASS |
| No unparseable dates | PASS |
| Row count > 0 | PASS |

## Results
| Metric | Value |
| --- | --- |
| trades | 895 |
| mean gross alpha | 19.101 |
| mean cost pct | 0.484 |
| mean net alpha | 18.617 |
| median net alpha | 7.287 |
| net win rate pct | 60.78 |
| mean net win | 39.574 |
| mean net loss | -13.863 |
| non overlapping periods | 15 |
| non overlapping t stat | 2.06 |

The t-stat uses one snapshot every 12 weeks so holding periods do not overlap. It is informational, not part of the verdict; below about 2 the edge cannot be told apart from luck.

## Verdict Criteria (defined before results were examined)
| Verdict | Criteria |
| --- | --- |
| PASS | Mean net alpha > 2.0% per 60d and net win rate > 55.0% |
| CONDITIONAL | Neither PASS nor FAIL |
| FAIL | Mean net alpha < 0.5% or net win rate < 50.0% |

## Verdict
**PASS**

## Next Study
**Study 06 -- Walk-Forward Validation** (uses this study's net alpha).