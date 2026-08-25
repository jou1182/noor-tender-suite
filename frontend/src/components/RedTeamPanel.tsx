"use client";

import React, { useState } from "react";
import { AlertTriangle, ChevronDown, ChevronUp, FileText } from "lucide-react";

interface Vulnerability {
  risk_type: string;
  description: string;
  severity: "High" | "Medium" | "Low";
  mitigation: string;
}

interface Props {
  vulnerabilities: Vulnerability[];
  rfis?: string[];
}

export function RedTeamPanel({ vulnerabilities, rfis = [] }: Props) {
  const [expanded, setExpanded] = useState<number | null>(null);

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 animate-in fade-in zoom-in duration-500">
        <h3 className="text-xl font-bold text-gray-800 flex items-center mb-4">
          <AlertTriangle className="mr-2 text-red-500" />
          Red Team Vulnerability Assessment
        </h3>
        <div className="space-y-4">
          {vulnerabilities.map((vuln, idx) => (
            <div key={idx} className="border border-gray-200 rounded-md overflow-hidden">
              <div 
                className="flex justify-between items-center p-4 bg-gray-50 cursor-pointer hover:bg-gray-100 transition"
                onClick={() => setExpanded(expanded === idx ? null : idx)}
              >
                <div className="flex items-center space-x-4">
                  <span className={`px-2 py-1 text-xs font-bold rounded-full ${vuln.severity === 'High' ? 'bg-red-100 text-red-800' : vuln.severity === 'Medium' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'}`}>
                    {vuln.severity} Risk
                  </span>
                  <span className="font-semibold text-gray-700">{vuln.risk_type}</span>
                </div>
                {expanded === idx ? <ChevronUp size={20} className="text-gray-500" /> : <ChevronDown size={20} className="text-gray-500" />}
              </div>
              {expanded === idx && (
                <div className="p-4 bg-white text-sm text-gray-600 space-y-3">
                  <div><strong className="text-gray-800">Observation:</strong> {vuln.description}</div>
                  <div><strong className="text-gray-800">Recommended Mitigation:</strong> {vuln.mitigation}</div>
                </div>
              )}
            </div>
          ))}
          {vulnerabilities.length === 0 && <p className="text-gray-500">No major vulnerabilities detected.</p>}
        </div>
      </div>

      {rfis.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 animate-in fade-in zoom-in duration-700">
          <h3 className="text-xl font-bold text-gray-800 flex items-center mb-4">
            <FileText className="mr-2 text-blue-500" />
            Automated RFI Drafts
          </h3>
          <div className="grid gap-4 md:grid-cols-2">
            {rfis.map((rfi, idx) => (
              <div key={idx} className="bg-gray-50 p-4 border rounded-md whitespace-pre-wrap text-xs text-gray-700 font-mono overflow-auto h-48">
                {rfi}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
