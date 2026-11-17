# SmartPay Reconciliation — Implementation Plan and Test Strategy

**Version:** 1.0

## 1. Build sequence

Build in vertical slices. Keep the application runnable after each slice.

### Phase 1 — Repository and contracts
- Create frontend and backend directories.
- Add README, environment example, and ignore rules.
- Define Pydantic request/response schemas.
- Implement CSV contracts and sample fixtures.
- Confirm local startup commands.

### Phase 2 — Deterministic sample data
- Create a fixed-seed generator.
- Generate platform and bank CSV files.
- Include every mandatory assessment scenario.
- Create a machine-readable expected-results fixture for tests.

### Phase 3 — Backend reconciliation
- Implement parsing and validation.
- Implement decimal-safe normalization.
- Implement duplicate grouping and canonicalization.
- Implement reference matching and amount validation.
- Implement next-month look-ahead.
- Implement refund-to-original validation.
- Implement aggregate rounding analysis.
- Implement additional exception types.
- Return traceable results with reason codes.

### Phase 4 — API and exports
- Add `/health`, `/validate`, `/sample-data`, and `/reconcile`.
- Add CSV export for reconciliation and exceptions.
- Add structured errors and useful logs.
- Add API tests.

### Phase 5 — Frontend
- Add application shell and navigation.
- Add data upload and sample-data selection.
- Add reporting-month selector.
- Add dashboard cards and charts driven by API data.
- Add searchable/filterable investigation table.
- Add exception detail view.
- Add CSV export actions.
- Add loading, empty, and error states.

### Phase 6 — Verification
- Run backend tests.
- Run frontend tests and lint/build.
- Manually verify sample-data workflow.
- Verify exports against visible results.
- Fix all critical issues.
- Document known limitations.

### Phase 7 — Submission and deployment
- Deploy backend and frontend.
- Configure production API URL and CORS.
- Verify deployed health and end-to-end workflow.
- Create source ZIP without secrets or dependencies.
- Record demo video.
- Preserve actual AI conversations and execution logs.

## 2. Backend test cases

| ID | Scenario | Expected result |
|---|---|---|
| T01 | Exact reference, amount, currency and valid settlement date | Confirmed match |
| T02 | Settlement occurs two days after payment | Confirmed match |
| T03 | Payment on last day of month, settlement in following month | `SETTLED_NEXT_MONTH` |
| T04 | Aggregate-only small precision/rounding variance | `AGGREGATE_ROUNDING_DIFFERENCE`, with arithmetic evidence |
| T05 | Duplicate platform row | `DUPLICATE_PLATFORM_RECORD`; canonical total counts once |
| T06 | Duplicate bank row | `DUPLICATE_BANK_RECORD`; canonical total counts once |
| T07 | Refund has no original payment reference target | `ORPHAN_REFUND` |
| T08 | Payment has no settlement in look-ahead window | `MISSING_SETTLEMENT` |
| T09 | Reference matches but amount differs | `AMOUNT_MISMATCH` |
| T10 | Bank credit has no platform record | `UNMATCHED_BANK_CREDIT` |
| T11 | Reference matches but currency differs | `CURRENCY_MISMATCH` |
| T12 | Invalid date or malformed amount | Validation error with source row |
| T13 | Two possible bank matches for one platform reference | Ambiguous/duplicate review; no arbitrary auto-match |
| T14 | Same inputs and configuration run twice | Identical classifications and totals, excluding run metadata |

## 3. Aggregate rounding test design

The test must prove a difference that appears at aggregate level and must not be a disguised missing transaction.

Example fixture (analytical precision test):
- Platform amounts: `10.005`, `10.005`, `10.005`
- Bank posted amounts: `10.00`, `10.00`, `10.00`
- Platform aggregate: `30.015`
- Bank aggregate: `30.00`
- Aggregate variance: `0.015`

The implementation must state the rounding policy. This fixture is an intentionally simplified precision scenario; do not imply that a bank necessarily posts sub-minor-unit INR amounts. A more realistic fixture may use per-row fee/tax allocation and a documented rounding method.

Test that:
- All references are present.
- No row is missing or duplicated.
- The variance is within configured tolerance.
- The result shows the exact arithmetic and tolerance.
- Individual rows are not falsely marked as missing.

## 4. Frontend verification checklist

- Upload valid CSVs.
- Reject malformed CSV with understandable feedback.
- Load generated sample dataset.
- Select a reporting month and run reconciliation.
- Dashboard metrics match API response.
- Filter exceptions by category.
- Search by transaction reference.
- Open an exception and inspect evidence.
- Export results and open the CSV.
- Confirm no hard-coded example numbers remain in live dashboard.
- Confirm responsive layout at desktop and mobile widths.

## 5. Definition of done

A feature is done only when:
- Implementation exists.
- Error and edge cases are handled.
- Automated test exists where applicable.
- UI/API behavior has been manually verified where applicable.
- Documentation is updated.
- No unverified claim is made in the README or demo.

## 6. Time-boxed priority for a two-hour assessment

If time is constrained, prioritize:
1. Correct sample data and deterministic backend engine.
2. Tests for all four mandatory gap types.
3. Working API and simple but functional dashboard.
4. Investigation table and CSV export.
5. Deployment and demo only after local functionality works.

Do not sacrifice financial correctness to add animations, an LLM chat feature, elaborate microservices, or unnecessary authentication.

## 7. Production limitations to disclose

Potential production risks include late or revised bank files, ambiguous references, timezone/currency/rounding policy differences, duplicate ingestion, incomplete refund lineage, concurrent runs, access control, data retention, and audit requirements. The demo should not claim production readiness.
