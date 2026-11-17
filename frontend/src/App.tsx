import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { DashboardView } from './components/DashboardView';
import { ReconciliationUploadView } from './components/ReconciliationUploadView';
import { InvestigationView } from './components/InvestigationView';
import { ReportsView } from './components/ReportsView';
import { runReconciliation } from './api/client';
import { ReconciliationResponse } from './types';
import { Loader2, AlertCircle, RefreshCw } from 'lucide-react';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<string>('dashboard');
  const [data, setData] = useState<ReconciliationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [investigationCategory, setInvestigationCategory] = useState<string>('ALL');

  // Load initial reconciliation run on startup using deterministic sample data
  const loadInitialData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await runReconciliation(null, null, '2026-10', '0.02', true);
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to connect to reconciliation backend API.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  const handleSelectCategoryFromDashboard = (category: string) => {
    setInvestigationCategory(category);
    setCurrentTab('investigation');
  };

  const handleReconciliationComplete = (res: ReconciliationResponse) => {
    setData(res);
    setInvestigationCategory('ALL');
    setCurrentTab('dashboard');
  };

  return (
    <div className="min-h-screen bg-[#0b1329] text-slate-100 flex flex-col font-sans selection:bg-blue-600 selection:text-white">
      {/* Top Navigation */}
      <Navbar
        currentTab={currentTab}
        setCurrentTab={(tab) => {
          if (tab === 'investigation') setInvestigationCategory('ALL');
          setCurrentTab(tab);
        }}
        runId={data?.run_id}
        isSynthetic={data?.summary.is_synthetic}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <div className="h-96 flex flex-col items-center justify-center space-y-4">
            <Loader2 className="h-10 w-10 text-blue-500 animate-spin" />
            <div className="text-sm text-slate-400 font-medium">Connecting to SmartPay Backend & Ingesting Dataset...</div>
          </div>
        ) : error ? (
          <div className="max-w-md mx-auto my-16 bg-rose-950/40 border border-rose-800 rounded-xl p-6 text-center space-y-4">
            <AlertCircle className="h-12 w-12 text-rose-400 mx-auto" />
            <h2 className="text-lg font-bold text-white">Backend Connection Error</h2>
            <p className="text-xs text-rose-300 leading-relaxed">{error}</p>
            <button
              onClick={loadInitialData}
              className="px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold inline-flex items-center space-x-2 transition"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              <span>Retry Connection</span>
            </button>
          </div>
        ) : data ? (
          <div>
            {currentTab === 'dashboard' && (
              <DashboardView 
                data={data} 
                onSelectCategory={handleSelectCategoryFromDashboard}
              />
            )}

            {currentTab === 'reconcile' && (
              <ReconciliationUploadView 
                onReconciliationComplete={handleReconciliationComplete}
                initialPeriod={data.reporting_period}
              />
            )}

            {currentTab === 'investigation' && (
              <InvestigationView 
                items={data.items} 
                initialCategory={investigationCategory}
              />
            )}

            {currentTab === 'reports' && (
              <ReportsView data={data} />
            )}
          </div>
        ) : null}
      </main>

      {/* Operational Footer */}
      <footer className="border-t border-slate-800/80 bg-[#0f172a] py-4 text-xs text-slate-400">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div>
            <span className="font-semibold text-slate-300">SmartPay Reconciliation Engine</span> • High-Integrity Financial Settlement
          </div>
          <div className="flex items-center space-x-4 text-[11px]">
            <span>Decimal-Safe Money Representation</span>
            <span>•</span>
            <span>In-Memory Run Store</span>
            <span>•</span>
            <span className="text-blue-400">Deterministic Engine v1.0</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
