import React from 'react';
import { PackageSearch, FileSpreadsheet, CheckCircle2, TrendingDown, TrendingUp, Calculator } from 'lucide-react';

export interface VendorEvaluation {
  vendor_name: string;
  raw_bid: number;
  scope_coverage_pct: number;
  normalized_penalty: number;
  normalized_bid: number;
  variance_to_budget: number;
  is_optimal: boolean;
}

export interface PackageMetadata {
  trade_package: string;
  item_count: number;
  estimated_value: number;
}

export interface ProcurementData {
  packages: PackageMetadata[];
  concrete_evaluation: {
    budget: number;
    vendors: VendorEvaluation[];
  };
}

interface Props {
  data: ProcurementData | null;
}

export const ProcurementStudio: React.FC<Props> = ({ data }) => {
  if (!data) return null;

  const formatCurrency = (val: number) => `SAR ${val.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;

  return (
    <div className="bg-slate-900 rounded-lg shadow-xl border border-slate-700 mt-8 mb-8 animate-in fade-in zoom-in duration-500 overflow-hidden text-slate-100 font-sans">
      <div className="bg-black/40 p-4 border-b border-slate-700 flex justify-between items-center">
        <h3 className="text-lg font-bold flex items-center text-indigo-400 tracking-wide">
          <PackageSearch className="mr-3" size={22} />
          Supplier Procurement & RFQ Evaluation Studio
        </h3>
      </div>
      
      <div className="p-6 flex flex-col xl:flex-row gap-8">
        
        {/* Auto-Clustered Trade Packages (Left Column) */}
        <div className="xl:w-1/3">
          <h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4 flex items-center border-b border-slate-700 pb-2">
            <FileSpreadsheet size={14} className="mr-2 text-slate-400" /> Auto-Clustered Trade Packages
          </h4>
          <div className="space-y-3">
            {data.packages.map((pkg, idx) => (
              <div key={idx} className="bg-slate-800/80 border border-slate-600 p-4 rounded-lg flex flex-col shadow-sm">
                <span className="text-sm font-bold text-indigo-300 mb-2">{pkg.trade_package}</span>
                <div className="flex justify-between items-center mt-1">
                  <span className="text-[10px] uppercase font-bold tracking-widest text-slate-400 bg-slate-900/50 px-2 py-1 rounded">Lines: {pkg.item_count}</span>
                  <span className="text-xs font-mono font-bold text-emerald-400">{formatCurrency(pkg.estimated_value)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Vendor Comparative Evaluation Matrix (Right Column) */}
        <div className="xl:w-2/3">
          <h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4 flex items-center border-b border-slate-700 pb-2">
            <Calculator size={14} className="mr-2 text-slate-400" /> Quotation Normalization Matrix (Concrete Package)
          </h4>
          <div className="mb-4 bg-indigo-900/20 border border-indigo-500/30 p-4 rounded-lg flex justify-between items-center shadow-inner">
            <span className="text-xs font-bold text-indigo-300 uppercase tracking-widest">Internal Target Budget Baseline</span>
            <span className="text-xl font-mono font-black text-indigo-400">{formatCurrency(data.concrete_evaluation.budget)}</span>
          </div>
          
          <div className="overflow-x-auto rounded-lg border border-slate-700">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-800/90 text-slate-400 font-mono text-[10px] uppercase tracking-wider">
                <tr>
                  <th className="px-5 py-4 border-b border-slate-700 font-semibold">Vendor / Supplier</th>
                  <th className="px-5 py-4 border-b border-slate-700 text-right font-semibold">Raw Bid</th>
                  <th className="px-5 py-4 border-b border-slate-700 text-right font-semibold">Scope Coverage</th>
                  <th className="px-5 py-4 border-b border-slate-700 text-right font-semibold">Normalization Penalty</th>
                  <th className="px-5 py-4 border-b border-slate-700 text-right font-semibold text-white">Adjusted Bid</th>
                  <th className="px-5 py-4 border-b border-slate-700 text-center font-semibold">Ranking</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50 text-slate-300">
                {data.concrete_evaluation.vendors.map((vendor, idx) => (
                  <tr key={idx} className={`transition-colors ${vendor.is_optimal ? 'bg-emerald-900/20' : 'bg-slate-900/50 hover:bg-slate-800/50'}`}>
                    <td className="px-5 py-4 font-bold text-slate-200 text-xs tracking-wide">{vendor.vendor_name}</td>
                    <td className="px-5 py-4 font-mono text-right">{formatCurrency(vendor.raw_bid)}</td>
                    <td className="px-5 py-4 font-mono text-right">
                      <span className={vendor.scope_coverage_pct < 100 ? 'text-orange-400 font-bold bg-orange-950/40 px-2 py-0.5 rounded' : 'text-slate-400'}>
                        {vendor.scope_coverage_pct}%
                      </span>
                    </td>
                    <td className="px-5 py-4 font-mono text-right text-orange-400 font-medium">
                      {vendor.normalized_penalty > 0 ? `+${formatCurrency(vendor.normalized_penalty)}` : '-'}
                    </td>
                    <td className="px-5 py-4 font-mono font-bold text-right text-white tracking-tight">
                      {formatCurrency(vendor.normalized_bid)}
                    </td>
                    <td className="px-5 py-4 flex justify-center">
                      {vendor.is_optimal ? (
                        <div className="flex items-center w-max text-[10px] uppercase tracking-wider font-bold text-emerald-400 bg-emerald-900/40 px-3 py-1.5 rounded border border-emerald-500/40 shadow-sm">
                          <CheckCircle2 size={14} className="mr-1.5" /> Optimal Target
                        </div>
                      ) : (
                        <div className={`flex items-center w-max text-[10px] uppercase tracking-wider font-bold px-3 py-1.5 rounded border shadow-sm ${vendor.variance_to_budget > 0 ? 'text-rose-400 bg-rose-900/20 border-rose-500/30' : 'text-slate-400 bg-slate-800 border-slate-600'}`}>
                           {vendor.variance_to_budget > 0 ? <TrendingUp size={14} className="mr-1.5 text-rose-500" /> : <TrendingDown size={14} className="mr-1.5" />}
                           Over Budget
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  );
};
