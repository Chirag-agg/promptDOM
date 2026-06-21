import { ArrowLeft, Network, Box, TextSearch, Tag, Layers, Share2 } from 'lucide-react';

interface KnowledgeDetailsProps {
  pack: any;
  onBack: () => void;
}

export function KnowledgeDetails({ pack, onBack }: KnowledgeDetailsProps) {
  return (
    <div className="flex flex-col h-full space-y-4">
      {/* Header */}
      <div className="flex items-center space-x-3 pb-2 border-b border-slate-800">
        <button
          onClick={onBack}
          className="p-1 hover:bg-slate-800 rounded text-slate-400 transition-colors"
        >
          <ArrowLeft size={16} />
        </button>
        <div className="flex-1">
          <h2 className="text-sm font-bold text-slate-200">{pack.hostname}</h2>
          <div className="text-[10px] text-slate-500">
            {pack.snapshots_used.length} snapshots • {pack.page_variants.length} page variants
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar space-y-6 pr-1 pb-8">
        
        {/* Core Identity */}
        <div className="space-y-3">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-widest flex items-center space-x-2">
            <Network size={12} />
            <span>Core Identity</span>
          </h3>
          <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-lg font-black px-3 py-1 rounded-lg border bg-orange-500/10 text-orange-400 border-orange-500/20 tracking-wider">
                {pack.archetype}
              </span>
              <div className="flex flex-col items-end">
                <span className="text-2xl font-bold mono text-emerald-400">{(pack.knowledge_confidence * 100).toFixed(0)}%</span>
                <span className="text-[10px] text-slate-500 uppercase tracking-widest">Confidence</span>
              </div>
            </div>
            {pack.patterns.length > 0 && (
              <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-800">
                {pack.patterns.map((p: string, i: number) => (
                  <span key={i} className="px-2 py-1 bg-slate-950 border border-slate-700 rounded text-[10px] text-slate-300 font-medium">
                    {p}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Region Knowledge */}
        <div className="space-y-3">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-widest flex items-center space-x-2">
            <Box size={12} />
            <span>Region Knowledge</span>
          </h3>
          <div className="grid grid-cols-1 gap-2">
            {pack.region_knowledge.map((rk: any, i: number) => (
              <div key={i} className="bg-slate-900 border border-slate-800 p-3 rounded-lg flex flex-col space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-bold text-pink-400 bg-pink-500/10 px-2 py-0.5 rounded border border-pink-500/20">
                    {rk.region_type}
                  </span>
                  <span className="text-[10px] text-slate-500 mono bg-slate-950 px-2 py-0.5 rounded">
                    Freq: {(rk.frequency * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="text-[10px] text-slate-400 mono">
                  Avg Bounds: X:{Math.round(rk.avg_bounds.x)} Y:{Math.round(rk.avg_bounds.y)} W:{Math.round(rk.avg_bounds.width)} H:{Math.round(rk.avg_bounds.height)}
                </div>
                {rk.common_selectors.length > 0 && (
                  <div className="text-[10px] text-slate-500 flex items-start space-x-1">
                    <Tag size={10} className="mt-0.5 shrink-0" />
                    <span className="truncate">{rk.common_selectors.join(', ')}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Concept Signatures */}
        <div className="space-y-3">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-widest flex items-center space-x-2">
            <TextSearch size={12} />
            <span>Concept Signatures</span>
          </h3>
          <div className="grid grid-cols-1 gap-2">
            {pack.concept_knowledge.map((ck: any, i: number) => (
              <div key={i} className="bg-slate-900 border border-slate-800 p-3 rounded-lg flex flex-col space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-bold text-emerald-400">"{ck.concept}"</span>
                  <span className="text-[10px] text-slate-500 mono bg-slate-950 px-2 py-0.5 rounded">
                    Freq: {(ck.frequency * 100).toFixed(0)}%
                  </span>
                </div>
                
                <div className="flex items-center space-x-2">
                  <Layers size={10} className="text-slate-500" />
                  <div className="flex flex-wrap gap-1">
                    {ck.region_types.map((rt: string, j: number) => (
                      <span key={j} className="text-[9px] text-pink-400 bg-pink-500/10 px-1 rounded border border-pink-500/20">
                        {rt}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="text-[10px] text-slate-400 mono space-y-1">
                  {ck.selectors.map((sel: string, j: number) => (
                    <div key={j} className="flex items-start space-x-1 bg-slate-950 p-1 rounded">
                      <Tag size={10} className="mt-0.5 text-slate-600 shrink-0" />
                      <span className="truncate">{sel}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Relational Memory (Graph) */}
        {pack.graph && pack.graph.triples && pack.graph.triples.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-widest flex items-center space-x-2">
              <Share2 size={12} />
              <span>Relational Memory</span>
            </h3>
            <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex flex-col space-y-3">
              {pack.graph.triples.map((t: any, i: number) => (
                <div key={i} className="flex items-center space-x-2 text-xs border-b border-slate-800/50 pb-2 last:border-0 last:pb-0">
                  <span className="font-bold text-slate-300 w-1/3 truncate text-right">{t.source}</span>
                  <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-[10px] text-emerald-400 font-mono tracking-widest border border-emerald-500/20 shrink-0">
                    {t.relation.replace('_', ' ')}
                  </span>
                  <span className="font-bold text-slate-300 w-1/3 truncate">{t.target}</span>
                  <span className="text-[10px] text-slate-500 ml-auto mono">{(t.confidence * 100).toFixed(0)}%</span>
                </div>
              ))}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
