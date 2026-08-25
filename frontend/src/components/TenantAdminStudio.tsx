import React from 'react';
import { Building2, ShieldCheck, KeyRound, Activity, AlertOctagon, RotateCw } from 'lucide-react';

export const TenantAdminStudio: React.FC = () => {
  const tenants = [
    { id: "org_a9b8c7", name: "Technical Proposals Team", tokens: "4.2M", limit: "10M", status: "Active" },
    { id: "org_d6e5f4", name: "Commercial Estimation", tokens: "8.9M", limit: "10M", status: "Warning" },
    { id: "org_g3h2i1", name: "Contracts & Legal", tokens: "1.1M", limit: "5M", status: "Active" },
    { id: "org_j0k9l8", name: "Global Administration", tokens: "120K", limit: "Unlimited", status: "Active" }
  ];

  return (
    <div className="bg-slate-900 rounded-lg shadow-2xl border border-slate-700 mt-8 mb-16 animate-in fade-in duration-500 text-slate-100 font-sans">
      <div className="bg-black/40 p-5 border-b border-slate-700 flex flex-col md:flex-row justify-between items-start md:items-center">
        <h3 className="text-xl font-black flex items-center text-blue-400 tracking-wide">
          <Building2 className="mr-3" size={26} />
          Enterprise Multi-Tenant Administration
        </h3>
        <div className="flex items-center text-[10px] uppercase tracking-widest font-bold bg-blue-900/40 text-blue-400 border border-blue-500/30 px-3 py-1.5 rounded-full shadow-sm mt-3 md:mt-0">
          <ShieldCheck size={14} className="mr-1.5" /> Strict Data Isolation Active
        </div>
      </div>
      
      <div className="p-6">
        <h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4 border-b border-slate-700 pb-2 flex items-center">
          <Activity size={14} className="mr-2 text-slate-400" /> Active Organization Workspaces
        </h4>
        
        <div className="overflow-x-auto rounded-lg border border-slate-700 shadow-inner">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-800/90 text-slate-400 font-mono text-[10px] uppercase tracking-wider">
              <tr>
                <th className="px-4 py-3 border-b border-slate-700 font-semibold">Workspace Name</th>
                <th className="px-4 py-3 border-b border-slate-700 font-semibold">Tenant ID</th>
                <th className="px-4 py-3 border-b border-slate-700 font-semibold">LLM Token Usage</th>
                <th className="px-4 py-3 border-b border-slate-700 font-semibold">Health Status</th>
                <th className="px-4 py-3 border-b border-slate-700 font-semibold text-center">Admin Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50 text-slate-300 bg-slate-900/50">
              {tenants.map((tenant, idx) => (
                <tr key={idx} className="hover:bg-slate-800/50 transition-colors">
                  <td className="px-4 py-4 font-bold text-slate-200">{tenant.name}</td>
                  <td className="px-4 py-4 font-mono text-xs text-indigo-400">{tenant.id}</td>
                  <td className="px-4 py-4">
                    <div className="flex items-center">
                      <span className="font-mono font-bold text-emerald-400 mr-2">{tenant.tokens}</span>
                      <span className="text-[10px] text-slate-500">/ {tenant.limit}</span>
                    </div>
                  </td>
                  <td className="px-4 py-4">
                    <span className={`text-[10px] uppercase tracking-widest font-bold px-2.5 py-1 rounded-full ${
                      tenant.status === 'Active' ? 'bg-emerald-950/40 text-emerald-400 border border-emerald-500/30' : 'bg-amber-950/40 text-amber-400 border border-amber-500/30'
                    }`}>
                      {tenant.status}
                    </span>
                  </td>
                  <td className="px-4 py-4 flex justify-center space-x-3">
                    <button className="text-slate-400 hover:text-blue-400 transition-colors flex items-center text-xs font-bold" title="Rotate API Key">
                      <RotateCw size={14} className="mr-1" /> Rotate Keys
                    </button>
                    <button className="text-slate-500 hover:text-rose-400 transition-colors flex items-center text-xs font-bold" title="Suspend Workspace">
                      <AlertOctagon size={14} className="mr-1" /> Suspend
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
