import { useEffect, useState } from 'react';
import { Camera, Clock, Tag, Grid3X3, Globe, ArrowRight } from 'lucide-react';
import { studioApi } from '../../api/client';

interface SnapshotBrowserProps {
  onSelect: (snapshot: any) => void;
}

export function SnapshotBrowser({ onSelect }: SnapshotBrowserProps) {
  const [snapshots, setSnapshots] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchSnapshots = async () => {
    try {
      const data = await studioApi.listCaptures();
      setSnapshots(data);
    } catch (err) {
      console.error('Failed to fetch snapshots:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSnapshots();
  }, []);

  if (isLoading) {
    return <div className="p-8 text-center text-slate-500 animate-pulse">Loading snapshots...</div>;
  }

  if (snapshots.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-slate-500 space-y-4">
        <Camera size={48} className="opacity-20" />
        <p>No snapshots captured yet.</p>
        <p className="text-sm">Use the capture button above to snapshot a page.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3 pr-1 custom-scrollbar pb-4">
      {snapshots.map((snap) => {
        const hostname = snap.hostname || new URL(snap.url).hostname;
        return (
          <button
            key={snap.snapshot_id}
            onClick={() => onSelect(snap)}
            className="w-full text-left bg-slate-900 border border-slate-700 hover:border-blue-500 hover:bg-slate-800 rounded-xl p-4 transition-all group flex flex-col space-y-3"
          >
            <div className="flex justify-between items-start">
              <div className="flex items-center space-x-2 text-slate-300 font-medium">
                <Globe size={16} className="text-slate-500" />
                <span>{hostname}</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-1 px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 text-[10px] font-bold">
                  <Tag size={10} />
                  <span>{snap.semantic_elements.length}</span>
                </div>
                <div className="flex items-center space-x-1 px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 text-[10px] font-bold">
                  <Grid3X3 size={10} />
                  <span>{snap.layout_elements.length}</span>
                </div>
              </div>
            </div>

            <p className="text-slate-200 text-sm font-medium leading-relaxed truncate">
              {snap.title}
            </p>

            <div className="flex justify-between items-center text-xs text-slate-500 pt-2 border-t border-slate-800">
              <div className="flex items-center space-x-1">
                <Clock size={12} />
                <span>{new Date(snap.captured_at).toLocaleString()}</span>
              </div>

              <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity text-blue-400">
                <span>Inspect</span>
                <ArrowRight size={14} />
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}
