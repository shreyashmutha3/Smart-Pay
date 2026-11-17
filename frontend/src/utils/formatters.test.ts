import { describe, it, expect } from 'vitest';
import { 
  formatCurrency, 
  formatDate, 
  getStatusLabel, 
  getStatusBadgeClasses, 
  getSeverityBadgeClasses 
} from './formatters';

describe('formatters', () => {
  it('formats currency correctly in INR', () => {
    const res = formatCurrency('1500.00', 'INR');
    expect(res).toContain('1,500.00');
  });

  it('formats zero or missing amounts safely', () => {
    expect(formatCurrency(null)).toBe('-');
    expect(formatCurrency(undefined)).toBe('-');
    expect(formatCurrency('')).toBe('-');
  });

  it('formats ISO dates with UTC time zone', () => {
    const formatted = formatDate('2026-10-15T10:30:00Z');
    expect(formatted).toContain('2026');
    expect(formatted).toContain('UTC');
  });

  it('maps all 4 mandatory scenario statuses to human readable labels', () => {
    expect(getStatusLabel('SETTLED_NEXT_MONTH')).toBe('Settled Next Month');
    expect(getStatusLabel('AGGREGATE_ROUNDING_DIFFERENCE')).toBe('Aggregate Rounding');
    expect(getStatusLabel('DUPLICATE_PLATFORM_RECORD')).toBe('Duplicate Platform Record');
    expect(getStatusLabel('DUPLICATE_BANK_RECORD')).toBe('Duplicate Bank Record');
    expect(getStatusLabel('ORPHAN_REFUND')).toBe('Orphan Refund');
  });

  it('returns distinct badge styles for mandatory exceptions', () => {
    const nextMonthClass = getStatusBadgeClasses('SETTLED_NEXT_MONTH');
    const duplicateClass = getStatusBadgeClasses('DUPLICATE_PLATFORM_RECORD');
    const orphanClass = getStatusBadgeClasses('ORPHAN_REFUND');

    expect(nextMonthClass).toContain('sky');
    expect(duplicateClass).toContain('orange');
    expect(orphanClass).toContain('rose');
  });

  it('assigns correct alert styles for critical severities', () => {
    const critClass = getSeverityBadgeClasses('CRITICAL');
    expect(critClass).toContain('rose');
  });
});
