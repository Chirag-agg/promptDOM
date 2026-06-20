import { Globe, Lock, RotateCw, ChevronLeft, ChevronRight, Camera } from 'lucide-react';
import mockupImage from '../../assets/mockup.png';
import type { StudioState } from '../../state/studio';

export function BrowserPanel({ }: { state: StudioState }) {
  return (
    <div className="flex flex-col h-full w-full">
      {/* Fake Browser Top Bar */}
      <div className="flex items-center space-x-2 px-3 py-2 border-b border-slate-700 bg-slate-800 shrink-0">
        <div className="flex space-x-1.5 mr-2">
          <div className="w-3 h-3 rounded-full bg-red-500"></div>
          <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
          <div className="w-3 h-3 rounded-full bg-green-500"></div>
        </div>
        
        <div className="flex items-center space-x-2 text-slate-400">
          <ChevronLeft size={16} />
          <ChevronRight size={16} />
          <RotateCw size={14} />
        </div>

        <div className="flex-1 flex items-center justify-center bg-slate-900 rounded text-sm py-1 px-3 border border-slate-700 text-slate-300 ml-2">
          <Lock size={12} className="mr-2 text-slate-500" />
          <span className="mono text-xs">https://youtube.com</span>
        </div>
        
        <Globe size={16} className="text-slate-400 ml-2" />
      </div>

      {/* Fake Browser Content Area */}
      <div className="flex-1 bg-black relative overflow-hidden flex flex-col group">
        <img 
          src={mockupImage} 
          alt="Browser View Placeholder" 
          className="w-full h-full object-cover opacity-90 transition-opacity duration-300 group-hover:opacity-100" 
        />
        
        {/* Overlay capture indicator */}
        <div className="absolute top-4 right-4 bg-slate-900/80 backdrop-blur border border-slate-700 px-3 py-1.5 rounded-md flex items-center space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <Camera size={14} className="text-blue-400" />
          <span className="text-xs text-slate-300 font-medium tracking-wide">Live Capture Active</span>
        </div>
      </div>
    </div>
  );
}
