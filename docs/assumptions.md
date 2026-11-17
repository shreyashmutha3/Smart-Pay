# SmartPay Reconciliation — Accounting & System Assumptions

**Version:** 1.0  
**Context:** Onelab AI Native Engineer Intern Assessment

---

## 1. Timing & Look-Ahead Window
- **Typical 2-Day Batch Delay:** As specified in the assessment brief, payment gateways record transactions immediately while acquiring banks settle in batches (typically with a 2-day delay).
- **Calendar Boundary Handling:** Transactions occurring on the final days of a reporting month (e.g., October 30–31) will naturally settle in the subsequent calendar month (November 2–3). Rather than classifying these as missing settlements, the engine searches through the end of the next calendar month.
- **Settlement Classification:** Records linked across the monthly boundary are explicitly labeled `SETTLED_NEXT_MONTH` and quantified as timing differences, not balance deficits.

---

## 2. Monetary Precision & Currency Segregation
- **Decimal Safety:** All financial math is conducted strictly using Python `Decimal`. Binary floating-point representation (`float`) is barred from authoritative monetary calculations to prevent binary rounding inaccuracies.
- **Currency Isolation:** Transactions in different currencies (e.g., `INR` vs `USD`) are strictly segregated into distinct reconciliation buckets and metrics. Currencies are **never** combined into a single total.
- **Minor Units & Precision:** Standard INR precision is two decimal places. In analytical test fixtures simulating micro-fee allocations, fractional paise (3 decimal places, e.g. `10.005`) are evaluated against bank rounded postings (`10.00`) to test aggregate precision drift.

---

## 3. Aggregate Rounding Difference Rules
- **Condition:** Occurs only when 1:1 reference linkage is verified across a comparable population, but individual fractional rounding causes the summed platform total and summed bank total to diverge.
- **Configurable Tolerance:** Default threshold is configured to `0.02 INR`.
- **Explainability:** The engine exposes the exact formula: `Sum(Platform) - Sum(Bank) = Variance`, the count of records in the population, and the configured tolerance. Arbitrary unexplained differences are never labeled as rounding.

---

## 4. Duplicate Record Handling & Ledger Integrity
- **Platform Duplicates:** Detected when `transaction_id` is repeated.
- **Bank Duplicates:** Detected when `bank_entry_id` is repeated or when `(transaction_reference, amount, currency, settlement_timestamp)` matches an existing credit.
- **Canonical Ledger Treatment:** The first encountered record is designated `is_canonical = True` and counted in gross/net/matched totals. Subsequent occurrences are marked `is_canonical = False` and `included_in_totals = False`.
- **Audit Preservation:** Duplicate rows are **never** silently dropped. They are preserved, linked to their original file row numbers, presented in the Investigation Centre, and exported with quantified overstatement risk.

---

## 5. Refund Lineage
- **Target Linkage:** Platform refunds must supply an `original_transaction_id` pointing to an existing canonical platform payment.
- **Orphan Refunds:** Refunds missing this reference or referencing an unrecorded transaction are classified as `ORPHAN_REFUND` with a financial impact equal to the refund amount. The engine never guesses or invents an original payment.

---

## 6. Persistence & State
- **Session Lifespan:** Reconciliation runs and uploaded files are maintained in-memory for the demo session. Runs do not survive server restarts.
