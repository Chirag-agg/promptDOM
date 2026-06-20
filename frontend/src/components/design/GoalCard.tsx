export function GoalCard({ goal, reasoning }: { goal: string; reasoning: string }) {
  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-widest border-b border-slate-800 pb-2 mb-3">Goal</h3>
      <p className="text-lg font-medium text-slate-200">{goal}</p>
      {reasoning && (
        <p className="text-sm text-slate-400 mt-2 italic border-l-2 border-blue-500 pl-3">{reasoning}</p>
      )}
    </div>
  );
}
