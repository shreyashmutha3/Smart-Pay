# SmartPay Reconciliation Engine

A high-integrity payment reconciliation engine that bridges payment platform records and bank settlement files, deterministically explaining every discrepancy at month-end.

Built for the **Onelab AI Native Engineer Intern Assessment**.

---

## 1. Executive Summary

A payment platform records transactions in real-time upon processing, whereas acquiring banks batch and settle funds later (with a typical 2-day delay). At month-end, finance teams must reconcile internal platform records with bank settlement statements.

SmartPay implements a deterministic, auditable, and decimal-safe reconciliation engine that handles:

### The Four Mandatory Scenarios:
1. **Settled in Following Month (`SETTLED_NEXT_MONTH`):** A transaction processed in late October settles on November 2nd. The engine looks across the calendar boundary into the next month, links the records, and quantifies the timing difference rather than falsely flagging it as missing.
2. **Aggregate Rounding Difference (`AGGREGATE_ROUNDING_DIFFERENCE`):** Sub-paise fee sharing (e.g., three platform entries of `10.005` vs bank rounded postings of `10.00`) creates an aggregate drift of `0.015 INR` that only appears upon summation. The engine outputs reproducible arithmetic proof within a configurable `0.02 INR` tolerance.
3. **Duplicate Entry (`DUPLICATE_PLATFORM_RECORD` / `DUPLICATE_BANK_RECORD`):** Repeated events are identified and tagged with their source row number. Duplicate entries are isolated to prevent double-counting in canonical ledger totals, while preserving full audit provenance.
4. **Orphan Refund (`ORPHAN_REFUND`):** A platform refund references an `original_transaction_id` that cannot be found in the platform payment records. Flagged with high severity for investigation.

### Additional Edge Cases Detected:
- **`MISSING_SETTLEMENT`:** Platform payment with no bank credit within the look-ahead window.
- **`UNMATCHED_BANK_CREDIT`:** Bank statement credit with no corresponding platform transaction.
- **`AMOUNT_MISMATCH`:** Matching reference but differing amounts (e.g., unexpected bank processing fees).
- **`CURRENCY_MISMATCH`:** Matching reference but conflicting currencies (`USD` vs `INR`).
- **`POSSIBLE_MATCH_REQUIRES_REVIEW`:** Ambiguous matches (multiple bank credits for a single reference).
- **`INVALID_RECORD`:** Malformed CSV rows (unparseable dates, negative values, non-numeric amounts).

---

## 2. Technology Stack

- **Backend:** Python 3.10+, FastAPI, Uvicorn, Pydantic v2, Pytest, Httpx.
- **Financial Math:** Python `Decimal` (no binary float for monetary values; currencies strictly segregated).
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, Recharts.
- **Testing:** Pytest (backend) & Vitest (frontend).

---

## 3. Quick Start & Local Run Commands

### Prerequisites:
- Python 3.10 or higher
- Node.js 18 or higher (with npm)

### Backend Setup:
```powershell
# Option A: One-click script (Recommended)
.\run_backend.ps1

# Option B: Direct command using the project virtual environment
$env:PYTHONPATH="backend"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
*Backend runs at `http://localhost:8000`. API docs available at `http://localhost:8000/docs`.*

### Frontend Setup:
```bash
# 1. Navigate to frontend directory and install dependencies
cd frontend
npm install

# 2. Start the Vite development server
npm run dev
```
*Frontend runs at `http://localhost:5173` with automatic API proxying.*

---

## 4. Automated Test Commands & Results

### Backend Pytest Suite (25 Tests):
```powershell
$env:PYTHONPATH="backend"
.\.venv\Scripts\python.exe -m pytest backend/tests -v
```
**Actual Result: 25 / 25 PASSED in 1.33s**
- `test_t01_exact_match` through `test_t14_determinism`: All 14 core rules verified.
- 11 API integration tests: Health, validation, file upload, error responses, not-found routes, exports, and dynamic KPI calculations.

### Frontend Vitest Suite (6 Tests):
```bash
cd frontend
npm test
```
**Actual Result: 6 / 6 PASSED in 44ms**

### Frontend Production Build:
```bash
cd frontend
npm run build
```
**Actual Result: Built cleanly in 12.99s to `frontend/dist/`**

---

## 5. How to Reproduce Each Scenario in the UI

1. Open `http://localhost:5173`.
2. The UI automatically runs reconciliation using the deterministic dataset (`sample_data/`).
3. **Scenario 1 (Next-Month Settlement):**
   - Click the **"1. Settled Next Month"** card on the Dashboard or filter by `SETTLED_NEXT_MONTH` in the Investigation Centre.
   - Inspect transaction `TXN-NEXT-M01` (Row 24): platform processed on `2026-10-30`, bank settled on `2026-11-02`.
4. **Scenario 2 (Aggregate Rounding):**
   - Click the **"2. Aggregate Rounding"** card.
   - Inspect transactions `TXN-RND-001`, `002`, `003`: each has `10.005` in platform and `10.00` in bank. Summed platform is `30.015`, summed bank is `30.00`, giving net aggregate variance `0.015 INR`.
5. **Scenario 3 (Duplicate Records):**
   - Click the **"3. Duplicate Entries"** card.
   - Inspect `TXN-DUP-PLT-001` (Row 23) and `BNK-DUP-001B` (Row 26): both isolated as `Duplicate` with `included_in_totals = false`.
6. **Scenario 4 (Orphan Refund):**
   - Click the **"4. Orphan Refund"** card.
   - Inspect `TXN-ORPHAN-REF-001` (Row 27): refund referencing unrecorded parent `TXN-NONEXISTENT-999`.

---

## 6. Project Directory Structure

```text
smart_pay/
├── 01_PRD.md
├── 02_SYSTEM_ARCHITECTURE.md
├── 03_DATA_CONTRACTS_AND_RECONCILIATION_RULES.md
├── 04_IMPLEMENTATION_AND_TEST_PLAN.md
├── 05_AGENT_WORKING_RULES_AND_SUBMISSION.md
├── README.md
├── .env.example
├── sample_data/
│   ├── platform_transactions.csv
│   └── bank_settlements.csv
├── docs/
│   ├── assumptions.md
│   ├── data_dictionary.md
│   ├── architecture.md
│   ├── test_results.md
│   ├── known_limitations.md
│   └── prompts.md
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   └── routes.py
│   │   ├── models/
│   │   │   └── schemas.py
│   │   └── services/
│   │       ├── ingestion.py
│   │       ├── reconciliation.py
│   │       ├── export.py
│   │       └── data_generator.py
│   └── tests/
│       ├── test_reconciliation.py
│       └── test_api.py
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── tailwind.config.js
    ├── index.html
    └── src/
        ├── App.tsx
        ├── main.tsx
        ├── index.css
        ├── types/
        │   └── index.ts
        ├── api/
        │   └── client.ts
        ├── utils/
        │   ├── formatters.ts
        │   └── formatters.test.ts
        └── components/
            ├── Navbar.tsx
            ├── DashboardView.tsx
            ├── ReconciliationUploadView.tsx
            ├── InvestigationView.tsx
            └── ReportsView.tsx
```

---

## 7. Deployment Status

- **Status:** Configured for local execution and production containerization. Not deployed to a remote cloud host as no cloud provider credentials/hosting target were supplied.
- **Production Deployment Instructions:**
  - Build frontend static assets via `npm run build`.
  - Serve frontend via static CDN/Nginx or mount `frontend/dist` inside FastAPI.
  - Set `VITE_API_URL` to production API domain.
  - Run Uvicorn in production mode: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4`.

---

## 8. Production Risk Statement (3 Honest Sentences)

1. Bank settlement extracts can arrive delayed, out of order, or be retroactively amended across clearing cycles, causing valid transactions to be prematurely or incorrectly flagged as missing.
2. Minor precision discrepancies between internal fee split engines and external clearing bank rounding policies can aggregate into noticeable financial drift unless contractually bound by explicit rounding and allocation policies.
3. In multi-hop payment routing or dispute resolution lifecycles, transaction references can be stripped or truncated by intermediary payment aggregators, requiring structured human exception triage rather than fully automated straight-through processing.
