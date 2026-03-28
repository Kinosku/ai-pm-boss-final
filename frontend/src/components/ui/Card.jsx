export function StatCard({ label, value, icon, iconColor, sub }) {
  return (
    <div className="bg-surface-container ghost-border rounded-2xl p-5">
      <div className="flex items-start justify-between mb-3">
        <span className={`text-2xl ${iconColor || "text-primary"}`}>{icon}</span>
      </div>
      <p className="text-2xl font-bold font-headline">{value ?? "—"}</p>
      <p className="text-xs text-on-surface-variant mt-1">{label}</p>
      {sub && <p className="text-[10px] text-slate-500 mt-0.5 truncate">{sub}</p>}
    </div>
  );
}

export function Card({ children, className = "" }) {
  return (
    <div className={`bg-surface-container ghost-border rounded-2xl ${className}`}>
      {children}
    </div>
  );
}
