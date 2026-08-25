import React from 'react';
import { Scale, AlertCircle, ShieldAlert, CheckCircle2 } from 'lucide-react';

export interface ContractRisk {
  clause_ref: string;
  clause_text: string;
  risk_type: string;
  severity: "High" | "Medium" | "Low";
  summary: string;
  counter_clause: string;
}

interface Props {
  data: { risks: ContractRisk[] } | null;
}

export const ContractRiskMatrixTable: React.FC<Props> = ({ data }) => {
  if (!data || !data.risks || data.risks.length === 0) return null;

  const getSeverityColor = (sev: string) => {
    switch (sev) {
      case 'High': return 'bg-red-100 text-red-800 border-red-200';
      case 'Medium': return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'Low': return 'bg-blue-100 text-blue-800 border-blue-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 mt-8 animate-in fade-in zoom-in duration-500 overflow-hidden">
      <div className="bg-slate-900 p-4 border-b border-slate-800">
        <h3 className="text-lg font-bold text-white flex items-center">
          <Scale className="mr-2 text-indigo-400" />
          Contractual Risk & FIDIC Claim Exposure Engine
        </h3>
      </div>
      
      <div className="p-0 overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider w-32">Clause Ref</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Severity Ranking</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider w-1/3">Client Draft / Exposure Logic</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider w-1/3">Proposed Mitigation / Counter-Clause</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.risks.map((risk, idx) => (
              <tr key={idx} className="hover:bg-slate-50 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-slate-800 align-top">
                  {risk.clause_ref}
                </td>
                <td className="px-6 py-4 whitespace-nowrap align-top">
                  <span className={`px-3 py-1 inline-flex text-xs leading-5 font-bold rounded-full border shadow-sm ${getSeverityColor(risk.severity)}`}>
                    {risk.severity === 'High' && <ShieldAlert size={14} className="mr-1.5 inline" />}
                    {risk.severity === 'Medium' && <AlertCircle size={14} className="mr-1.5 inline" />}
                    {risk.severity} Risk
                  </span>
                  <div className="mt-2.5 text-[11px] font-bold text-gray-400 uppercase tracking-wide">{risk.risk_type}</div>
                </td>
                <td className="px-6 py-4 text-sm text-gray-600 align-top">
                  <div className="mb-3 p-3 bg-red-50 border border-red-100 rounded-md text-red-900 font-mono text-xs leading-relaxed">
                    "{risk.clause_text}"
                  </div>
                  <p className="font-medium text-slate-700 leading-snug">{risk.summary}</p>
                </td>
                <td className="px-6 py-4 text-sm text-gray-600 align-top">
                  <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-md text-emerald-900 font-mono text-xs relative leading-relaxed shadow-sm">
                    <CheckCircle2 size={18} className="absolute -top-2.5 -right-2.5 text-emerald-500 bg-white rounded-full shadow-sm" />
                    "{risk.counter_clause}"
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
