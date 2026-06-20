import { Activity } from 'lucide-react';

interface ExecutionProps {
  cssLines: number;
  jsLines: number;
  targetsIdentified: number;
  targetsGrounded: number;
  estimatedRisk: string;
}

export function ExecutionCard({ stats }: { stats: ExecutionProps }) {
  const getRiskColor = (risk: string) => {
    switch (risk.toLowerCase()) {
      case 'low': return 'text-green-400';
      case 'medium': return 'text-yellow-400';
      case 'high': return 'text-red-400';
      default: return 'text-slate-400';
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-widest border-b border-slate-800 pb-2 mb-3 flex items-center">
        <Activity size={16} className="mr-2 text-blue-500" />
        Execution Summary
      </h3>
      
      <div className="space-y-4 text-sm">
        <div>
          <div className="flex justify-between text-slate-400 mb-1">
            <span>Generated CSS</span>
            <span className="text-slate-200 mono">{stats.cssLines} lines</span>
          </div>
          <div className="flex justify-between text-slate-400">
            <span>Generated JS</span>
            <span className="text-slate-200 mono">{stats.jsLines} lines</span>
          </div>
        </div>

        <div className="pt-3 border-t border-slate-800">
          <div className="flex justify-between text-slate-400 mb-1">
            <span>Targets Identified</span>
            <span className="text-slate-200 mono">{stats.targetsIdentified}</span>
          </div>
          <div className="flex justify-between text-slate-400">
            <span>Targets Grounded</span>
            <span className="text-slate-200 mono">{stats.targetsGrounded}</span>
          </div>
        </div>

        <div className="pt-3 border-t border-slate-800 flex justify-between font-medium">
          <span className="text-slate-400">Estimated Risk</span>
          <span className={getRiskColor(stats.estimatedRisk)}>{stats.estimatedRisk}</span>
        </div>
      </div>
    </div>
  );
}
