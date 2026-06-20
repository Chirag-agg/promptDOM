import { useState } from 'react';
import { Camera, Loader2 } from 'lucide-react';
import { studioApi } from '../../api/client';
import { SnapshotBrowser } from './SnapshotBrowser';
import { SnapshotDetails } from './SnapshotDetails';

export function SnapshotExplorer() {
  const [selectedSnapshot, setSelectedSnapshot] = useState<any | null>(null);
  const [isCapturing, setIsCapturing] = useState(false);
  const [captureError, setCaptureError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleCapture = async () => {
    setIsCapturing(true);
    setCaptureError(null);
    try {
      const snapshot = await studioApi.captureCurrentPage();
      setSelectedSnapshot(snapshot);
      setRefreshKey(k => k + 1);
    } catch (err: any) {
      setCaptureError(err.message || 'Failed to capture page');
    } finally {
      setIsCapturing(false);
    }
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Top Action Bar */}
      <div className="flex items-center justify-between px-1 pb-4 shrink-0">
        <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-widest">
          Site Snapshots
        </h3>
        <button
          onClick={handleCapture}
          disabled={isCapturing}
          className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-400 text-white text-xs font-semibold px-4 py-2 rounded-lg transition-colors shadow-lg shadow-blue-900/20 active:scale-95 border border-blue-500 disabled:border-slate-600"
        >
          {isCapturing ? (
            <>
              <Loader2 size={14} className="animate-spin" />
              <span>Capturing…</span>
            </>
          ) : (
            <>
              <Camera size={14} />
              <span>Capture Current Page</span>
            </>
          )}
        </button>
      </div>

      {/* Error */}
      {captureError && (
        <div className="mb-3 p-2 bg-red-900/20 border border-red-900/50 rounded-lg text-xs text-red-400 mono shrink-0">
          {captureError}
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-y-auto custom-scrollbar pr-1">
        {selectedSnapshot ? (
          <SnapshotDetails
            snapshot={selectedSnapshot}
            onBack={() => setSelectedSnapshot(null)}
          />
        ) : (
          <SnapshotBrowser
            key={refreshKey}
            onSelect={setSelectedSnapshot}
          />
        )}
      </div>
    </div>
  );
}
