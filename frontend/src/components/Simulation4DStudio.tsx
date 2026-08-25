import React, { useState, useEffect } from 'react';
import { Play, Pause, FastForward, Presentation, Layers } from 'lucide-react';

export interface ElementState {
  state: "PLANNED" | "IN_PROGRESS" | "COMPLETED" | "CRITICAL_DELAY";
  color: string;
  progress: number;
}

export interface Simulation4DData {
  simulation_timestamp: string;
  element_states: Record<string, ElementState>;
  total_elements: number;
}

export interface PitchDeckData {
  title: string;
  slides: any[];
}

interface Simulation4DStudioProps {
  pitchData: PitchDeckData;
  simulationData: Simulation4DData;
}

export const Simulation4DStudio: React.FC<Simulation4DStudioProps> = ({ pitchData, simulationData }) => {
  const [isPlaying, setIsPlaying] = useState(true);
  const [timelineProgress, setTimelineProgress] = useState(0);

  // Simple mock animation loop for the timeline UI
  useEffect(() => {
    let interval: any;
    if (isPlaying) {
      interval = setInterval(() => {
        setTimelineProgress(prev => (prev >= 100 ? 0 : prev + 1));
      }, 100);
    }
    return () => clearInterval(interval);
  }, [isPlaying]);

  return (
    <div className="bg-slate-900 rounded-lg shadow-2xl border border-slate-700 mt-8 mb-8 animate-in fade-in duration-500 font-sans text-slate-100">
      <div className="bg-black/40 p-5 border-b border-slate-700 flex flex-col md:flex-row justify-between items-start md:items-center">
        <h3 className="text-xl font-black flex items-center text-cyan-400 tracking-wide">
          <Presentation className="mr-3" size={26} />
          {pitchData.title} & 4D Digital Twin
        </h3>
        <button className="flex items-center text-[10px] uppercase tracking-widest font-bold bg-cyan-600 hover:bg-cyan-500 text-white px-4 py-2 rounded shadow-md mt-3 md:mt-0 transition-colors">
          Export Pitch Deck (PDF)
        </button>
      </div>
      
      <div className="p-6 grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* 4D Simulation Canvas (Mocked WebGL Abstraction) */}
        <div className="col-span-1 lg:col-span-3">
          <div className="bg-slate-950 p-1 rounded-lg border border-slate-800 relative shadow-inner overflow-hidden h-[400px] flex flex-col">
            
            {/* 3D Scene Mock Container */}
            <div className="flex-grow flex items-center justify-center relative">
              <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-slate-800 via-slate-950 to-slate-950 opacity-50"></div>
              
              {/* Mock 3D Elements based on State */}
              <div className="relative z-10 grid grid-cols-3 gap-8 perspective-1000 transform -rotate-12 scale-125">
                {Object.entries(simulationData.element_states).map(([guid, stateInfo], idx) => (
                  <div key={guid} className="flex flex-col items-center">
                    <div 
                       className="w-16 h-24 rounded-sm shadow-2xl transition-colors duration-700 border-2 border-white/10"
                       style={{ backgroundColor: stateInfo.color, opacity: stateInfo.state === 'PLANNED' ? 0.3 : 1 }}
                    >
                      {stateInfo.state === 'IN_PROGRESS' && (
                        <div className="w-full bg-white/20 bottom-0 absolute" style={{ height: `${stateInfo.progress}%` }}></div>
                      )}
                    </div>
                    <div className="text-[8px] font-mono mt-2 text-slate-400 bg-black/50 px-1 rounded">{guid}</div>
                  </div>
                ))}
              </div>
              
              <div className="absolute top-4 left-4 flex flex-col gap-2">
                <span className="text-xs font-bold text-slate-400 flex items-center"><div className="w-3 h-3 rounded bg-slate-400 mr-2"></div> Planned</span>
                <span className="text-xs font-bold text-slate-400 flex items-center"><div className="w-3 h-3 rounded bg-blue-500 mr-2"></div> In Progress</span>
                <span className="text-xs font-bold text-slate-400 flex items-center"><div className="w-3 h-3 rounded bg-emerald-500 mr-2"></div> Completed</span>
                <span className="text-xs font-bold text-slate-400 flex items-center"><div className="w-3 h-3 rounded bg-red-500 mr-2"></div> Critical Delay</span>
              </div>
            </div>
            
            {/* Playback Controls */}
            <div className="bg-slate-900 border-t border-slate-800 p-4 flex items-center gap-4 z-20">
              <button 
                onClick={() => setIsPlaying(!isPlaying)}
                className="bg-cyan-600 hover:bg-cyan-500 text-white p-2 rounded-full transition-colors"
              >
                {isPlaying ? <Pause size={16} /> : <Play size={16} />}
              </button>
              <button className="text-slate-400 hover:text-slate-200">
                <FastForward size={16} />
              </button>
              
              <div className="flex-grow flex items-center gap-3">
                <div className="text-xs font-mono text-slate-400">Month 1</div>
                <div className="h-2 flex-grow bg-slate-800 rounded-full overflow-hidden relative">
                  <div className="h-full bg-cyan-500 transition-all duration-100 ease-linear" style={{ width: `${timelineProgress}%` }}></div>
                </div>
                <div className="text-xs font-mono text-slate-400">Month 12</div>
              </div>
            </div>
            
          </div>
        </div>

        {/* Pitch Deck Slide Navigator */}
        <div className="col-span-1 space-y-4">
          <div className="bg-slate-800/50 p-5 rounded-lg border border-slate-700 h-full">
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4 flex items-center border-b border-slate-700 pb-2">
              <Layers size={14} className="mr-2 text-cyan-400" /> Deck Architecture
            </h4>
            
            <div className="space-y-3">
              {pitchData.slides.map((slide, idx) => (
                <div key={idx} className="bg-slate-900/50 p-3 rounded border border-slate-700/50">
                  <div className="text-[10px] font-black text-cyan-400 uppercase tracking-wider mb-1">Slide 0{idx + 1}</div>
                  <div className="text-sm font-semibold text-slate-200">{slide.type.replace(/_/g, ' ')}</div>
                  {slide.type === 'EXECUTIVE_SUMMARY' && <div className="text-xs text-slate-400 mt-1 truncate">{slide.content}</div>}
                  {slide.type === 'DCMA_METRICS' && <div className="text-xs text-slate-400 mt-1">DCMA Score: {slide.score}</div>}
                  {slide.type === '4D_DIGITAL_TWIN' && <div className="text-xs text-slate-400 mt-1">Interactive Simulation Embedded</div>}
                </div>
              ))}
            </div>
            
          </div>
        </div>
        
      </div>
    </div>
  );
};
