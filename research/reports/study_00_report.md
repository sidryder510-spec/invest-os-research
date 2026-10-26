# Study 00 -- Engine Validation
**Protocol Version:** 1.1
**Config Version:** 1.2.0
**Research Engine Version:** 3.0.0
**Engine SHA256:** `032aa2c0bd77bac1...fc87f27b`
**Study Version:** 1.0.0
**Execution Date:** 2026-10-26

---

## Objective
Validate the frozen research engine before any study results are produced.
If this study fails, no subsequent study result can be trusted.

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
| Execution Time | 09:40:02 |
| Runtime | 1.2 seconds |

## Validation Results
| Check | Result | Detail |
| --- | --- | --- |
| Required columns present | PASS | All present |
| No duplicate trades | PASS | 0 duplicates |
| Exactly Top-5 per snapshot | PASS | All snapshots have 5 stocks |
| Sequential ranks per snapshot | PASS | All ranks sequential |
| No null returns or alpha | PASS | 0 nulls |
| alpha == stock_return - nifty_return | PASS | Consistent (max diff=0.0001) |
| Weekly snapshot spacing | FAIL | 13 irregular gaps (min=7d max=1029d) |
| Engine vs dump snapshot count | PASS | Engine=179 Dump=179 (OK) |

## Summary
| Metric | Value |
| --- | --- |
| Total checks run | 8 |
| Checks passed | 7 |
| Checks failed | 1 |
| Engine snapshots | 179 |
| Dump snapshots | 179 |
| Total trades | 895 |

## Conclusion
1 non-critical warning(s). Engine is usable but flagged items should be reviewed.

## Verdict Criteria (defined before results were examined)
| Verdict | Criteria |
| --- | --- |
| PASS | All checks pass |
| CONDITIONAL | <= 2 non-critical failures |
| FAIL | Any critical check fails or > 2 failures |

## Verdict
**CONDITIONAL** -- 1 non-critical warning(s).

## Research Impact
| Question | Answer |
| --- | --- |
| Does this change the model? | CONDITIONAL -- Review flagged items. |
| Does this change production? | NO -- Production system is separate. |
| Does this require rerunning previous studies? | NO -- This is Study 00. |

## Recommendation
Review warnings. Proceed to Study 01 with noted caveats.

## Next Study
**Study 01 -- Eligibility Audit:** Verifies that every stock was only
selected after accumulating 252 trading days of price history.