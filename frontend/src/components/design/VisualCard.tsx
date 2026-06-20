import { Check } from 'lucide-react';

interface VisualProps {
  theme: string;
  spacing: string;
  card_style: string;
}

export function VisualCard({ visual }: { visual: VisualProps }) {
  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-widest border-b border-slate-800 pb-2 mb-3">Visual</h3>
      <ul className="space-y-2">
        <li className="flex items-start space-x-2 text-slate-300">
          <Check size={16} className="text-green-500 mt-0.5 shrink-0" />
          <span>{visual.theme}</span>
        </li>
        <li className="flex items-start space-x-2 text-slate-300">
          <Check size={16} className="text-green-500 mt-0.5 shrink-0" />
          <span>{visual.spacing}</span>
        </li>
        <li className="flex items-start space-x-2 text-slate-300">
          <Check size={16} className="text-green-500 mt-0.5 shrink-0" />
          <span>{visual.card_style}</span>
        </li>
      </ul>
    </div>
  );
}
