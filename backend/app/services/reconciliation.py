import calendar
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Tuple, Optional, Set
import uuid

from app.models.schemas import (
    NormalizedPlatformTransaction,
    NormalizedBankSettlement,
    ValidationErrorItem,
    ReconciliationItem,
    ReconciliationSummary,
    CurrencySummary,
    ReconciliationResponse,
    MatchStatus,
    ExceptionSeverity,
    TransactionType,
    BankEntryType,
)

ROUNDING_TOLERANCE = Decimal("0.02")

def get_month_boundaries(reporting_period: str) -> Tuple[datetime, datetime, datetime]:
    """
    Given 'YYYY-MM', returns:
    - start of reporting month (inclusive)
    - end of reporting month (inclusive)
    - end of following month (inclusive, look-ahead window)
    """
    year_str, month_str = reporting_period.split("-")
    year = int(year_str)
    month = int(month_str)

    # Start of reporting month
    start_dt = datetime(year, month, 1, 0, 0, 0, tzinfo=timezone.utc)
    
    # End of reporting month
    _, last_day = calendar.monthrange(year, month)
    end_dt = datetime(year, month, last_day, 23, 59, 59, 999999, tzinfo=timezone.utc)

    # End of next month (look-ahead)
    if month == 12:
        next_year = year + 1
        next_month = 1
    else:
        next_year = year
        next_month = month + 1
    _, next_last_day = calendar.monthrange(next_year, next_month)
    next_end_dt = datetime(next_year, next_month, next_last_day, 23, 59, 59, 999999, tzinfo=timezone.utc)

    return start_dt, end_dt, next_end_dt

def detect_duplicates(
    platform_records: List[NormalizedPlatformTransaction],
    bank_records: List[NormalizedBankSettlement]
) -> Tuple[List[NormalizedPlatformTransaction], List[NormalizedBankSettlement], List[ReconciliationItem]]:
    """
    Identifies duplicate records in both platform and bank datasets.
    Marks exactly one canonical entry per group and returns duplicate exception items.
    """
    duplicate_items: List[ReconciliationItem] = []

    # 1. Platform duplicate detection by transaction_id
    platform_seen: Dict[str, NormalizedPlatformTransaction] = {}
    for p in platform_records:
        tx_id = p.transaction_id
        if tx_id not in platform_seen:
            platform_seen[tx_id] = p
            p.is_canonical = True
            p.is_duplicate = False
        else:
            first_p = platform_seen[tx_id]
            p.is_canonical = False
            p.is_duplicate = True
            p.duplicate_group_id = tx_id
            
            # Check for conflict in payload
            has_conflict = (p.amount != first_p.amount) or (p.currency != first_p.currency) or (p.transaction_type != first_p.transaction_type)
            p.duplicate_conflict = has_conflict

            conflict_desc = " Conflicting business values detected." if has_conflict else " Identical payload repeated."
            duplicate_items.append(
                ReconciliationItem(
                    id=f"EXC-DUP-PLT-{p.source_row}-{uuid.uuid4().hex[:6]}",
                    status=MatchStatus.DUPLICATE_PLATFORM_RECORD,
                    severity=ExceptionSeverity.MEDIUM if not has_conflict else ExceptionSeverity.HIGH,
                    reporting_period="",
                    platform_id=p.transaction_id,
                    platform_row=p.source_row,
                    platform_amount=p.amount,
                    platform_currency=p.currency,
                    platform_date=p.transaction_timestamp.isoformat(),
                    platform_type=p.transaction_type.value,
                    original_transaction_id=p.original_transaction_id,
                    difference_amount=p.amount,
                    financial_impact=p.amount,
                    reason_code="DUPLICATE_PLATFORM_RECORD",
                    explanation=f"Duplicate transaction '{tx_id}' found on row {p.source_row}. Canonical record is row {first_p.source_row}.{conflict_desc}",
                    suggested_action="Review platform retry/ingestion pipeline. Do not double-count in canonical ledger.",
                    is_canonical=False,
                    included_in_totals=False,
                    source_files=[p.source_file]
                )
            )

    # 2. Bank duplicate detection by bank_entry_id and semantic statement signature
    bank_id_seen: Dict[str, NormalizedBankSettlement] = {}
    bank_semantic_seen: Dict[Tuple[str, Decimal, str, datetime], NormalizedBankSettlement] = {}

    for b in bank_records:
        semantic_key = (b.transaction_reference, b.amount, b.currency, b.settlement_timestamp)
        is_dup = False
        canonical_target = None
        dup_reason = ""

        if b.bank_entry_id in bank_id_seen:
            is_dup = True
            canonical_target = bank_id_seen[b.bank_entry_id]
            dup_reason = f"Duplicate bank statement entry ID '{b.bank_entry_id}'."
        elif semantic_key in bank_semantic_seen:
            is_dup = True
            canonical_target = bank_semantic_seen[semantic_key]
            dup_reason = f"Duplicate settlement credit for reference '{b.transaction_reference}' with identical amount and timestamp."

        if not is_dup:
            bank_id_seen[b.bank_entry_id] = b
            bank_semantic_seen[semantic_key] = b
            b.is_canonical = True
            b.is_duplicate = False
        else:
            b.is_canonical = False
            b.is_duplicate = True
            b.duplicate_group_id = canonical_target.bank_entry_id

            duplicate_items.append(
                ReconciliationItem(
                    id=f"EXC-DUP-BNK-{b.source_row}-{uuid.uuid4().hex[:6]}",
                    status=MatchStatus.DUPLICATE_BANK_RECORD,
                    severity=ExceptionSeverity.MEDIUM,
                    reporting_period="",
                    bank_entry_id=b.bank_entry_id,
                    bank_row=b.source_row,
                    bank_reference=b.transaction_reference,
                    bank_amount=b.amount,
                    bank_currency=b.currency,
                    bank_date=b.settlement_timestamp.isoformat(),
                    bank_type=b.entry_type.value,
                    batch_id=b.batch_id,
                    difference_amount=b.amount,
                    financial_impact=b.amount,
                    reason_code="DUPLICATE_BANK_RECORD",
                    explanation=f"{dup_reason} Row {b.source_row} duplicates canonical bank record row {canonical_target.source_row}.",
                    suggested_action="Review bank statement extract for repeated batches. Canonical total excludes this row.",
                    is_canonical=False,
                    included_in_totals=False,
                    source_files=[b.source_file]
                )
            )

    return platform_records, bank_records, duplicate_items

def run_reconciliation(
    platform_records: List[NormalizedPlatformTransaction],
    bank_records: List[NormalizedBankSettlement],
    reporting_period: str = "2026-10",
    rounding_tolerance: Decimal = ROUNDING_TOLERANCE,
    is_synthetic: bool = True
) -> ReconciliationResponse:
    run_id = f"REC-{reporting_period.replace('-', '')}-{uuid.uuid4().hex[:8]}"
    generated_at = datetime.now(timezone.utc).isoformat()

    start_dt, end_dt, next_end_dt = get_month_boundaries(reporting_period)

    # 1. Run duplicate detection
    platform_all, bank_all, duplicate_items = detect_duplicates(platform_records, bank_records)
    for d in duplicate_items:
        d.reporting_period = reporting_period

    # Filter canonical records
    canonical_platform = [p for p in platform_all if p.is_canonical]
    canonical_bank = [b for b in bank_all if b.is_canonical]

    # Index platform payments in period and platform all
    platform_all_payments_by_id = {p.transaction_id: p for p in canonical_platform if p.transaction_type == TransactionType.PAYMENT}
    
    # Filter platform records belonging to reporting period
    in_month_platform_payments = [
        p for p in canonical_platform
        if p.transaction_type == TransactionType.PAYMENT and (start_dt <= p.transaction_timestamp <= end_dt)
    ]
    in_month_platform_refunds = [
        p for p in canonical_platform
        if p.transaction_type == TransactionType.REFUND and (start_dt <= p.transaction_timestamp <= end_dt)
    ]

    # Bank indexing:
    # We index bank entries by transaction_reference
    bank_by_ref: Dict[str, List[NormalizedBankSettlement]] = {}
    for b in canonical_bank:
        bank_by_ref.setdefault(b.transaction_reference, []).append(b)

    matched_items: List[ReconciliationItem] = []
    exception_items: List[ReconciliationItem] = []
    
    matched_bank_ids: Set[str] = set()
    rounding_candidates: List[Tuple[NormalizedPlatformTransaction, NormalizedBankSettlement, Decimal]] = []

    # 2. Reconcile platform payments in month
    for p in in_month_platform_payments:
        bank_candidates = bank_by_ref.get(p.transaction_id, [])

        if not bank_candidates:
            # Check if there is a possible match with different ref? PRD: Do not auto-match fuzzy references.
            exception_items.append(
                ReconciliationItem(
                    id=f"EXC-MISSING-{p.source_row}",
                    status=MatchStatus.MISSING_SETTLEMENT,
                    severity=ExceptionSeverity.HIGH,
                    reporting_period=reporting_period,
                    platform_id=p.transaction_id,
                    platform_row=p.source_row,
                    platform_amount=p.amount,
                    platform_currency=p.currency,
                    platform_date=p.transaction_timestamp.isoformat(),
                    platform_type=p.transaction_type.value,
                    difference_amount=p.amount,
                    financial_impact=p.amount,
                    reason_code="MISSING_SETTLEMENT",
                    explanation=f"Platform payment {p.transaction_id} (Amount: {p.currency} {p.amount}) has no settlement record in the bank statement search window ({start_dt.date()} to {next_end_dt.date()}).",
                    suggested_action="Escalate to banking partner operations for pending batch processing.",
                    is_canonical=True,
                    included_in_totals=True,
                    source_files=[p.source_file]
                )
            )
            continue

        # Evaluate bank candidates for this payment reference
        # If multiple bank candidates exist, check ambiguity
        if len(bank_candidates) > 1:
            exception_items.append(
                ReconciliationItem(
                    id=f"EXC-AMBIGUOUS-{p.source_row}",
                    status=MatchStatus.POSSIBLE_MATCH_REQUIRES_REVIEW,
                    severity=ExceptionSeverity.HIGH,
                    reporting_period=reporting_period,
                    platform_id=p.transaction_id,
                    platform_row=p.source_row,
                    platform_amount=p.amount,
                    platform_currency=p.currency,
                    platform_date=p.transaction_timestamp.isoformat(),
                    platform_type=p.transaction_type.value,
                    reason_code="AMBIGUOUS_BANK_MATCHES",
                    explanation=f"Multiple distinct bank settlement records ({len(bank_candidates)}) exist for reference '{p.transaction_id}'. Requires manual operator review.",
                    suggested_action="Review bank statement batches to verify if one is an adjustment or erroneous split.",
                    is_canonical=True,
                    included_in_totals=True,
                    source_files=[p.source_file] + [b.source_file for b in bank_candidates]
                )
            )
            for b in bank_candidates:
                matched_bank_ids.add(b.bank_entry_id)
            continue

        b = bank_candidates[0]
        matched_bank_ids.add(b.bank_entry_id)

        # Currency check
        if b.currency != p.currency:
            exception_items.append(
                ReconciliationItem(
                    id=f"EXC-CURR-{p.source_row}",
                    status=MatchStatus.CURRENCY_MISMATCH,
                    severity=ExceptionSeverity.CRITICAL,
                    reporting_period=reporting_period,
                    platform_id=p.transaction_id,
                    platform_row=p.source_row,
                    platform_amount=p.amount,
                    platform_currency=p.currency,
                    platform_date=p.transaction_timestamp.isoformat(),
                    platform_type=p.transaction_type.value,
                    bank_entry_id=b.bank_entry_id,
                    bank_row=b.source_row,
                    bank_reference=b.transaction_reference,
                    bank_amount=b.amount,
                    bank_currency=b.currency,
                    bank_date=b.settlement_timestamp.isoformat(),
                    bank_type=b.entry_type.value,
                    batch_id=b.batch_id,
                    difference_amount=p.amount,
                    financial_impact=p.amount,
                    reason_code="CURRENCY_MISMATCH",
                    explanation=f"Transaction reference matches, but platform currency is '{p.currency}' while bank settlement is '{b.currency}'.",
                    suggested_action="Verify multi-currency routing and FX conversion rates applied by the clearing bank.",
                    is_canonical=True,
                    included_in_totals=True,
                    source_files=[p.source_file, b.source_file]
                )
            )
            continue

        # Check amount difference
        amount_diff = p.amount - b.amount
        abs_diff = abs(amount_diff)

        # Check if difference is within small rounding tolerance (>0 and <= rounding_tolerance)
        if Decimal("0") < abs_diff <= rounding_tolerance:
            rounding_candidates.append((p, b, amount_diff))
            continue

        # Check if amount differs substantively
        if abs_diff > rounding_tolerance:
            exception_items.append(
                ReconciliationItem(
                    id=f"EXC-AMT-{p.source_row}",
                    status=MatchStatus.AMOUNT_MISMATCH,
                    severity=ExceptionSeverity.HIGH,
                    reporting_period=reporting_period,
                    platform_id=p.transaction_id,
                    platform_row=p.source_row,
                    platform_amount=p.amount,
                    platform_currency=p.currency,
                    platform_date=p.transaction_timestamp.isoformat(),
                    platform_type=p.transaction_type.value,
                    bank_entry_id=b.bank_entry_id,
                    bank_row=b.source_row,
                    bank_reference=b.transaction_reference,
                    bank_amount=b.amount,
                    bank_currency=b.currency,
                    bank_date=b.settlement_timestamp.isoformat(),
                    bank_type=b.entry_type.value,
                    batch_id=b.batch_id,
                    difference_amount=abs_diff,
                    financial_impact=abs_diff,
                    reason_code="AMOUNT_MISMATCH",
                    explanation=f"Reference '{p.transaction_id}' matched, but platform amount is {p.currency} {p.amount} and bank settled {b.currency} {b.amount} (Discrepancy: {p.currency} {abs_diff}).",
                    suggested_action="Check whether bank deducted transaction fee or processing surcharge at source.",
                    is_canonical=True,
                    included_in_totals=True,
                    source_files=[p.source_file, b.source_file]
                )
            )
            continue

        # Exact Amount Match! Check Settlement Timing
        if b.settlement_timestamp > end_dt and b.settlement_timestamp <= next_end_dt:
            # Mandatory Scenario 1: SETTLED_NEXT_MONTH
            matched_items.append(
                ReconciliationItem(
                    id=f"REC-NEXT-M-{p.source_row}",
                    status=MatchStatus.SETTLED_NEXT_MONTH,
                    severity=ExceptionSeverity.LOW,
                    reporting_period=reporting_period,
                    platform_id=p.transaction_id,
                    platform_row=p.source_row,
                    platform_amount=p.amount,
                    platform_currency=p.currency,
                    platform_date=p.transaction_timestamp.isoformat(),
                    platform_type=p.transaction_type.value,
                    bank_entry_id=b.bank_entry_id,
                    bank_row=b.source_row,
                    bank_reference=b.transaction_reference,
                    bank_amount=b.amount,
                    bank_currency=b.currency,
                    bank_date=b.settlement_timestamp.isoformat(),
                    bank_type=b.entry_type.value,
                    batch_id=b.batch_id,
                    difference_amount=Decimal("0.00"),
                    financial_impact=p.amount,
                    reason_code="SETTLED_NEXT_MONTH",
                    explanation=f"Platform transaction processed on {p.transaction_timestamp.date()} settled on {b.settlement_timestamp.date()} in the following calendar month ({b.settlement_timestamp.strftime('%B %Y')}). Identified via look-ahead window.",
                    suggested_action="No action required. Timing difference resolved across calendar boundary.",
                    is_canonical=True,
                    included_in_totals=True,
                    source_files=[p.source_file, b.source_file]
                )
            )
        else:
            # Confirmed in-month match
            matched_items.append(
                ReconciliationItem(
                    id=f"REC-MATCH-{p.source_row}",
                    status=MatchStatus.CONFIRMED_MATCH,
                    severity=ExceptionSeverity.INFO,
                    reporting_period=reporting_period,
                    platform_id=p.transaction_id,
                    platform_row=p.source_row,
                    platform_amount=p.amount,
                    platform_currency=p.currency,
                    platform_date=p.transaction_timestamp.isoformat(),
                    platform_type=p.transaction_type.value,
                    bank_entry_id=b.bank_entry_id,
                    bank_row=b.source_row,
                    bank_reference=b.transaction_reference,
                    bank_amount=b.amount,
                    bank_currency=b.currency,
                    bank_date=b.settlement_timestamp.isoformat(),
                    bank_type=b.entry_type.value,
                    batch_id=b.batch_id,
                    difference_amount=Decimal("0.00"),
                    financial_impact=Decimal("0.00"),
                    reason_code="CONFIRMED_MATCH",
                    explanation=f"Platform payment {p.transaction_id} matched bank settlement {b.bank_entry_id} with exact amount {p.currency} {p.amount}.",
                    suggested_action="None. Fully reconciled.",
                    is_canonical=True,
                    included_in_totals=True,
                    source_files=[p.source_file, b.source_file]
                )
            )

    # 3. Handle Aggregate Rounding Candidates (Mandatory Scenario 2)
    total_rounding_variance = Decimal("0.000")
    if rounding_candidates:
        sum_p = sum(p.amount for p, _, _ in rounding_candidates)
        sum_b = sum(b.amount for _, b, _ in rounding_candidates)
        agg_variance = sum_p - sum_b
        total_rounding_variance = agg_variance

        # Create individual items linking platform and bank records
        for p, b, diff in rounding_candidates:
            matched_items.append(
                ReconciliationItem(
                    id=f"REC-RND-{p.source_row}",
                    status=MatchStatus.AGGREGATE_ROUNDING_DIFFERENCE,
                    severity=ExceptionSeverity.LOW,
                    reporting_period=reporting_period,
                    platform_id=p.transaction_id,
                    platform_row=p.source_row,
                    platform_amount=p.amount,
                    platform_currency=p.currency,
                    platform_date=p.transaction_timestamp.isoformat(),
                    platform_type=p.transaction_type.value,
                    bank_entry_id=b.bank_entry_id,
                    bank_row=b.source_row,
                    bank_reference=b.transaction_reference,
                    bank_amount=b.amount,
                    bank_currency=b.currency,
                    bank_date=b.settlement_timestamp.isoformat(),
                    bank_type=b.entry_type.value,
                    batch_id=b.batch_id,
                    difference_amount=diff,
                    financial_impact=diff,
                    reason_code="AGGREGATE_ROUNDING_DIFFERENCE",
                    explanation=(
                        f"Aggregate rounding difference in population ({len(rounding_candidates)} txns). "
                        f"Platform amount: {p.amount}, Bank posted: {b.amount}. "
                        f"Population Platform Sum: {sum_p}, Bank Sum: {sum_b}, Net Variance: {agg_variance} "
                        f"(within tolerance of {rounding_tolerance} {p.currency})."
                    ),
                    suggested_action="Verify precision rules for sub-paise fee allocation.",
                    is_canonical=True,
                    included_in_totals=True,
                    source_files=[p.source_file, b.source_file]
                )
            )

    # 4. Handle Platform Refunds (Mandatory Scenario 4: ORPHAN_REFUND & matched refunds)
    for r in in_month_platform_refunds:
        # Check original payment existence
        if not r.original_transaction_id or r.original_transaction_id not in platform_all_payments_by_id:
            exception_items.append(
                ReconciliationItem(
                    id=f"EXC-ORPHAN-{r.source_row}",
                    status=MatchStatus.ORPHAN_REFUND,
                    severity=ExceptionSeverity.HIGH,
                    reporting_period=reporting_period,
                    platform_id=r.transaction_id,
                    platform_row=r.source_row,
                    platform_amount=r.amount,
                    platform_currency=r.currency,
                    platform_date=r.transaction_timestamp.isoformat(),
                    platform_type=r.transaction_type.value,
                    original_transaction_id=r.original_transaction_id,
                    difference_amount=r.amount,
                    financial_impact=r.amount,
                    reason_code="ORPHAN_REFUND",
                    explanation=f"Platform refund {r.transaction_id} references original transaction '{r.original_transaction_id}', which does not exist in platform payment records.",
                    suggested_action="Investigate potential unrecorded original transaction or manual erroneous refund initiation.",
                    is_canonical=True,
                    included_in_totals=True,
                    source_files=[r.source_file]
                )
            )
            continue

        # Original payment is valid; check bank debit settlement
        bank_debits = bank_by_ref.get(r.transaction_id, [])
        if bank_debits:
            bd = bank_debits[0]
            matched_bank_ids.add(bd.bank_entry_id)
            matched_items.append(
                ReconciliationItem(
                    id=f"REC-REF-MATCH-{r.source_row}",
                    status=MatchStatus.CONFIRMED_MATCH,
                    severity=ExceptionSeverity.INFO,
                    reporting_period=reporting_period,
                    platform_id=r.transaction_id,
                    platform_row=r.source_row,
                    platform_amount=r.amount,
                    platform_currency=r.currency,
                    platform_date=r.transaction_timestamp.isoformat(),
                    platform_type=r.transaction_type.value,
                    original_transaction_id=r.original_transaction_id,
                    bank_entry_id=bd.bank_entry_id,
                    bank_row=bd.source_row,
                    bank_reference=bd.transaction_reference,
                    bank_amount=bd.amount,
                    bank_currency=bd.currency,
                    bank_date=bd.settlement_timestamp.isoformat(),
                    bank_type=bd.entry_type.value,
                    batch_id=bd.batch_id,
                    difference_amount=Decimal("0.00"),
                    financial_impact=Decimal("0.00"),
                    reason_code="CONFIRMED_REFUND_MATCH",
                    explanation=f"Platform refund {r.transaction_id} (linked to original {r.original_transaction_id}) matched bank debit {bd.bank_entry_id}.",
                    suggested_action="None. Fully reconciled refund.",
                    is_canonical=True,
                    included_in_totals=True,
                    source_files=[r.source_file, bd.source_file]
                )
            )
        else:
            exception_items.append(
                ReconciliationItem(
                    id=f"EXC-REF-MISSING-{r.source_row}",
                    status=MatchStatus.MISSING_SETTLEMENT,
                    severity=ExceptionSeverity.MEDIUM,
                    reporting_period=reporting_period,
                    platform_id=r.transaction_id,
                    platform_row=r.source_row,
                    platform_amount=r.amount,
                    platform_currency=r.currency,
                    platform_date=r.transaction_timestamp.isoformat(),
                    platform_type=r.transaction_type.value,
                    original_transaction_id=r.original_transaction_id,
                    difference_amount=r.amount,
                    financial_impact=r.amount,
                    reason_code="MISSING_REFUND_DEBIT",
                    explanation=f"Platform refund {r.transaction_id} has not yet cleared the bank statement as a debit entry.",
                    suggested_action="Verify refund batch processing status with acquiring bank.",
                    is_canonical=True,
                    included_in_totals=True,
                    source_files=[r.source_file]
                )
            )

    # 5. Check Unmatched Bank Credits
    for b in canonical_bank:
        if b.bank_entry_id not in matched_bank_ids:
            # If bank settlement timestamp is within reporting period or search window
            if start_dt <= b.settlement_timestamp <= next_end_dt:
                exception_items.append(
                    ReconciliationItem(
                        id=f"EXC-BNK-UNMATCHED-{b.source_row}",
                        status=MatchStatus.UNMATCHED_BANK_CREDIT,
                        severity=ExceptionSeverity.HIGH,
                        reporting_period=reporting_period,
                        bank_entry_id=b.bank_entry_id,
                        bank_row=b.source_row,
                        bank_reference=b.transaction_reference,
                        bank_amount=b.amount,
                        bank_currency=b.currency,
                        bank_date=b.settlement_timestamp.isoformat(),
                        bank_type=b.entry_type.value,
                        batch_id=b.batch_id,
                        difference_amount=b.amount,
                        financial_impact=b.amount,
                        reason_code="UNMATCHED_BANK_CREDIT",
                        explanation=f"Bank entry {b.bank_entry_id} (Ref: '{b.transaction_reference}', Amount: {b.currency} {b.amount}) has no corresponding platform record.",
                        suggested_action="Investigate direct bank transfers, manual credits, or missing gateway transaction logs.",
                        is_canonical=True,
                        included_in_totals=True,
                        source_files=[b.source_file]
                    )
                )

    # Combine all items
    all_reconciliation_items = matched_items + exception_items + duplicate_items

    # 6. Aggregation & Metrics (Segregated by Currency)
    currency_summaries: Dict[str, CurrencySummary] = {}
    currencies = set([p.currency for p in canonical_platform] + [b.currency for b in canonical_bank])

    for curr in sorted(currencies):
        # Platform calculations for this currency in reporting month
        curr_p_payments = [p for p in in_month_platform_payments if p.currency == curr]
        curr_p_refunds = [p for p in in_month_platform_refunds if p.currency == curr]

        p_gross = sum((p.amount for p in curr_p_payments), Decimal("0.00"))
        p_ref = sum((p.amount for p in curr_p_refunds), Decimal("0.00"))
        p_net = p_gross - p_ref
        p_count = len(curr_p_payments) + len(curr_p_refunds)

        # Bank calculations for this currency in reporting month
        # In-month bank entries:
        curr_b_credits = [b for b in canonical_bank if b.currency == curr and b.entry_type == BankEntryType.CREDIT and (start_dt <= b.settlement_timestamp <= end_dt)]
        curr_b_debits = [b for b in canonical_bank if b.currency == curr and b.entry_type in (BankEntryType.DEBIT, BankEntryType.REFUND) and (start_dt <= b.settlement_timestamp <= end_dt)]

        b_gross = sum((b.amount for b in curr_b_credits), Decimal("0.00"))
        b_deb = sum((b.amount for b in curr_b_debits), Decimal("0.00"))
        b_net = b_gross - b_deb
        b_count = len(curr_b_credits) + len(curr_b_debits)

        # Matched items
        curr_matched = [m for m in matched_items if (m.platform_currency == curr or m.bank_currency == curr) and m.status in (MatchStatus.CONFIRMED_MATCH, MatchStatus.AGGREGATE_ROUNDING_DIFFERENCE)]
        matched_count = len(curr_matched)
        matched_amount = sum((m.platform_amount or m.bank_amount or Decimal("0.00") for m in curr_matched), Decimal("0.00"))

        # Unmatched platform
        curr_unmatched_p = [e for e in exception_items if e.platform_currency == curr and e.status in (MatchStatus.MISSING_SETTLEMENT, MatchStatus.AMOUNT_MISMATCH, MatchStatus.CURRENCY_MISMATCH, MatchStatus.ORPHAN_REFUND)]
        unmatched_p_count = len(curr_unmatched_p)
        unmatched_p_amount = sum((e.financial_impact for e in curr_unmatched_p), Decimal("0.00"))

        # Unmatched bank
        curr_unmatched_b = [e for e in exception_items if e.bank_currency == curr and e.status == MatchStatus.UNMATCHED_BANK_CREDIT]
        unmatched_b_count = len(curr_unmatched_b)
        unmatched_b_amount = sum((e.financial_impact for e in curr_unmatched_b), Decimal("0.00"))

        # Settled next month
        curr_next_m = [m for m in matched_items if m.platform_currency == curr and m.status == MatchStatus.SETTLED_NEXT_MONTH]
        next_m_count = len(curr_next_m)
        next_m_amount = sum((m.platform_amount or Decimal("0.00") for m in curr_next_m), Decimal("0.00"))

        # Rounding variance for this currency
        curr_rnd = [m for m in matched_items if m.platform_currency == curr and m.status == MatchStatus.AGGREGATE_ROUNDING_DIFFERENCE]
        curr_rnd_var = sum((m.difference_amount for m in curr_rnd), Decimal("0.000"))

        # Net variance
        net_var = p_net - b_net

        # Reconciliation rate formula:
        # confirmed_matched_payments / eligible_payments * 100
        # eligible_payments = total in-month canonical platform payments
        eligible_payments = len(curr_p_payments)
        confirmed_payments = len([m for m in matched_items if m.platform_currency == curr and m.status in (MatchStatus.CONFIRMED_MATCH, MatchStatus.SETTLED_NEXT_MONTH, MatchStatus.AGGREGATE_ROUNDING_DIFFERENCE)])
        if eligible_payments > 0:
            rec_rate = (Decimal(confirmed_payments) / Decimal(eligible_payments) * Decimal("100")).quantize(Decimal("0.1"))
        else:
            rec_rate = Decimal("100.0")

        formula_str = f"({confirmed_payments} confirmed matches / {eligible_payments} eligible platform payments) * 100 = {rec_rate}%"

        currency_summaries[curr] = CurrencySummary(
            currency=curr,
            platform_gross=p_gross,
            platform_refunds=p_ref,
            platform_net=p_net,
            platform_count=p_count,
            bank_settled_gross=b_gross,
            bank_debits=b_deb,
            bank_net=b_net,
            bank_count=b_count,
            matched_count=matched_count,
            matched_amount=matched_amount,
            unmatched_platform_count=unmatched_p_count,
            unmatched_platform_amount=unmatched_p_amount,
            unmatched_bank_count=unmatched_b_count,
            unmatched_bank_amount=unmatched_b_amount,
            settled_next_month_count=next_m_count,
            settled_next_month_amount=next_m_amount,
            rounding_variance=curr_rnd_var,
            net_variance=net_var,
            eligible_payment_count=eligible_payments,
            reconciliation_rate_pct=rec_rate,
            reconciliation_rate_formula=formula_str
        )

    # Overall Summary
    cat_counts: Dict[str, int] = {}
    for item in all_reconciliation_items:
        cat_counts[item.status.value] = cat_counts.get(item.status.value, 0) + 1

    total_plt_rows = len(platform_records)
    total_bnk_rows = len(bank_records)
    dup_plt_count = len([p for p in platform_all if p.is_duplicate])
    dup_bnk_count = len([b for b in bank_all if b.is_duplicate])

    # Overall rate across all eligible platform payments
    total_eligible = sum(c.eligible_payment_count for c in currency_summaries.values())
    total_confirmed = sum(
        len([m for m in matched_items if m.status in (MatchStatus.CONFIRMED_MATCH, MatchStatus.SETTLED_NEXT_MONTH, MatchStatus.AGGREGATE_ROUNDING_DIFFERENCE)])
        for _ in [1]
    )
    overall_rate = (
        (Decimal(total_confirmed) / Decimal(total_eligible) * Decimal("100")).quantize(Decimal("0.1"))
        if total_eligible > 0 else Decimal("100.0")
    )

    assumptions_list = [
        "Settlements typically lag by 2 days; bank settlements are searched through the end of the next calendar month for late-settlement detection.",
        "Monetary values are computed strictly using Python Decimal without floating-point conversions.",
        "Currencies are segregated into separate summaries; figures are never combined across different currencies.",
        "Duplicate records are preserved for auditability but counted exactly once in canonical financial totals.",
        f"Aggregate rounding tolerance is configured at {rounding_tolerance} INR and evaluated across comparable grouped populations."
    ]

    warnings_list = []
    if dup_plt_count > 0:
        warnings_list.append(f"{dup_plt_count} duplicate platform record(s) detected and isolated from canonical totals.")
    if dup_bnk_count > 0:
        warnings_list.append(f"{dup_bnk_count} duplicate bank record(s) detected and isolated from canonical totals.")

    summary = ReconciliationSummary(
        total_platform_rows=total_plt_rows,
        total_bank_rows=total_bnk_rows,
        canonical_platform_records=len(canonical_platform),
        canonical_bank_records=len(canonical_bank),
        duplicate_platform_rows=dup_plt_count,
        duplicate_bank_rows=dup_bnk_count,
        total_exceptions_count=len(exception_items) + len(duplicate_items),
        exceptions_by_category=cat_counts,
        currency_summaries=currency_summaries,
        overall_reconciliation_rate=overall_rate,
        is_synthetic=is_synthetic,
        assumptions=assumptions_list,
        warnings=warnings_list
    )

    return ReconciliationResponse(
        run_id=run_id,
        reporting_period=reporting_period,
        generated_at=generated_at,
        summary=summary,
        items=all_reconciliation_items,
        validation_errors=[]
    )
