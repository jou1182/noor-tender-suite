"use client";

import React from "react";
import { CheckCircle, XCircle } from "lucide-react";

interface Props {
  score: number;
}

export function AuditScoreCard({ score }: Props) {
  const passed = score >= 70;

  return (
    <div className={`p-6 rounded-xl shadow-md border-l-4 ${passed ? "border-green-500 bg-green-50" : "border-red-500 bg-red-50"}`}>
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-800">Tender Technical Score</h2>
          <p className="mt-1 text-sm text-gray-600">Based on multi-agent compliance evaluation.</p>
        </div>
        <div className="flex items-center space-x-2">
          {passed ? <CheckCircle className="h-8 w-8 text-green-600" /> : <XCircle className="h-8 w-8 text-red-600" />}
          <span className={`text-3xl font-black ${passed ? "text-green-700" : "text-red-700"}`}>
            {score.toFixed(1)}%
          </span>
        </div>
      </div>
      <div className="mt-4">
        {passed ? (
          <div className="p-3 bg-green-100 text-green-800 rounded-md font-medium text-sm">
            Status: Passed. The tender meets all critical requirements and is safe to proceed.
          </div>
        ) : (
          <div className="p-3 bg-red-100 text-red-800 rounded-md font-medium text-sm">
            Status: Failed. Immediate remediation required on critical gaps before submission.
          </div>
        )}
      </div>
    </div>
  );
}
