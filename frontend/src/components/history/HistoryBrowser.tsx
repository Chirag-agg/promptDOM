import { useEffect, useState } from 'react';
import { History, LayoutTemplate, Clock, ArrowRight, ExternalLink } from 'lucide-react';
import { studioApi } from '../../api/client';

export function HistoryBrowser({ onSelectRecord }: { onSelectRecord: (runId: string) => void }) {
  const [records, setRecords] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const data = await studioApi.getHistory();
        setRecords(data);
      } catch (err) {
        console.error("Failed to fetch history:", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchHistory();
  }, []);

  if (isLoading) {
    return <div className="p-8 text-center text-slate-500">Loading history...</div>;
  }

  if (records.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-slate-500 space-y-4">
        <History size={48} className="opacity-20" />
        <p>No transformation history found.</p>
        <p className="text-sm">Run your first redesign to see it here.</p>
      </div>
    );
  }

  const statusColors = {
    SUCCESS: 'bg-green-500/20 text-green-400 border-green-500/30',
    PARTIAL: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    FAILED: 'bg-red-500/20 text-red-400 border-red-500/30',
  };

  return (
    <div className="space-y-4 pr-2 custom-scrollbar pb-4">
      {records.map((record) => (
        <button
          key={record.run_id}
          onClick={() => onSelectRecord(record.run_id)}
          className="w-full text-left bg-slate-900 border border-slate-700 hover:border-blue-500 hover:bg-slate-800 rounded-xl p-4 transition-all group flex flex-col space-y-3"
        >
          <div className="flex justify-between items-start">
            <div className="flex items-center space-x-2 text-slate-300 font-medium">
              <LayoutTemplate size={16} className="text-slate-500" />
              <span>{record.site.replace('https://', '').replace('http://', '').split('/')[0]}</span>
            </div>
            <div className={`px-2 py-0.5 rounded text-[10px] font-bold border ${statusColors[record.status as keyof typeof statusColors] || statusColors.FAILED}`}>
              {record.status}
            </div>
          </div>
          
          <p className="text-slate-200 text-sm font-medium leading-relaxed truncate">
            "{record.prompt}"
          </p>
          
          <div className="flex justify-between items-center text-xs text-slate-500 pt-2 border-t border-slate-800">
            <div className="flex items-center space-x-1">
              <Clock size={12} />
              <span>{new Date(record.timestamp).toLocaleString()}</span>
            </div>
            
            <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity text-blue-400">
              <span>View Details</span>
              <ArrowRight size={14} />
            </div>
          </div>
        </button>
      ))}
    </div>
  );
}
