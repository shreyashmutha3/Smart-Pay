# SmartPay Reconciliation — Known Limitations & Production Risks

**Version:** 1.0

---

## 1. Architectural & Implementation Limitations

1. **In-Memory Run Store:**
   - Reconciliation runs and session records are stored in server memory (`RUNS_STORE`).
   - Runs do not survive server restarts. In production, this would be replaced with an ACID-compliant transactional datastore (e.g., PostgreSQL) with immutable audit logging.

2. **Single Calendar Month Run Scope:**
   - The reconciliation engine operates on a user-specified calendar month (with look-ahead into the following calendar month).
   - Multi-quarter or arbitrary multi-year continuous reconciliation rolling windows are not implemented in this version.

3. **Multi-Currency Segregation Without FX Conversion:**
   - The engine strictly isolates distinct currencies (e.g., `INR` and `USD`) to prevent erroneous mixed sums.
   - It does not fetch real-time or historical foreign exchange (FX) rates to present a consolidated multi-currency base ledger.

4. **Automated Accounting Posting:**
   - The system is an audit, matching, and discrepancy discovery tool. It does not initiate automated debit/credit ledger adjustments, payouts, or bank transfers.

---

## 2. Production Risks (Three Honest Failure Modes)

1. **Late, Revised, or Out-of-Sequence Bank Files:**
   Bank statement files may arrive after reporting deadlines, be revised retroactively by clearing partners, or contain inconsistent batch identifiers, causing valid transactions to be temporarily misclassified as missing settlements.

2. **Sub-Paise Precision & Fee Allocation Drift:**
   Variations between internal micro-fee calculations and gross clearing bank rounding rules can cause aggregate drift across high-volume pipelines unless explicit precision contracts and multi-tier fee reconciliation rules are enforced.

3. **Lineage Breakage in Multi-Hop Payment Routing:**
   When transactions undergo dispute escalations, partial refunds, or routing through intermediate payment aggregators, stable reference IDs can be stripped or truncated, requiring manual human investigation workflows rather than automated straight-through matching.
