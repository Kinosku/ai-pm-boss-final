import clsx from "clsx";

export default function Card({ children, className = "", glow = false, ...props }) {
  return (
    <div
      className={clsx(
        "bg-surface-container ghost-border rounded-2xl",
        glow && "ambient-glow",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function StatCard({ label, value, icon, iconColor = "text-primary", sub }) {
  return (
    <Card className="p-5 flex items-center gap-4">
      <div className={`w-10 h-10 rounded-xl bg-surface-container-high flex items-center justify-center shrink-0 ${iconColor}`}>
        <span className="material-symbols-outlined text-[22px]" style={{ fontVariationSettings: "'FILL' 1" }}>{icon}</span>
      </div>
      <div>
        <p className="text-2xl font-bold font-headline">{value ?? "—"}</p>
        <p className="text-xs text-on-surface-variant">{label}</p>
        {sub && <p className="text-[10px] text-slate-600 mt-0.5">{sub}</p>}
      </div>
    </Card>
  );
}
