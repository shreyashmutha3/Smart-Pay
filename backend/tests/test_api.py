import io
import pytest
import httpx
from decimal import Decimal
from app.main import app

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.fixture
async def async_client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest.mark.anyio
async def test_api_health(async_client):
    resp = await async_client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "smartpay-reconciliation"

@pytest.mark.anyio
async def test_api_sample_data(async_client):
    resp = await async_client.get("/api/v1/sample-data")
    assert resp.status_code == 200
    data = resp.json()
    assert "platform_csv" in data
    assert "bank_csv" in data
    assert data["reporting_period"] == "2026-10"
    assert "expected_outcomes" in data

@pytest.mark.anyio
async def test_api_validate_sample_data(async_client):
    resp = await async_client.post(
        "/api/v1/validate",
        data={"use_sample_data": "true"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_valid"] is True
    assert data["platform_row_count"] >= 30
    assert data["bank_row_count"] >= 30
    assert data["error_count"] == 0
    assert data["errors"] == []

@pytest.mark.anyio
async def test_api_validate_missing_files_error(async_client):
    resp = await async_client.post(
        "/api/v1/validate",
        data={"use_sample_data": "false"}
    )
    assert resp.status_code == 400
    assert "required" in resp.json()["detail"].lower()

@pytest.mark.anyio
async def test_api_validate_malformed_csv_missing_columns(async_client):
    bad_platform = "amount,currency\n100.00,INR\n"
    bad_bank = "amount,currency\n100.00,INR\n"
    files = {
        "platform_file": ("plat.csv", io.BytesIO(bad_platform.encode()), "text/csv"),
        "bank_file": ("bank.csv", io.BytesIO(bad_bank.encode()), "text/csv"),
    }
    resp = await async_client.post("/api/v1/validate", files=files, data={"use_sample_data": "false"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_valid"] is False
    assert data["error_count"] >= 2
    assert any("Missing required columns" in e["error_message"] for e in data["errors"])

@pytest.mark.anyio
async def test_api_validate_invalid_rows(async_client):
    bad_platform = (
        "transaction_id,original_transaction_id,transaction_type,amount,currency,transaction_timestamp,status,merchant_reference\n"
        "TXN-ERR-1,,PAYMENT,NOT_A_NUMBER,INR,2026-10-01T10:00:00Z,SUCCESS,\n"
        "TXN-ERR-2,,PAYMENT,-50.00,INR,2026-10-01T10:00:00Z,SUCCESS,\n"
        "TXN-ERR-3,,PAYMENT,100.00,INR,INVALID_DATE,SUCCESS,\n"
    )
    good_bank = (
        "bank_entry_id,transaction_reference,entry_type,amount,currency,settlement_timestamp,batch_id,description\n"
        "BNK-1,TXN-1,CREDIT,100.00,INR,2026-10-02T10:00:00Z,B1,Desc\n"
    )
    files = {
        "platform_file": ("plat.csv", io.BytesIO(bad_platform.encode()), "text/csv"),
        "bank_file": ("bank.csv", io.BytesIO(good_bank.encode()), "text/csv"),
    }
    resp = await async_client.post("/api/v1/validate", files=files, data={"use_sample_data": "false"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_valid"] is False
    assert data["error_count"] == 3
    err_msgs = [e["error_message"] for e in data["errors"]]
    assert any("Invalid decimal amount" in m for m in err_msgs)
    assert any("Amount must be positive" in m for m in err_msgs)
    assert any("Invalid ISO-8601" in m for m in err_msgs)

@pytest.mark.anyio
async def test_api_reconcile_sample_data_and_verify_scenarios(async_client):
    resp = await async_client.post(
        "/api/v1/reconcile",
        data={
            "reporting_period": "2026-10",
            "rounding_tolerance": "0.02",
            "use_sample_data": "true"
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    run_id = data["run_id"]
    summary = data["summary"]
    items = data["items"]

    # Verify summary fields
    assert summary["is_synthetic"] is True
    assert summary["total_platform_rows"] >= 34
    assert summary["total_bank_rows"] >= 33
    assert summary["duplicate_platform_rows"] == 1
    assert summary["duplicate_bank_rows"] == 1
    assert "INR" in summary["currency_summaries"]

    # Check 4 mandatory scenarios present in items
    statuses = [item["status"] for item in items]
    assert "SETTLED_NEXT_MONTH" in statuses
    assert "AGGREGATE_ROUNDING_DIFFERENCE" in statuses
    assert "DUPLICATE_PLATFORM_RECORD" in statuses
    assert "ORPHAN_REFUND" in statuses

    # Check additional scenarios
    assert "MISSING_SETTLEMENT" in statuses
    assert "UNMATCHED_BANK_CREDIT" in statuses
    assert "AMOUNT_MISMATCH" in statuses
    assert "CURRENCY_MISMATCH" in statuses

    # Verify retrieval by run_id
    get_run = await async_client.get(f"/api/v1/reconciliations/{run_id}")
    assert get_run.status_code == 200
    assert get_run.json()["run_id"] == run_id

    # Verify export full CSV
    exp_full = await async_client.get(f"/api/v1/reconciliations/{run_id}/export")
    assert exp_full.status_code == 200
    assert "text/csv" in exp_full.headers["content-type"]
    assert "SETTLED_NEXT_MONTH" in exp_full.text
    assert "CONFIRMED_MATCH" in exp_full.text

    # Verify export exceptions CSV
    exp_exc = await async_client.get(f"/api/v1/reconciliations/{run_id}/exceptions")
    assert exp_exc.status_code == 200
    assert "text/csv" in exp_exc.headers["content-type"]
    assert "CONFIRMED_MATCH" not in exp_exc.text
    assert "ORPHAN_REFUND" in exp_exc.text
    assert "DUPLICATE_PLATFORM_RECORD" in exp_exc.text

@pytest.mark.anyio
async def test_api_reconcile_file_upload(async_client):
    p_content = (
        "transaction_id,original_transaction_id,transaction_type,amount,currency,transaction_timestamp,status,merchant_reference\n"
        "TXN-CUSTOM-1,,PAYMENT,250.00,INR,2026-10-10T10:00:00Z,SUCCESS,M1\n"
    )
    b_content = (
        "bank_entry_id,transaction_reference,entry_type,amount,currency,settlement_timestamp,batch_id,description\n"
        "BNK-CUSTOM-1,TXN-CUSTOM-1,CREDIT,250.00,INR,2026-10-12T10:00:00Z,B1,Cust1\n"
    )
    files = {
        "platform_file": ("p.csv", io.BytesIO(p_content.encode()), "text/csv"),
        "bank_file": ("b.csv", io.BytesIO(b_content.encode()), "text/csv"),
    }
    resp = await async_client.post(
        "/api/v1/reconcile",
        files=files,
        data={"reporting_period": "2026-10", "rounding_tolerance": "0.02", "use_sample_data": "false"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]["is_synthetic"] is False
    assert len(data["items"]) == 1
    assert data["items"][0]["status"] == "CONFIRMED_MATCH"
    assert Decimal(str(data["items"][0]["platform_amount"])) == Decimal("250.00")

@pytest.mark.anyio
async def test_api_reconcile_invalid_period(async_client):
    resp = await async_client.post(
        "/api/v1/reconcile",
        data={"reporting_period": "2026-13", "use_sample_data": "true"}
    )
    assert resp.status_code == 400
    assert "invalid reporting_period" in resp.json()["detail"].lower()

@pytest.mark.anyio
async def test_api_not_found_endpoints(async_client):
    resp1 = await async_client.get("/api/v1/reconciliations/REC-UNKNOWN-999")
    assert resp1.status_code == 404
    resp2 = await async_client.get("/api/v1/reconciliations/REC-UNKNOWN-999/export")
    assert resp2.status_code == 404
    resp3 = await async_client.get("/api/v1/reconciliations/REC-UNKNOWN-999/exceptions")
    assert resp3.status_code == 404

@pytest.mark.anyio
async def test_financial_integrity_dynamic_metrics(async_client):
    """Verifies that KPIs are dynamically calculated by the reconciliation engine from actual rows"""
    resp = await async_client.post(
        "/api/v1/reconcile",
        data={"reporting_period": "2026-10", "use_sample_data": "true"}
    )
    data = resp.json()
    inr = data["summary"]["currency_summaries"]["INR"]
    
    # Net variance = platform_net - bank_net
    calc_net_var = Decimal(str(inr["platform_net"])) - Decimal(str(inr["bank_net"]))
    assert Decimal(str(inr["net_variance"])) == calc_net_var

    # Platform Net = platform_gross - platform_refunds
    calc_plat_net = Decimal(str(inr["platform_gross"])) - Decimal(str(inr["platform_refunds"]))
    assert Decimal(str(inr["platform_net"])) == calc_plat_net
