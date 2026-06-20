import type { ReactNode } from 'react';

interface AppLayoutProps {
  leftPanel: ReactNode;
  centerPanel: ReactNode;
  rightPanel: ReactNode;
}

export function AppLayout({ leftPanel, centerPanel, rightPanel }: AppLayoutProps) {
  return (
    <div className="flex flex-col h-screen w-screen bg-slate-900 text-slate-200 overflow-hidden">
      {/* Global Header */}
      <header className="h-12 border-b border-slate-800 bg-slate-950 flex items-center justify-between px-4 shrink-0 z-20">
        <div className="flex items-center space-x-3">
          <div className="bg-blue-600 w-3 h-3 rounded-full shadow-[0_0_10px_rgba(37,99,235,0.8)]"></div>
          <h1 className="text-sm font-semibold tracking-wide text-white">PromptDOM Studio</h1>
        </div>
        
        <div className="flex items-center space-x-6 text-xs text-slate-400 mono">
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span>Connected: Ollama</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-blue-500"></span>
            <span>Page: youtube.com</span>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel */}
        <div className="w-[30%] h-full border-r border-slate-800 bg-slate-900 flex flex-col relative z-10">
          {leftPanel}
        </div>

        {/* Center Panel */}
        <div className="w-[40%] h-full flex flex-col bg-slate-800 shadow-2xl z-20">
          {centerPanel}
        </div>

        {/* Right Panel */}
        <div className="w-[30%] h-full border-l border-slate-800 bg-slate-900 flex flex-col relative z-10">
          {rightPanel}
        </div>
      </div>
    </div>
  );
}
