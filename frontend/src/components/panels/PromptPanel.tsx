import { Play, Loader2 } from 'lucide-react';
import { useState } from 'react';
import type { StudioState } from '../../state/studio';

export function PromptPanel({ state, onRun }: { state: StudioState, onRun: (prompt: string) => void }) {
  const [prompt, setPrompt] = useState(state.prompt);

  return (
    <div className="flex flex-col h-full w-full bg-slate-900 border-x border-slate-800 shadow-xl z-10">
      <div className="border-b border-slate-800 bg-slate-900 shrink-0">
        <div className="flex space-x-1 px-2 pt-2">
          <Tab active>Prompt</Tab>
          <Tab>Design Plan</Tab>
          <Tab>Reference Images</Tab>
        </div>
      </div>

      <div className="flex-1 p-6 flex flex-col relative">
        <div className="flex-1 bg-slate-950 rounded-xl border border-slate-700 focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500 transition-all flex flex-col overflow-hidden shadow-inner">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className="flex-1 w-full bg-transparent text-slate-200 p-4 resize-none outline-none font-sans text-lg placeholder:text-slate-600"
            placeholder="Describe the desired UI transformation..."
          />
          
          <div className="p-3 bg-slate-900 border-t border-slate-800 flex justify-between items-center">
            <span className="text-xs text-slate-500 mono">Shift + Enter to insert newline</span>
            <button 
              onClick={() => onRun(prompt)}
              disabled={state.isProcessing || !prompt.trim()}
              className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-400 text-white px-6 py-2 rounded-lg font-medium transition-colors shadow-lg shadow-blue-900/20 active:scale-95"
            >
              <span>{state.isProcessing ? 'Running...' : 'Run Redesign'}</span>
              {state.isProcessing ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} fill="currentColor" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function Tab({ children, active }: { children: React.ReactNode, active?: boolean }) {
  return (
    <button 
      disabled={!active}
      className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
        active 
          ? 'border-blue-500 text-blue-400 bg-slate-800/50 rounded-t-lg' 
          : 'border-transparent text-slate-500 hover:text-slate-400 opacity-50 cursor-not-allowed'
      }`}
    >
      {children}
    </button>
  );
}
