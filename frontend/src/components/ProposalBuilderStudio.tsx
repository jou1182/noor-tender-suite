import React, { useState } from 'react';
import { BookOpen, Users, Truck, Zap, Save, CheckCircle } from 'lucide-react';

export interface MethodStatement {
  boq_item: string;
  method_statement_text: string;
  crew_composition: string[];
  equipment_allocation: string[];
  productivity_rate: number;
  unit: string;
}

interface Props {
  initialData: MethodStatement[] | null;
}

export const ProposalBuilderStudio: React.FC<Props> = ({ initialData }) => {
  // Use either the incoming server data or a mock for empty states
  const safeData = initialData && initialData.length > 0 ? initialData : [
    {
      boq_item: "Earthworks & Excavation",
      method_statement_text: "1. Site clearing\n2. Utility detection\n3. Deep excavation\n4. Shoring",
      crew_composition: ["1 Supervisor", "2 Operators", "3 Laborers"],
      equipment_allocation: ["Excavator", "Dump Truck"],
      productivity_rate: 150,
      unit: "units/day"
    }
  ];

  const [statements, setStatements] = useState<MethodStatement[]>(safeData);
  const [activeTab, setActiveTab] = useState(0);
  const [isSaved, setIsSaved] = useState(true);

  if (!statements || statements.length === 0) return null;

  const activeStatement = statements[activeTab];

  const handleTextChange = (text: string) => {
    const updated = [...statements];
    updated[activeTab].method_statement_text = text;
    setStatements(updated);
    setIsSaved(false);
  };

  const handleProductivityChange = (val: number) => {
    const updated = [...statements];
    updated[activeTab].productivity_rate = val;
    setStatements(updated);
    setIsSaved(false);
  };

  const handleSave = () => {
    setIsSaved(true);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 mt-8 animate-in fade-in zoom-in duration-500 overflow-hidden">
      <div className="bg-slate-900 p-4 flex justify-between items-center">
        <h3 className="text-lg font-bold text-white flex items-center">
          <BookOpen className="mr-2 text-blue-400" />
          Generative Technical Proposal Studio
        </h3>
        <button 
          onClick={handleSave}
          className="flex items-center bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded text-sm font-medium transition shadow-sm"
        >
          {isSaved ? <CheckCircle size={16} className="mr-2" /> : <Save size={16} className="mr-2" />}
          {isSaved ? 'Saved to State' : 'Save Changes'}
        </button>
      </div>

      <div className="flex flex-col md:flex-row min-h-[400px]">
        {/* Sidebar Navigation */}
        <div className="w-full md:w-1/4 bg-gray-50 border-r border-gray-200 p-3">
          <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3 ml-2 mt-1">Generated BOQ Context</h4>
          <ul className="space-y-1.5">
            {statements.map((stmt, idx) => (
              <li key={idx}>
                <button
                  onClick={() => setActiveTab(idx)}
                  className={`w-full text-left px-3 py-2.5 rounded-md text-sm font-semibold transition-colors ${activeTab === idx ? 'bg-blue-100 text-blue-900 shadow-sm' : 'text-gray-600 hover:bg-gray-200'}`}
                >
                  {stmt.boq_item}
                </button>
              </li>
            ))}
          </ul>
        </div>

        {/* Editor Content */}
        <div className="w-full md:w-3/4 p-6 bg-white">
          <h2 className="text-2xl font-bold text-gray-800 mb-5">{activeStatement.boq_item}</h2>
          
          <div className="grid md:grid-cols-3 gap-6 mb-6">
            <div className="col-span-2">
              <label className="block text-sm font-semibold text-gray-700 mb-2">Methodology Narrative & Codes</label>
              <textarea 
                className="w-full h-56 p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm font-mono text-gray-800 shadow-inner leading-relaxed bg-slate-50"
                value={activeStatement.method_statement_text}
                onChange={(e) => handleTextChange(e.target.value)}
              />
            </div>
            
            <div className="space-y-4">
              <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
                <label className="flex items-center text-xs font-bold text-slate-500 uppercase mb-2">
                  <Users size={16} className="mr-1.5" /> Crew Composition
                </label>
                <ul className="text-sm text-slate-700 list-disc pl-5 space-y-1 font-medium">
                  {activeStatement.crew_composition.map((c, i) => <li key={i}>{c}</li>)}
                </ul>
              </div>
              
              <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
                <label className="flex items-center text-xs font-bold text-slate-500 uppercase mb-2">
                  <Truck size={16} className="mr-1.5" /> Equipment Allocation
                </label>
                <ul className="text-sm text-slate-700 list-disc pl-5 space-y-1 font-medium">
                  {activeStatement.equipment_allocation.map((e, i) => <li key={i}>{e}</li>)}
                </ul>
              </div>

              <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                <label className="flex items-center text-xs font-bold text-blue-700 uppercase mb-3">
                  <Zap size={16} className="mr-1.5" /> Productivity Rate
                </label>
                <div className="flex items-center">
                  <input 
                    type="number" 
                    value={activeStatement.productivity_rate}
                    onChange={(e) => handleProductivityChange(parseFloat(e.target.value) || 0)}
                    className="w-24 p-2 border border-blue-300 rounded text-base text-center mr-3 font-bold text-blue-900 focus:ring-blue-500"
                  />
                  <span className="text-sm text-blue-800 font-bold">{activeStatement.unit}</span>
                </div>
              </div>
            </div>
          </div>
          
          <div className="flex justify-end border-t border-gray-200 pt-5 mt-2">
            <button className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2.5 rounded-lg shadow-md transition font-semibold text-sm">
              Lock & Run Auto-Audit Pipeline
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
