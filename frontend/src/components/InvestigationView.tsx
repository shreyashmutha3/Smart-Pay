import React, { useState, useMemo } from 'react';
import { 
  Search, 
  Filter, 
  SlidersHorizontal, 
  X, 
  ArrowRight, 
  ExternalLink, 
  CheckCircle2, 
  AlertTriangle,
  Building2,
  CreditCard,
  ShieldAlert,
  Info
} from 'lucide-react';
import { ReconciliationItem, MatchStatus, ExceptionSeverity } from '../types';
import { formatCurrency, formatDate, getStatusLabel, getStatusBadgeClasses, getSeverityBadgeClasses } from '../utils/formatters';

interface InvestigationViewProps {
  items: ReconciliationItem[];
  initialCategory?: string;
}

export const InvestigationView: React.FC<InvestigationViewProps> = ({ items, initialCategory = 'ALL' }) => {
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>(initialCategory);
  const [selectedSeverity, setSelectedSeverity] = useState<string>('ALL');
  const [canonicalFilter, setCanonicalFilter] = useState<string>('ALL'); // 'ALL' | 'CANONICAL' | 'DUPLICATES'
  
  const [inspectingItem, setInspectingItem] = useState<ReconciliationItem | null>(null);

  // Filtered items
  const filteredItems = useMemo(() => {
    return items.filter((item) => {
      // Search match
      const query = searchQuery.toLowerCase().trim();
      if (query) {
        const matchesQuery = 
          (item.platform_id?.toLowerCase().includes(query)) ||
          (item.bank_entry_id?.toLowerCase().includes(query)) ||
          (item.bank_reference?.toLowerCase().includes(query)) ||
          (item.original_transaction_id?.toLowerCase().includes(query)) ||
          (item.reason_code?.toLowerCase().includes(query)) ||
          (item.explanation?.toLowerCase().includes(query));
        if (!matchesQuery) return false;
      }

      // Status filter
      if (selectedStatus !== 'ALL' && item.status !== selectedStatus) {
        return false;
      }

      // Severity filter
      if (selectedSeverity !== 'ALL' && item.severity !== selectedSeverity) {
        return false;
      }

      // Canonical filter
      if (canonicalFilter === 'CANONICAL' && !item.is_canonical) return false;
      if (canonicalFilter === 'DUPLICATES' && item.is_canonical) return false;

      return true;
    });
  }, [items, searchQuery, selectedStatus, selectedSeverity, canonicalFilter]);

  return (
    <div className="space-y-6">
      {/* Search and Filters Bar */}
      <div className="bg-[#111c38] border border-slate-800 rounded-xl p-5 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          {/* Search Input */}
          <div className="relative flex-1">
            <Search className="h-4 w-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by Platform ID, Bank Entry ID, Reference, or reason..."
              className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
            {searchQuery && (
              <button 
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>

          {/* Counts Badge */}
          <div className="text-xs text-slate-400 font-medium px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 shrink-0">
            Showing <span className="text-white font-bold">{filteredItems.length}</span> of {items.length} records
          </div>
        </div>

        {/* Filter Selectors */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-3 border-t border-slate-800/80">
          {/* Status / Category Dropdown */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
              Exception / Match Category
            </label>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500 font-medium"
            >
              <option value="ALL">All Categories ({items.length})</option>
              <option value="CONFIRMED_MATCH">Confirmed Matches</option>
              <optgroup label="Mandatory Assessment Cases">
                <option value="SETTLED_NEXT_MONTH">1. Settled Next Month</option>
                <option value="AGGREGATE_ROUNDING_DIFFERENCE">2. Aggregate Rounding Difference</option>
                <option value="DUPLICATE_PLATFORM_RECORD">3. Duplicate Platform Record</option>
                <option value="DUPLICATE_BANK_RECORD">3. Duplicate Bank Record</option>
                <option value="ORPHAN_REFUND">4. Orphan Refund</option>
              </optgroup>
              <optgroup label="Additional Discrepancies">
                <option value="MISSING_SETTLEMENT">Missing Settlement</option>
                <option value="UNMATCHED_BANK_CREDIT">Unmatched Bank Credit</option>
                <option value="AMOUNT_MISMATCH">Amount Mismatch</option>
                <option value="CURRENCY_MISMATCH">Currency Mismatch</option>
                <option value="POSSIBLE_MATCH_REQUIRES_REVIEW">Ambiguous / Under Review</option>
              </optgroup>
            </select>
          </div>

          {/* Severity Dropdown */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
              Severity Level
            </label>
            <select
              value={selectedSeverity}
              onChange={(e) => setSelectedSeverity(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500 font-medium"
            >
              <option value="ALL">All Severities</option>
              <option value="INFO">Info (Confirmed)</option>
              <option value="LOW">Low (Timing / Rounding)</option>
              <option value="MEDIUM">Medium (Duplicates / Incomplete)</option>
              <option value="HIGH">High (Missing / Mismatch)</option>
              <option value="CRITICAL">Critical (Currency / Systemic)</option>
            </select>
          </div>

          {/* Canonical / Duplicate Filter */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
              Canonical Accounting Status
            </label>
            <select
              value={canonicalFilter}
              onChange={(e) => setCanonicalFilter(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500 font-medium"
            >
              <option value="ALL">All Records</option>
              <option value="CANONICAL">Canonical Only (Included in Totals)</option>
              <option value="DUPLICATES">Duplicates Only (Excluded from Totals)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Data Table */}
      <div className="bg-[#111c38] border border-slate-800 rounded-xl overflow-hidden shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-900/90 text-slate-400 text-[11px] font-semibold uppercase tracking-wider border-b border-slate-800">
                <th className="py-3 px-4">Status & Reason</th>
                <th className="py-3 px-4">Platform Reference</th>
                <th className="py-3 px-4">Bank Statement Ref</th>
                <th className="py-3 px-4 text-right">Platform Amount</th>
                <th className="py-3 px-4 text-right">Bank Amount</th>
                <th className="py-3 px-4 text-right">Impact</th>
                <th className="py-3 px-4 text-center">Canonical</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-xs">
              {filteredItems.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    No transactions match the selected filters or search query.
                  </td>
                </tr>
              ) : (
                filteredItems.map((item) => (
                  <tr 
                    key={item.id}
                    onClick={() => setInspectingItem(item)}
                    className="hover:bg-slate-800/40 cursor-pointer transition"
                  >
                    {/* Status & Reason */}
                    <td className="py-3 px-4">
                      <div className="space-y-1">
                        <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold tracking-wide ${getStatusBadgeClasses(item.status)}`}>
                          {getStatusLabel(item.status)}
                        </span>
                        <div className="text-[11px] font-mono text-slate-400">
                          {item.reason_code}
                        </div>
                      </div>
                    </td>

                    {/* Platform Reference */}
                    <td className="py-3 px-4 font-mono text-slate-200">
                      {item.platform_id ? (
                        <div>
                          <div className="font-semibold text-blue-400">{item.platform_id}</div>
                          <div className="text-[10px] text-slate-400">
                            Row {item.platform_row} • {formatDate(item.platform_date)}
                          </div>
                        </div>
                      ) : (
                        <span className="text-slate-600">—</span>
                      )}
                    </td>

                    {/* Bank Reference */}
                    <td className="py-3 px-4 font-mono text-slate-200">
                      {item.bank_entry_id ? (
                        <div>
                          <div className="font-semibold text-purple-300">{item.bank_entry_id}</div>
                          <div className="text-[10px] text-slate-400">
                            Row {item.bank_row} • {formatDate(item.bank_date)}
                          </div>
                        </div>
                      ) : (
                        <span className="text-slate-600">—</span>
                      )}
                    </td>

                    {/* Platform Amount */}
                    <td className="py-3 px-4 text-right font-mono font-medium text-slate-200">
                      {item.platform_amount !== null && item.platform_amount !== undefined
                        ? formatCurrency(item.platform_amount, item.platform_currency || 'INR')
                        : '—'}
                    </td>

                    {/* Bank Amount */}
                    <td className="py-3 px-4 text-right font-mono font-medium text-slate-200">
                      {item.bank_amount !== null && item.bank_amount !== undefined
                        ? formatCurrency(item.bank_amount, item.bank_currency || 'INR')
                        : '—'}
                    </td>

                    {/* Financial Impact */}
                    <td className="py-3 px-4 text-right font-mono font-semibold">
                      {Number(item.financial_impact) > 0 ? (
                        <span className="text-amber-400">
                          {formatCurrency(item.financial_impact, item.platform_currency || item.bank_currency || 'INR')}
                        </span>
                      ) : (
                        <span className="text-emerald-400">0.00</span>
                      )}
                    </td>

                    {/* Canonical status */}
                    <td className="py-3 px-4 text-center">
                      {item.is_canonical ? (
                        <span className="inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          Canonical
                        </span>
                      ) : (
                        <span className="inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold bg-orange-500/10 text-orange-400 border border-orange-500/20">
                          Duplicate
                        </span>
                      )}
                    </td>

                    {/* Action */}
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setInspectingItem(item);
                        }}
                        className="px-2.5 py-1 rounded bg-slate-800 hover:bg-blue-600 hover:text-white text-slate-300 text-xs font-medium transition"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Side-by-Side Investigation Drawer */}
      {inspectingItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="bg-[#0f172a] border border-slate-700 rounded-2xl max-w-4xl w-full p-6 space-y-6 shadow-2xl relative my-8">
            {/* Drawer Header */}
            <div className="flex items-start justify-between border-b border-slate-800 pb-4">
              <div>
                <div className="flex items-center space-x-2">
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${getStatusBadgeClasses(inspectingItem.status)}`}>
                    {getStatusLabel(inspectingItem.status)}
                  </span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${getSeverityBadgeClasses(inspectingItem.severity)}`}>
                    {inspectingItem.severity}
                  </span>
                </div>
                <h2 className="text-lg font-bold text-white mt-1.5 font-mono">
                  Audit Investigation: {inspectingItem.id}
                </h2>
              </div>
              <button 
                onClick={() => setInspectingItem(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Side-by-Side Evidence Panels */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Left: Platform Evidence */}
              <div className="bg-[#111c38] border border-slate-800 rounded-xl p-4 space-y-3">
                <div className="flex items-center space-x-2 text-blue-400 font-semibold text-xs uppercase tracking-wider border-b border-slate-800/80 pb-2">
                  <CreditCard className="h-4 w-4" />
                  <span>Platform Transaction Evidence</span>
                </div>
                <dl className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <dt className="text-slate-500 font-medium">Transaction ID</dt>
                    <dd className="text-white font-mono font-semibold">{inspectingItem.platform_id || 'Not recorded'}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-500 font-medium">Source Row #</dt>
                    <dd className="text-slate-300 font-mono">{inspectingItem.platform_row ? `Row ${inspectingItem.platform_row}` : '—'}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-500 font-medium">Amount & Currency</dt>
                    <dd className="text-white font-mono font-bold">
                      {inspectingItem.platform_amount !== null && inspectingItem.platform_amount !== undefined
                        ? formatCurrency(inspectingItem.platform_amount, inspectingItem.platform_currency || 'INR')
                        : '—'}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-slate-500 font-medium">Transaction Date</dt>
                    <dd className="text-slate-300">{formatDate(inspectingItem.platform_date)}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-500 font-medium">Event Type</dt>
                    <dd className="text-slate-300 font-mono">{inspectingItem.platform_type || 'PAYMENT'}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-500 font-medium">Original Tx ID (Refund target)</dt>
                    <dd className="text-amber-400 font-mono font-semibold">{inspectingItem.original_transaction_id || 'None (Normal payment)'}</dd>
                  </div>
                </dl>
              </div>

              {/* Right: Bank Settlement Evidence */}
              <div className="bg-[#111c38] border border-slate-800 rounded-xl p-4 space-y-3">
                <div className="flex items-center space-x-2 text-purple-400 font-semibold text-xs uppercase tracking-wider border-b border-slate-800/80 pb-2">
                  <Building2 className="h-4 w-4" />
                  <span>Bank Settlement Evidence</span>
                </div>
                <dl className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <dt className="text-slate-500 font-medium">Bank Entry ID</dt>
                    <dd className="text-white font-mono font-semibold">{inspectingItem.bank_entry_id || 'No bank record'}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-500 font-medium">Source Row #</dt>
                    <dd className="text-slate-300 font-mono">{inspectingItem.bank_row ? `Row ${inspectingItem.bank_row}` : '—'}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-500 font-medium">Settled Amount</dt>
                    <dd className="text-white font-mono font-bold">
                      {inspectingItem.bank_amount !== null && inspectingItem.bank_amount !== undefined
                        ? formatCurrency(inspectingItem.bank_amount, inspectingItem.bank_currency || 'INR')
                        : '—'}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-slate-500 font-medium">Settlement Date</dt>
                    <dd className="text-slate-300">{formatDate(inspectingItem.bank_date)}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-500 font-medium">Batch ID</dt>
                    <dd className="text-slate-300 font-mono">{inspectingItem.batch_id || 'Direct transfer'}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-500 font-medium">Transaction Reference</dt>
                    <dd className="text-slate-300 font-mono">{inspectingItem.bank_reference || '—'}</dd>
                  </div>
                </dl>
              </div>
            </div>

            {/* Audit Assessment & Plain-English Explanation */}
            <div className="bg-[#111c38] border border-slate-800 rounded-xl p-5 space-y-3">
              <div className="flex items-center space-x-2 text-amber-400 text-xs font-bold uppercase tracking-wider">
                <ShieldAlert className="h-4 w-4" />
                <span>Deterministic Reconciliation Finding</span>
              </div>
              <p className="text-sm text-slate-200 leading-relaxed bg-slate-900/80 p-3 rounded-lg border border-slate-800 font-medium">
                {inspectingItem.explanation}
              </p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2 text-xs">
                <div className="bg-slate-900/50 p-2.5 rounded border border-slate-800">
                  <span className="text-slate-500 block">Financial Impact</span>
                  <span className="text-white font-mono font-bold text-sm">
                    {formatCurrency(inspectingItem.financial_impact, inspectingItem.platform_currency || inspectingItem.bank_currency || 'INR')}
                  </span>
                </div>
                <div className="bg-slate-900/50 p-2.5 rounded border border-slate-800">
                  <span className="text-slate-500 block">Reason Code</span>
                  <span className="text-blue-400 font-mono font-semibold">{inspectingItem.reason_code}</span>
                </div>
                <div className="bg-slate-900/50 p-2.5 rounded border border-slate-800">
                  <span className="text-slate-500 block">Canonical Status</span>
                  <span className={inspectingItem.is_canonical ? 'text-emerald-400 font-semibold' : 'text-orange-400 font-semibold'}>
                    {inspectingItem.is_canonical ? 'Counted in Ledger' : 'Isolated (Duplicate)'}
                  </span>
                </div>
              </div>

              <div className="mt-3 pt-3 border-t border-slate-800 flex items-start space-x-2 text-xs text-slate-300">
                <Info className="h-4 w-4 text-blue-400 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-white">Suggested Operator Action: </span>
                  <span>{inspectingItem.suggested_action}</span>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="flex justify-end pt-2">
              <button
                onClick={() => setInspectingItem(null)}
                className="px-5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold transition"
              >
                Close Audit View
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
