# SmartPay Reconciliation — Product Requirements Document (PRD)

**Version:** 1.0  
**Purpose:** Build a working payment reconciliation application for the Onelab AI Native Engineer Intern assessment.

## 1. Product summary

SmartPay Reconciliation compares payment-platform transaction records with bank settlement records and explains why they do not balance at month-end.

The application must do more than compare totals. It must identify transaction-level matches, classify discrepancies, quantify their financial impact, and provide evidence that an operator can investigate.

## 2. Problem statement

A payment platform records a customer payment when it is processed. The bank batches and settles the funds later (the assessment describes a typical two-day delay). At month-end, every transaction should have a corresponding settlement, but the platform and bank records may differ.

The assessment explicitly requires these four gap types:

1. A transaction that settled in the following month.
2. A rounding difference that only appears when amounts are summed.
3. A duplicate entry in one dataset.
4. A refund with no matching original transaction.

No source files are supplied. The application must generate its own synthetic test data and clearly state its assumptions.

## 3. Goals

- Reconcile platform transactions against bank settlements.
- Identify and explain the four mandatory gap types.
- Identify useful additional cases such as missing settlements and amount mismatches.
- Make results reproducible and auditable.
- Allow users to upload CSV files or use generated sample data.
- Present a clear dashboard and transaction-level investigation view.
- Provide automated tests and exportable results.

## 4. Non-goals

For this assessment, do not build:
- A real bank integration or payment initiation system.
- A production-grade accounting ledger.
- Automated refunds, payouts, or journal postings.
- An LLM-based financial matching decision-maker.
- Multi-tenant enterprise identity management.
- A complex distributed microservice architecture.

AI may optionally summarize already-computed findings, but deterministic code must make all matching and financial decisions.

## 5. Users and primary user stories

### Finance / reconciliation analyst
- As an analyst, I can upload platform and bank CSVs so I can reconcile a selected period.
- As an analyst, I can see matched, unmatched, duplicate, late, rounding, and refund exceptions.
- As an analyst, I can open an exception and see the records and rule that caused it.
- As an analyst, I can export results for review.

### Engineering / assessment reviewer
- As a reviewer, I can run the app locally from documented instructions.
- As a reviewer, I can load deterministic sample data and reproduce all mandatory scenarios.
- As a reviewer, I can run automated tests and inspect assumptions and limitations.

## 6. Functional requirements

### FR-01: Data ingestion
- Accept platform transaction CSV and bank settlement CSV.
- Validate required columns, data types, dates, currency, and amount formats.
- Show actionable validation errors; do not silently drop malformed rows.
- Preserve original row numbers and source record identifiers for traceability.
- Provide a generated sample-data option.

### FR-02: Reconciliation run
- Allow a user to choose a reporting month.
- Reconcile records for that month while looking into the following month for late settlements.
- Produce a run identifier, timestamp, input row counts, and summary totals.
- Keep the original input records unchanged.

### FR-03: Matching
- Match using stable transaction references where available.
- Validate amount, currency, direction/type, and settlement date separately.
- Do not treat an ID match with a wrong amount as a successful financial match.
- Avoid many-to-many or ambiguous matches. Mark ambiguous cases for review.

### FR-04: Mandatory exception detection
- **Next-month settlement:** platform payment belongs to reporting month, but matching bank settlement is dated in the next calendar month.
- **Aggregate rounding:** individual amounts may be rounded or represented at a different precision; detect a small aggregate difference after grouping comparable records. Do not label arbitrary unexplained differences as rounding.
- **Duplicate:** repeated business record in either dataset. Identify duplicate rows and count their financial impact only once in the canonical reconciliation totals.
- **Orphan refund:** refund references an original payment that cannot be found in the available platform records.

### FR-05: Additional exception detection
- Platform payment with no bank settlement in the searched settlement window.
- Bank credit with no matching platform payment.
- Reference matched but amount differs.
- Currency mismatch.
- Invalid or unsupported record type.
- Ambiguous candidate matches.

### FR-06: Investigation UI
Each exception should show:
- Exception category and severity.
- Platform record and/or bank record details.
- Reference IDs.
- Amounts and currencies.
- Transaction and settlement dates.
- Rule/reason explanation.
- Financial impact and whether it is included in totals.
- Suggested next investigation action (informational only).

### FR-07: Dashboard
Show:
- Platform transaction count and amount.
- Bank settlement count and amount.
- Matched count and amount.
- Unmatched count and amount.
- Exception count by category.
- Reconciliation rate, with the denominator clearly defined.
- Net difference and reporting period.
- Clear indication that sample data is synthetic.

### FR-08: Export
- Export transaction-level reconciliation results to CSV.
- Export exception report to CSV.
- Include run ID, reporting period, category, reason, references, amounts, and dates.

## 7. Quality requirements

- Financial arithmetic uses decimal-safe representation (Python `Decimal` or integer minor units); never binary float for money calculations.
- All dates are parsed consistently and timezone assumptions are documented.
- Deterministic output for the same input files and configuration.
- Useful logging without exposing sensitive data.
- Backend validation and structured error responses.
- Responsive and accessible UI.
- No fake success states or hard-coded dashboard metrics.
- Tests cover all mandatory cases and normal matching.

## 8. Acceptance criteria

The product is acceptable when:
1. It starts locally using README instructions.
2. A user can load generated sample data and run a reconciliation.
3. All four mandatory gap types are represented in sample data and correctly classified.
4. The following-month settlement is found by looking beyond the month boundary.
5. Aggregate rounding is distinguished from a missing transaction and is supported by a reproducible calculation.
6. Duplicate records are identified and are not double-counted in canonical totals.
7. Orphan refunds are identified by a missing original-payment reference.
8. Additional missing/amount-mismatch cases are tested.
9. The dashboard is populated from actual backend results, not static mock values.
10. CSV exports contain the same results shown in the UI.
11. Automated tests pass and test instructions are documented.
12. Assumptions and known limitations are disclosed.

## 9. Assessment submission outputs

Prepare:
- Full brainstorming conversation (retain wrong turns).
- Distilled prompt and exact raw prompt sent to the coding agent.
- Full Antigravity execution conversation/log (retain failed attempts and corrections).
- Test cases and actual test results.
- Working deployed link.
- Source-code ZIP.
- Demo video.
- Exactly three concise sentences describing what could go wrong in production.

Do not fabricate a deployment, test result, or conversation history. Capture these from the actual work performed.
