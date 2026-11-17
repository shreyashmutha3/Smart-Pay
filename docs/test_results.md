# SmartPay Reconciliation — Automated Test Results

**Date:** November 17, 2026  
**Test Suites:** Backend Pytest (25 tests) & Frontend Vitest (6 tests)  
**Overall Status:** **31 / 31 PASSED (100%)**

---

## 1. Backend Pytest Suite

```text
============================= test session starts =============================
platform win32 -- Python 3.10.11, pytest-9.2.0, pluggy-1.7.0
plugins: anyio-4.16.0
collected 25 items

backend/tests/test_api.py::test_api_health PASSED                        [  4%]
backend/tests/test_api.py::test_api_sample_data PASSED                   [  8%]
backend/tests/test_api.py::test_api_validate_sample_data PASSED          [ 12%]
backend/tests/test_api.py::test_api_validate_missing_files_error PASSED  [ 16%]
backend/tests/test_api.py::test_api_validate_malformed_csv_missing_columns PASSED [ 20%]
backend/tests/test_api.py::test_api_validate_invalid_rows PASSED         [ 24%]
backend/tests/test_api.py::test_api_reconcile_sample_data_and_verify_scenarios PASSED [ 28%]
backend/tests/test_api.py::test_api_reconcile_file_upload PASSED         [ 32%]
backend/tests/test_api.py::test_api_reconcile_invalid_period PASSED      [ 36%]
backend/tests/test_api.py::test_api_not_found_endpoints PASSED           [ 40%]
backend/tests/test_api.py::test_financial_integrity_dynamic_metrics PASSED [ 44%]
backend/tests/test_reconciliation.py::test_t01_exact_match PASSED        [ 48%]
backend/tests/test_reconciliation.py::test_t02_two_day_lag_settlement PASSED [ 52%]
backend/tests/test_reconciliation.py::test_t03_settled_next_month PASSED [ 56%]
backend/tests/test_reconciliation.py::test_t04_aggregate_rounding_difference PASSED [ 60%]
backend/tests/test_reconciliation.py::test_t05_duplicate_platform_row PASSED [ 64%]
backend/tests/test_reconciliation.py::test_t06_duplicate_bank_row PASSED [ 68%]
backend/tests/test_reconciliation.py::test_t07_orphan_refund PASSED      [ 72%]
backend/tests/test_reconciliation.py::test_t08_missing_settlement PASSED [ 76%]
backend/tests/test_reconciliation.py::test_t09_amount_mismatch PASSED    [ 80%]
backend/tests/test_reconciliation.py::test_t10_unmatched_bank_credit PASSED [ 84%]
backend/tests/test_reconciliation.py::test_t11_currency_mismatch PASSED  [ 88%]
backend/tests/test_reconciliation.py::test_t12_validation_error_handling PASSED [ 92%]
backend/tests/test_reconciliation.py::test_t13_ambiguous_matches PASSED  [ 96%]
backend/tests/test_reconciliation.py::test_t14_determinism PASSED        [100%]

============================= 25 passed in 1.33s ==============================
```

---

## 2. Core Scenario Verification Matrix

| Test ID | Scenario | Status | Verified Outcome |
|---|---|---|---|
| **T01** | Standard 1:1 Match | **PASSED** | Exact reference, date, amount, currency matched with 0 variance. |
| **T02** | 2-Day Batch Delay | **PASSED** | Confirmed match for payment on 2026-10-02 settling 2026-10-04. |
| **T03** | Mandatory: Settled Next Month | **PASSED** | Payment on 2026-10-30 settling 2026-11-02 linked as `SETTLED_NEXT_MONTH` via look-ahead window. |
| **T04** | Mandatory: Aggregate Rounding | **PASSED** | 3 payments of 10.005 vs bank 10.00 detected with net aggregate variance = 0.015 INR. |
| **T05** | Mandatory: Duplicate Platform | **PASSED** | Row 22 canonical; row 23 flagged `DUPLICATE_PLATFORM_RECORD`; 1500.00 counted once. |
| **T06** | Mandatory: Duplicate Bank | **PASSED** | Statement line `BNK-DUP-001B` flagged `DUPLICATE_BANK_RECORD`; excluded from canonical. |
| **T07** | Mandatory: Orphan Refund | **PASSED** | Refund `TXN-ORPHAN-REF-001` targeting non-existent parent flagged `ORPHAN_REFUND`. |
| **T08** | Missing Settlement | **PASSED** | Platform payment `TXN-MISSING-001` flagged `MISSING_SETTLEMENT`. |
| **T09** | Amount Mismatch | **PASSED** | Difference of 99.00 INR correctly detected and quantified. |
| **T10** | Unmatched Bank Credit | **PASSED** | Unknown bank credit `BNK-UNMATCHED-001` flagged `UNMATCHED_BANK_CREDIT`. |
| **T11** | Currency Mismatch | **PASSED** | Platform in `USD` vs bank in `INR` flagged `CURRENCY_MISMATCH`. |
| **T12** | Semantic Row Validation | **PASSED** | Rejects non-numeric amounts and malformed dates with row references. |
| **T13** | Ambiguous Matches | **PASSED** | Multiple bank credits flagged `POSSIBLE_MATCH_REQUIRES_REVIEW` (no auto-confirm). |
| **T14** | Determinism Test | **PASSED** | Consecutive runs with identical inputs produce bit-identical ledger results. |

---

## 3. Frontend Vitest Suite

```text
> smartpay-frontend@1.0.0 test
> vitest run

 RUN  v1.6.1 frontend

 ✓ src/utils/formatters.test.ts  (6 tests) 44ms

 Test Files  1 passed (1)
      Tests  6 passed (6)
   Duration  2.69s
```
