import React, { useState } from 'react';
import { 
  UploadCloud, 
  FileText, 
  CheckCircle2, 
  AlertCircle, 
  Sparkles, 
  ArrowRight, 
  Sliders, 
  Calendar,
  Layers,
  HelpCircle
} from 'lucide-react';
import { validateData, runReconciliation } from '../api/client';
import { ReconciliationResponse, ValidateResponse, ValidationErrorItem } from '../types';

interface ReconciliationUploadViewProps {
  onReconciliationComplete: (res: ReconciliationResponse) => void;
  initialPeriod?: string;
}

export const ReconciliationUploadView: React.FC<ReconciliationUploadViewProps> = ({ 
  onReconciliationComplete,
  initialPeriod = '2026-10'
}) => {
  const [useSampleData, setUseSampleData] = useState<boolean>(true);
  const [reportingPeriod, setReportingPeriod] = useState<string>(initialPeriod);
  const [roundingTolerance, setRoundingTolerance] = useState<string>('0.02');
  
  const [platformFile, setPlatformFile] = useState<File | null>(null);
  const [bankFile, setBankFile] = useState<File | null>(null);

  const [isValidating, setIsValidating] = useState<boolean>(false);
  const [validationResult, setValidationResult] = useState<ValidateResponse | null>(null);

  const [isReconciling, setIsReconciling] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleValidate = async () => {
    setErrorMsg(null);
    setIsValidating(true);
    try {
      const res = await validateData(platformFile, bankFile, useSampleData);
      setValidationResult(res);
    } catch (err: any) {
      setErrorMsg(err.message || 'Validation failed');
    } finally {
      setIsValidating(false);
    }
  };

  const handleExecute = async () => {
    setErrorMsg(null);
    setIsReconciling(true);
    try {
      const res = await runReconciliation(
        platformFile,
        bankFile,
        reportingPeriod,
        roundingTolerance,
        useSampleData
      );
      onReconciliationComplete(res);
    } catch (err: any) {
      setErrorMsg(err.message || 'Reconciliation execution failed');
    } finally {
      setIsReconciling(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Title */}
      <div className="bg-[#111c38] border border-slate-800 rounded-xl p-6">
        <div className="flex items-center space-x-3">
          <div className="h-10 w-10 rounded-lg bg-blue-600/20 text-blue-400 flex items-center justify-center">
            <Layers className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">Run Reconciliation</h1>
            <p className="text-xs text-slate-400 mt-1">
              Select reporting period, configure rules, and provide Platform Transactions and Bank Settlement records.
            </p>
          </div>
        </div>
      </div>

      {/* Configuration Bar */}
      <div className="bg-[#111c38] border border-slate-800 rounded-xl p-6 space-y-5">
        <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
          <Sliders className="h-4 w-4 text-blue-400" />
          <span>Period & Reconciliation Rules</span>
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {/* Reporting Period */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5 flex items-center space-x-1.5">
              <Calendar className="h-3.5 w-3.5 text-slate-400" />
              <span>Reporting Month (YYYY-MM)</span>
            </label>
            <input
              type="text"
              value={reportingPeriod}
              onChange={(e) => setReportingPeriod(e.target.value)}
              placeholder="2026-10"
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500 font-mono"
            />
            <p className="text-[11px] text-slate-400 mt-1">
              Look-ahead window will automatically search into the following calendar month.
            </p>
          </div>

          {/* Rounding Tolerance */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5 flex items-center space-x-1.5">
              <HelpCircle className="h-3.5 w-3.5 text-slate-400" />
              <span>Aggregate Rounding Tolerance (INR)</span>
            </label>
            <input
              type="text"
              value={roundingTolerance}
              onChange={(e) => setRoundingTolerance(e.target.value)}
              placeholder="0.02"
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500 font-mono"
            />
            <p className="text-[11px] text-slate-400 mt-1">
              Evaluated across comparable canonical populations; differences within this threshold generate arithmetic proof.
            </p>
          </div>
        </div>
      </div>

      {/* Dataset Selection Mode */}
      <div className="bg-[#111c38] border border-slate-800 rounded-xl p-6 space-y-5">
        <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
          <FileText className="h-4 w-4 text-blue-400" />
          <span>Source Datasets</span>
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            onClick={() => setUseSampleData(true)}
            className={`p-4 rounded-xl border cursor-pointer transition ${
              useSampleData
                ? 'bg-blue-600/10 border-blue-500 text-white shadow-md shadow-blue-500/5'
                : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
            }`}
          >
            <div className="flex items-center space-x-2.5">
              <div className={`h-4 w-4 rounded-full border flex items-center justify-center ${
                useSampleData ? 'border-blue-400 bg-blue-500' : 'border-slate-600'
              }`}>
                {useSampleData && <div className="h-1.5 w-1.5 rounded-full bg-white" />}
              </div>
              <span className="font-semibold text-sm text-white">Deterministic Synthetic Dataset</span>
              <span className="text-[10px] bg-amber-500/10 text-amber-400 px-1.5 py-0.5 rounded border border-amber-500/20">Recommended</span>
            </div>
            <p className="text-xs text-slate-400 mt-2 pl-6">
              Loads 35+ verified records containing all 4 mandatory scenarios (Next-Month Settlement, Aggregate Rounding, Duplicates, Orphan Refund) and edge cases.
            </p>
          </div>

          <div
            onClick={() => setUseSampleData(false)}
            className={`p-4 rounded-xl border cursor-pointer transition ${
              !useSampleData
                ? 'bg-blue-600/10 border-blue-500 text-white shadow-md shadow-blue-500/5'
                : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
            }`}
          >
            <div className="flex items-center space-x-2.5">
              <div className={`h-4 w-4 rounded-full border flex items-center justify-center ${
                !useSampleData ? 'border-blue-400 bg-blue-500' : 'border-slate-600'
              }`}>
                {!useSampleData && <div className="h-1.5 w-1.5 rounded-full bg-white" />}
              </div>
              <span className="font-semibold text-sm text-white">Upload Custom CSV Files</span>
            </div>
            <p className="text-xs text-slate-400 mt-2 pl-6">
              Upload your own platform transactions CSV and bank settlements CSV conforming to the data contracts.
            </p>
          </div>
        </div>

        {/* File Dropzones when Custom CSV is selected */}
        {!useSampleData && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-3 border-t border-slate-800">
            {/* Platform CSV */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-2">Platform Transactions CSV</label>
              <div className="border-2 border-dashed border-slate-700 hover:border-blue-500 rounded-xl p-5 text-center bg-slate-900/40 transition">
                <UploadCloud className="h-8 w-8 text-slate-400 mx-auto mb-2" />
                <input
                  type="file"
                  accept=".csv"
                  onChange={(e) => setPlatformFile(e.target.files?.[0] || null)}
                  className="hidden"
                  id="platform-file"
                />
                <label htmlFor="platform-file" className="cursor-pointer text-xs font-medium text-blue-400 hover:text-blue-300">
                  {platformFile ? platformFile.name : 'Choose Platform CSV'}
                </label>
                <p className="text-[10px] text-slate-400 mt-1">Requires transaction_id, amount, currency, timestamp, status</p>
              </div>
            </div>

            {/* Bank CSV */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-2">Bank Settlements CSV</label>
              <div className="border-2 border-dashed border-slate-700 hover:border-blue-500 rounded-xl p-5 text-center bg-slate-900/40 transition">
                <UploadCloud className="h-8 w-8 text-slate-400 mx-auto mb-2" />
                <input
                  type="file"
                  accept=".csv"
                  onChange={(e) => setBankFile(e.target.files?.[0] || null)}
                  className="hidden"
                  id="bank-file"
                />
                <label htmlFor="bank-file" className="cursor-pointer text-xs font-medium text-blue-400 hover:text-blue-300">
                  {bankFile ? bankFile.name : 'Choose Bank Settlement CSV'}
                </label>
                <p className="text-[10px] text-slate-400 mt-1">Requires bank_entry_id, transaction_reference, amount, timestamp</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Validation Result Box */}
      {validationResult && (
        <div className={`p-4 rounded-xl border ${
          validationResult.is_valid
            ? 'bg-emerald-950/40 border-emerald-800 text-emerald-300'
            : 'bg-rose-950/40 border-rose-800 text-rose-300'
        }`}>
          <div className="flex items-center space-x-2">
            {validationResult.is_valid ? (
              <CheckCircle2 className="h-5 w-5 text-emerald-400" />
            ) : (
              <AlertCircle className="h-5 w-5 text-rose-400" />
            )}
            <h3 className="text-sm font-bold">
              {validationResult.is_valid
                ? `Validation Passed: ${validationResult.platform_row_count} platform rows, ${validationResult.bank_row_count} bank rows ready.`
                : `Validation Found ${validationResult.error_count} Schema / Semantic Error(s)`}
            </h3>
          </div>

          {!validationResult.is_valid && validationResult.errors.length > 0 && (
            <div className="mt-3 space-y-1.5 max-h-48 overflow-y-auto pr-2">
              {validationResult.errors.map((err, idx) => (
                <div key={idx} className="text-xs bg-black/30 p-2 rounded border border-rose-900/50 flex items-start space-x-2 font-mono">
                  <span className="text-rose-400 font-semibold shrink-0">Row {err.source_row}:</span>
                  <span>{err.error_message}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Global Error Banner */}
      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-300 flex items-center space-x-2 text-xs">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex items-center justify-end space-x-3">
        <button
          onClick={handleValidate}
          disabled={isValidating || isReconciling}
          className="px-4 py-2.5 rounded-lg border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-200 text-sm font-medium transition disabled:opacity-50"
        >
          {isValidating ? 'Validating...' : 'Validate Schema & Rows'}
        </button>

        <button
          onClick={handleExecute}
          disabled={isReconciling || isValidating}
          className="px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold shadow-lg shadow-blue-600/30 flex items-center space-x-2 transition disabled:opacity-50"
        >
          {isReconciling ? (
            <span>Processing Engine...</span>
          ) : (
            <>
              <span>Execute Reconciliation</span>
              <ArrowRight className="h-4 w-4" />
            </>
          )}
        </button>
      </div>
    </div>
  );
};
