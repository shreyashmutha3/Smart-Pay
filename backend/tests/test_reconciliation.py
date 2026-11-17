import pytest
from decimal import Decimal
from datetime import datetime, timezone
from app.services.data_generator import generate_synthetic_data
from app.services.ingestion import ingest_platform_csv, ingest_bank_csv
from app.services.reconciliation import run_reconciliation, detect_duplicates
from app.models.schemas import (
    MatchStatus,
    ExceptionSeverity,
    TransactionType,
    BankEntryType,
    NormalizedPlatformTransaction,
    NormalizedBankSettlement
)

@pytest.fixture
def sample_datasets():
    platform_csv, bank_csv, expected = generate_synthetic_data()
    p_records, p_errors = ingest_platform_csv(platform_csv, "platform.csv")
    b_records, b_errors = ingest_bank_csv(bank_csv, "bank.csv")
    return p_records, b_records, expected, p_errors, b_errors

def test_t01_exact_match(sample_datasets):
    """T01: Exact reference, amount, currency and valid settlement date -> Confirmed match"""
    p_records, b_records, _, _, _ = sample_datasets
    res = run_reconciliation(p_records, b_records, reporting_period="2026-10")
    
    t01_item = next((item for item in res.items if item.platform_id == "TXN-NORM-001"), None)
    assert t01_item is not None
    assert t01_item.status == MatchStatus.CONFIRMED_MATCH
    assert t01_item.platform_amount == Decimal("1500.00")
    assert t01_item.bank_amount == Decimal("1500.00")
    assert t01_item.financial_impact == Decimal("0.00")

def test_t02_two_day_lag_settlement(sample_datasets):
    """T02: Settlement occurs two days after payment within reporting month -> Confirmed match"""
    p_records, b_records, _, _, _ = sample_datasets
    res = run_reconciliation(p_records, b_records, reporting_period="2026-10")
    
    # TXN-NORM-002: processed 2026-10-02, settled 2026-10-04 (2 days later)
    item = next((item for item in res.items if item.platform_id == "TXN-NORM-002"), None)
    assert item is not None
    assert item.status == MatchStatus.CONFIRMED_MATCH

def test_t03_settled_next_month(sample_datasets):
    """T03: Payment on last day of month, settlement in following month -> SETTLED_NEXT_MONTH"""
    p_records, b_records, _, _, _ = sample_datasets
    res = run_reconciliation(p_records, b_records, reporting_period="2026-10")
    
    # TXN-NEXT-M01: processed 2026-10-30, settled 2026-11-02
    item1 = next((item for item in res.items if item.platform_id == "TXN-NEXT-M01"), None)
    assert item1 is not None
    assert item1.status == MatchStatus.SETTLED_NEXT_MONTH
    assert item1.bank_entry_id == "BNK-NEXT-M01"
    assert "following calendar month" in item1.explanation

    # TXN-NEXT-M02: processed 2026-10-31, settled 2026-11-03
    item2 = next((item for item in res.items if item.platform_id == "TXN-NEXT-M02"), None)
    assert item2 is not None
    assert item2.status == MatchStatus.SETTLED_NEXT_MONTH

def test_t04_aggregate_rounding_difference(sample_datasets):
    """T04: Aggregate-only small precision/rounding variance -> AGGREGATE_ROUNDING_DIFFERENCE"""
    p_records, b_records, _, _, _ = sample_datasets
    res = run_reconciliation(p_records, b_records, reporting_period="2026-10")
    
    rnd_items = [item for item in res.items if item.status == MatchStatus.AGGREGATE_ROUNDING_DIFFERENCE]
    assert len(rnd_items) == 3
    # Platform amounts are 10.005 each -> sum = 30.015
    # Bank posted amounts are 10.00 each -> sum = 30.000
    # Net aggregate variance = 0.015 (within 0.02 INR tolerance)
    item = rnd_items[0]
    assert "Aggregate rounding difference" in item.explanation
    assert "0.015" in item.explanation
    # Must be tracked in currency summary
    inr_summary = res.summary.currency_summaries["INR"]
    assert inr_summary.rounding_variance == Decimal("0.015")

def test_t05_duplicate_platform_row(sample_datasets):
    """T05: Duplicate platform row -> DUPLICATE_PLATFORM_RECORD; canonical total counts once"""
    p_records, b_records, _, _, _ = sample_datasets
    res = run_reconciliation(p_records, b_records, reporting_period="2026-10")
    
    dup_items = [item for item in res.items if item.status == MatchStatus.DUPLICATE_PLATFORM_RECORD]
    assert len(dup_items) == 1
    dup = dup_items[0]
    assert dup.platform_id == "TXN-DUP-PLT-001"
    assert dup.is_canonical is False
    assert dup.included_in_totals is False
    assert dup.financial_impact == Decimal("1500.00")
    assert res.summary.duplicate_platform_rows == 1

def test_t06_duplicate_bank_row(sample_datasets):
    """T06: Duplicate bank row -> DUPLICATE_BANK_RECORD; canonical total counts once"""
    p_records, b_records, _, _, _ = sample_datasets
    res = run_reconciliation(p_records, b_records, reporting_period="2026-10")
    
    dup_items = [item for item in res.items if item.status == MatchStatus.DUPLICATE_BANK_RECORD]
    assert len(dup_items) == 1
    dup = dup_items[0]
    assert dup.bank_reference == "TXN-DUP-BNK-001"
    assert dup.is_canonical is False
    assert dup.included_in_totals is False
    assert dup.financial_impact == Decimal("2200.00")
    assert res.summary.duplicate_bank_rows == 1

def test_t07_orphan_refund(sample_datasets):
    """T07: Refund has no original payment reference target -> ORPHAN_REFUND"""
    p_records, b_records, _, _, _ = sample_datasets
    res = run_reconciliation(p_records, b_records, reporting_period="2026-10")
    
    item = next((item for item in res.items if item.platform_id == "TXN-ORPHAN-REF-001"), None)
    assert item is not None
    assert item.status == MatchStatus.ORPHAN_REFUND
    assert item.original_transaction_id == "TXN-NONEXISTENT-999"
    assert item.financial_impact == Decimal("750.00")

def test_t08_missing_settlement(sample_datasets):
    """T08: Payment has no settlement in look-ahead window -> MISSING_SETTLEMENT"""
    p_records, b_records, _, _, _ = sample_datasets
    res = run_reconciliation(p_records, b_records, reporting_period="2026-10")
    
    item = next((item for item in res.items if item.platform_id == "TXN-MISSING-001"), None)
    assert item is not None
    assert item.status == MatchStatus.MISSING_SETTLEMENT
    assert item.financial_impact == Decimal("5000.00")

def test_t09_amount_mismatch(sample_datasets):
    """T09: Reference matches but amount differs -> AMOUNT_MISMATCH"""
    p_records, b_records, _, _, _ = sample_datasets
    res = run_reconciliation(p_records, b_records, reporting_period="2026-10")
    
    item = next((item for item in res.items if item.platform_id == "TXN-AMT-MISMATCH-001"), None)
    assert item is not None
    assert item.status == MatchStatus.AMOUNT_MISMATCH
    assert item.difference_amount == Decimal("99.00")

def test_t10_unmatched_bank_credit(sample_datasets):
    """T10: Bank credit has no platform record -> UNMATCHED_BANK_CREDIT"""
    p_records, b_records, _, _, _ = sample_datasets
    res = run_reconciliation(p_records, b_records, reporting_period="2026-10")
    
    item = next((item for item in res.items if item.bank_entry_id == "BNK-UNMATCHED-001"), None)
    assert item is not None
    assert item.status == MatchStatus.UNMATCHED_BANK_CREDIT
    assert item.financial_impact == Decimal("3400.00")

def test_t11_currency_mismatch(sample_datasets):
    """T11: Reference matches but currency differs -> CURRENCY_MISMATCH"""
    p_records, b_records, _, _, _ = sample_datasets
    res = run_reconciliation(p_records, b_records, reporting_period="2026-10")
    
    item = next((item for item in res.items if item.platform_id == "TXN-CURR-MISMATCH-001"), None)
    assert item is not None
    assert item.status == MatchStatus.CURRENCY_MISMATCH
    assert item.platform_currency == "USD"
    assert item.bank_currency == "INR"

def test_t12_validation_error_handling():
    """T12: Invalid date or malformed amount -> Validation error with source row"""
    malformed_csv = """transaction_id,original_transaction_id,transaction_type,amount,currency,transaction_timestamp,status,merchant_reference
TXN-BAD-01,,PAYMENT,NOT_A_DECIMAL,INR,2026-10-01T10:00:00Z,SUCCESS,
TXN-BAD-02,,PAYMENT,50.00,INR,INVALID_DATE_FORMAT,SUCCESS,
"""
    records, errors = ingest_platform_csv(malformed_csv, "malformed.csv")
    assert len(records) == 0
    assert len(errors) == 2
    assert errors[0].source_row == 2
    assert "Invalid decimal amount" in errors[0].error_message
    assert errors[1].source_row == 3
    assert "Invalid ISO-8601" in errors[1].error_message

def test_t13_ambiguous_matches():
    """T13: Multiple bank matches for one reference -> POSSIBLE_MATCH_REQUIRES_REVIEW (no arbitrary match)"""
    p_records = [
        NormalizedPlatformTransaction(
            source_file="p.csv",
            source_row=2,
            transaction_id="TXN-AMB-01",
            original_transaction_id=None,
            transaction_type=TransactionType.PAYMENT,
            amount=Decimal("1000.00"),
            currency="INR",
            transaction_timestamp=datetime(2026, 10, 5, 10, 0, tzinfo=timezone.utc),
            status="SUCCESS",
            raw_payload={}
        )
    ]
    b_records = [
        NormalizedBankSettlement(
            source_file="b.csv",
            source_row=2,
            bank_entry_id="BNK-AMB-01",
            transaction_reference="TXN-AMB-01",
            entry_type=BankEntryType.CREDIT,
            amount=Decimal("500.00"),
            currency="INR",
            settlement_timestamp=datetime(2026, 10, 7, 10, 0, tzinfo=timezone.utc),
            raw_payload={}
        ),
        NormalizedBankSettlement(
            source_file="b.csv",
            source_row=3,
            bank_entry_id="BNK-AMB-02",
            transaction_reference="TXN-AMB-01",
            entry_type=BankEntryType.CREDIT,
            amount=Decimal("500.00"),
            currency="INR",
            settlement_timestamp=datetime(2026, 10, 8, 10, 0, tzinfo=timezone.utc),
            raw_payload={}
        )
    ]
    res = run_reconciliation(p_records, b_records, reporting_period="2026-10")
    amb_item = next((item for item in res.items if item.status == MatchStatus.POSSIBLE_MATCH_REQUIRES_REVIEW), None)
    assert amb_item is not None
    assert amb_item.reason_code == "AMBIGUOUS_BANK_MATCHES"

def test_t14_determinism(sample_datasets):
    """T14: Same inputs run twice produce identical classifications and totals"""
    p_records, b_records, _, _, _ = sample_datasets
    run1 = run_reconciliation(p_records, b_records, reporting_period="2026-10")
    run2 = run_reconciliation(p_records, b_records, reporting_period="2026-10")
    
    assert run1.summary.total_platform_rows == run2.summary.total_platform_rows
    assert run1.summary.total_bank_rows == run2.summary.total_bank_rows
    assert run1.summary.exceptions_by_category == run2.summary.exceptions_by_category
    assert run1.summary.overall_reconciliation_rate == run2.summary.overall_reconciliation_rate
    assert len(run1.items) == len(run2.items)
    
    for i in range(len(run1.items)):
        assert run1.items[i].status == run2.items[i].status
        assert run1.items[i].financial_impact == run2.items[i].financial_impact
        assert run1.items[i].platform_id == run2.items[i].platform_id
