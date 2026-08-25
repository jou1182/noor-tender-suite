import React from 'react';
import { BarChart2, TrendingDown, TrendingUp, AlertTriangle } from 'lucide-react';

export interface BenchmarkResult {
  tender_id: number;
  client_name: string;
  rank: number;
  score: number;
  budget: number;
  is_outlier: boolean;
  variance_from_mean: number;
}

interface Props {
  data: {
    mean_score: number;
    stdev_score: number;
    rankings: BenchmarkResult[];
    outliers: number[];
  } | null;
}

export const ComparativeBenchmarking: React.FC<Props> = ({ data }) => {
  if (!data || !data.rankings) return null;

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mt-8 animate-in fade-in zoom-in duration-500">
      <h3 className="text-xl font-bold text-gray-800 flex items-center mb-6">
        <BarChart2 className="mr-2 text-indigo-600" />
        Multi-Bidder Comparative Benchmarking
      </h3>
      
      <div className="grid md:grid-cols-3 gap-4 mb-8">
        <div className="p-4 bg-indigo-50 rounded-lg border border-indigo-100">
          <p className="text-sm text-indigo-800 font-semibold uppercase">Mean Score</p>
          <p className="text-3xl font-bold text-indigo-900">{data.mean_score}</p>
        </div>
        <div className="p-4 bg-blue-50 rounded-lg border border-blue-100">
          <p className="text-sm text-blue-800 font-semibold uppercase">Bidders Analyzed</p>
          <p className="text-3xl font-bold text-blue-900">{data.rankings.length}</p>
        </div>
        <div className="p-4 bg-orange-50 rounded-lg border border-orange-100">
          <p className="text-sm text-orange-800 font-semibold uppercase">Outliers Detected</p>
          <p className="text-3xl font-bold text-orange-900">{data.outliers.length}</p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left text-gray-600">
          <thead className="text-xs text-gray-700 uppercase bg-gray-100">
            <tr>
              <th className="px-4 py-3">Rank</th>
              <th className="px-4 py-3">Bidder / Client</th>
              <th className="px-4 py-3">Technical Score</th>
              <th className="px-4 py-3">Variance</th>
              <th className="px-4 py-3">Budget</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {data.rankings.map((bidder) => (
              <tr key={bidder.tender_id} className={`border-b ${bidder.is_outlier ? 'bg-red-50' : 'hover:bg-gray-50'}`}>
                <td className="px-4 py-3 font-bold text-gray-900">#{bidder.rank}</td>
                <td className="px-4 py-3 font-medium">{bidder.client_name || `Bidder ${bidder.tender_id}`}</td>
                <td className="px-4 py-3 font-bold text-indigo-600">{bidder.score}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center">
                    {bidder.variance_from_mean > 0 ? <TrendingUp size={16} className="text-green-500 mr-1" /> : <TrendingDown size={16} className="text-red-500 mr-1" />}
                    <span className={bidder.variance_from_mean > 0 ? "text-green-600" : "text-red-600"}>
                      {bidder.variance_from_mean > 0 ? "+" : ""}{bidder.variance_from_mean}
                    </span>
                  </div>
                </td>
                <td className="px-4 py-3">${bidder.budget.toLocaleString()}</td>
                <td className="px-4 py-3">
                  {bidder.is_outlier && (
                    <span className="flex items-center text-red-600 font-semibold text-xs">
                      <AlertTriangle size={14} className="mr-1" /> Outlier
                    </span>
                  )}
                  {!bidder.is_outlier && bidder.rank === 1 && (
                    <span className="text-green-600 font-semibold text-xs bg-green-100 px-2 py-1 rounded-full">Top Pick</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
