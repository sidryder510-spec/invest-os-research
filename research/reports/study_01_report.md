# Study 01 -- Eligibility Audit
**Protocol Version:** 1.1
**Config Version:** 1.2.0
**Research Engine Version:** 3.0.0
**Engine SHA256:** `032aa2c0bd77bac1...fc87f27b`
**Study Version:** 1.0.0
**Execution Date:** 2026-10-26

---

## Objective
Verify that no stock was selected into the Top 5 portfolio before accumulating 252 trading days of price history at the snapshot date.

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
| Execution Time | 09:40:04 |
| Runtime | 5.2 seconds |

## Method
Market data loaded via engine `load_market_data()`. Snapshots via `get_snapshot_dates()`. Top-5 selections reconstructed via `generate_historical_candidates()`. Independent of `trade_dump.csv`. Eligibility: rows_available >= 252. Violation: was_selected AND NOT eligible.

## Acceptance Tests
| Test | Result |
| --- | --- |
| CSV exported | PASS |
| Row count > 0 | PASS |
| No duplicate snapshot/symbol rows | PASS |
| Consistent symbol count per snapshot | PASS |
| selected_rank in [1,5] or NA | PASS |
| was_selected and selected_rank consistent | PASS |
| Required columns present | PASS |

## Results
| Metric | Value |
| --- | --- |
| Total snapshots audited | 179 |
| Total stock-snapshot combinations | 89321 |
| Eligible combinations | 65161 |
| Ineligible combinations | 24160 |
| Total selections audited | 895 |
| Selection violations | 0 |

### First Eligibility Dates
| Symbol | First Eligible Date | Selections Before Eligible |
| --- | --- | --- |
| ADANIENSOL | 2016-08-24 | 0 |
| ADANIENT | 2012-10-04 | 0 |
| ADANIGREEN | 2020-11-17 | 0 |
| AJANTPHARM | 2012-10-04 | 0 |
| ANANDRATHI | 2023-07-04 | 0 |
| ANANTRAJ | 2012-10-04 | 0 |
| APARINDS | 2012-10-04 | 0 |
| APLAPOLLO | 2013-01-07 | 0 |
| ASTRAL | 2012-10-04 | 0 |
| ATGL | 2020-11-17 | 0 |
| ATUL | 2012-10-04 | 0 |
| AUROPHARMA | 2012-10-04 | 0 |
| AVANTIFEED | 2012-10-04 | 0 |
| BAJFINANCE | 2012-10-04 | 0 |
| BALRAMCHIN | 2012-10-04 | 0 |
| BBOX | 2012-10-04 | 0 |
| BEML | 2012-10-04 | 0 |
| BSE | 2020-11-17 | 0 |
| BSOFT | 2012-10-04 | 0 |
| CEATLTD | 2012-10-04 | 0 |
| CGPOWER | 2012-10-04 | 0 |
| CIEINDIA | 2012-10-04 | 0 |
| COCHINSHIP | 2020-11-17 | 0 |
| CUPID | 2017-11-03 | 0 |
| DIXON | 2020-11-17 | 0 |
| ELECON | 2012-10-04 | 0 |
| ESCORTS | 2012-10-04 | 0 |
| FACT | 2012-10-04 | 0 |
| FINCABLES | 2012-10-04 | 0 |
| FORCEMOT | 2020-11-17 | 0 |
| GALLANTT | 2012-10-04 | 0 |
| GODFRYPHLP | 2012-10-04 | 0 |
| GPIL | 2012-10-04 | 0 |
| GRANULES | 2012-10-04 | 0 |
| GRAPHITE | 2012-10-04 | 0 |
| GRAVITA | 2012-10-04 | 0 |
| GVT&D | 2012-10-04 | 0 |
| HBLENGINE | 2012-10-04 | 0 |
| HEGAM | 2012-10-04 | 0 |
| HINDALCO | 2012-10-04 | 0 |
| HSCL | 2012-10-04 | 0 |
| HUDCO | 2020-11-17 | 0 |
| IDEA | 2012-10-04 | 0 |
| IFCI | 2012-10-04 | 0 |
| INDIAMART | 2020-11-17 | 0 |
| INDIANB | 2012-10-04 | 0 |
| INOXWIND | 2016-07-25 | 0 |
| INTELLECT | 2016-07-25 | 0 |
| IRFC | 2023-07-04 | 0 |
| ITI | 2012-10-04 | 0 |
| JBMA | 2012-10-04 | 0 |
| JINDALSAW | 2012-10-04 | 0 |
| JKCEMENT | 2012-10-04 | 0 |
| JSL | 2012-10-04 | 0 |
| JSWENERGY | 2012-10-04 | 0 |
| JWL | 2012-10-04 | 0 |
| KEC | 2012-10-04 | 0 |
| KEI | 2012-10-04 | 0 |
| KIRLOSENG | 2012-10-04 | 0 |
| LAURUSLABS | 2017-12-22 | 0 |
| MANAPPURAM | 2012-10-04 | 0 |
| MAZDOCK | 2021-10-22 | 0 |
| MOTILALOFS | 2012-10-04 | 0 |
| MUTHOOTFIN | 2012-10-04 | 0 |
| NAVINFLUOR | 2012-10-04 | 0 |
| NBCC | 2014-03-11 | 0 |
| NEULANDLAB | 2012-10-04 | 0 |
| OLECTRA | 2012-10-04 | 0 |
| PATANJALI | 2012-10-04 | 0 |
| PCBL | 2012-10-04 | 0 |
| PGEL | 2012-10-11 | 0 |
| POONAWALLA | 2012-10-04 | 0 |
| PRIVISCL | 2016-07-25 | 0 |
| RVNL | 2020-11-17 | 0 |
| SRF | 2012-10-04 | 0 |
| SUZLON | 2012-10-04 | 0 |
| TARIL | 2012-10-04 | 0 |
| TATAELXSI | 2012-10-04 | 0 |
| TATAINVEST | 2012-10-04 | 0 |
| TEJASNET | 2020-11-17 | 0 |
| TITAGARH | 2012-10-04 | 0 |
| TTML | 2012-10-04 | 0 |
| TVSMOTOR | 2012-10-04 | 0 |
| UNITDSPR | 2012-10-04 | 0 |
| UNOMINDA | 2012-10-04 | 0 |
| VEDL | 2012-10-04 | 0 |
| WELSPUNLIV | 2012-10-04 | 0 |
| WOCKPHARMA | 2012-10-04 | 0 |
| ZENTEC | 2016-07-25 | 0 |

### Violation Detail
No violations found.

## Conclusion
Zero violations across 179 snapshots and 89321 observations. Every Top-5 selection had >= 252 days of history. Engine eligibility is correct.

## Verdict Criteria (defined before results were examined)
| Verdict | Criteria |
| --- | --- |
| PASS | Zero violations across full history |
| CONDITIONAL | < 5 violations, all before 2010, none at Rank 1 |
| FAIL | Any violation after 2010, any at Rank 1, or >= 5 total |

## Verdict
**PASS** -- Zero selection violations.

## Research Impact
| Question | Answer |
| --- | --- |
| Does this change the model? | NO -- Engine behaviour confirmed correct. |
| Does this change production? | NO -- Production system is separate. |
| Does this require rerunning previous studies? | NO -- This is Study 01. |

## Recommendation
Proceed to Study 02 -- Selection Concentration.

## Next Study
**Study 02 -- Selection Concentration:** Uses `trade_dump.csv` directly.
Quantifies concentration (HHI, Gini) and computes alpha with/without EICHERMOT.