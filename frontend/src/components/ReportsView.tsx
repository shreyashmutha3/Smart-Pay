import React from 'react';
import { FileDown, Download, CheckCircle2, ShieldCheck, FileSpreadsheet, AlertCircle } from 'lucide-react';
import { ReconciliationResponse } from '../types';
import { getFullExportUrl, getExceptionsExportUrl } from '../api/client';
import { formatCurrency, formatDate } from '../utils/formatters';

interface ReportsViewProps {
  data: ReconciliationResponse;
}

export const ReportsView: React.FC<ReportsViewProps> = ({ data }) => {
  const { summary, items, run_id, reporting_period, generated_at } = data;

  const handleDownloadFull = () => {
    window.open(getFullExportUrl(run_id), '_blank');
  };

  const handleDownloadExceptions = () => {
    window.open(getExceptionsExportUrl(run_id), '_blank');
  };

  const exceptionItems = items.filter(it => it.status !== 'CONFIRMED_MATCH');

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="bg-[#111c38] border border-slate-800 rounded-xl p-6">
        <div className="flex items-center space-x-3">
          <div className="h-10 w-10 rounded-lg bg-emerald-600/20 text-emerald-400 flex items-center justify-center">
            <FileSpreadsheet className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">Reconciliation Reports & Exports</h1>
            <p className="text-xs text-slate-400 mt-1">
              Download audit-ready CSV extracts. Exported values match visible dashboard metrics and investigation records.
            </p>
          </div>
        </div>
      </div>

      {/* Export Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Full Reconciliation Export */}
        <div className="bg-[#111c38] border border-slate-800 rounded-xl p-6 flex flex-col justify-between space-y-4 hover:border-slate-700 transition">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-blue-400">Comprehensive Audit Export</span>
              <span className="text-xs text-slate-400 font-mono">{items.length} records</span>
            </div>
            <h2 className="text-lg font-bold text-white">Full Reconciliation CSV</h2>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed">
              Contains all confirmed matches, timing differences (settled next month), rounding proofs, duplicate records, and unresolved discrepancies with complete row provenance.
            </p>
          </div>

          <div className="pt-4 border-t border-slate-800/80 flex items-center justify-between">
            <div className="text-[11px] text-slate-400 font-mono">
              reconciliation_full_{run_id}.csv
            </div>
            <button
              onClick={handleDownloadFull}
              className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold flex items-center space-x-2 transition shadow-lg shadow-blue-600/20"
            >
              <Download className="h-4 w-4" />
              <span>Download CSV</span>
            </button>
          </div>
        </div>

        {/* Exceptions-Only Export */}
        <div className="bg-[#111c38] border border-slate-800 rounded-xl p-6 flex flex-col justify-between space-y-4 hover:border-slate-700 transition">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-rose-400">Exception & Variance Report</span>
              <span className="text-xs text-rose-400 font-mono">{exceptionItems.length} exceptions</span>
            </div>
            <h2 className="text-lg font-bold text-white">Exceptions-Only CSV</h2>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed">
              Focused export strictly containing items that require operational action: next-month settlements, duplicate rows, orphan refunds, amount/currency mismatches, and missing credits.
            </p>
          </div>

          <div className="pt-4 border-t border-slate-800/80 flex items-center justify-between">
            <div className="text-[11px] text-slate-400 font-mono">
              reconciliation_exceptions_{run_id}.csv
            </div>
            <button
              onClick={handleDownloadExceptions}
              className="px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold flex items-center space-x-2 transition shadow-lg shadow-rose-600/20"
            >
              <Download className="h-4 w-4" />
              <span>Download Exceptions CSV</span>
            </button>
          </div>
        </div>
      </div>

      {/* Run Metadata and Summary Card */}
      <div className="bg-[#111c38] border border-slate-800 rounded-xl p-6 space-y-4">
        <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
          <ShieldCheck className="h-4 w-4 text-emerald-400" />
          <span>Execution Run Provenance</span>
        </h3>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
          <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
            <span className="text-slate-500 block">Run Identifier</span>
            <span className="text-white font-bold">{run_id}</span>
          </div>
          <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
            <span className="text-slate-500 block">Reporting Period</span>
            <span className="text-blue-400 font-bold">{reporting_period}</span>
          </div>
          <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
            <span className="text-slate-500 block">Executed At</span>
            <span className="text-slate-300">{formatDate(generated_at)}</span>
          </div>
          <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
            <span className="text-slate-500 block">Overall Reconciled</span>
            <span className="text-emerald-400 font-bold">{String(summary.overall_reconciliation_rate)}%</span>
          </div>
        </div>
      </div>

      {/* CSV Schema Preview */}
      <div className="bg-[#111c38] border border-slate-800 rounded-xl p-6 space-y-3">
        <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">Exported CSV Column Headers</h3>
        <p className="text-xs text-slate-400">
          The following standard audit fields are included in every generated CSV export row:
        </p>
        <div className="flex flex-wrap gap-1.5 font-mono text-[11px] pt-2">
          {[
            'run_id', 'reporting_period', 'item_id', 'status', 'severity', 'reason_code',
            'is_canonical', 'included_in_totals', 'platform_id', 'platform_row', 'platform_amount',
            'platform_currency', 'platform_date', 'original_transaction_id', 'bank_entry_id',
            'bank_row', 'bank_reference', 'bank_amount', 'bank_currency', 'bank_date',
            'difference_amount', 'financial_impact', 'explanation', 'suggested_action'
          ].map((col) => (
            <span key={col} className="bg-slate-900 text-slate-300 px-2 py-1 rounded border border-slate-700">
              {col}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};
