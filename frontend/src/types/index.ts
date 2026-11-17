export type MatchStatus =
  | 'CONFIRMED_MATCH'
  | 'SETTLED_NEXT_MONTH'
  | 'AGGREGATE_ROUNDING_DIFFERENCE'
  | 'DUPLICATE_PLATFORM_RECORD'
  | 'DUPLICATE_BANK_RECORD'
  | 'ORPHAN_REFUND'
  | 'MISSING_SETTLEMENT'
  | 'UNMATCHED_BANK_CREDIT'
  | 'AMOUNT_MISMATCH'
  | 'CURRENCY_MISMATCH'
  | 'INVALID_RECORD'
  | 'POSSIBLE_MATCH_REQUIRES_REVIEW';

export type ExceptionSeverity = 'INFO' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface ValidationErrorItem {
  source_file: string;
  source_row: number;
  field?: string;
  invalid_value?: string;
  error_message: string;
  raw_payload?: Record<string, any>;
}

export interface ReconciliationItem {
  id: string;
  status: MatchStatus;
  severity: ExceptionSeverity;
  reporting_period: string;

  // Platform evidence
  platform_id?: string;
  platform_row?: number;
  platform_amount?: string | number;
  platform_currency?: string;
  platform_date?: string;
  platform_type?: string;
  original_transaction_id?: string;

  // Bank evidence
  bank_entry_id?: string;
  bank_row?: number;
  bank_reference?: string;
  bank_amount?: string | number;
  bank_currency?: string;
  bank_date?: string;
  bank_type?: string;
  batch_id?: string;

  // Audit
  difference_amount: string | number;
  financial_impact: string | number;
  reason_code: string;
  explanation: string;
  suggested_action: string;
  is_canonical: boolean;
  included_in_totals: boolean;
  source_files: string[];
}

export interface CurrencySummary {
  currency: string;
  platform_gross: string | number;
  platform_refunds: string | number;
  platform_net: string | number;
  platform_count: number;

  bank_settled_gross: string | number;
  bank_debits: string | number;
  bank_net: string | number;
  bank_count: number;

  matched_count: number;
  matched_amount: string | number;

  unmatched_platform_count: number;
  unmatched_platform_amount: string | number;

  unmatched_bank_count: number;
  unmatched_bank_amount: string | number;

  settled_next_month_count: number;
  settled_next_month_amount: string | number;

  rounding_variance: string | number;
  net_variance: string | number;

  eligible_payment_count: number;
  reconciliation_rate_pct: string | number;
  reconciliation_rate_formula: string;
}

export interface ReconciliationSummary {
  total_platform_rows: number;
  total_bank_rows: number;
  canonical_platform_records: number;
  canonical_bank_records: number;
  duplicate_platform_rows: number;
  duplicate_bank_rows: number;

  total_exceptions_count: number;
  exceptions_by_category: Record<string, number>;
  currency_summaries: Record<string, CurrencySummary>;

  overall_reconciliation_rate: string | number;
  is_synthetic: boolean;
  assumptions: string[];
  warnings: string[];
}

export interface ReconciliationResponse {
  run_id: string;
  reporting_period: string;
  generated_at: string;
  summary: ReconciliationSummary;
  items: ReconciliationItem[];
  validation_errors: ValidationErrorItem[];
}

export interface ValidateResponse {
  is_valid: boolean;
  platform_row_count: number;
  bank_row_count: number;
  error_count: number;
  errors: ValidationErrorItem[];
}

export interface SampleDataResponse {
  reporting_period: string;
  platform_csv: string;
  bank_csv: string;
  expected_outcomes: {
    reporting_period: string;
    settled_next_month: string[];
    aggregate_rounding: string[];
    duplicate_platform: string[];
    duplicate_bank: string[];
    orphan_refund: string[];
    missing_settlement: string[];
    unmatched_bank_credit: string[];
    amount_mismatch: string[];
    currency_mismatch: string[];
    confirmed_normal_matches: string[];
  };
  disclaimer: string;
}
