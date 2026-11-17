import { MatchStatus, ExceptionSeverity } from '../types';

export function formatCurrency(amount?: string | number | null, currency: string = 'INR'): string {
  if (amount === undefined || amount === null || amount === '') return '-';
  const num = typeof amount === 'number' ? amount : parseFloat(amount);
  if (isNaN(num)) return String(amount);

  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 3,
  }).format(num);
}

export function formatDate(isoStr?: string | null): string {
  if (!isoStr) return '-';
  try {
    const d = new Date(isoStr);
    return d.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'UTC',
    }) + ' UTC';
  } catch {
    return isoStr;
  }
}

export function getStatusLabel(status: MatchStatus): string {
  switch (status) {
    case 'CONFIRMED_MATCH':
      return 'Confirmed Match';
    case 'SETTLED_NEXT_MONTH':
      return 'Settled Next Month';
    case 'AGGREGATE_ROUNDING_DIFFERENCE':
      return 'Aggregate Rounding';
    case 'DUPLICATE_PLATFORM_RECORD':
      return 'Duplicate Platform Record';
    case 'DUPLICATE_BANK_RECORD':
      return 'Duplicate Bank Record';
    case 'ORPHAN_REFUND':
      return 'Orphan Refund';
    case 'MISSING_SETTLEMENT':
      return 'Missing Settlement';
    case 'UNMATCHED_BANK_CREDIT':
      return 'Unmatched Bank Credit';
    case 'AMOUNT_MISMATCH':
      return 'Amount Mismatch';
    case 'CURRENCY_MISMATCH':
      return 'Currency Mismatch';
    case 'INVALID_RECORD':
      return 'Invalid Record';
    case 'POSSIBLE_MATCH_REQUIRES_REVIEW':
      return 'Ambiguous / Requires Review';
    default:
      return status;
  }
}

export function getStatusBadgeClasses(status: MatchStatus): string {
  switch (status) {
    case 'CONFIRMED_MATCH':
      return 'bg-emerald-950/70 text-emerald-400 border border-emerald-800/60';
    case 'SETTLED_NEXT_MONTH':
      return 'bg-sky-950/70 text-sky-400 border border-sky-800/60';
    case 'AGGREGATE_ROUNDING_DIFFERENCE':
      return 'bg-amber-950/70 text-amber-400 border border-amber-800/60';
    case 'DUPLICATE_PLATFORM_RECORD':
    case 'DUPLICATE_BANK_RECORD':
      return 'bg-orange-950/70 text-orange-400 border border-orange-800/60';
    case 'ORPHAN_REFUND':
    case 'MISSING_SETTLEMENT':
    case 'AMOUNT_MISMATCH':
    case 'CURRENCY_MISMATCH':
      return 'bg-rose-950/70 text-rose-400 border border-rose-800/60';
    case 'UNMATCHED_BANK_CREDIT':
      return 'bg-purple-950/70 text-purple-400 border border-purple-800/60';
    default:
      return 'bg-slate-800 text-slate-300 border border-slate-700';
  }
}

export function getSeverityBadgeClasses(severity: ExceptionSeverity): string {
  switch (severity) {
    case 'INFO':
      return 'bg-slate-800 text-slate-400';
    case 'LOW':
      return 'bg-blue-900/60 text-blue-300 border border-blue-700/50';
    case 'MEDIUM':
      return 'bg-amber-950/60 text-amber-300 border border-amber-700/50';
    case 'HIGH':
      return 'bg-orange-950/70 text-orange-300 border border-orange-700/50';
    case 'CRITICAL':
      return 'bg-rose-950/80 text-rose-200 border border-rose-700/60 animate-pulse';
  }
}
