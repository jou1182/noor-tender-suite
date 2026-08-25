"use client";

import React, { useState } from "react";

export interface ComplianceRecord {
  clause_code: string;
  requirement: string;
  status: string;
  severity: string;
  gap_analysis: string;
}

interface Props {
  records: ComplianceRecord[];
}

export function ComplianceMatrixTable({ records }: Props) {
  const [filter, setFilter] = useState("All");

  const filtered = filter === "All" ? records : records.filter(r => r.status === filter);

  return (
    <div className="w-full overflow-x-auto shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
      <div className="p-4 bg-white border-b border-gray-200">
        <label className="mr-2 font-medium text-gray-700">Filter Status:</label>
        <select className="border border-gray-300 rounded p-1" value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="All">All</option>
          <option value="Compliant">Compliant</option>
          <option value="Non-Compliant">Non-Compliant</option>
        </select>
      </div>
      <table className="min-w-full divide-y divide-gray-300">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">Clause</th>
            <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">Requirement</th>
            <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
            <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">Severity</th>
            <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">Gap Analysis</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 bg-white">
          {filtered.map((r, i) => (
            <tr key={i}>
              <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-900">{r.clause_code}</td>
              <td className="px-3 py-4 text-sm text-gray-500">{r.requirement}</td>
              <td className="whitespace-nowrap px-3 py-4 text-sm">
                <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${r.status === 'Compliant' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                  {r.status}
                </span>
              </td>
              <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">{r.severity}</td>
              <td className="px-3 py-4 text-sm text-gray-500">{r.gap_analysis}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
