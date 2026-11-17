import csv
import io
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Tuple, Any, Optional

from app.models.schemas import (
    PlatformTransactionRaw,
    BankSettlementRaw,
    NormalizedPlatformTransaction,
    NormalizedBankSettlement,
    ValidationErrorItem,
    TransactionType,
    BankEntryType,
)

PLATFORM_REQUIRED_COLUMNS = {
    "transaction_id", "transaction_type", "amount", "currency", "transaction_timestamp", "status"
}

BANK_REQUIRED_COLUMNS = {
    "bank_entry_id", "transaction_reference", "entry_type", "amount", "currency", "settlement_timestamp"
}

def parse_iso_datetime(date_str: str) -> Optional[datetime]:
    """Parse ISO-8601 string into a UTC datetime object."""
    if not date_str or not date_str.strip():
        return None
    cleaned = date_str.strip()
    try:
        # Standard fromisoformat handles +00:00 or Z
        if cleaned.endswith("Z"):
            cleaned = cleaned[:-1] + "+00:00"
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt
    except Exception:
        return None

def parse_decimal_safe(amount_str: str) -> Optional[Decimal]:
    """Parse string to Decimal without binary floating-point conversion."""
    if not amount_str or not amount_str.strip():
        return None
    try:
        val = Decimal(amount_str.strip())
        return val
    except InvalidOperation:
        return None

def ingest_platform_csv(
    file_content: str, filename: str = "platform_transactions.csv"
) -> Tuple[List[NormalizedPlatformTransaction], List[ValidationErrorItem]]:
    records: List[NormalizedPlatformTransaction] = []
    errors: List[ValidationErrorItem] = []

    reader = csv.DictReader(io.StringIO(file_content))
    if not reader.fieldnames:
        errors.append(
            ValidationErrorItem(
                source_file=filename,
                source_row=1,
                error_message="CSV file is empty or missing headers."
            )
        )
        return records, errors

    missing_cols = PLATFORM_REQUIRED_COLUMNS - set(reader.fieldnames)
    if missing_cols:
        errors.append(
            ValidationErrorItem(
                source_file=filename,
                source_row=1,
                error_message=f"Missing required columns: {', '.join(sorted(missing_cols))}"
            )
        )
        return records, errors

    for row_idx, row in enumerate(reader, start=2):
        tx_id = (row.get("transaction_id") or "").strip()
        orig_id = (row.get("original_transaction_id") or "").strip() or None
        tx_type_raw = (row.get("transaction_type") or "").strip().upper()
        amount_raw = (row.get("amount") or "").strip()
        currency_raw = (row.get("currency") or "").strip().upper()
        ts_raw = (row.get("transaction_timestamp") or "").strip()
        status_raw = (row.get("status") or "").strip().upper()
        merchant_ref = (row.get("merchant_reference") or "").strip() or None

        row_errors = []
        if not tx_id:
            row_errors.append("transaction_id is empty")

        if tx_type_raw not in ("PAYMENT", "REFUND"):
            row_errors.append(f"Invalid transaction_type '{tx_type_raw}', expected PAYMENT or REFUND")

        parsed_amount = parse_decimal_safe(amount_raw)
        if parsed_amount is None:
            row_errors.append(f"Invalid decimal amount '{amount_raw}'")
        elif parsed_amount <= 0:
            row_errors.append(f"Amount must be positive, got '{amount_raw}'")

        if not currency_raw or len(currency_raw) != 3:
            row_errors.append(f"Invalid currency code '{currency_raw}'")

        parsed_ts = parse_iso_datetime(ts_raw)
        if parsed_ts is None:
            row_errors.append(f"Invalid ISO-8601 transaction_timestamp '{ts_raw}'")

        if row_errors:
            for err in row_errors:
                errors.append(
                    ValidationErrorItem(
                        source_file=filename,
                        source_row=row_idx,
                        field="row",
                        invalid_value=str(row),
                        error_message=err,
                        raw_payload=row
                    )
                )
            continue

        records.append(
            NormalizedPlatformTransaction(
                source_file=filename,
                source_row=row_idx,
                transaction_id=tx_id,
                original_transaction_id=orig_id,
                transaction_type=TransactionType(tx_type_raw),
                amount=parsed_amount,
                currency=currency_raw,
                transaction_timestamp=parsed_ts,
                status=status_raw,
                merchant_reference=merchant_ref,
                raw_payload=row
            )
        )

    return records, errors

def ingest_bank_csv(
    file_content: str, filename: str = "bank_settlements.csv"
) -> Tuple[List[NormalizedBankSettlement], List[ValidationErrorItem]]:
    records: List[NormalizedBankSettlement] = []
    errors: List[ValidationErrorItem] = []

    reader = csv.DictReader(io.StringIO(file_content))
    if not reader.fieldnames:
        errors.append(
            ValidationErrorItem(
                source_file=filename,
                source_row=1,
                error_message="CSV file is empty or missing headers."
            )
        )
        return records, errors

    missing_cols = BANK_REQUIRED_COLUMNS - set(reader.fieldnames)
    if missing_cols:
        errors.append(
            ValidationErrorItem(
                source_file=filename,
                source_row=1,
                error_message=f"Missing required columns: {', '.join(sorted(missing_cols))}"
            )
        )
        return records, errors

    for row_idx, row in enumerate(reader, start=2):
        bank_id = (row.get("bank_entry_id") or "").strip()
        ref = (row.get("transaction_reference") or "").strip()
        entry_type_raw = (row.get("entry_type") or "").strip().upper()
        amount_raw = (row.get("amount") or "").strip()
        currency_raw = (row.get("currency") or "").strip().upper()
        ts_raw = (row.get("settlement_timestamp") or "").strip()
        batch_id = (row.get("batch_id") or "").strip() or None
        description = (row.get("description") or "").strip() or None

        row_errors = []
        if not bank_id:
            row_errors.append("bank_entry_id is empty")
        if not ref:
            row_errors.append("transaction_reference is empty")

        if entry_type_raw not in ("CREDIT", "DEBIT", "REFUND"):
            row_errors.append(f"Invalid entry_type '{entry_type_raw}', expected CREDIT, DEBIT, or REFUND")

        parsed_amount = parse_decimal_safe(amount_raw)
        if parsed_amount is None:
            row_errors.append(f"Invalid decimal amount '{amount_raw}'")
        elif parsed_amount <= 0:
            row_errors.append(f"Amount must be positive, got '{amount_raw}'")

        if not currency_raw or len(currency_raw) != 3:
            row_errors.append(f"Invalid currency code '{currency_raw}'")

        parsed_ts = parse_iso_datetime(ts_raw)
        if parsed_ts is None:
            row_errors.append(f"Invalid ISO-8601 settlement_timestamp '{ts_raw}'")

        if row_errors:
            for err in row_errors:
                errors.append(
                    ValidationErrorItem(
                        source_file=filename,
                        source_row=row_idx,
                        field="row",
                        invalid_value=str(row),
                        error_message=err,
                        raw_payload=row
                    )
                )
            continue

        records.append(
            NormalizedBankSettlement(
                source_file=filename,
                source_row=row_idx,
                bank_entry_id=bank_id,
                transaction_reference=ref,
                entry_type=BankEntryType(entry_type_raw),
                amount=parsed_amount,
                currency=currency_raw,
                settlement_timestamp=parsed_ts,
                batch_id=batch_id,
                description=description,
                raw_payload=row
            )
        )

    return records, errors
