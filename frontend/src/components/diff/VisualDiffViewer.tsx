import { AlertCircle, ArrowRight, CheckCircle2, XCircle } from 'lucide-react';
import { API_BASE_URL } from '../../api/client';

export function VisualDiffViewer({ execution }: { execution: any }) {
  if (!execution) return null;

  return (
    <div className="flex flex-col space-y-6">
      {/* Metrics & Summary */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-slate-900 border border-slate-700 p-4 rounded-xl flex flex-col items-center justify-center text-center">
          <span className="text-3xl font-bold text-red-400">{execution.objective_metrics?.dom_nodes_removed || 0}</span>
          <span className="text-xs text-slate-400 font-medium uppercase tracking-wider mt-1">Nodes Removed</span>
        </div>
        <div className="bg-slate-900 border border-slate-700 p-4 rounded-xl flex flex-col items-center justify-center text-center">
          <span className="text-3xl font-bold text-blue-400">{execution.objective_metrics?.dom_nodes_changed || 0}</span>
          <span className="text-xs text-slate-400 font-medium uppercase tracking-wider mt-1">Nodes Changed</span>
        </div>
        <div className="bg-slate-900 border border-slate-700 p-4 rounded-xl flex flex-col items-center justify-center text-center">
          <span className="text-3xl font-bold text-green-400">{execution.objective_metrics?.dom_nodes_added || 0}</span>
          <span className="text-xs text-slate-400 font-medium uppercase tracking-wider mt-1">Nodes Added</span>
        </div>
      </div>

      {execution.diff_summary && (
        <div className="bg-slate-900 border border-slate-700 p-4 rounded-xl">
          <h4 className="text-sm font-semibold text-slate-300 mb-2 flex items-center gap-2">
            <AlertCircle size={16} /> Diff Summary
          </h4>
          <p className="text-sm text-slate-400 whitespace-pre-wrap">{execution.diff_summary}</p>
        </div>
      )}

      {/* Visual Diff: Before | After */}
      <div className="grid grid-cols-2 gap-4">
        <div className="flex flex-col space-y-2">
          <span className="text-xs font-bold text-slate-500 tracking-wider uppercase">Before</span>
          <div className="bg-slate-900 border border-slate-700 rounded-xl overflow-hidden aspect-video relative">
            {execution.before_screenshot_path ? (
              <img src={`${API_BASE_URL}${execution.before_screenshot_path}`} alt="Before" className="w-full h-full object-cover object-top" />
            ) : (
              <div className="flex items-center justify-center h-full text-slate-600">No Image</div>
            )}
          </div>
        </div>

        <div className="flex flex-col space-y-2">
          <span className="text-xs font-bold text-slate-500 tracking-wider uppercase">After</span>
          <div className="bg-slate-900 border border-slate-700 rounded-xl overflow-hidden aspect-video relative">
            {execution.after_screenshot_path ? (
              <img src={`${API_BASE_URL}${execution.after_screenshot_path}`} alt="After" className="w-full h-full object-cover object-top" />
            ) : (
              <div className="flex items-center justify-center h-full text-slate-600">No Image</div>
            )}
            <div className={`absolute top-2 right-2 px-2 py-1 rounded text-xs font-bold flex items-center gap-1 ${
              execution.success ? 'bg-green-500/20 text-green-400 border border-green-500/30' : 
              'bg-red-500/20 text-red-400 border border-red-500/30'
            }`}>
              {execution.success ? <CheckCircle2 size={12} /> : <XCircle size={12} />}
              {execution.success ? 'SUCCESS' : 'FAILED'}
            </div>
          </div>
        </div>
      </div>

      {/* Reference Image below if it exists */}
      {execution.reference_screenshot_path && (
        <div className="flex flex-col space-y-2 pt-4 border-t border-slate-800">
          <span className="text-xs font-bold text-slate-500 tracking-wider uppercase flex items-center gap-2">
            Reference Target
          </span>
          <div className="bg-slate-900 border border-slate-700 rounded-xl overflow-hidden aspect-video relative">
            <img src={`${API_BASE_URL}${execution.reference_screenshot_path}`} alt="Reference" className="w-full h-full object-contain bg-black" />
          </div>
        </div>
      )}
    </div>
  );
}
