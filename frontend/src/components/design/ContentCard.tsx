import { Check, X } from 'lucide-react';

interface ContentProps {
  remove: string[];
  prioritize: string[];
}

export function ContentCard({ content }: { content: ContentProps }) {
  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-widest border-b border-slate-800 pb-2 mb-3">Content</h3>
      <div className="space-y-4">
        {content.prioritize && content.prioritize.length > 0 && (
          <ul className="space-y-2">
            {content.prioritize.map((item, idx) => (
              <li key={idx} className="flex items-start space-x-2 text-slate-300">
                <Check size={16} className="text-green-500 mt-0.5 shrink-0" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        )}
        
        {content.remove && content.remove.length > 0 && (
          <ul className="space-y-2">
            {content.remove.map((item, idx) => (
              <li key={idx} className="flex items-start space-x-2 text-slate-400 opacity-80">
                <X size={16} className="text-red-500 mt-0.5 shrink-0" />
                <span className="line-through">{item}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
