import React from 'react';
import { ShieldCheck, ShieldAlert, CheckCircle2, XCircle } from 'lucide-react';

export interface EtimadData {
  status: string;
  readiness_score: number;
  local_content_score: number;
  missing_mandatory_attachments: string[];
}

interface Props {
  data: EtimadData | null;
}

export const EtimadReadinessCard: React.FC<Props> = ({ data }) => {
  if (!data) return null;

  const isCompliant = data.status === 'COMPLIANT';

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mt-8 animate-in fade-in zoom-in duration-500">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-xl font-bold text-gray-800 flex items-center">
          {isCompliant ? <ShieldCheck className="mr-2 text-green-600" /> : <ShieldAlert className="mr-2 text-red-600" />}
          ETIMAD Compliance Readiness
        </h3>
        <span className={`px-3 py-1 rounded-full text-sm font-bold ${isCompliant ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
          {data.status}
        </span>
      </div>
      
      <div className="grid md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="font-medium text-gray-700">Overall Readiness Score</span>
              <span className="font-bold text-gray-900">{data.readiness_score}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div className={`h-2.5 rounded-full ${isCompliant ? 'bg-green-600' : 'bg-red-600'}`} style={{ width: `${data.readiness_score}%` }}></div>
            </div>
          </div>
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="font-medium text-gray-700">Local Content Score (Baseline)</span>
              <span className="font-bold text-gray-900">{data.local_content_score}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div className="bg-blue-600 h-2.5 rounded-full" style={{ width: `${Math.min(100, data.local_content_score)}%` }}></div>
            </div>
          </div>
        </div>

        <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
          <h4 className="font-semibold text-gray-800 mb-3 text-sm uppercase">Mandatory Requirements</h4>
          {data.missing_mandatory_attachments.length === 0 ? (
            <div className="flex items-center text-green-700 text-sm">
              <CheckCircle2 size={16} className="mr-2" /> All mandatory ETIMAD attachments verified.
            </div>
          ) : (
            <ul className="space-y-2">
              {data.missing_mandatory_attachments.map((item, idx) => (
                <li key={idx} className="flex items-start text-red-700 text-sm">
                  <XCircle size={16} className="mr-2 mt-0.5 flex-shrink-0" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
};
