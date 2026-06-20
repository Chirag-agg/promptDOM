import { Check, ArrowRight, Trash2, Paintbrush, Plus } from 'lucide-react';

export function ReviewChangesCard({ changes }: { changes: any[] }) {
  if (!changes || changes.length === 0) return null;

  const removes = changes.filter(c => c.type === 'REMOVE');
  const moves = changes.filter(c => c.type === 'MOVE');
  const restyles = changes.filter(c => c.type === 'RESTYLE');
  const adds = changes.filter(c => c.type === 'ADD');

  const removeCount = removes.length;
  const totalCount = changes.length;
  
  let impact = 'LOW';
  if (totalCount > 10 || removeCount > 3) {
    impact = 'HIGH';
  } else if (totalCount > 5 || removeCount > 1) {
    impact = 'MEDIUM';
  }

  const impactColors = {
    LOW: 'text-green-400 bg-green-400/10 border-green-400/20',
    MEDIUM: 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20',
    HIGH: 'text-red-400 bg-red-400/10 border-red-400/20'
  };

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl overflow-hidden mb-4 shadow-lg">
      <div className="bg-slate-800/50 p-4 border-b border-slate-700 flex justify-between items-center">
        <h3 className="font-semibold text-slate-200">Executable Changes</h3>
        <span className={`text-xs px-2 py-1 rounded-full border font-bold tracking-wider ${impactColors[impact as keyof typeof impactColors]}`}>
          IMPACT: {impact}
        </span>
      </div>
      
      <div className="p-4 space-y-6">
        {removes.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-red-400 mb-2 flex items-center gap-2">
              <Trash2 size={16} /> REMOVE
            </h4>
            <ul className="space-y-1">
              {removes.map((c, i) => (
                <li key={i} className="text-slate-300 text-sm flex items-start gap-2">
                  <Check size={14} className="mt-1 shrink-0 text-slate-500" />
                  <span>{c.target}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {moves.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-blue-400 mb-2 flex items-center gap-2">
              <ArrowRight size={16} /> MOVE
            </h4>
            <ul className="space-y-1">
              {moves.map((c, i) => (
                <li key={i} className="text-slate-300 text-sm flex items-start gap-2">
                  <Check size={14} className="mt-1 shrink-0 text-slate-500" />
                  <span><strong className="text-slate-200 font-medium">{c.target}</strong> to {c.destination}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {restyles.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-purple-400 mb-2 flex items-center gap-2">
              <Paintbrush size={16} /> RESTYLE
            </h4>
            <ul className="space-y-1">
              {restyles.map((c, i) => (
                <li key={i} className="text-slate-300 text-sm flex items-start gap-2">
                  <Check size={14} className="mt-1 shrink-0 text-slate-500" />
                  <span><strong className="text-slate-200 font-medium">{c.target}</strong>: {c.style_goal}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {adds.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-green-400 mb-2 flex items-center gap-2">
              <Plus size={16} /> ADD
            </h4>
            <ul className="space-y-1">
              {adds.map((c, i) => (
                <li key={i} className="text-slate-300 text-sm flex items-start gap-2">
                  <Check size={14} className="mt-1 shrink-0 text-slate-500" />
                  <span><strong className="text-slate-200 font-medium">{c.target}</strong>: {c.description}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
