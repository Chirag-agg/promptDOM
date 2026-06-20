export function ConfidenceMeter({ confidence }: { confidence: number }) {
  // Convert 0-1 to 0-100
  const percentage = Math.round(confidence * 100);
  
  // Create 10 blocks for the meter
  const blocks = 10;
  const filledBlocks = Math.round((percentage / 100) * blocks);
  
  let colorClass = 'text-green-500';
  if (percentage < 40) colorClass = 'text-red-500';
  else if (percentage < 70) colorClass = 'text-yellow-500';

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-widest border-b border-slate-800 pb-2 mb-3">Design Confidence</h3>
      <div className="flex items-center space-x-4">
        <div className={`mono text-lg tracking-[0.2em] ${colorClass}`}>
          {Array.from({ length: blocks }).map((_, i) => (
            <span key={i}>{i < filledBlocks ? '█' : '░'}</span>
          ))}
        </div>
        <span className={`font-mono font-bold ${colorClass}`}>{percentage}%</span>
      </div>
    </div>
  );
}
