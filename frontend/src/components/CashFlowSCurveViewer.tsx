import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, AlertTriangle } from 'lucide-react';

export interface FrontLoadedItem {
  item: string;
  proposed_rate: number;
  baseline_rate: number;
  variance_pct: number;
}

export interface SCurvePoint {
  month: number;
  cum_early_pct: number;
  cum_late_pct: number;
  cum_early: number;
  cum_late: number;
}

interface Props {
  data: {
    scurve: SCurvePoint[];
    front_loaded_warnings: FrontLoadedItem[];
  } | null;
}

export const CashFlowSCurveViewer: React.FC<Props> = ({ data }) => {
  if (!data || !data.scurve) return null;

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mt-8 animate-in fade-in zoom-in duration-500">
      <h3 className="text-xl font-bold text-gray-800 flex items-center mb-6">
        <TrendingUp className="mr-2 text-green-600" />
        Predictive Cash Flow & S-Curve Engine
      </h3>
      
      {data.front_loaded_warnings.length > 0 && (
        <div className="mb-6 p-5 bg-orange-50 border border-orange-200 rounded-lg text-sm text-orange-900 shadow-inner">
          <strong className="flex items-center mb-3 text-orange-700 text-base">
            <AlertTriangle size={20} className="mr-2" /> Unbalanced Bidding Detected (Front-Loading Risk)
          </strong>
          <ul className="list-disc pl-8 space-y-2 font-medium">
            {data.front_loaded_warnings.map((warn, i) => (
              <li key={i}>
                <span className="font-bold">{warn.item}</span>: Proposed rate ${warn.proposed_rate.toLocaleString()} vs Historical Baseline ${warn.baseline_rate.toLocaleString()} 
                <span className="text-red-600 ml-2 font-bold">(+{warn.variance_pct}%)</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      
      <div className="h-[400px] w-full mt-4 bg-gray-50 p-4 rounded-lg border border-gray-100 shadow-inner">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={data.scurve}
            margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
          >
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
            <XAxis 
              dataKey="month" 
              label={{ value: 'Project Timeline (Months)', position: 'insideBottom', offset: -10, fill: '#4b5563', fontSize: 14, fontWeight: 'bold' }} 
              tick={{fill: '#6b7280'}}
            />
            <YAxis 
              label={{ value: 'Cumulative Financial %', angle: -90, position: 'insideLeft', fill: '#4b5563', fontWeight: 'bold' }} 
              domain={[0, 100]} 
              tick={{fill: '#6b7280'}}
            />
            <Tooltip 
              formatter={(value: any) => [`${value}%`, 'Cumulative Spend']}
              labelFormatter={(label) => `Month ${label}`}
              contentStyle={{borderRadius: '8px', border: '1px solid #d1d5db', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'}}
            />
            <Legend verticalAlign="top" height={36} wrapperStyle={{fontWeight: 600, color: '#374151'}} />
            <Line type="monotone" dataKey="cum_early_pct" name="Early Dates Curve" stroke="#2563eb" strokeWidth={3} activeDot={{ r: 8 }} />
            <Line type="monotone" dataKey="cum_late_pct" name="Late Dates Curve" stroke="#9333ea" strokeWidth={3} strokeDasharray="5 5" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
