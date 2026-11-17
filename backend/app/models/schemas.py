from decimal import Decimal
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class TransactionType(str, Enum):
    PAYMENT = "PAYMENT"
    REFUND = "REFUND"

class BankEntryType(str, Enum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"
    REFUND = "REFUND"

class ExceptionSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class MatchStatus(str, Enum):
    CONFIRMED_MATCH = "CONFIRMED_MATCH"
    SETTLED_NEXT_MONTH = "SETTLED_NEXT_MONTH"
    AGGREGATE_ROUNDING_DIFFERENCE = "AGGREGATE_ROUNDING_DIFFERENCE"
    DUPLICATE_PLATFORM_RECORD = "DUPLICATE_PLATFORM_RECORD"
    DUPLICATE_BANK_RECORD = "DUPLICATE_BANK_RECORD"
    ORPHAN_REFUND = "ORPHAN_REFUND"
    MISSING_SETTLEMENT = "MISSING_SETTLEMENT"
    UNMATCHED_BANK_CREDIT = "UNMATCHED_BANK_CREDIT"
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
    CURRENCY_MISMATCH = "CURRENCY_MISMATCH"
    INVALID_RECORD = "INVALID_RECORD"
    POSSIBLE_MATCH_REQUIRES_REVIEW = "POSSIBLE_MATCH_REQUIRES_REVIEW"

class PlatformTransactionRaw(BaseModel):
    transaction_id: str
    original_transaction_id: Optional[str] = None
    transaction_type: str = "PAYMENT"
    amount: str
    currency: str = "INR"
    transaction_timestamp: str
    status: str = "SUCCESS"
    merchant_reference: Optional[str] = None

class BankSettlementRaw(BaseModel):
    bank_entry_id: str
    transaction_reference: str
    entry_type: str = "CREDIT"
    amount: str
    currency: str = "INR"
    settlement_timestamp: str
    batch_id: Optional[str] = None
    description: Optional[str] = None

class NormalizedPlatformTransaction(BaseModel):
    source_file: str
    source_row: int
    transaction_id: str
    original_transaction_id: Optional[str] = None
    transaction_type: TransactionType
    amount: Decimal
    currency: str
    transaction_timestamp: datetime
    status: str
    merchant_reference: Optional[str] = None
    raw_payload: Dict[str, Any]
    is_canonical: bool = True
    is_duplicate: bool = False
    duplicate_group_id: Optional[str] = None
    duplicate_conflict: bool = False

class NormalizedBankSettlement(BaseModel):
    source_file: str
    source_row: int
    bank_entry_id: str
    transaction_reference: str
    entry_type: BankEntryType
    amount: Decimal
    currency: str
    settlement_timestamp: datetime
    batch_id: Optional[str] = None
    description: Optional[str] = None
    raw_payload: Dict[str, Any]
    is_canonical: bool = True
    is_duplicate: bool = False
    duplicate_group_id: Optional[str] = None
    duplicate_conflict: bool = False

class ValidationErrorItem(BaseModel):
    source_file: str
    source_row: int
    field: Optional[str] = None
    invalid_value: Optional[str] = None
    error_message: str
    raw_payload: Optional[Dict[str, Any]] = None

class ReconciliationItem(BaseModel):
    id: str
    status: MatchStatus
    severity: ExceptionSeverity
    reporting_period: str
    
    # Platform evidence
    platform_id: Optional[str] = None
    platform_row: Optional[int] = None
    platform_amount: Optional[Decimal] = None
    platform_currency: Optional[str] = None
    platform_date: Optional[str] = None
    platform_type: Optional[str] = None
    original_transaction_id: Optional[str] = None
    
    # Bank evidence
    bank_entry_id: Optional[str] = None
    bank_row: Optional[int] = None
    bank_reference: Optional[str] = None
    bank_amount: Optional[Decimal] = None
    bank_currency: Optional[str] = None
    bank_date: Optional[str] = None
    bank_type: Optional[str] = None
    batch_id: Optional[str] = None
    
    # Audit & Explainability
    difference_amount: Decimal = Decimal("0.00")
    financial_impact: Decimal = Decimal("0.00")
    reason_code: str
    explanation: str
    suggested_action: str
    is_canonical: bool = True
    included_in_totals: bool = True
    source_files: List[str] = Field(default_factory=list)

class CurrencySummary(BaseModel):
    currency: str
    platform_gross: Decimal
    platform_refunds: Decimal
    platform_net: Decimal
    platform_count: int
    
    bank_settled_gross: Decimal
    bank_debits: Decimal
    bank_net: Decimal
    bank_count: int
    
    matched_count: int
    matched_amount: Decimal
    
    unmatched_platform_count: int
    unmatched_platform_amount: Decimal
    
    unmatched_bank_count: int
    unmatched_bank_amount: Decimal
    
    settled_next_month_count: int
    settled_next_month_amount: Decimal
    
    rounding_variance: Decimal
    net_variance: Decimal
    
    eligible_payment_count: int
    reconciliation_rate_pct: Decimal
    reconciliation_rate_formula: str

class ReconciliationSummary(BaseModel):
    total_platform_rows: int
    total_bank_rows: int
    canonical_platform_records: int
    canonical_bank_records: int
    duplicate_platform_rows: int
    duplicate_bank_rows: int
    
    total_exceptions_count: int
    exceptions_by_category: Dict[str, int]
    currency_summaries: Dict[str, CurrencySummary]
    
    overall_reconciliation_rate: Decimal
    is_synthetic: bool = True
    assumptions: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

class ReconciliationResponse(BaseModel):
    run_id: str
    reporting_period: str
    generated_at: str
    summary: ReconciliationSummary
    items: List[ReconciliationItem]
    validation_errors: List[ValidationErrorItem] = Field(default_factory=list)

class ValidateResponse(BaseModel):
    is_valid: bool
    platform_row_count: int
    bank_row_count: int
    error_count: int
    errors: List[ValidationErrorItem]
