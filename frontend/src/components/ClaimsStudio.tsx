import React, { useState } from 'react';
import { Clock, Download, FileText, Calendar, DollarSign, AlertOctagon, CheckCircle } from 'lucide-react';

interface Entitlement {
  event_date: string;
  notice_date: string;
  days_elapsed: number;
  is_time_barred: boolean;
  warning: string;
}

export interface ClaimsData {
  baseline_completion: string;
  impacted_completion: string;
  eot_days: number;
  entitlement: Entitlement;
  prolongation_cost: number;
  draft_claim_letter: string;
}

interface Props {
  data: ClaimsData | null;
}

export const ClaimsStudio: React.FC<Props> = ({ data }) => {
  const [letter, setLetter] = useState(data?.draft_claim_letter ?? '');

  if (!data) return null;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 mt-8 animate-in fade-in zoom-in duration-500 overflow-hidden">
      <div className="bg-slate-900 p-4 border-b border-slate-800 flex justify-between items-center">
        <h3 className="text-lg font-bold text-white flex items-center">
          <Clock className="mr-2 text-rose-400" />
          Post-Award Variation Orders & TIA Claims Studio
        </h3>
        <button className="flex items-center bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded text-sm font-medium transition shadow-sm">
          <Download size={16} className="mr-2" /> Export Claim Notice PDF
        </button>
      </div>

      <div className="p-6 bg-slate-50">
        {/* Metrics Row */}
        <div className="grid md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex flex-col">
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wide flex items-center mb-1.5"><Calendar size={14} className="mr-1.5 text-slate-400"/> Baseline Completion</span>
            <span className="text-xl font-black text-slate-800 tracking-tight">{data.baseline_completion}</span>
          </div>
          <div className="bg-white p-4 rounded-lg border border-rose-200 shadow-sm flex flex-col relative overflow-hidden">
            <div className="absolute top-0 left-0 w-1 h-full bg-rose-500"></div>
            <span className="text-[11px] font-bold text-rose-600 uppercase tracking-wide flex items-center mb-1.5"><Calendar size={14} className="mr-1.5 text-rose-400"/> Impacted Completion</span>
            <span className="text-xl font-black text-rose-800 tracking-tight">{data.impacted_completion}</span>
          </div>
          <div className="bg-white p-4 rounded-lg border border-orange-200 shadow-sm flex flex-col relative overflow-hidden">
            <div className="absolute top-0 left-0 w-1 h-full bg-orange-500"></div>
            <span className="text-[11px] font-bold text-orange-600 uppercase tracking-wide flex items-center mb-1.5"><Clock size={14} className="mr-1.5 text-orange-400"/> Fragnet Delay (EoT)</span>
            <span className="text-xl font-black text-orange-800 tracking-tight">+{data.eot_days} Days</span>
          </div>
          <div className="bg-white p-4 rounded-lg border border-emerald-200 shadow-sm flex flex-col relative overflow-hidden">
            <div className="absolute top-0 left-0 w-1 h-full bg-emerald-500"></div>
            <span className="text-[11px] font-bold text-emerald-600 uppercase tracking-wide flex items-center mb-1.5"><DollarSign size={14} className="mr-1.5 text-emerald-400"/> Prolongation Cost</span>
            <span className="text-xl font-black text-emerald-800 tracking-tight">SAR {data.prolongation_cost.toLocaleString()}</span>
          </div>
        </div>

        {/* Entitlement Evaluation */}
        <div className={`mb-6 p-5 rounded-lg border shadow-sm ${data.entitlement.is_time_barred ? 'bg-red-50 border-red-200' : 'bg-blue-50 border-blue-200'}`}>
          <h4 className="text-base font-bold flex items-center mb-3">
            {data.entitlement.is_time_barred ? (
              <><AlertOctagon size={20} className="mr-2 text-red-600" /> <span className="text-red-900">Contractual Time-Bar Warning</span></>
            ) : (
              <><CheckCircle size={20} className="mr-2 text-blue-600" /> <span className="text-blue-900">Legal Entitlement Secured (Within 28 Days)</span></>
            )}
          </h4>
          <p className={`text-sm leading-relaxed ${data.entitlement.is_time_barred ? 'text-red-800' : 'text-blue-800'}`}>
            Engineer Event Date: <strong className="px-1">{data.entitlement.event_date}</strong> | Notice of Claim Submitted: <strong className="px-1">{data.entitlement.notice_date}</strong> 
            <br/><span className="text-xs opacity-75 mt-1 inline-block">({data.entitlement.days_elapsed} days elapsed)</span>
            <br />
            <span className="inline-block mt-2 font-medium">{data.entitlement.warning}</span>
          </p>
        </div>

        {/* Claim Generator */}
        <div>
          <h4 className="text-xs font-bold text-slate-600 uppercase flex items-center mb-2 ml-1 tracking-wider">
            <FileText size={16} className="mr-2 text-slate-400" /> Draft Notice of Claim Letter (Editable Matrix)
          </h4>
          <textarea 
            className="w-full h-64 p-5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm font-mono text-slate-700 shadow-inner leading-relaxed bg-white"
            value={letter}
            onChange={(e) => setLetter(e.target.value)}
          />
        </div>
      </div>
    </div>
  );
};
