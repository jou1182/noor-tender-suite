import React from 'react';
import { Calculator, CheckCircle, AlertTriangle } from 'lucide-react';

export interface EngineeringCheck {
  check_name: string;
  calculated_value: number;
  required_value: number;
  unit: string;
  is_safe: boolean;
  warning: string;
}

interface Props {
  data: { checks: EngineeringCheck[] } | null;
}

export const EngineeringCalculationCard: React.FC<Props> = ({ data }) => {
  if (!data || !data.checks || data.checks.length === 0) return null;

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mt-8 animate-in fade-in zoom-in duration-500">
      <h3 className="text-xl font-bold text-gray-800 flex items-center mb-6">
        <Calculator className="mr-2 text-blue-600" />
        Engineering Calculation & Math Validation Engine
      </h3>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-2">
        {data.checks.map((check, idx) => (
          <div key={idx} className={`p-5 rounded-lg border ${check.is_safe ? 'bg-gray-50 border-gray-200' : 'bg-red-50 border-red-200 shadow-sm'}`}>
            <div className="flex justify-between items-start mb-2">
              <h4 className="font-semibold text-gray-800 text-sm">{check.check_name}</h4>
              {check.is_safe ? <CheckCircle size={20} className="text-green-500" /> : <AlertTriangle size={20} className="text-red-500" />}
            </div>
            
            <div className="flex items-center space-x-8 my-4">
              <div>
                <p className="text-xs text-gray-500 uppercase font-semibold">Calculated</p>
                <p className={`text-xl font-bold ${check.is_safe ? 'text-gray-900' : 'text-red-700'}`}>
                  {check.calculated_value} <span className="text-xs font-normal text-gray-500">{check.unit}</span>
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500 uppercase font-semibold">Threshold Limit</p>
                <p className="text-xl font-bold text-gray-700">
                  {check.required_value} <span className="text-xs font-normal text-gray-500">{check.unit}</span>
                </p>
              </div>
            </div>
            
            {!check.is_safe && (
              <p className="text-xs font-medium text-red-600 mt-2 bg-red-100 p-2.5 rounded shadow-inner">
                {check.warning}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
