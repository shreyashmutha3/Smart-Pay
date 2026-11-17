import csv
import io
from typing import List
from app.models.schemas import ReconciliationResponse, ReconciliationItem

CSV_HEADERS = [
    "run_id",
    "reporting_period",
    "item_id",
    "status",
    "severity",
    "reason_code",
    "is_canonical",
    "included_in_totals",
    "platform_id",
    "platform_row",
    "platform_type",
    "platform_amount",
    "platform_currency",
    "platform_date",
    "original_transaction_id",
    "bank_entry_id",
    "bank_row",
    "bank_reference",
    "bank_type",
    "bank_amount",
    "bank_currency",
    "bank_date",
    "batch_id",
    "difference_amount",
    "financial_impact",
    "explanation",
    "suggested_action"
]

def item_to_row(run_id: str, reporting_period: str, item: ReconciliationItem) -> dict:
    return {
        "run_id": run_id,
        "reporting_period": reporting_period,
        "item_id": item.id,
        "status": item.status.value,
        "severity": item.severity.value,
        "reason_code": item.reason_code,
        "is_canonical": "YES" if item.is_canonical else "NO",
        "included_in_totals": "YES" if item.included_in_totals else "NO",
        "platform_id": item.platform_id or "",
        "platform_row": item.platform_row if item.platform_row is not None else "",
        "platform_type": item.platform_type or "",
        "platform_amount": str(item.platform_amount) if item.platform_amount is not None else "",
        "platform_currency": item.platform_currency or "",
        "platform_date": item.platform_date or "",
        "original_transaction_id": item.original_transaction_id or "",
        "bank_entry_id": item.bank_entry_id or "",
        "bank_row": item.bank_row if item.bank_row is not None else "",
        "bank_reference": item.bank_reference or "",
        "bank_type": item.bank_type or "",
        "bank_amount": str(item.bank_amount) if item.bank_amount is not None else "",
        "bank_currency": item.bank_currency or "",
        "bank_date": item.bank_date or "",
        "batch_id": item.batch_id or "",
        "difference_amount": str(item.difference_amount),
        "financial_impact": str(item.financial_impact),
        "explanation": item.explanation,
        "suggested_action": item.suggested_action
    }

def export_full_reconciliation_csv(response: ReconciliationResponse) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_HEADERS, lineterminator="\n")
    writer.writeheader()
    for item in response.items:
        writer.writerow(item_to_row(response.run_id, response.reporting_period, item))
    return output.getvalue()

def export_exceptions_csv(response: ReconciliationResponse) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_HEADERS, lineterminator="\n")
    writer.writeheader()
    for item in response.items:
        # Exclude CONFIRMED_MATCH items
        if item.status.value != "CONFIRMED_MATCH":
            writer.writerow(item_to_row(response.run_id, response.reporting_period, item))
    return output.getvalue()
