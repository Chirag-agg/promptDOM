

export function CritiqueCard({ issues }: { issues?: string[] }) {
  if (!issues || issues.length === 0) return null;

  return (
    <div className="bg-red-950/30 border border-red-900/50 rounded-xl p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-red-400 uppercase tracking-widest border-b border-red-900/50 pb-2 mb-3">Design Critique</h3>
      <p className="text-xs text-red-300/80 mb-3">Potential Issues</p>
      <ul className="space-y-2">
        {issues.map((issue, idx) => (
          <li key={idx} className="flex items-start space-x-2 text-red-300">
            <span className="text-red-500 mt-0.5 shrink-0 text-lg leading-none">•</span>
            <span>{issue}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
