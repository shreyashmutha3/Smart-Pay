# SmartPay Reconciliation — System Architecture

**Version:** 1.0

---

## 1. System Overview

```
   ┌──────────────────────────────────────────────────────────────┐
   │                  React + TypeScript + Vite                   │
   │   Tailwind CSS • Lucide Icons • Recharts Financial Graphs    │
   └───────────────┬──────────────────────────────▲───────────────┘
                   │                              │
      HTTP Upload  │                              │ JSON Results &
      & Run Params │                              │ CSV Streams
                   ▼                              │
   ┌──────────────────────────────────────────────┴───────────────┐
   │                   FastAPI Backend Application                │
   │                                                              │
   │  ┌───────────────────────┐    ┌───────────────────────────┐  │
   │  │   Ingestion & Schema  │    │   Deterministic Engine    │  │
   │  │   Validation Layer    │───►│   - Duplicate Grouping    │  │
   │  │   (Source File & Row) │    │   - Stable Ref Matching   │  │
   │  └───────────────────────┘    │   - Look-ahead Window     │  │
   │                               │   - Refund Lineage Target │  │
   │  ┌───────────────────────┐    │   - Aggregate Rounding    │  │
   │  │   Decimal Normalizer  │    └─────────────┬─────────────┘  │
   │  │   & UTC Parser        │                  │                │
   │  └───────────────────────┘                  ▼                │
   │                               ┌───────────────────────────┐  │
   │  ┌───────────────────────┐    │   Financial Aggregator    │  │
   │  │   In-Memory Run Store │◄───│   - Currency Segregation  │  │
   │  │   & CSV Exporters     │    │   - Canonical Totaling    │  │
   │  └───────────────────────┘    │   - Exact Rate Formula    │  │
   │                               └───────────────────────────┘  │
   └──────────────────────────────────────────────────────────────┘
```

---

## 2. Component Design

### Frontend (`frontend/`)
- **Technology:** React 18, TypeScript 5, Vite 5, Tailwind CSS, Recharts.
- **Views:**
  - `DashboardView`: Real-time KPI summary cards, status distribution bar charts, exception severity pie charts, and period selectors.
  - `ReconciliationUploadView`: 1-click synthetic dataset loader, custom drag-and-drop CSV upload, tolerance slider, and actionable validation feedback.
  - `InvestigationView`: Audit centre featuring global fuzzy/exact search, multi-factor category/severity/canonical filters, and a side-by-side transaction audit drawer.
  - `ReportsView`: One-click streaming download of complete results CSV and exceptions-only CSV.

### Backend (`backend/`)
- **Framework:** FastAPI with Uvicorn.
- **Layered Services:**
  - `ingestion.py`: CSV schema validation, non-empty checks, preserving original row numbers and raw payloads.
  - `reconciliation.py`: Core matching logic:
    1. Duplicate detection: platform and bank duplicates isolated before canonical calculation.
    2. Reference matching & look-ahead: searches next calendar month for delayed bank batches (`SETTLED_NEXT_MONTH`).
    3. Aggregate rounding detection: computes exact arithmetic proof across comparable canonical sets.
    4. Refund tracing: verifies `original_transaction_id` existence to flag `ORPHAN_REFUND`.
    5. Discrepancy classification: `MISSING_SETTLEMENT`, `UNMATCHED_BANK_CREDIT`, `AMOUNT_MISMATCH`, `CURRENCY_MISMATCH`.
  - `data_generator.py`: Fixed seed (42) generator producing 34 platform transactions and 33 bank entries covering all scenarios.
  - `export.py`: Audit-ready CSV streaming generator.

---

## 3. Data Integrity Principles
1. **Never Float:** Python `Decimal` is enforced across all math operations.
2. **Never Double Count:** Non-canonical rows are segregated with `included_in_totals = False`.
3. **Never Mix Currencies:** Every currency is isolated into its own `CurrencySummary`.
4. **Never Guess Matches:** Fuzzy or ambiguous records are placed in `POSSIBLE_MATCH_REQUIRES_REVIEW`.
