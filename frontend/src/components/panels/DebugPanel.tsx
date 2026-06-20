import { useState } from 'react';
import { ChevronRight, ChevronDown, AlertCircle } from 'lucide-react';
import type { StudioState } from '../../state/studio';

export function DebugPanel({ state }: { state: StudioState }) {
  const result = state.result;

  return (
    <div className="flex flex-col h-full w-full bg-slate-950 overflow-y-auto">
      <div className="sticky top-0 p-3 border-b border-slate-800 bg-slate-900/90 backdrop-blur z-10 shrink-0">
        <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Debugger</h3>
      </div>

      <div className="p-2 space-y-1">
        {state.error && (
          <div className="p-3 bg-red-900/20 border border-red-900/50 rounded-lg mb-4 flex items-start space-x-2">
            <AlertCircle size={16} className="text-red-500 mt-0.5 shrink-0" />
            <p className="text-xs text-red-400 font-mono break-all">{state.error}</p>
          </div>
        )}

        {state.isProcessing && (
          <div className="p-4 text-center text-xs text-blue-400 mono animate-pulse">
            Executing transformation pipeline...
          </div>
        )}

        {!state.isProcessing && !result && !state.error && (
          <div className="p-4 text-center text-xs text-slate-500 mono">
            No active session. Run a redesign to view logs.
          </div>
        )}

        {result && (
          <>
            <Accordion title="Goal Analysis" defaultOpen={false}>
              <pre className="mono text-xs text-green-400 bg-slate-900 p-3 rounded-b-lg border-x border-b border-slate-800 overflow-x-auto">
{JSON.stringify({
  primary_goal: "RESTYLE",
  secondary_goals: ["LAYOUT_CHANGE"],
  reasoning: result.design_plan?.reasoning || "Derived from prompt."
}, null, 2)}
              </pre>
            </Accordion>

            <Accordion title="Design Plan" defaultOpen={true}>
              <pre className="mono text-xs text-blue-400 bg-slate-900 p-3 rounded-b-lg border-x border-b border-slate-800 overflow-x-auto">
{JSON.stringify(result.design_plan || {}, null, 2)}
              </pre>
            </Accordion>

            <Accordion title="Generated CSS" defaultOpen={true}>
              <pre className="mono text-xs text-purple-400 bg-slate-900 p-3 rounded-b-lg border-x border-b border-slate-800 overflow-x-auto">
{result.transformation?.css || "/* No CSS generated */"}
              </pre>
            </Accordion>

            <Accordion title="Generated JavaScript" defaultOpen={false}>
              <pre className="mono text-xs text-yellow-400 bg-slate-900 p-3 rounded-b-lg border-x border-b border-slate-800 overflow-x-auto">
{result.transformation?.javascript || "// No JS generated"}
              </pre>
            </Accordion>

            <Accordion title="Iterations" defaultOpen={false}>
              <pre className="mono text-xs text-slate-400 bg-slate-900 p-3 rounded-b-lg border-x border-b border-slate-800 overflow-x-auto">
{JSON.stringify([
  {
    iteration: 1,
    success: true,
    feedback: "Transformation completed. Evaluator step disabled in this version.",
    confidence: result.transformation?.confidence || 0,
    affected_elements: result.transformation?.affected_elements || []
  }
], null, 2)}
              </pre>
            </Accordion>
          </>
        )}
      </div>
    </div>
  );
}

function Accordion({ title, children, defaultOpen = false }: { title: string, children: React.ReactNode, defaultOpen?: boolean }) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="flex flex-col">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center space-x-2 p-2 bg-slate-800 hover:bg-slate-700 transition-colors border border-slate-700 ${isOpen ? 'rounded-t-lg border-b-0' : 'rounded-lg'}`}
      >
        {isOpen ? <ChevronDown size={14} className="text-slate-400" /> : <ChevronRight size={14} className="text-slate-400" />}
        <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-widest">{title}</h4>
      </button>
      {isOpen && children}
    </div>
  );
}
