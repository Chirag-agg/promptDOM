import { useState, useMemo } from 'react';
import { Search, Tag } from 'lucide-react';

interface SemanticElement {
  tag: string;
  text: string | null;
  aria_label: string | null;
  role: string | null;
  selector: string;
}

const TAG_COLORS: Record<string, string> = {
  button: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  a: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  input: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  textarea: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  select: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  h1: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  h2: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  h3: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  h4: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  h5: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  h6: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
};

export function SemanticElementsTable({ elements }: { elements: SemanticElement[] }) {
  const [search, setSearch] = useState('');

  const filtered = useMemo(() => {
    if (!search.trim()) return elements;
    const q = search.toLowerCase();
    return elements.filter(el =>
      (el.tag && el.tag.toLowerCase().includes(q)) ||
      (el.text && el.text.toLowerCase().includes(q)) ||
      (el.aria_label && el.aria_label.toLowerCase().includes(q)) ||
      (el.role && el.role.toLowerCase().includes(q)) ||
      (el.selector && el.selector.toLowerCase().includes(q))
    );
  }, [elements, search]);

  return (
    <div className="flex flex-col space-y-3">
      {/* Search */}
      <div className="relative">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search semantic elements..."
          className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-300 placeholder:text-slate-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
        />
      </div>

      {/* Count */}
      <div className="text-xs text-slate-500 flex items-center space-x-1">
        <Tag size={12} />
        <span>Showing {filtered.length} of {elements.length} elements</span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-slate-700">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-slate-800 text-slate-400 uppercase tracking-wider">
              <th className="text-left px-3 py-2 font-semibold">Tag</th>
              <th className="text-left px-3 py-2 font-semibold">Text</th>
              <th className="text-left px-3 py-2 font-semibold">ARIA Label</th>
              <th className="text-left px-3 py-2 font-semibold">Role</th>
              <th className="text-left px-3 py-2 font-semibold">Selector</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 && (
              <tr>
                <td colSpan={5} className="px-3 py-6 text-center text-slate-500">
                  {search ? 'No elements match your search.' : 'No semantic elements captured.'}
                </td>
              </tr>
            )}
            {filtered.map((el, i) => (
              <tr key={i} className="border-t border-slate-800 hover:bg-slate-800/50 transition-colors">
                <td className="px-3 py-2">
                  <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold border ${TAG_COLORS[el.tag] || 'bg-slate-500/20 text-slate-400 border-slate-500/30'}`}>
                    {el.tag}
                  </span>
                </td>
                <td className="px-3 py-2 text-slate-300 max-w-[200px] truncate">{el.text || <span className="text-slate-600">—</span>}</td>
                <td className="px-3 py-2 text-slate-400 max-w-[150px] truncate">{el.aria_label || <span className="text-slate-600">—</span>}</td>
                <td className="px-3 py-2 text-slate-400">{el.role || <span className="text-slate-600">—</span>}</td>
                <td className="px-3 py-2 text-slate-500 mono text-[10px] max-w-[250px] truncate">{el.selector}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
