"use client";
import React, { useState } from 'react';
import { Edit3, CheckCircle, Download } from 'lucide-react';

interface RfiStudioProps {
  initialRfis: string[];
}

export const RfiStudio: React.FC<RfiStudioProps> = ({ initialRfis }) => {
  const [rfis, setRfis] = useState<{ text: string, approved: boolean }[]>(
    initialRfis.map(r => ({ text: r, approved: false }))
  );

  const updateText = (index: number, text: string) => {
    const newRfis = [...rfis];
    newRfis[index].text = text;
    setRfis(newRfis);
  };

  const toggleApprove = (index: number) => {
    const newRfis = [...rfis];
    newRfis[index].approved = !newRfis[index].approved;
    setRfis(newRfis);
  };

  const downloadRfi = (rfi: {text: string}, index: number) => {
    const blob = new Blob([rfi.text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `RFI_Draft_${index + 1}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (rfis.length === 0) return null;

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mt-8 animate-in fade-in zoom-in duration-700">
      <h3 className="text-xl font-bold text-gray-800 flex items-center mb-6">
        <Edit3 className="mr-2 text-indigo-500" />
        Interactive RFI Studio
      </h3>
      <div className="space-y-6">
        {rfis.map((rfi, idx) => (
          <div key={idx} className={`border rounded-lg p-4 transition-colors ${rfi.approved ? 'border-green-400 bg-green-50' : 'border-gray-200'}`}>
            <div className="flex justify-between items-center mb-3">
              <h4 className="font-semibold text-gray-700">RFI #{idx + 1}</h4>
              <div className="flex space-x-2">
                <button onClick={() => toggleApprove(idx)} className={`flex items-center space-x-1 px-3 py-1.5 rounded text-sm font-medium ${rfi.approved ? 'bg-green-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
                  <CheckCircle size={16} /> <span>{rfi.approved ? 'Approved' : 'Approve'}</span>
                </button>
                <button onClick={() => downloadRfi(rfi, idx)} className="flex items-center space-x-1 px-3 py-1.5 rounded text-sm font-medium bg-blue-100 text-blue-700 hover:bg-blue-200">
                  <Download size={16} /> <span>Export</span>
                </button>
              </div>
            </div>
            <textarea 
              className="w-full h-32 p-3 border border-gray-300 rounded focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm font-mono text-gray-800"
              value={rfi.text}
              onChange={(e) => updateText(idx, e.target.value)}
            />
          </div>
        ))}
      </div>
    </div>
  );
};
