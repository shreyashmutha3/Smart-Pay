import csv
import io
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Tuple

def generate_synthetic_data() -> Tuple[str, str, Dict[str, any]]:
    """
    Generates deterministic synthetic platform and bank CSV datasets
    meeting all requirements of the PRD and rules:
    - Fixed seed / deterministic values
    - >= 35 records
    - 4 mandatory scenarios explicitly included
    - Additional edge cases (missing settlement, unmatched credit, amount mismatch, currency mismatch, duplicate bank)
    - Documented expected outcomes
    """
    platform_rows: List[Dict[str, str]] = []
    bank_rows: List[Dict[str, str]] = []
    
    # Track expected classifications for automated test assertions
    expected_results = {
        "reporting_period": "2026-10",
        "settled_next_month": ["TXN-NEXT-M01", "TXN-NEXT-M02"],
        "aggregate_rounding": ["TXN-RND-001", "TXN-RND-002", "TXN-RND-003"],
        "duplicate_platform": ["TXN-DUP-PLT-001"],
        "duplicate_bank": ["BNK-DUP-001B"],
        "orphan_refund": ["TXN-ORPHAN-REF-001"],
        "missing_settlement": ["TXN-MISSING-001"],
        "unmatched_bank_credit": ["BNK-UNMATCHED-001"],
        "amount_mismatch": ["TXN-AMT-MISMATCH-001"],
        "currency_mismatch": ["TXN-CURR-MISMATCH-001"],
        "confirmed_normal_matches": [
            "TXN-NORM-001", "TXN-NORM-002", "TXN-NORM-003", "TXN-NORM-004", "TXN-NORM-005",
            "TXN-NORM-006", "TXN-NORM-007", "TXN-NORM-008", "TXN-NORM-009", "TXN-NORM-010",
            "TXN-NORM-011", "TXN-NORM-012", "TXN-NORM-013", "TXN-NORM-014", "TXN-NORM-015",
            "TXN-NORM-016", "TXN-NORM-017", "TXN-NORM-018", "TXN-NORM-019", "TXN-NORM-020",
            "TXN-NORM-REF-P01", "TXN-NORM-REF-R01"
        ]
    }
    
    # 1. Normal Confirmed Matches (15 payments)
    normal_payments = [
        ("TXN-NORM-001", "1500.00", "2026-10-01T10:00:00Z", "2026-10-03T11:30:00Z", "BATCH-OCT-01"),
        ("TXN-NORM-002", "2450.50", "2026-10-02T11:15:00Z", "2026-10-04T12:00:00Z", "BATCH-OCT-01"),
        ("TXN-NORM-003", "780.00",  "2026-10-03T14:20:00Z", "2026-10-05T09:45:00Z", "BATCH-OCT-02"),
        ("TXN-NORM-004", "3200.00", "2026-10-05T09:00:00Z", "2026-10-07T14:10:00Z", "BATCH-OCT-02"),
        ("TXN-NORM-005", "450.00",  "2026-10-06T16:30:00Z", "2026-10-08T10:20:00Z", "BATCH-OCT-03"),
        ("TXN-NORM-006", "12000.00","2026-10-08T12:00:00Z", "2026-10-10T15:00:00Z", "BATCH-OCT-03"),
        ("TXN-NORM-007", "890.00",  "2026-10-10T13:45:00Z", "2026-10-12T11:15:00Z", "BATCH-OCT-04"),
        ("TXN-NORM-008", "1150.00", "2026-10-12T15:10:00Z", "2026-10-14T09:30:00Z", "BATCH-OCT-04"),
        ("TXN-NORM-009", "640.00",  "2026-10-14T08:30:00Z", "2026-10-16T13:00:00Z", "BATCH-OCT-05"),
        ("TXN-NORM-010", "999.00",  "2026-10-15T17:00:00Z", "2026-10-17T10:45:00Z", "BATCH-OCT-05"),
        ("TXN-NORM-011", "2500.00", "2026-10-18T10:15:00Z", "2026-10-20T12:30:00Z", "BATCH-OCT-06"),
        ("TXN-NORM-012", "1850.00", "2026-10-19T11:45:00Z", "2026-10-21T14:20:00Z", "BATCH-OCT-06"),
        ("TXN-NORM-013", "3100.00", "2026-10-22T14:30:00Z", "2026-10-24T16:00:00Z", "BATCH-OCT-07"),
        ("TXN-NORM-014", "420.00",  "2026-10-24T09:20:00Z", "2026-10-26T11:00:00Z", "BATCH-OCT-07"),
        ("TXN-NORM-015", "5600.00", "2026-10-25T15:00:00Z", "2026-10-27T13:15:00Z", "BATCH-OCT-08"),
        ("TXN-NORM-016", "720.00",  "2026-10-26T10:10:00Z", "2026-10-28T12:00:00Z", "BATCH-OCT-08"),
        ("TXN-NORM-017", "1340.00", "2026-10-27T11:30:00Z", "2026-10-29T14:15:00Z", "BATCH-OCT-09"),
        ("TXN-NORM-018", "499.00",  "2026-10-28T14:00:00Z", "2026-10-30T10:30:00Z", "BATCH-OCT-09"),
        ("TXN-NORM-019", "2890.00", "2026-10-29T09:45:00Z", "2026-10-31T15:20:00Z", "BATCH-OCT-10"),
        ("TXN-NORM-020", "610.00",  "2026-10-29T16:15:00Z", "2026-10-31T17:00:00Z", "BATCH-OCT-10"),
    ]
    
    for tx_id, amt, p_time, b_time, batch in normal_payments:
        platform_rows.append({
            "transaction_id": tx_id,
            "original_transaction_id": "",
            "transaction_type": "PAYMENT",
            "amount": amt,
            "currency": "INR",
            "transaction_timestamp": p_time,
            "status": "SUCCESS",
            "merchant_reference": f"ORDER-{tx_id}"
        })
        bank_rows.append({
            "bank_entry_id": f"BNK-{tx_id}",
            "transaction_reference": tx_id,
            "entry_type": "CREDIT",
            "amount": amt,
            "currency": "INR",
            "settlement_timestamp": b_time,
            "batch_id": batch,
            "description": f"Settlement for {tx_id}"
        })
        
    # Normal matched refund (Payment + legitimate Refund linked by original_transaction_id)
    platform_rows.append({
        "transaction_id": "TXN-NORM-REF-P01",
        "original_transaction_id": "",
        "transaction_type": "PAYMENT",
        "amount": "1500.00",
        "currency": "INR",
        "transaction_timestamp": "2026-10-05T09:30:00Z",
        "status": "REFUNDED",
        "merchant_reference": "ORDER-REF-01"
    })
    bank_rows.append({
        "bank_entry_id": "BNK-NORM-REF-P01",
        "transaction_reference": "TXN-NORM-REF-P01",
        "entry_type": "CREDIT",
        "amount": "1500.00",
        "currency": "INR",
        "settlement_timestamp": "2026-10-07T11:00:00Z",
        "batch_id": "BATCH-OCT-02",
        "description": "Settlement for TXN-NORM-REF-P01"
    })
    platform_rows.append({
        "transaction_id": "TXN-NORM-REF-R01",
        "original_transaction_id": "TXN-NORM-REF-P01",
        "transaction_type": "REFUND",
        "amount": "1500.00",
        "currency": "INR",
        "transaction_timestamp": "2026-10-08T14:00:00Z",
        "status": "SUCCESS",
        "merchant_reference": "REFUND-01"
    })
    bank_rows.append({
        "bank_entry_id": "BNK-NORM-REF-R01",
        "transaction_reference": "TXN-NORM-REF-R01",
        "entry_type": "DEBIT",
        "amount": "1500.00",
        "currency": "INR",
        "settlement_timestamp": "2026-10-10T16:30:00Z",
        "batch_id": "BATCH-OCT-03",
        "description": "Debit for TXN-NORM-REF-R01"
    })

    # 2. Mandatory Scenario 1: SETTLED_NEXT_MONTH
    # Payment in late October (reporting month), settlement in early November (next calendar month)
    platform_rows.append({
        "transaction_id": "TXN-NEXT-M01",
        "original_transaction_id": "",
        "transaction_type": "PAYMENT",
        "amount": "4500.00",
        "currency": "INR",
        "transaction_timestamp": "2026-10-30T17:45:00Z",
        "status": "SUCCESS",
        "merchant_reference": "ORDER-NEXT-01"
    })
    bank_rows.append({
        "bank_entry_id": "BNK-NEXT-M01",
        "transaction_reference": "TXN-NEXT-M01",
        "entry_type": "CREDIT",
        "amount": "4500.00",
        "currency": "INR",
        "settlement_timestamp": "2026-11-02T10:00:00Z", # Settled in November
        "batch_id": "BATCH-NOV-01",
        "description": "Late settlement for TXN-NEXT-M01"
    })

    platform_rows.append({
        "transaction_id": "TXN-NEXT-M02",
        "original_transaction_id": "",
        "transaction_type": "PAYMENT",
        "amount": "8200.00",
        "currency": "INR",
        "transaction_timestamp": "2026-10-31T20:15:00Z",
        "status": "SUCCESS",
        "merchant_reference": "ORDER-NEXT-02"
    })
    bank_rows.append({
        "bank_entry_id": "BNK-NEXT-M02",
        "transaction_reference": "TXN-NEXT-M02",
        "entry_type": "CREDIT",
        "amount": "8200.00",
        "currency": "INR",
        "settlement_timestamp": "2026-11-03T11:30:00Z", # Settled in November
        "batch_id": "BATCH-NOV-01",
        "description": "Late settlement for TXN-NEXT-M02"
    })

    # 3. Mandatory Scenario 2: AGGREGATE_ROUNDING_DIFFERENCE
    # Three transactions with precise sub-paise fees:
    # Platform: 10.005 each -> sum = 30.015
    # Bank posted: 10.00 each -> sum = 30.00
    # Aggregate difference = 0.015 (within tolerance of 0.02 INR)
    # References match exactly 1:1, but aggregate difference emerges when summed.
    rounding_txns = [
        ("TXN-RND-001", "10.005", "10.00", "2026-10-15T09:00:00Z", "2026-10-17T10:00:00Z"),
        ("TXN-RND-002", "10.005", "10.00", "2026-10-15T09:01:00Z", "2026-10-17T10:01:00Z"),
        ("TXN-RND-003", "10.005", "10.00", "2026-10-15T09:02:00Z", "2026-10-17T10:02:00Z"),
    ]
    for p_id, p_amt, b_amt, p_time, b_time in rounding_txns:
        platform_rows.append({
            "transaction_id": p_id,
            "original_transaction_id": "",
            "transaction_type": "PAYMENT",
            "amount": p_amt,
            "currency": "INR",
            "transaction_timestamp": p_time,
            "status": "SUCCESS",
            "merchant_reference": f"FEE-SPLIT-{p_id}"
        })
        bank_rows.append({
            "bank_entry_id": f"BNK-{p_id}",
            "transaction_reference": p_id,
            "entry_type": "CREDIT",
            "amount": b_amt,
            "currency": "INR",
            "settlement_timestamp": b_time,
            "batch_id": "BATCH-OCT-05",
            "description": f"Posted settlement {p_id}"
        })

    # 4. Mandatory Scenario 3: DUPLICATE_PLATFORM_RECORD and DUPLICATE_BANK_RECORD
    # Duplicate in Platform:
    # Row 1 (canonical)
    platform_rows.append({
        "transaction_id": "TXN-DUP-PLT-001",
        "original_transaction_id": "",
        "transaction_type": "PAYMENT",
        "amount": "1500.00",
        "currency": "INR",
        "transaction_timestamp": "2026-10-14T11:00:00Z",
        "status": "SUCCESS",
        "merchant_reference": "ORDER-DUP-01"
    })
    # Row 2 (duplicate platform event, identical payload)
    platform_rows.append({
        "transaction_id": "TXN-DUP-PLT-001",
        "original_transaction_id": "",
        "transaction_type": "PAYMENT",
        "amount": "1500.00",
        "currency": "INR",
        "transaction_timestamp": "2026-10-14T11:00:00Z",
        "status": "SUCCESS",
        "merchant_reference": "ORDER-DUP-01"
    })
    # Bank only received and settled it once:
    bank_rows.append({
        "bank_entry_id": "BNK-DUP-PLT-001",
        "transaction_reference": "TXN-DUP-PLT-001",
        "entry_type": "CREDIT",
        "amount": "1500.00",
        "currency": "INR",
        "settlement_timestamp": "2026-10-16T12:00:00Z",
        "batch_id": "BATCH-OCT-05",
        "description": "Settlement for TXN-DUP-PLT-001"
    })

    # Duplicate in Bank:
    # Platform has 1 payment:
    platform_rows.append({
        "transaction_id": "TXN-DUP-BNK-001",
        "original_transaction_id": "",
        "transaction_type": "PAYMENT",
        "amount": "2200.00",
        "currency": "INR",
        "transaction_timestamp": "2026-10-18T14:30:00Z",
        "status": "SUCCESS",
        "merchant_reference": "ORDER-DUP-BNK-01"
    })
    # Bank has 2 settlement entries for the same reference:
    bank_rows.append({
        "bank_entry_id": "BNK-DUP-001A",
        "transaction_reference": "TXN-DUP-BNK-001",
        "entry_type": "CREDIT",
        "amount": "2200.00",
        "currency": "INR",
        "settlement_timestamp": "2026-10-20T10:00:00Z",
        "batch_id": "BATCH-OCT-06",
        "description": "Settlement batch A"
    })
    bank_rows.append({
        "bank_entry_id": "BNK-DUP-001B",
        "transaction_reference": "TXN-DUP-BNK-001",
        "entry_type": "CREDIT",
        "amount": "2200.00",
        "currency": "INR",
        "settlement_timestamp": "2026-10-20T10:00:00Z",
        "batch_id": "BATCH-OCT-06",
        "description": "Duplicate statement line BNK-DUP-001B"
    })

    # 5. Mandatory Scenario 4: ORPHAN_REFUND
    # Platform refund referencing an unknown original transaction
    platform_rows.append({
        "transaction_id": "TXN-ORPHAN-REF-001",
        "original_transaction_id": "TXN-NONEXISTENT-999",
        "transaction_type": "REFUND",
        "amount": "750.00",
        "currency": "INR",
        "transaction_timestamp": "2026-10-22T16:00:00Z",
        "status": "SUCCESS",
        "merchant_reference": "REFUND-ORPHAN-01"
    })

    # 6. Additional Useful Scenarios:
    # A. MISSING_SETTLEMENT (Platform payment with no bank credit)
    platform_rows.append({
        "transaction_id": "TXN-MISSING-001",
        "original_transaction_id": "",
        "transaction_type": "PAYMENT",
        "amount": "5000.00",
        "currency": "INR",
        "transaction_timestamp": "2026-10-12T13:00:00Z",
        "status": "SUCCESS",
        "merchant_reference": "ORDER-MISSING-01"
    })

    # B. UNMATCHED_BANK_CREDIT (Bank credit with no platform payment)
    bank_rows.append({
        "bank_entry_id": "BNK-UNMATCHED-001",
        "transaction_reference": "EXT-UNKNOWN-REF-888",
        "entry_type": "CREDIT",
        "amount": "3400.00",
        "currency": "INR",
        "settlement_timestamp": "2026-10-15T15:30:00Z",
        "batch_id": "BATCH-OCT-05",
        "description": "Direct bank credit without platform ref"
    })

    # C. AMOUNT_MISMATCH (Reference matches, but amounts differ)
    platform_rows.append({
        "transaction_id": "TXN-AMT-MISMATCH-001",
        "original_transaction_id": "",
        "transaction_type": "PAYMENT",
        "amount": "1999.00",
        "currency": "INR",
        "transaction_timestamp": "2026-10-23T11:20:00Z",
        "status": "SUCCESS",
        "merchant_reference": "ORDER-MISMATCH-01"
    })
    bank_rows.append({
        "bank_entry_id": "BNK-AMT-001",
        "transaction_reference": "TXN-AMT-MISMATCH-001",
        "entry_type": "CREDIT",
        "amount": "1900.00", # Discrepancy of 99.00 INR
        "currency": "INR",
        "settlement_timestamp": "2026-10-25T14:00:00Z",
        "batch_id": "BATCH-OCT-07",
        "description": "Partial settlement for TXN-AMT-MISMATCH-001"
    })

    # D. CURRENCY_MISMATCH (Reference matches, but currency differs)
    platform_rows.append({
        "transaction_id": "TXN-CURR-MISMATCH-001",
        "original_transaction_id": "",
        "transaction_type": "PAYMENT",
        "amount": "500.00",
        "currency": "USD", # Platform in USD
        "transaction_timestamp": "2026-10-24T12:00:00Z",
        "status": "SUCCESS",
        "merchant_reference": "ORDER-USD-01"
    })
    bank_rows.append({
        "bank_entry_id": "BNK-CURR-001",
        "transaction_reference": "TXN-CURR-MISMATCH-001",
        "entry_type": "CREDIT",
        "amount": "500.00",
        "currency": "INR", # Bank settled as INR
        "settlement_timestamp": "2026-10-26T10:00:00Z",
        "batch_id": "BATCH-OCT-07",
        "description": "Settlement currency mismatch"
    })

    # Write platform CSV to string
    platform_csv_io = io.StringIO()
    platform_fieldnames = [
        "transaction_id", "original_transaction_id", "transaction_type",
        "amount", "currency", "transaction_timestamp", "status", "merchant_reference"
    ]
    platform_writer = csv.DictWriter(platform_csv_io, fieldnames=platform_fieldnames, lineterminator="\n")
    platform_writer.writeheader()
    for row in platform_rows:
        platform_writer.writerow(row)
    platform_csv = platform_csv_io.getvalue()

    # Write bank CSV to string
    bank_csv_io = io.StringIO()
    bank_fieldnames = [
        "bank_entry_id", "transaction_reference", "entry_type",
        "amount", "currency", "settlement_timestamp", "batch_id", "description"
    ]
    bank_writer = csv.DictWriter(bank_csv_io, fieldnames=bank_fieldnames, lineterminator="\n")
    bank_writer.writeheader()
    for row in bank_rows:
        bank_writer.writerow(row)
    bank_csv = bank_csv_io.getvalue()

    return platform_csv, bank_csv, expected_results

if __name__ == "__main__":
    plt_csv, bnk_csv, expected = generate_synthetic_data()
    with open("sample_data/platform_transactions.csv", "w", newline="") as f:
        f.write(plt_csv)
    with open("sample_data/bank_settlements.csv", "w", newline="") as f:
        f.write(bnk_csv)
    print(f"Generated sample datasets successfully. Platform rows: {len(plt_csv.splitlines())}, Bank rows: {len(bnk_csv.splitlines())}")
