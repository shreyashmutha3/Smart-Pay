import React from 'react';
import { LayoutDashboard, FileCheck2, Search, FileDown, Layers, ShieldCheck, Sparkles } from 'lucide-react';

interface NavbarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  runId?: string;
  isSynthetic?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ currentTab, setCurrentTab, runId, isSynthetic }) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'reconcile', label: 'Reconciliation', icon: Layers },
    { id: 'investigation', label: 'Investigation Centre', icon: Search },
    { id: 'reports', label: 'Reports & Exports', icon: FileDown },
  ];

  return (
    <header className="border-b border-slate-800 bg-[#0f172a]/90 backdrop-blur sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="h-10 w-10 rounded-xl bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <FileCheck2 className="h-6 w-6 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg text-white tracking-tight">SmartPay</span>
              <span className="text-xs px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono font-medium">Reconciler</span>
            </div>
            <p className="text-[11px] text-slate-400">Payment Platform & Bank Settlement Engine</p>
          </div>
        </div>

        {/* Center Nav tabs */}
        <nav className="flex space-x-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setCurrentTab(item.id)}
                className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Icon className={`h-4 w-4 ${isActive ? 'text-blue-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Right Status pill */}
        <div className="flex items-center space-x-3">
          {isSynthetic && (
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-medium">
              <Sparkles className="h-3.5 w-3.5" />
              <span>Synthetic Data</span>
            </div>
          )}
          {runId && (
            <div className="hidden md:flex items-center space-x-1.5 text-xs text-slate-400 bg-slate-800/80 px-2.5 py-1 rounded-md border border-slate-700/60 font-mono">
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
              <span>{runId}</span>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
