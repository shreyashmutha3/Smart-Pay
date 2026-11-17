# SmartPay Reconciliation — Engineering Prompts & Execution Record

**Version:** 1.0

---

## 1. Distilled Prompt

```text
Act as a senior full-stack engineer and technical lead. Build a payment reconciliation application using FastAPI (Python Decimal) and React (Vite + TypeScript + Tailwind CSS + Recharts). Ingest platform transaction CSV and bank settlement CSV files (with typical 2-day batch settlement delay). Reconcile month-end records deterministically, segregating currencies and preserving complete row provenance.

Demonstrate and verify all four mandatory gap scenarios:
1. Transaction settled in the following month (look-ahead window).
2. Aggregate rounding difference appearing only upon summation.
3. Duplicate business entry in one dataset (canonical total counted once).
4. Orphan refund with no matching original transaction.

Also detect missing settlements, unmatched bank credits, amount mismatches, and currency mismatches. Provide an executive dashboard with dynamic KPIs, a searchable/filterable Investigation Centre with side-by-side evidence inspection, CSV exports, automated backend and frontend tests, and comprehensive audit documentation.
```

---

## 2. Exact Raw Master Prompt

```text
MASTER PROMPT — Google Antigravity
Act as a senior full-stack engineer, technical lead, and careful financial-systems reviewer. Build the complete SmartPay Reconciliation application in the currently open workspace.
First: read the project documents
Before coding, read these files completely:
- 01_PRD.md
- 02_SYSTEM_ARCHITECTURE.md
- 03_DATA_CONTRACTS_AND_RECONCILIATION_RULES.md
- 04_IMPLEMENTATION_AND_TEST_PLAN.md
- 05_AGENT_WORKING_RULES_AND_SUBMISSION.md
Treat them as the project specification. The assessment brief takes precedence if any detail conflicts. The assessment supplies no data files, so generate deterministic synthetic data and clearly label assumptions.
Product objective
A payment platform records transactions immediately. The bank batches and settles funds later (typically two days after payment, according to the assessment scenario). At month-end, reconcile platform transactions with bank settlement records and explain every gap.

The four mandatory cases are:
1. A transaction settled in the following month.
2. A rounding difference that only becomes visible when amounts are summed.
3. A duplicate entry in one dataset.
4. A refund with no matching original transaction.
Also support useful additional cases: missing settlement, unmatched bank credit, amount mismatch, currency mismatch, invalid records, and ambiguous matches.
Required stack
- Frontend: React + TypeScript + Vite.
- UI: Tailwind CSS and shadcn/ui (or equivalent accessible components).
- Charts: Recharts.
- Backend: Python + FastAPI.
- Data handling: Pandas where useful.
- Money: Python Decimal or integer minor units. Never use binary float for authoritative money calculations.
- Tests: Pytest for backend; Vitest or equivalent for frontend.
- Keep deployment configuration straightforward.
Do not add a database unless it materially improves the working assessment deliverable. If using in-memory storage, disclose that runs do not survive server restarts.
...
```
