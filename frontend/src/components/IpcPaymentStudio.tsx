import React from 'react';
import { Calculator, FileText, Banknote, Percent, ScrollText, Download } from 'lucide-react';

export interface IPCData {
  contract_value: number;
  cumulative_gross: number;
  actual_retention: number;
  actual_recovery: number;
  liquidated_damages: number;
  total_deductions: number;
  cumulative_net: number;
  amount_due_pre_vat: number;
  vat_amount: number;
  total_certified_payment: number;
  advance_payment_balance: number;
  retention_balance_to_cap: number;
}

interface IpcPaymentStudioProps {
  data: IPCData;
}

export const IpcPaymentStudio: React.FC<IpcPaymentStudioProps> = ({ data }) => {
  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-SA', { style: 'currency', currency: 'SAR', maximumFractionDigits: 2 }).format(val);
  };

  return (
    <div className="bg-slate-900 rounded-lg shadow-2xl border border-slate-700 mt-8 mb-8 animate-in fade-in duration-500 font-sans text-slate-100">
      
      {/* Header */}
      <div className="bg-black/40 p-5 border-b border-slate-700 flex flex-col md:flex-row justify-between items-start md:items-center">
        <h3 className="text-xl font-black flex items-center text-teal-400 tracking-wide">
          <Banknote className="mr-3" size={26} />
          Interim Payment Certificate (IPC) Studio
        </h3>
        <button className="flex items-center text-[10px] uppercase tracking-widest font-bold bg-teal-600 hover:bg-teal-500 text-white px-4 py-2 rounded shadow-md mt-3 md:mt-0 transition-colors">
          <Download size={14} className="mr-1.5" /> Export Official IPC (.PDF)
        </button>
      </div>
      
      <div className="p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* IPC Primary Ledger */}
        <div className="col-span-1 lg:col-span-2">
          <div className="bg-slate-800/80 rounded-lg border border-slate-700 h-full overflow-hidden shadow-inner">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest p-4 border-b border-slate-700 bg-black/20 flex items-center">
              <ScrollText size={14} className="mr-2 text-teal-400" /> Billing Ledger Breakdown
            </h4>
            
            <div className="p-4 space-y-3">
              {/* Gross Row */}
              <div className="flex justify-between items-center py-2 border-b border-slate-700/50">
                <span className="text-sm font-semibold text-slate-300">Cumulative Gross Valuation</span>
                <span className="font-mono text-slate-200">{formatCurrency(data.cumulative_gross)}</span>
              </div>
              
              {/* Deductions Block */}
              <div className="pl-4 border-l-2 border-rose-900/50 space-y-2 py-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-400 flex items-center"><Percent size={12} className="mr-1 text-rose-500"/> Retention Holdback (10%)</span>
                  <span className="font-mono text-xs text-rose-400">-{formatCurrency(data.actual_retention)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-400 flex items-center"><Calculator size={12} className="mr-1 text-rose-500"/> Advance Payment Amortization</span>
                  <span className="font-mono text-xs text-rose-400">-{formatCurrency(data.actual_recovery)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-400 flex items-center"><FileText size={12} className="mr-1 text-rose-500"/> Liquidated Damages (Penalties)</span>
                  <span className="font-mono text-xs text-rose-400">-{formatCurrency(data.liquidated_damages)}</span>
                </div>
              </div>
              
              {/* Net Valuation */}
              <div className="flex justify-between items-center py-2 border-t border-b border-slate-700/50 bg-slate-900/30 px-2 rounded">
                <span className="text-sm font-bold text-slate-200">Cumulative Net Valuation</span>
                <span className="font-mono font-bold text-slate-200">{formatCurrency(data.cumulative_net)}</span>
              </div>
              
              {/* VAT Row */}
              <div className="flex justify-between items-center py-2 border-b border-slate-700/50 px-2">
                <span className="text-sm font-semibold text-slate-400">Standard Value Added Tax (15%)</span>
                <span className="font-mono text-slate-400">{formatCurrency(data.vat_amount)}</span>
              </div>

              {/* Total Certified Highlight */}
              <div className="flex justify-between items-center pt-4 pb-2 px-2 mt-2">
                <span className="text-lg font-black text-teal-400 uppercase tracking-widest">Total Certified Payment</span>
                <span className="text-2xl font-black font-mono text-teal-400">{formatCurrency(data.total_certified_payment)}</span>
              </div>
            </div>
            
          </div>
        </div>

        {/* Contract Cap Monitoring Cards */}
        <div className="col-span-1 space-y-4">
          
          <div className="bg-slate-800/50 p-5 rounded-lg border border-slate-700 shadow-inner">
             <div className="text-[10px] uppercase tracking-widest font-bold text-slate-500 mb-1">Contract Total Value</div>
             <div className="text-xl font-mono font-bold text-slate-300">{formatCurrency(data.contract_value)}</div>
          </div>
          
          <div className="bg-amber-950/20 p-5 rounded-lg border border-amber-900/40 shadow-inner">
             <div className="text-[10px] uppercase tracking-widest font-bold text-amber-500 mb-1">Remaining Advance Balance</div>
             <div className="text-lg font-mono font-bold text-amber-400">{formatCurrency(data.advance_payment_balance)}</div>
             <div className="text-[9px] text-amber-600/80 uppercase mt-1">To be recovered in future IPCs</div>
          </div>
          
          <div className="bg-emerald-950/20 p-5 rounded-lg border border-emerald-900/40 shadow-inner">
             <div className="text-[10px] uppercase tracking-widest font-bold text-emerald-500 mb-1">Retention Cap Remaining</div>
             <div className="text-lg font-mono font-bold text-emerald-400">{formatCurrency(data.retention_balance_to_cap)}</div>
             <div className="text-[9px] text-emerald-600/80 uppercase mt-1">Until 5% Maximum Cap is Reached</div>
          </div>
          
        </div>
        
      </div>
    </div>
  );
};
