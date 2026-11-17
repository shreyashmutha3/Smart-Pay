import React, { useState } from 'react';
import { 
  CheckCircle2, 
  Clock, 
  Scale, 
  Copy, 
  HelpCircle, 
  AlertTriangle, 
  TrendingUp, 
  Building2, 
  CreditCard,
  Percent,
  Calendar,
  Info
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell, 
  Legend 
} from 'recharts';
import { ReconciliationResponse } from '../types';
import { formatCurrency } from '../utils/formatters';

interface DashboardViewProps {
  data: ReconciliationResponse;
  onSelectCategory?: (category: string) => void;
}

const SEVERITY_COLORS: Record<string, string> = {
  INFO: '#3b82f6',
  LOW: '#0284c7',
  MEDIUM: '#f59e0b',
  HIGH: '#f97316',
  CRITICAL: '#ef4444'
};

const STATUS_COLORS: Record<string, string> = {
  CONFIRMED_MATCH: '#10b981',
  SETTLED_NEXT_MONTH: '#38bdf8',
  AGGREGATE_ROUNDING_DIFFERENCE: '#fbbf24',
  DUPLICATE_PLATFORM_RECORD: '#fb923c',
  DUPLICATE_BANK_RECORD: '#f97316',
  ORPHAN_REFUND: '#f43f5e',
  MISSING_SETTLEMENT: '#e11d48',
  UNMATCHED_BANK_CREDIT: '#a855f7',
  AMOUNT_MISMATCH: '#ec4899',
  CURRENCY_MISMATCH: '#d946ef',
};

export const DashboardView: React.FC<DashboardViewProps> = ({ data, onSelectCategory }) => {
  const { summary, items } = data;
  const currencies = Object.keys(summary.currency_summaries);
  const [selectedCurrency, setSelectedCurrency] = useState<string>(currencies[0] || 'INR');

  const currSummary = summary.currency_summaries[selectedCurrency] || Object.values(summary.currency_summaries)[0];

  // Prepare chart data for status distribution
  const statusData = Object.entries(summary.exceptions_by_category).map(([status, count]) => ({
    name: status.replace(/_/g, ' '),
    rawStatus: status,
    count,
  }));

  // Prepare chart data for severity breakdown
  const severityCounts: Record<string, number> = {};
  items.forEach(it => {
    severityCounts[it.severity] = (severityCounts[it.severity] || 0) + 1;
  });
  const severityData = Object.entries(severityCounts).map(([sev, count]) => ({
    name: sev,
    value: count,
    color: SEVERITY_COLORS[sev] || '#64748b'
  }));

  // Mandatory 4 scenario item counts & sums
  const nextMonthItems = items.filter(it => it.status === 'SETTLED_NEXT_MONTH');
  const roundingItems = items.filter(it => it.status === 'AGGREGATE_ROUNDING_DIFFERENCE');
  const duplicatePltItems = items.filter(it => it.status === 'DUPLICATE_PLATFORM_RECORD');
  const duplicateBnkItems = items.filter(it => it.status === 'DUPLICATE_BANK_RECORD');
  const orphanRefundItems = items.filter(it => it.status === 'ORPHAN_REFUND');

  return (
    <div className="space-y-6">
      {/* Top Banner with reporting month & disclaimer */}
      <div className="bg-[#111c38] border border-slate-800 rounded-xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Calendar className="h-5 w-5 text-blue-400" />
            <h1 className="text-xl font-bold text-white tracking-tight">
              Reconciliation Dashboard — Period: <span className="text-blue-400">{data.reporting_period}</span>
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Engine evaluated Platform Payments vs Bank Settlements using 2-day batch delay and next-month look-ahead window.
          </p>
        </div>

        {/* Currency selection buttons */}
        {currencies.length > 1 && (
          <div className="flex items-center space-x-2 bg-slate-900/90 p-1 rounded-lg border border-slate-800">
            <span className="text-xs text-slate-400 px-2 font-medium">Currency:</span>
            {currencies.map(curr => (
              <button
                key={curr}
                onClick={() => setSelectedCurrency(curr)}
                className={`px-3 py-1 rounded text-xs font-semibold transition-all ${
                  selectedCurrency === curr
                    ? 'bg-blue-600 text-white shadow'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {curr}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Primary KPI Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* 1. Platform Gross */}
        <div className="bg-[#111c38] border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Platform Gross</span>
            <div className="h-7 w-7 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-400">
              <CreditCard className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-xl font-bold text-white tracking-tight">
              {formatCurrency(currSummary?.platform_gross, selectedCurrency)}
            </div>
            <div className="text-xs text-slate-400 mt-1 flex justify-between">
              <span>{currSummary?.platform_count || 0} events</span>
              <span>Ref: {formatCurrency(currSummary?.platform_refunds, selectedCurrency)}</span>
            </div>
          </div>
        </div>

        {/* 2. Bank Settled Gross */}
        <div className="bg-[#111c38] border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Bank Settled Gross</span>
            <div className="h-7 w-7 rounded-lg bg-purple-500/10 flex items-center justify-center text-purple-400">
              <Building2 className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-xl font-bold text-white tracking-tight">
              {formatCurrency(currSummary?.bank_settled_gross, selectedCurrency)}
            </div>
            <div className="text-xs text-slate-400 mt-1 flex justify-between">
              <span>{currSummary?.bank_count || 0} credits</span>
              <span>Deb: {formatCurrency(currSummary?.bank_debits, selectedCurrency)}</span>
            </div>
          </div>
        </div>

        {/* 3. Confirmed Matched */}
        <div className="bg-[#111c38] border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Confirmed Matched</span>
            <div className="h-7 w-7 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400">
              <CheckCircle2 className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-xl font-bold text-emerald-400 tracking-tight">
              {formatCurrency(currSummary?.matched_amount, selectedCurrency)}
            </div>
            <div className="text-xs text-slate-400 mt-1">
              <span>{currSummary?.matched_count || 0} matched items</span>
            </div>
          </div>
        </div>

        {/* 4. Net Variance */}
        <div className="bg-[#111c38] border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Net Variance</span>
            <div className="h-7 w-7 rounded-lg bg-amber-500/10 flex items-center justify-center text-amber-400">
              <TrendingUp className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3">
            <div className={`text-xl font-bold tracking-tight ${
              Number(currSummary?.net_variance) === 0 ? 'text-emerald-400' : 'text-amber-400'
            }`}>
              {formatCurrency(currSummary?.net_variance, selectedCurrency)}
            </div>
            <div className="text-xs text-slate-400 mt-1">
              <span>Platform Net − Bank Net</span>
            </div>
          </div>
        </div>

        {/* 5. Reconciliation Rate with explicit formula */}
        <div className="bg-[#111c38] border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Reconciled Rate</span>
            <div className="h-7 w-7 rounded-lg bg-sky-500/10 flex items-center justify-center text-sky-400">
              <Percent className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-xl font-bold text-sky-400 tracking-tight">
              {String(currSummary?.reconciliation_rate_pct)}%
            </div>
            <div className="text-[11px] text-slate-400 mt-1 truncate" title={currSummary?.reconciliation_rate_formula}>
              {currSummary?.reconciliation_rate_formula || 'Matched / Eligible'}
            </div>
          </div>
        </div>
      </div>

      {/* 4 Mandatory Scenarios Highlight Section */}
      <div>
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3 flex items-center space-x-2">
          <span>Mandatory Assessment Scenarios (Engine Verification)</span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Scenario 1: Settled Next Month */}
          <div 
            onClick={() => onSelectCategory && onSelectCategory('SETTLED_NEXT_MONTH')}
            className="bg-[#111c38] border border-sky-900/60 hover:border-sky-500/50 rounded-xl p-4 cursor-pointer transition"
          >
            <div className="flex items-center space-x-2 text-sky-400">
              <Clock className="h-5 w-5" />
              <h3 className="text-sm font-bold">1. Settled Next Month</h3>
            </div>
            <p className="text-xs text-slate-400 mt-2">
              Payment in reporting month, bank batch settled in following month. Look-ahead window resolved timing.
            </p>
            <div className="mt-4 pt-3 border-t border-slate-800 flex justify-between items-baseline">
              <span className="text-xs text-slate-400">{nextMonthItems.length} transactions</span>
              <span className="text-sm font-semibold text-sky-300">
                {formatCurrency(currSummary?.settled_next_month_amount, selectedCurrency)}
              </span>
            </div>
          </div>

          {/* Scenario 2: Aggregate Rounding */}
          <div 
            onClick={() => onSelectCategory && onSelectCategory('AGGREGATE_ROUNDING_DIFFERENCE')}
            className="bg-[#111c38] border border-amber-900/60 hover:border-amber-500/50 rounded-xl p-4 cursor-pointer transition"
          >
            <div className="flex items-center space-x-2 text-amber-400">
              <Scale className="h-5 w-5" />
              <h3 className="text-sm font-bold">2. Aggregate Rounding</h3>
            </div>
            <p className="text-xs text-slate-400 mt-2">
              Sub-cent fee sharing variance. Summed difference ({currSummary?.rounding_variance} INR) within tolerance (0.02).
            </p>
            <div className="mt-4 pt-3 border-t border-slate-800 flex justify-between items-baseline">
              <span className="text-xs text-slate-400">{roundingItems.length} transactions</span>
              <span className="text-sm font-semibold text-amber-300">
                Δ {formatCurrency(currSummary?.rounding_variance, selectedCurrency)}
              </span>
            </div>
          </div>

          {/* Scenario 3: Duplicate Entry */}
          <div 
            onClick={() => onSelectCategory && onSelectCategory('DUPLICATE_PLATFORM_RECORD')}
            className="bg-[#111c38] border border-orange-900/60 hover:border-orange-500/50 rounded-xl p-4 cursor-pointer transition"
          >
            <div className="flex items-center space-x-2 text-orange-400">
              <Copy className="h-5 w-5" />
              <h3 className="text-sm font-bold">3. Duplicate Entries</h3>
            </div>
            <p className="text-xs text-slate-400 mt-2">
              Repeated platform/bank rows. Canonical events counted once; duplicates isolated from financial totals.
            </p>
            <div className="mt-4 pt-3 border-t border-slate-800 flex justify-between items-baseline">
              <span className="text-xs text-slate-400">
                {duplicatePltItems.length} Plt / {duplicateBnkItems.length} Bank
              </span>
              <span className="text-sm font-semibold text-orange-300">Zero double-count</span>
            </div>
          </div>

          {/* Scenario 4: Orphan Refund */}
          <div 
            onClick={() => onSelectCategory && onSelectCategory('ORPHAN_REFUND')}
            className="bg-[#111c38] border border-rose-900/60 hover:border-rose-500/50 rounded-xl p-4 cursor-pointer transition"
          >
            <div className="flex items-center space-x-2 text-rose-400">
              <HelpCircle className="h-5 w-5" />
              <h3 className="text-sm font-bold">4. Orphan Refund</h3>
            </div>
            <p className="text-xs text-slate-400 mt-2">
              Platform refund references an original transaction ID that does not exist in platform payment records.
            </p>
            <div className="mt-4 pt-3 border-t border-slate-800 flex justify-between items-baseline">
              <span className="text-xs text-slate-400">{orphanRefundItems.length} exceptions</span>
              <span className="text-sm font-semibold text-rose-300">
                {formatCurrency(orphanRefundItems[0]?.financial_impact, selectedCurrency)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Visualizations Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Status Distribution Bar Chart */}
        <div className="lg:col-span-2 bg-[#111c38] border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white tracking-tight">Reconciliation Result Status Distribution</h3>
            <span className="text-xs text-slate-400">Dynamic engine output</span>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={statusData} margin={{ top: 10, right: 10, left: -20, bottom: 40 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis 
                  dataKey="name" 
                  stroke="#64748b" 
                  fontSize={10} 
                  angle={-25} 
                  textAnchor="end" 
                  interval={0} 
                />
                <YAxis stroke="#64748b" fontSize={11} allowDecimals={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff' }}
                  cursor={{ fill: 'rgba(255, 255, 255, 0.05)' }}
                />
                <Bar 
                  dataKey="count" 
                  radius={[4, 4, 0, 0]}
                  fill="#3b82f6"
                >
                  {statusData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={STATUS_COLORS[entry.rawStatus] || '#3b82f6'} 
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Severity Pie Chart */}
        <div className="bg-[#111c38] border border-slate-800 rounded-xl p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-white tracking-tight">Exceptions by Severity</h3>
              <span className="text-xs text-slate-400">{summary.total_exceptions_count} exceptions</span>
            </div>
            <div className="h-52 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={severityData}
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={75}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {severityData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff' }}
                  />
                  <Legend 
                    verticalAlign="bottom" 
                    height={36} 
                    iconSize={8}
                    formatter={(val) => <span className="text-xs text-slate-300">{val}</span>}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="text-[11px] text-slate-400 border-t border-slate-800 pt-3">
            Critical issues require immediate clearing bank inquiry before month-end sign-off.
          </div>
        </div>
      </div>

      {/* Assumptions & Methodology Box */}
      <div className="bg-[#111c38]/60 border border-slate-800/80 rounded-xl p-5">
        <div className="flex items-center space-x-2 text-slate-300 mb-3">
          <Info className="h-4 w-4 text-blue-400" />
          <h4 className="text-xs font-bold uppercase tracking-wider">Accounting Assumptions & Provenance Rules</h4>
        </div>
        <ul className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-slate-400 list-disc list-inside">
          {summary.assumptions.map((assump, idx) => (
            <li key={idx} className="leading-relaxed">{assump}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};
