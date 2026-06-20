import { useState, useEffect, useRef } from 'react';
import { ChevronRight, ChevronDown, Image, Tag, Grid3X3, FileText, ShieldCheck, Layers, AlertTriangle, BrainCircuit, Loader2, Play, RotateCw, Network } from 'lucide-react';
import { studioApi } from '../../api/client';
import { API_BASE_URL } from '../../api/client';
import { SemanticElementsTable } from './SemanticElementsTable';
import { LayoutElementsTable } from './LayoutElementsTable';

interface SnapshotDetailsProps {
  snapshot: any;
  onBack: () => void;
}

export function SnapshotDetails({ snapshot, onBack }: SnapshotDetailsProps) {
  const [summary, setSummary] = useState<any>(null);
  const [health, setHealth] = useState<any>(null);
  const [domContent, setDomContent] = useState<string | null>(null);
  const [showOverlay, setShowOverlay] = useState(false);
  const [hoveredBox, setHoveredBox] = useState<number | null>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const [imgDimensions, setImgDimensions] = useState<{ width: number; height: number; naturalWidth: number; naturalHeight: number } | null>(null);

  const [intelligence, setIntelligence] = useState<any>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const [archetype, setArchetype] = useState<any>(null);
  const [isDetecting, setIsDetecting] = useState(false);

  const handleDetectArchetype = async () => {
    setIsDetecting(true);
    try {
      const data = await studioApi.getArchetype(snapshot.snapshot_id);
      setArchetype(data);
    } catch (err) {
      console.error('Archetype detection failed:', err);
    } finally {
      setIsDetecting(false);
    }
  };

  const handleAnalyze = async () => {
    setIsAnalyzing(true);
    try {
      const data = await studioApi.analyzeSnapshot(snapshot.snapshot_id);
      setIntelligence(data);
    } catch (err) {
      console.error('Analysis failed:', err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  useEffect(() => {
    studioApi.getCaptureSummary(snapshot.snapshot_id).then(setSummary).catch(console.error);
    studioApi.getCaptureHealth(snapshot.snapshot_id).then(setHealth).catch(console.error);
  }, [snapshot.snapshot_id]);

  const loadDom = async () => {
    if (domContent !== null) return;
    try {
      const res = await fetch(`${API_BASE_URL}/${snapshot.dom_path}`);
      const text = await res.text();
      setDomContent(text);
    } catch (err) {
      setDomContent('Failed to load DOM content.');
    }
  };

  const handleImageLoad = () => {
    if (imgRef.current) {
      setImgDimensions({
        width: imgRef.current.clientWidth,
        height: imgRef.current.clientHeight,
        naturalWidth: imgRef.current.naturalWidth,
        naturalHeight: imgRef.current.naturalHeight,
      });
    }
  };

  const hostname = snapshot.hostname || new URL(snapshot.url).hostname;

  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  };

  const healthColor = health
    ? health.score >= 0.8 ? 'text-emerald-400' : health.score >= 0.5 ? 'text-amber-400' : 'text-red-400'
    : 'text-slate-500';

  const healthBg = health
    ? health.score >= 0.8 ? 'bg-emerald-500/10 border-emerald-500/30' : health.score >= 0.5 ? 'bg-amber-500/10 border-amber-500/30' : 'bg-red-500/10 border-red-500/30'
    : 'bg-slate-800 border-slate-700';

  return (
    <div className="flex flex-col space-y-4 pb-8">
      {/* Back Button */}
      <button
        onClick={onBack}
        className="self-start flex items-center space-x-1 text-sm text-slate-400 hover:text-blue-400 transition-colors"
      >
        <ChevronRight size={14} className="rotate-180" />
        <span>Back to snapshots</span>
      </button>

      {/* Header */}
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-semibold text-white">{hostname}</h3>
            <p className="text-sm text-slate-400 truncate">{snapshot.title}</p>
          </div>
          {health && (
            <div className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg border ${healthBg}`}>
              <ShieldCheck size={16} className={healthColor} />
              <span className={`text-sm font-bold mono ${healthColor}`}>{(health.score * 100).toFixed(0)}%</span>
            </div>
          )}
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          <StatCard icon={<Tag size={12} />} label="Semantic" value={summary?.semantic_count ?? snapshot.semantic_elements.length} />
          <StatCard icon={<Grid3X3 size={12} />} label="Layout" value={summary?.layout_count ?? snapshot.layout_elements.length} />
          <StatCard icon={<FileText size={12} />} label="DOM Size" value={summary ? formatBytes(summary.dom_size_bytes) : '...'} />
          <StatCard icon={<Image size={12} />} label="Screenshot" value={summary ? formatBytes(summary.screenshot_size_bytes) : '...'} />
        </div>

        {/* Meta */}
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-[10px] text-slate-500 mono">
          <span>ID: {snapshot.snapshot_id.slice(0, 8)}…</span>
          <span>URL: {snapshot.url}</span>
          <span>Captured: {new Date(snapshot.captured_at).toLocaleString()}</span>
        </div>
      </div>

      {/* Health Warnings */}
      {health && health.warnings.length > 0 && (
        <div className="bg-amber-900/10 border border-amber-900/30 rounded-xl p-3 space-y-1.5">
          <div className="flex items-center space-x-2 text-amber-400 text-xs font-semibold uppercase tracking-wider">
            <AlertTriangle size={14} />
            <span>Capture Warnings</span>
          </div>
          {health.warnings.map((w: string, i: number) => (
            <p key={i} className="text-xs text-amber-300/80 pl-6">• {w}</p>
          ))}
        </div>
      )}

      {/* Screenshot with Overlay */}
      <Accordion title="Screenshot Preview" icon={<Image size={14} className="text-blue-400" />} defaultOpen={true}>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <button
              onClick={() => setShowOverlay(!showOverlay)}
              className={`flex items-center space-x-2 text-xs px-3 py-1.5 rounded-lg border transition-colors ${
                showOverlay 
                  ? 'bg-blue-600/20 border-blue-500/40 text-blue-400' 
                  : 'bg-slate-800 border-slate-700 text-slate-400 hover:text-slate-300'
              }`}
            >
              <Layers size={12} />
              <span>{showOverlay ? 'Hide' : 'Show'} Layout Boxes</span>
            </button>
          </div>
          <div className="relative bg-black rounded-lg overflow-hidden border border-slate-700">
            <img
              ref={imgRef}
              src={`${API_BASE_URL}/${snapshot.screenshot_path}?t=${Date.now()}`}
              alt="Page Screenshot"
              className="w-full h-auto"
              onLoad={handleImageLoad}
            />
            {showOverlay && imgDimensions && snapshot.layout_elements.map((el: any, i: number) => {
              const scaleX = imgDimensions.width / imgDimensions.naturalWidth;
              const scaleY = imgDimensions.height / imgDimensions.naturalHeight;
              const x = el.x * scaleX;
              const y = el.y * scaleY;
              const w = el.width * scaleX;
              const h = el.height * scaleY;
              // Skip elements that are too small or off-screen
              if (w < 2 || h < 2 || x + w < 0 || y + h < 0) return null;
              return (
                <div
                  key={i}
                  className="absolute border border-blue-400/40 hover:border-blue-400 hover:bg-blue-400/10 transition-colors cursor-pointer"
                  style={{ left: x, top: y, width: w, height: h }}
                  onMouseEnter={() => setHoveredBox(i)}
                  onMouseLeave={() => setHoveredBox(null)}
                >
                  {hoveredBox === i && (
                    <div className="absolute bottom-full left-0 mb-1 bg-slate-900/95 backdrop-blur border border-slate-600 rounded px-2 py-1 text-[10px] text-blue-300 mono whitespace-nowrap z-50 shadow-xl">
                      {el.selector.length > 60 ? el.selector.slice(0, 60) + '…' : el.selector}
                      <span className="text-slate-500 ml-2">{Math.round(el.width)}×{Math.round(el.height)}</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </Accordion>

      {/* Semantic Elements */}
      <Accordion title={`Semantic Elements (${snapshot.semantic_elements.length})`} icon={<Tag size={14} className="text-emerald-400" />} defaultOpen={true}>
        <SemanticElementsTable elements={snapshot.semantic_elements} />
      </Accordion>

      {/* Layout Elements */}
      <Accordion title={`Layout Elements (${snapshot.layout_elements.length})`} icon={<Grid3X3 size={14} className="text-amber-400" />} defaultOpen={false}>
        <LayoutElementsTable elements={snapshot.layout_elements} />
      </Accordion>

      {/* Website Intelligence */}
      <Accordion title="Website Intelligence" icon={<BrainCircuit size={14} className="text-pink-400" />} defaultOpen={true}>
        <div className="space-y-4">
          {!intelligence ? (
            <div className="flex flex-col items-center justify-center p-6 text-slate-400 space-y-4 border border-dashed border-slate-700 rounded-lg">
              <BrainCircuit size={32} className="opacity-50" />
              <p className="text-sm">Run heuristic analysis to detect page regions</p>
              <button
                onClick={handleAnalyze}
                disabled={isAnalyzing}
                className="flex items-center space-x-2 bg-pink-600 hover:bg-pink-500 disabled:bg-slate-700 disabled:text-slate-500 text-white px-4 py-2 rounded-lg font-medium transition-colors"
              >
                {isAnalyzing ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
                <span>{isAnalyzing ? 'Analyzing...' : 'Analyze Regions'}</span>
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">Detected Regions ({intelligence.regions.length})</span>
                <button
                  onClick={handleAnalyze}
                  disabled={isAnalyzing}
                  className="text-xs text-pink-400 hover:text-pink-300 flex items-center space-x-1"
                >
                  <RotateCw size={12} className={isAnalyzing ? 'animate-spin' : ''} />
                  <span>Re-analyze</span>
                </button>
              </div>
              <div className="grid grid-cols-1 gap-3">
                {intelligence.regions.sort((a: any, b: any) => b.confidence - a.confidence).map((region: any, i: number) => (
                  <div key={i} className="bg-slate-950 border border-slate-800 p-3 rounded-lg flex flex-col space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold px-2 py-0.5 rounded border bg-pink-500/10 text-pink-400 border-pink-500/20">
                        {region.region_type}
                      </span>
                      <div className="flex items-center space-x-2">
                        <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                          <div className="h-full bg-pink-500" style={{ width: `${region.confidence * 100}%` }} />
                        </div>
                        <span className="text-[10px] text-slate-500 mono">{Math.round(region.confidence * 100)}%</span>
                      </div>
                    </div>
                    <div className="text-[10px] text-slate-400 mono truncate">{region.selector}</div>
                    <div className="text-[10px] text-slate-500">
                      <strong>Evidence:</strong> {region.evidence.join(', ')}
                    </div>
                    <div className="text-[10px] text-slate-600 mono flex space-x-3">
                      <span>X: {Math.round(region.x)}</span>
                      <span>Y: {Math.round(region.y)}</span>
                      <span>W: {Math.round(region.width)}</span>
                      <span>H: {Math.round(region.height)}</span>
                    </div>
                  </div>
                ))}
                {intelligence.regions.length === 0 && (
                  <div className="text-center text-xs text-slate-500 p-4">No regions detected.</div>
                )}
              </div>
            </div>
          )}
        </div>
      </Accordion>

      {/* Website Archetype & Patterns */}
      <Accordion title="Website Archetype & Patterns" icon={<Network size={14} className="text-orange-400" />} defaultOpen={true}>
        <div className="space-y-4">
          {!archetype ? (
            <div className="flex flex-col items-center justify-center p-6 text-slate-400 space-y-4 border border-dashed border-slate-700 rounded-lg">
              <Network size={32} className="opacity-50" />
              <p className="text-sm">Detect holistic website archetype and patterns</p>
              <button
                onClick={handleDetectArchetype}
                disabled={isDetecting}
                className="flex items-center space-x-2 bg-orange-600 hover:bg-orange-500 disabled:bg-slate-700 disabled:text-slate-500 text-white px-4 py-2 rounded-lg font-medium transition-colors"
              >
                {isDetecting ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
                <span>{isDetecting ? 'Detecting...' : 'Detect Archetype'}</span>
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">Holistic Understanding</span>
                <button
                  onClick={handleDetectArchetype}
                  disabled={isDetecting}
                  className="text-xs text-orange-400 hover:text-orange-300 flex items-center space-x-1"
                >
                  <RotateCw size={12} className={isDetecting ? 'animate-spin' : ''} />
                  <span>Re-detect</span>
                </button>
              </div>

              {/* Main Archetype Card */}
              <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl flex flex-col space-y-4 relative overflow-hidden">
                <div className="absolute -right-4 -top-4 opacity-5">
                  <Network size={120} />
                </div>
                
                <div className="flex items-center justify-between relative z-10">
                  <span className="text-lg font-black px-3 py-1 rounded-lg border bg-orange-500/10 text-orange-400 border-orange-500/20 tracking-wider">
                    {archetype.archetype}
                  </span>
                  <div className="flex flex-col items-end">
                    <span className="text-2xl font-bold mono text-white">{Math.round(archetype.confidence * 100)}%</span>
                    <span className="text-[10px] text-slate-500 uppercase tracking-widest">Confidence</span>
                  </div>
                </div>

                <div className="space-y-1 relative z-10">
                  <h4 className="text-[10px] text-slate-500 uppercase tracking-widest mb-2">Evidence</h4>
                  {archetype.evidence.map((ev: string, i: number) => (
                    <div key={i} className="flex items-start space-x-2 text-xs text-slate-300">
                      <span className="text-emerald-400 mt-0.5">✓</span>
                      <span>{ev}</span>
                    </div>
                  ))}
                  {archetype.evidence.length === 0 && (
                    <div className="text-xs text-slate-500 italic">No clear evidence detected.</div>
                  )}
                </div>

                {/* Detected Patterns */}
                {archetype.patterns.length > 0 && (
                  <div className="space-y-2 relative z-10 pt-2 border-t border-slate-800">
                    <h4 className="text-[10px] text-slate-500 uppercase tracking-widest">Detected Patterns</h4>
                    <div className="flex flex-wrap gap-2">
                      {archetype.patterns.map((p: string, i: number) => (
                        <span key={i} className="px-2 py-1 bg-slate-800 border border-slate-700 rounded text-[10px] text-slate-300 font-medium">
                          {p}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Competitors & Scores */}
              {Object.keys(archetype.archetype_scores).length > 1 && (
                <div className="bg-slate-900 border border-slate-800 p-3 rounded-lg space-y-2">
                  <h4 className="text-[10px] text-slate-500 uppercase tracking-widest">Archetype Score Signals</h4>
                  <div className="grid grid-cols-2 gap-2">
                    {Object.entries(archetype.archetype_scores)
                      .sort((a: any, b: any) => b[1] - a[1])
                      .map(([arc, score]: [string, any], i: number) => (
                      <div key={i} className="flex items-center justify-between bg-slate-950 px-2 py-1.5 rounded border border-slate-800">
                        <span className="text-[10px] text-slate-400">{arc}</span>
                        <span className="text-[10px] text-orange-400 mono font-bold">{score} pts</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </Accordion>

      {/* DOM Inspector */}
      <Accordion title="DOM Inspector" icon={<FileText size={14} className="text-purple-400" />} defaultOpen={false} onOpen={loadDom}>
        {domContent === null ? (
          <div className="p-4 text-center text-xs text-slate-500 animate-pulse">Loading DOM...</div>
        ) : (
          <div className="max-h-[400px] overflow-auto bg-slate-950 rounded-lg border border-slate-800 p-3">
            <pre className="text-[10px] text-slate-400 mono whitespace-pre-wrap break-all leading-relaxed">{domContent}</pre>
          </div>
        )}
      </Accordion>
    </div>
  );
}

function StatCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: string | number }) {
  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-lg px-3 py-2 flex items-center space-x-2">
      <div className="text-slate-500">{icon}</div>
      <div>
        <p className="text-[10px] text-slate-500 uppercase tracking-wider">{label}</p>
        <p className="text-sm text-slate-200 font-semibold mono">{value}</p>
      </div>
    </div>
  );
}

function Accordion({ title, icon, children, defaultOpen = false, onOpen }: {
  title: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
  defaultOpen?: boolean;
  onOpen?: () => void;
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  const handleToggle = () => {
    const next = !isOpen;
    setIsOpen(next);
    if (next && onOpen) onOpen();
  };

  return (
    <div className="flex flex-col">
      <button
        onClick={handleToggle}
        className={`flex items-center space-x-2 p-3 bg-slate-800 hover:bg-slate-700 transition-colors border border-slate-700 ${isOpen ? 'rounded-t-xl border-b-0' : 'rounded-xl'}`}
      >
        {isOpen ? <ChevronDown size={14} className="text-slate-400" /> : <ChevronRight size={14} className="text-slate-400" />}
        {icon}
        <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-widest">{title}</h4>
      </button>
      {isOpen && (
        <div className="bg-slate-900 p-3 rounded-b-xl border-x border-b border-slate-700">
          {children}
        </div>
      )}
    </div>
  );
}
