# SmartPay Reconciliation — Data Contracts and Reconciliation Rules

**Version:** 1.0  
**Important:** The assessment supplies no input files or formal schema. The schemas and rules below are explicit implementation assumptions and must be documented in the application.

## 1. Input CSV contracts

### Platform transactions CSV

Required columns:

| Column | Type | Meaning |
|---|---|---|
| `transaction_id` | string | Unique platform event/record ID |
| `original_transaction_id` | string, nullable | Original payment reference for a refund |
| `transaction_type` | enum | `PAYMENT` or `REFUND` |
| `amount` | decimal string | Signed or unsigned amount; see convention below |
| `currency` | ISO-like currency code | For example `INR` |
| `transaction_timestamp` | ISO-8601 datetime | When platform recorded the event |
| `status` | enum/string | For example `SUCCESS`, `REFUNDED` |
| `merchant_reference` | string, nullable | Optional business reference |

### Bank settlements CSV

Required columns:

| Column | Type | Meaning |
|---|---|---|
| `bank_entry_id` | string | Unique bank statement row ID |
| `transaction_reference` | string | Reference to platform transaction |
| `entry_type` | enum | `CREDIT`, `DEBIT`, `REFUND`, or documented equivalent |
| `amount` | decimal string | Settlement amount |
| `currency` | ISO-like currency code | For example `INR` |
| `settlement_timestamp` | ISO-8601 datetime | When funds settled |
| `batch_id` | string, nullable | Bank settlement batch |
| `description` | string, nullable | Bank narrative |

## 2. Money and sign conventions

Choose and consistently implement one convention:
- Platform `PAYMENT` amount is positive.
- Platform `REFUND` amount is positive in the source data but represents an outflow; normalize it to a negative signed amount.
- Bank `CREDIT` is positive.
- Bank `DEBIT` / `REFUND` is negative.

All amounts must be parsed using `Decimal`. Do not use binary floating point for currency calculations.

Currency precision is currency-specific. For INR, standard minor-unit precision is two decimal places. Keep source precision for analysis if the synthetic test intentionally includes sub-paise values; document that such values are analytical test inputs and not necessarily valid bank-posted INR amounts.

## 3. Dates and reporting window

- Reporting period is a calendar month in a configured business timezone.
- Store and compare timestamps consistently; preferably parse ISO-8601 offsets and normalize internally to UTC.
- For a reporting month, include platform transactions whose transaction timestamp falls within that month.
- Search bank settlements through at least the end of the following calendar month for late-settlement detection.
- The assessment says settlements typically occur two days later. Treat this as a sample-data assumption, not a universal guarantee.
- A bank settlement dated in the next month is a `SETTLED_NEXT_MONTH` exception, not a permanently missing payment.
- If no matching settlement is found within the configured look-ahead window, classify as `MISSING_SETTLEMENT` or `PENDING_SETTLEMENT` according to the documented policy.

## 4. Duplicate detection

Detect duplicates independently in each source before matching.

Preferred duplicate key:
- Platform: `transaction_id` plus material business fields, or a repeated `transaction_id` with conflicting payloads flagged as a duplicate/conflict.
- Bank: `bank_entry_id` for repeated identical statement rows; additionally detect repeated `transaction_reference` + amount + currency + settlement date when bank IDs differ.

Do not silently delete duplicates. Preserve every row and mark:
- canonical row
- duplicate row(s)
- duplicate group key
- whether the duplicate has identical or conflicting content

For canonical financial totals, count a duplicate business event once. Show the duplicate row separately as an exception and disclose the treatment.

## 5. Matching order

Recommended deterministic order:

1. Parse and validate both datasets.
2. Identify duplicates and establish canonical records.
3. Separate payment and refund records.
4. Match exact normalized transaction references.
5. Validate currency and signed amount.
6. Validate date window and settlement timing.
7. Search following-month bank records for unmatched in-month payments.
8. Match refund records to original payments using `original_transaction_id`.
9. Identify orphan refunds and unmatched bank entries.
10. Calculate aggregate rounding variance on comparable canonical populations.
11. Produce summary totals and exception results.

Do not use fuzzy matching to auto-confirm a financial match. If a possible match is inferred from amount/date/description, label it `POSSIBLE_MATCH_REQUIRES_REVIEW`.

## 6. Mandatory exception rules

### A. `SETTLED_NEXT_MONTH`
Condition:
- Platform payment transaction date is within the reporting month.
- A bank settlement with the same reference and currency is found in the following month.
- Amount and direction are compatible.

Result:
- Link both records.
- Mark the payment as late/next-month settled.
- Include the amount in the reporting-period timing explanation.
- Do not also count it as an unmatched payment.

### B. `AGGREGATE_ROUNDING_DIFFERENCE`
Condition:
- Compare totals for the same currency, transaction population, direction, and settlement scope.
- The aggregate difference is within a configurable small tolerance.
- The difference is explainable by documented per-record rounding or precision conversion.
- Individual reference matching has not revealed a substantive missing/duplicate/amount exception that explains the same variance.

Result:
- Report source total, bank total, variance, tolerance, population count, and calculation.
- Do not mark unrelated transactions as matched solely because the total is close.
- Do not call every small unexplained difference “rounding.”

Suggested initial tolerance for a demo: configurable `0.02` in INR, but label this as an assumption and make it configurable. The test fixture should deliberately produce a reproducible aggregate-only variance.

### C. `DUPLICATE_PLATFORM_RECORD` / `DUPLICATE_BANK_RECORD`
Condition:
- A duplicate group is found according to the documented keys above.

Result:
- Identify all duplicate rows and the canonical row.
- Explain whether values are identical or conflicting.
- Avoid double-counting duplicates in canonical totals.
- Quantify potential overstatement if the duplicate were counted.

### D. `ORPHAN_REFUND`
Condition:
- Platform record is a refund.
- `original_transaction_id` is missing or does not resolve to a known original payment in the available data.

Result:
- Flag refund and reference (or missing reference).
- State that the original payment cannot be found in the supplied platform records.
- Do not invent a matching payment.

## 7. Additional exception codes

- `MISSING_SETTLEMENT`: platform payment has no bank settlement in the search window.
- `UNMATCHED_BANK_CREDIT`: bank credit has no platform payment.
- `AMOUNT_MISMATCH`: reference matches but signed amount differs.
- `CURRENCY_MISMATCH`: reference matches but currency differs.
- `INVALID_RECORD`: row fails schema or semantic validation.
- `POSSIBLE_MATCH_REQUIRES_REVIEW`: candidate is not sufficiently certain for automatic matching.
- `DUPLICATE_CONFLICT`: repeated reference has materially different content.

## 8. Financial calculations and definitions

Clearly define every dashboard metric.

Suggested definitions:
- `platform_gross`: sum of canonical successful platform payments in the reporting month, before refunds unless separately stated.
- `bank_settled_gross`: sum of matching canonical bank credits for the relevant payment population.
- `matched_amount`: sum of amounts from confirmed, amount-valid matches.
- `unmatched_platform_amount`: canonical platform payment amount with no confirmed settlement in the search window.
- `unmatched_bank_amount`: canonical bank credit amount with no confirmed platform transaction.
- `net_variance`: comparable platform amount minus comparable bank amount. Do not mix currencies.
- `match_rate`: confirmed matched canonical platform payment count divided by eligible canonical platform payment count. Show numerator and denominator.

Do not add amounts in different currencies. Provide per-currency summaries.

## 9. Synthetic dataset requirements

Generate deterministic data using a fixed random seed. Include at least:
- 10 ordinary exact matches.
- 2 next-month settlements.
- A small aggregate rounding case with documented arithmetic.
- 1 duplicate platform row.
- 1 duplicate bank row.
- 1 orphan refund.
- 1 missing settlement.
- 1 amount mismatch.
- 1 unmatched bank credit.

Ensure the sample data has enough rows to demonstrate useful dashboard charts. Include a data dictionary and known expected classifications so tests can assert outcomes.
