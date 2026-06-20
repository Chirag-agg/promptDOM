import { useState, useMemo } from 'react';
import { Search, Grid3X3 } from 'lucide-react';

interface LayoutElement {
  selector: string;
  x: number;
  y: number;
  width: number;
  height: number;
  visible: boolean;
}

export function LayoutElementsTable({ elements }: { elements: LayoutElement[] }) {
  const [search, setSearch] = useState('');

  const filtered = useMemo(() => {
    if (!search.trim()) return elements;
    const q = search.toLowerCase();
    return elements.filter(el => el.selector.toLowerCase().includes(q));
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
          placeholder="Search layout elements by selector..."
          className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-300 placeholder:text-slate-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
        />
      </div>

      {/* Count */}
      <div className="text-xs text-slate-500 flex items-center space-x-1">
        <Grid3X3 size={12} />
        <span>Showing {filtered.length} of {elements.length} elements</span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-slate-700">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-slate-800 text-slate-400 uppercase tracking-wider">
              <th className="text-left px-3 py-2 font-semibold">Selector</th>
              <th className="text-right px-3 py-2 font-semibold">X</th>
              <th className="text-right px-3 py-2 font-semibold">Y</th>
              <th className="text-right px-3 py-2 font-semibold">Width</th>
              <th className="text-right px-3 py-2 font-semibold">Height</th>
              <th className="text-center px-3 py-2 font-semibold">Visible</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 && (
              <tr>
                <td colSpan={6} className="px-3 py-6 text-center text-slate-500">
                  {search ? 'No elements match your search.' : 'No layout elements captured.'}
                </td>
              </tr>
            )}
            {filtered.map((el, i) => (
              <tr key={i} className="border-t border-slate-800 hover:bg-slate-800/50 transition-colors">
                <td className="px-3 py-2 text-slate-400 mono text-[10px] max-w-[300px] truncate">{el.selector}</td>
                <td className="px-3 py-2 text-right text-slate-300 mono">{Math.round(el.x)}</td>
                <td className="px-3 py-2 text-right text-slate-300 mono">{Math.round(el.y)}</td>
                <td className="px-3 py-2 text-right text-slate-300 mono">{Math.round(el.width)}</td>
                <td className="px-3 py-2 text-right text-slate-300 mono">{Math.round(el.height)}</td>
                <td className="px-3 py-2 text-center">
                  <span className={`inline-block w-2 h-2 rounded-full ${el.visible ? 'bg-emerald-500' : 'bg-red-500'}`} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
