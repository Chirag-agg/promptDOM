import { useState } from 'react';
import { Hammer, Loader2 } from 'lucide-react';
import { studioApi } from '../../api/client';
import { KnowledgeBrowser } from './KnowledgeBrowser';
import { KnowledgeDetails } from './KnowledgeDetails';

export function KnowledgeExplorer() {
  const [selectedPack, setSelectedPack] = useState<any | null>(null);
  const [isBuilding, setIsBuilding] = useState(false);
  const [buildTarget, setBuildTarget] = useState('');
  const [buildError, setBuildError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleBuild = async () => {
    if (!buildTarget.trim()) return;
    setIsBuilding(true);
    setBuildError(null);
    try {
      const pack = await studioApi.buildKnowledgePack(buildTarget.trim());
      setSelectedPack(pack);
      setRefreshKey(k => k + 1);
      setBuildTarget('');
    } catch (err: any) {
      setBuildError(err.message || 'Failed to build pack');
    } finally {
      setIsBuilding(false);
    }
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Top Action Bar */}
      <div className="flex flex-col space-y-3 px-1 pb-4 shrink-0 border-b border-slate-800 mb-4">
        <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-widest">
          Knowledge Base
        </h3>
        
        <div className="flex items-center space-x-2">
          <input
            type="text"
            placeholder="Hostname (e.g. youtube.com)"
            value={buildTarget}
            onChange={(e) => setBuildTarget(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleBuild()}
            className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-emerald-500"
          />
          <button
            onClick={handleBuild}
            disabled={isBuilding || !buildTarget.trim()}
            className="flex items-center space-x-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 disabled:text-slate-400 text-white text-xs font-semibold px-4 py-1.5 rounded-lg transition-colors shadow-lg shadow-emerald-900/20 active:scale-95 border border-emerald-500 disabled:border-slate-600 shrink-0"
          >
            {isBuilding ? (
              <>
                <Loader2 size={14} className="animate-spin" />
                <span>Building…</span>
              </>
            ) : (
              <>
                <Hammer size={14} />
                <span>Build Pack</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error */}
      {buildError && (
        <div className="mb-3 p-2 bg-red-900/20 border border-red-900/50 rounded-lg text-xs text-red-400 mono shrink-0">
          {buildError}
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-y-auto custom-scrollbar pr-1">
        {selectedPack ? (
          <KnowledgeDetails
            pack={selectedPack}
            onBack={() => setSelectedPack(null)}
          />
        ) : (
          <KnowledgeBrowser
            key={refreshKey}
            onSelect={setSelectedPack}
          />
        )}
      </div>
    </div>
  );
}
