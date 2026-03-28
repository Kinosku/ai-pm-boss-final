export function SprintProgressBar({ completed, planned, label }) {
  const pct = planned > 0 ? Math.min(Math.round((completed / planned) * 100), 100) : 0;
  return (
    <div>
      <div className="flex justify-between text-xs text-on-surface-variant mb-1.5">
        <span>{label || "Progress"}</span>
        <span>{completed} / {planned} ({pct}%)</span>
      </div>
      <div className="h-2 bg-white/5 rounded-full overflow-hidden">
        <div
          className="h-full velocity-gradient-bg rounded-full transition-all duration-700"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export function DonutChart({ value, max, label, color = "#00ffb4" }) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  const r = 36, cx = 44, cy = 44;
  const circ = 2 * Math.PI * r;
  const dash = (pct / 100) * circ;
  return (
    <div className="flex flex-col items-center">
      <svg width={88} height={88} viewBox="0 0 88 88">
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth={8} />
        <circle cx={cx} cy={cy} r={r} fill="none" stroke={color} strokeWidth={8}
          strokeDasharray={`${dash} ${circ}`} strokeLinecap="round"
          transform={`rotate(-90 ${cx} ${cy})`} />
        <text x={cx} y={cy} textAnchor="middle" dominantBaseline="middle"
          fill="#e8eaed" fontSize={14} fontWeight="bold">{value}</text>
      </svg>
      <p className="text-xs text-on-surface-variant mt-1">{label}</p>
    </div>
  );
}
