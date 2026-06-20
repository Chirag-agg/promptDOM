import { Check } from 'lucide-react';

interface LayoutProps {
  primary_layout: string;
  navigation_position: string;
  content_density: string;
}

export function LayoutCard({ layout }: { layout: LayoutProps }) {
  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-widest border-b border-slate-800 pb-2 mb-3">Layout</h3>
      <ul className="space-y-2">
        <li className="flex items-start space-x-2 text-slate-300">
          <Check size={16} className="text-green-500 mt-0.5 shrink-0" />
          <span>{layout.primary_layout}</span>
        </li>
        <li className="flex items-start space-x-2 text-slate-300">
          <Check size={16} className="text-green-500 mt-0.5 shrink-0" />
          <span>{layout.navigation_position}</span>
        </li>
        <li className="flex items-start space-x-2 text-slate-300">
          <Check size={16} className="text-green-500 mt-0.5 shrink-0" />
          <span>{layout.content_density}</span>
        </li>
      </ul>
    </div>
  );
}
