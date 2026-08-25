import React from 'react';
import { FileDiff, AlertTriangle, FileMinus, FilePlus } from 'lucide-react';

export interface TextChange {
  type: "addition" | "deletion";
  content: string;
}

export interface BoqVariance {
  item: string;
  base_qty: number;
  new_qty: number;
  delta: number;
}

export interface DriftData {
  text_changes: TextChange[];
  impacted_clauses: string[];
  boq_variances: BoqVariance[];
}

interface Props {
  data: DriftData | null;
}

export const AddendumDiffViewer: React.FC<Props> = ({ data }) => {
  if (!data || (data.text_changes.length === 0 && data.boq_variances.length === 0)) return null;

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mt-8 animate-in fade-in zoom-in duration-700">
      <h3 className="text-xl font-bold text-gray-800 flex items-center mb-6">
        <FileDiff className="mr-2 text-purple-600" />
        Addenda Version Drift Engine
      </h3>
      
      <div className="grid md:grid-cols-2 gap-8">
        <div>
          <h4 className="font-semibold text-gray-800 flex items-center mb-4">
            Contractual Text Deltas
          </h4>
          <div className="bg-gray-900 rounded-lg p-4 font-mono text-xs overflow-y-auto h-64 border border-gray-800 shadow-inner">
            {data.text_changes.map((change, idx) => (
              <div key={idx} className={`mb-1 flex ${change.type === 'addition' ? 'text-green-400 bg-green-900/20' : 'text-red-400 bg-red-900/20'} px-2 py-1 rounded`}>
                {change.type === 'addition' ? <FilePlus size={14} className="mr-2 mt-0.5 flex-shrink-0" /> : <FileMinus size={14} className="mr-2 mt-0.5 flex-shrink-0" />}
                <span className="break-all">{change.content}</span>
              </div>
            ))}
          </div>
          
          {data.impacted_clauses.length > 0 && (
            <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-800">
              <strong className="flex items-center"><AlertTriangle size={16} className="mr-2 text-yellow-600" /> RE-AUDIT REQUIRED:</strong> 
              Clauses impacted by text drift: {data.impacted_clauses.join(", ")}
            </div>
          )}
        </div>

        <div>
          <h4 className="font-semibold text-gray-800 flex items-center mb-4">
            BOQ Quantity Variances
          </h4>
          <div className="overflow-x-auto border border-gray-200 rounded-lg">
            <table className="w-full text-sm text-left text-gray-600">
              <thead className="text-xs text-gray-700 uppercase bg-gray-100 border-b">
                <tr>
                  <th className="px-4 py-3">Item</th>
                  <th className="px-4 py-3">Base Qty</th>
                  <th className="px-4 py-3">Addendum Qty</th>
                  <th className="px-4 py-3">Delta</th>
                </tr>
              </thead>
              <tbody>
                {data.boq_variances.map((variance, idx) => (
                  <tr key={idx} className="border-b hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">{variance.item}</td>
                    <td className="px-4 py-3">{variance.base_qty}</td>
                    <td className="px-4 py-3">{variance.new_qty}</td>
                    <td className="px-4 py-3">
                      <span className={`font-bold ${variance.delta > 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {variance.delta > 0 ? "+" : ""}{variance.delta}
                      </span>
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
