import { Lock, RotateCw, ChevronLeft, ChevronRight, Camera } from 'lucide-react';
import { useState, useEffect } from 'react';
import type { StudioState } from '../../state/studio';
import { API_BASE_URL } from '../../api/client';

export function BrowserPanel({ }: { state: StudioState }) {
  const [screenshotUrl, setScreenshotUrl] = useState(`${API_BASE_URL}/browser/screenshot?t=${Date.now()}`);
  const [isLive, setIsLive] = useState(true);

  useEffect(() => {
    if (!isLive) return;
    
    // Auto refresh every 3 seconds
    const interval = setInterval(() => {
      setScreenshotUrl(`${API_BASE_URL}/browser/screenshot?t=${Date.now()}`);
    }, 3000);
    
    return () => clearInterval(interval);
  }, [isLive]);

  const handleManualRefresh = () => {
    setScreenshotUrl(`${API_BASE_URL}/browser/screenshot?t=${Date.now()}`);
  };

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
          <button onClick={handleManualRefresh} className="hover:text-slate-200 transition-colors">
            <RotateCw size={14} className={isLive ? "animate-[spin_3s_linear_infinite]" : ""} />
          </button>
        </div>

        <div className="flex-1 flex items-center justify-center bg-slate-900 rounded text-sm py-1 px-3 border border-slate-700 text-slate-300 ml-2">
          <Lock size={12} className="mr-2 text-slate-500" />
          <span className="mono text-xs">Live Connected Browser</span>
        </div>
        
        <button 
          onClick={() => setIsLive(!isLive)} 
          className={`ml-2 text-xs font-semibold px-2 py-0.5 rounded transition-colors ${isLive ? 'bg-green-900/50 text-green-400 border border-green-800' : 'bg-slate-800 text-slate-400 border border-slate-700'}`}
        >
          {isLive ? 'LIVE' : 'PAUSED'}
        </button>
      </div>

      {/* Fake Browser Content Area */}
      <div className="flex-1 bg-black relative overflow-hidden flex flex-col group">
        <img 
          src={screenshotUrl} 
          alt="Browser View" 
          className="w-full h-full object-contain bg-slate-950 transition-opacity duration-300"
          onError={(e) => {
            // Fallback placeholder if backend is not running or no active page
            e.currentTarget.style.display = 'none';
          }}
          onLoad={(e) => {
            e.currentTarget.style.display = 'block';
          }}
        />
        
        {/* Overlay capture indicator */}
        <div className={`absolute top-4 right-4 bg-slate-900/80 backdrop-blur border border-slate-700 px-3 py-1.5 rounded-md flex items-center space-x-2 transition-opacity ${isLive ? 'opacity-100' : 'opacity-0'}`}>
          <Camera size={14} className="text-blue-400 animate-pulse" />
          <span className="text-xs text-slate-300 font-medium tracking-wide">Capturing</span>
        </div>
      </div>
    </div>
  );
}
