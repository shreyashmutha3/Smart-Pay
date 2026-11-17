from decimal import Decimal
from typing import Optional, Dict
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response
from fastapi.responses import PlainTextResponse

from app.models.schemas import (
    ReconciliationResponse,
    ValidateResponse,
    ValidationErrorItem,
)
from app.services.data_generator import generate_synthetic_data
from app.services.ingestion import ingest_platform_csv, ingest_bank_csv
from app.services.reconciliation import run_reconciliation
from app.services.export import export_full_reconciliation_csv, export_exceptions_csv

router = APIRouter(prefix="/api/v1")

# In-memory session store for reconciliation runs
RUNS_STORE: Dict[str, ReconciliationResponse] = {}

@router.get("/sample-data")
def get_sample_data():
    """Returns deterministic synthetic sample datasets and metadata."""
    platform_csv, bank_csv, expected = generate_synthetic_data()
    return {
        "reporting_period": expected["reporting_period"],
        "platform_csv": platform_csv,
        "bank_csv": bank_csv,
        "expected_outcomes": expected,
        "disclaimer": "This synthetic dataset contains 34 platform transactions and 33 bank entries deterministically generated with seed 42 to demonstrate all 4 mandatory gap scenarios and edge cases."
    }

@router.post("/validate", response_model=ValidateResponse)
async def validate_csvs(
    platform_file: Optional[UploadFile] = File(None),
    bank_file: Optional[UploadFile] = File(None),
    use_sample_data: bool = Form(False)
):
    """Validates schemas, headers, date formats, currencies, and decimal amounts."""
    if use_sample_data:
        p_csv, b_csv, _ = generate_synthetic_data()
        platform_content = p_csv
        bank_content = b_csv
        p_filename = "synthetic_platform_transactions.csv"
        b_filename = "synthetic_bank_settlements.csv"
    else:
        if not platform_file or not bank_file:
            raise HTTPException(status_code=400, detail="Both platform_file and bank_file are required when not using sample data.")
        p_bytes = await platform_file.read()
        b_bytes = await bank_file.read()
        platform_content = p_bytes.decode("utf-8", errors="replace")
        bank_content = b_bytes.decode("utf-8", errors="replace")
        p_filename = platform_file.filename or "platform.csv"
        b_filename = bank_file.filename or "bank.csv"

    p_records, p_errors = ingest_platform_csv(platform_content, p_filename)
    b_records, b_errors = ingest_bank_csv(bank_content, b_filename)

    all_errors = p_errors + b_errors
    return ValidateResponse(
        is_valid=(len(all_errors) == 0),
        platform_row_count=len(p_records),
        bank_row_count=len(b_records),
        error_count=len(all_errors),
        errors=all_errors
    )

@router.post("/reconcile", response_model=ReconciliationResponse)
async def reconcile_data(
    platform_file: Optional[UploadFile] = File(None),
    bank_file: Optional[UploadFile] = File(None),
    reporting_period: str = Form("2026-10"),
    rounding_tolerance: str = Form("0.02"),
    use_sample_data: bool = Form(False)
):
    """Executes deterministic reconciliation for a chosen reporting month."""
    # Validate reporting_period format
    try:
        parts = reporting_period.split("-")
        if len(parts) != 2 or len(parts[0]) != 4 or not (1 <= int(parts[1]) <= 12):
            raise ValueError()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid reporting_period format. Expected 'YYYY-MM' (e.g. 2026-10).")

    try:
        tolerance = Decimal(rounding_tolerance)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid rounding_tolerance. Must be a decimal number.")

    is_synthetic = use_sample_data
    if use_sample_data:
        p_csv, b_csv, _ = generate_synthetic_data()
        platform_content = p_csv
        bank_content = b_csv
        p_filename = "synthetic_platform_transactions.csv"
        b_filename = "synthetic_bank_settlements.csv"
    else:
        if not platform_file or not bank_file:
            raise HTTPException(status_code=400, detail="Both platform_file and bank_file are required.")
        p_bytes = await platform_file.read()
        b_bytes = await bank_file.read()
        if not p_bytes or not b_bytes:
            raise HTTPException(status_code=400, detail="Uploaded CSV files cannot be empty.")
        platform_content = p_bytes.decode("utf-8", errors="replace")
        bank_content = b_bytes.decode("utf-8", errors="replace")
        p_filename = platform_file.filename or "platform.csv"
        b_filename = bank_file.filename or "bank.csv"

    p_records, p_errors = ingest_platform_csv(platform_content, p_filename)
    b_records, b_errors = ingest_bank_csv(bank_content, b_filename)

    response = run_reconciliation(
        platform_records=p_records,
        bank_records=b_records,
        reporting_period=reporting_period,
        rounding_tolerance=tolerance,
        is_synthetic=is_synthetic
    )

    response.validation_errors = p_errors + b_errors

    # Save to in-memory store
    RUNS_STORE[response.run_id] = response
    return response

@router.get("/reconciliations/{run_id}", response_model=ReconciliationResponse)
def get_reconciliation_run(run_id: str):
    """Retrieves an existing reconciliation run from in-memory store."""
    if run_id not in RUNS_STORE:
        raise HTTPException(status_code=404, detail=f"Reconciliation run '{run_id}' not found. In-memory runs do not survive server restarts.")
    return RUNS_STORE[run_id]

@router.get("/reconciliations/{run_id}/export")
def export_reconciliation_csv(run_id: str):
    """Exports full reconciliation results as CSV."""
    if run_id not in RUNS_STORE:
        raise HTTPException(status_code=404, detail=f"Reconciliation run '{run_id}' not found.")
    run = RUNS_STORE[run_id]
    csv_data = export_full_reconciliation_csv(run)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=reconciliation_full_{run_id}.csv"}
    )

@router.get("/reconciliations/{run_id}/exceptions")
def export_reconciliation_exceptions_csv(run_id: str):
    """Exports exception-only report as CSV."""
    if run_id not in RUNS_STORE:
        raise HTTPException(status_code=404, detail=f"Reconciliation run '{run_id}' not found.")
    run = RUNS_STORE[run_id]
    csv_data = export_exceptions_csv(run)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=reconciliation_exceptions_{run_id}.csv"}
    )
