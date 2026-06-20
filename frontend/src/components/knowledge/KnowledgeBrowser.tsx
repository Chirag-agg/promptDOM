import { useEffect, useState } from 'react';
import { Network, Database, ChevronRight, Brain } from 'lucide-react';
import { studioApi } from '../../api/client';

interface KnowledgeBrowserProps {
  onSelect: (pack: any) => void;
}

export function KnowledgeBrowser({ onSelect }: KnowledgeBrowserProps) {
  const [packs, setPacks] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchPacks = async () => {
    try {
      const data = await studioApi.listKnowledgePacks();
      setPacks(data);
    } catch (err) {
      console.error('Failed to fetch knowledge packs:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPacks();
  }, []);

  if (isLoading) {
    return <div className="p-8 text-center text-slate-500 animate-pulse">Loading knowledge base...</div>;
  }

  if (packs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-slate-500 space-y-4">
        <Brain size={48} className="opacity-20" />
        <p>No knowledge packs built yet.</p>
        <p className="text-sm">Use the build button above to aggregate captures.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3 pr-1 custom-scrollbar pb-4">
      {packs.map((pack) => (
        <button
          key={pack.pack_id}
          onClick={() => onSelect(pack)}
          className="w-full text-left bg-slate-900 border border-slate-700 hover:border-emerald-500 hover:bg-slate-800 rounded-xl p-4 transition-all group flex flex-col space-y-3"
        >
          <div className="flex justify-between items-start">
            <div className="flex items-center space-x-2 text-slate-200 font-bold">
              <Database size={16} className="text-emerald-500" />
              <span>{pack.hostname}</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="flex items-center space-x-1 px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] font-bold mono">
                <span>{(pack.knowledge_confidence * 100).toFixed(0)}% CONF</span>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2 text-xs font-bold px-2 py-1 rounded border bg-orange-500/10 text-orange-400 border-orange-500/20 self-start">
            <Network size={12} />
            <span>{pack.archetype}</span>
          </div>

          <div className="flex justify-between items-center text-xs text-slate-500 pt-2 border-t border-slate-800">
            <div className="flex items-center space-x-3">
              <span>{pack.snapshots_used.length} snapshots</span>
              <span>{pack.concept_knowledge.length} concepts</span>
            </div>

            <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity text-emerald-400">
              <span>Explore</span>
              <ChevronRight size={14} />
            </div>
          </div>
        </button>
      ))}
    </div>
  );
}
