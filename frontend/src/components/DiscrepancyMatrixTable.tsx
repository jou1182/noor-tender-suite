import React from 'react';
import { AlertOctagon } from 'lucide-react';

export interface Discrepancy {
  activity: string;
  boq_quantity: number;
  method_rate: number;
  p6_duration: number;
  expected_duration: number;
  variance_percent: number;
  severity: string;
  conflict: string;
}

interface Props {
  discrepancies: Discrepancy[];
}

export const DiscrepancyMatrixTable: React.FC<Props> = ({ discrepancies }) => {
  if (!discrepancies || discrepancies.length === 0) return null;

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 animate-in fade-in zoom-in duration-500">
      <h3 className="text-xl font-bold text-gray-800 flex items-center mb-6">
        <AlertOctagon className="mr-2 text-orange-500" />
        BOQ vs Schedule Reconciliation Engine
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left text-gray-600">
          <thead className="text-xs text-gray-700 uppercase bg-gray-100">
            <tr>
              <th className="px-4 py-3">Activity</th>
              <th className="px-4 py-3">BOQ Qty</th>
              <th className="px-4 py-3">Method Rate/Day</th>
              <th className="px-4 py-3">P6 Duration</th>
              <th className="px-4 py-3">Expected Duration</th>
              <th className="px-4 py-3">Variance</th>
              <th className="px-4 py-3">Severity</th>
            </tr>
          </thead>
          <tbody>
            {discrepancies.map((d, idx) => (
              <tr key={idx} className="border-b hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-900">{d.activity}</td>
                <td className="px-4 py-3">{d.boq_quantity}</td>
                <td className="px-4 py-3">{d.method_rate}</td>
                <td className="px-4 py-3 font-bold">{d.p6_duration}d</td>
                <td className="px-4 py-3">{d.expected_duration}d</td>
                <td className="px-4 py-3 text-red-600 font-bold">{d.variance_percent}%</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 text-xs font-bold rounded-full ${d.severity === 'High' ? 'bg-red-100 text-red-800' : 'bg-orange-100 text-orange-800'}`}>
                    {d.severity}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
