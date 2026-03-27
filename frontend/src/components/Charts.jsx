"use client";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid, Legend,
} from "recharts";

const tooltipStyle = {
  backgroundColor: "#1c2026",
  border: "1px solid rgba(255,255,255,0.06)",
  borderRadius: 8,
  color: "#e0e2eb",
  fontSize: 12,
};

// ─── Velocity Bar Chart ───────────────────────────────────────────────────────
export function VelocityChart({ data = [] }) {
  return (
    <ResponsiveContainer width="100%" height={180}>
      <BarChart data={data} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
        <XAxis dataKey="sprint_name" tick={{ fill: "#83958a", fontSize: 10 }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fill: "#83958a", fontSize: 10 }} axisLine={false} tickLine={false} />
        <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
        <Bar dataKey="points_planned"   fill="rgba(0,200,255,0.25)" radius={[4,4,0,0]} name="Planned" />
        <Bar dataKey="points_completed" fill="#00ffb4"              radius={[4,4,0,0]} name="Delivered" />
      </BarChart>
    </ResponsiveContainer>
  );
}

// ─── Burndown Line Chart ──────────────────────────────────────────────────────
export function BurndownChart({ data = [] }) {
  return (
    <ResponsiveContainer width="100%" height={180}>
      <LineChart data={data} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
        <XAxis dataKey="day"      tick={{ fill: "#83958a", fontSize: 10 }} axisLine={false} tickLine={false} />
        <YAxis                    tick={{ fill: "#83958a", fontSize: 10 }} axisLine={false} tickLine={false} />
        <Tooltip contentStyle={tooltipStyle} />
        <Line dataKey="ideal"     stroke="rgba(255,255,255,0.2)" strokeDasharray="4 4" dot={false} name="Ideal" />
        <Line dataKey="remaining" stroke="#00ffb4" strokeWidth={2} dot={false} name="Remaining" />
      </LineChart>
    </ResponsiveContainer>
  );
}

// ─── Sprint Progress Bar ──────────────────────────────────────────────────────
export function SprintProgressBar({ completed, planned, label }) {
  const pct = planned > 0 ? Math.min(Math.round((completed / planned) * 100), 100) : 0;
  const color = pct >= 75 ? "#00ffb4" : pct >= 50 ? "#facc15" : "#f87171";
  return (
    <div className="space-y-1.5">
      {label && (
        <div className="flex justify-between text-xs">
          <span className="text-on-surface-variant">{label}</span>
          <span className="font-mono" style={{ color }}>{pct}%</span>
        </div>
      )}
      <div className="h-1.5 w-full bg-surface-container-high rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
      <div className="flex justify-between text-[10px] text-slate-500">
        <span>{completed} pts delivered</span>
        <span>{planned} pts planned</span>
      </div>
    </div>
  );
}

// ─── Health Score Ring ────────────────────────────────────────────────────────
export function HealthRing({ score = 0, size = 80 }) {
  const r   = (size - 10) / 2;
  const circ = 2 * Math.PI * r;
  const dash = (score / 100) * circ;
  const color = score >= 75 ? "#00ffb4" : score >= 50 ? "#facc15" : "#f87171";

  return (
    <svg width={size} height={size} className="-rotate-90">
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={6} />
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={6}
        strokeDasharray={`${dash} ${circ}`} strokeLinecap="round" className="transition-all duration-700" />
      <text x="50%" y="50%" dominantBaseline="middle" textAnchor="middle"
        fill={color} fontSize={size * 0.22} fontWeight="700"
        style={{ transform: "rotate(90deg)", transformOrigin: "center" }}>
        {score}
      </text>
    </svg>
  );
}
