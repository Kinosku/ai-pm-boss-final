"use client";
import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";
import Navbar  from "../components/Navbar";
import { risksApi } from "../services/api";
import { severityColor, timeAgo } from "../utils/helpers";

export default function RisksPage() {
  const [risks, setRisks]   = useState([]);
  const [counts, setCounts] = useState({});
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    Promise.all([risksApi.list({ status: "open" }), risksApi.counts()])
      .then(([r, c]) => { setRisks(r.data); setCounts(c.data); })
      .finally(() => setLoading(false));
  }, []);

  const filtered = filter === "all" ? risks : risks.filter((r) => r.severity === filter);

  const resolve = async (id) => {
    await risksApi.resolve(id);
    setRisks((prev) => prev.filter((r) => r.id !== id));
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar title="Risk Alerts" />
        <main className="flex-1 overflow-y-auto px-8 py-6">

          {/* Header */}
          <div className="flex items-start justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold font-headline">Risk Alerts</h1>
              <p className="text-on-surface-variant text-sm mt-1">AI-detected risks across all projects</p>
            </div>
            {/* Severity counts */}
            <div className="flex gap-3">
              {[
                { label: "High Risk",   key: "high",   color: "text-red-400    bg-red-500/10    border-red-500/20" },
                { label: "Medium Risk", key: "medium", color: "text-yellow-400 bg-yellow-500/10 border-yellow-500/20" },
                { label: "Low Risk",    key: "low",    color: "text-slate-400  bg-slate-500/10  border-slate-500/20" },
              ].map(({ label, key, color }) => (
                <button key={key} onClick={() => setFilter(filter === key ? "all" : key)}
                  className={`px-4 py-2 rounded-xl border text-xs font-bold transition-all ${color} ${filter === key ? "ring-1 ring-current" : ""}`}>
                  <span className="text-lg font-headline block">{(counts[key] || 0) + (key === "high" ? counts.critical || 0 : 0)}</span>
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Alert cards */}
          <div className="space-y-4">
            {loading && <p className="text-slate-500 text-sm">Loading risks…</p>}
            {!loading && filtered.length === 0 && (
              <div className="text-center py-16 text-slate-500">
                <span className="material-symbols-outlined text-5xl mb-3 block">check_circle</span>
                <p className="font-semibold">No {filter !== "all" ? filter : ""} risks found 🎉</p>
              </div>
            )}
            {filtered.map((risk) => (
              <div key={risk.id} className={`bg-surface-container ghost-border rounded-2xl p-5 border-l-4 ${
                risk.severity === "critical" || risk.severity === "high" ? "border-l-red-500" :
                risk.severity === "medium" ? "border-l-yellow-500" : "border-l-slate-600"
              }`}>
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`text-[9px] font-bold uppercase tracking-widest px-2 py-0.5 rounded ${
                        risk.severity === "high" || risk.severity === "critical" ? "bg-red-500 text-black" :
                        risk.severity === "medium" ? "bg-yellow-500 text-black" : "bg-slate-600 text-white"
                      }`}>⚠️ {risk.severity} RISK</span>
                      <span className="text-[10px] text-slate-500 font-mono">{risk.alert_id}</span>
                    </div>
                    <h3 className="text-lg font-bold mb-1">{risk.title}</h3>
                    {risk.description && <p className="text-sm text-on-surface-variant mb-3">{risk.description}</p>}
                    {risk.recommendation && (
                      <div className="bg-surface-container-high rounded-xl px-4 py-3 text-sm text-on-surface-variant border border-white/5">
                        <span className="font-semibold text-on-surface">Recommendation: </span>{risk.recommendation}
                      </div>
                    )}
                    <p className="text-[10px] text-slate-500 mt-2">Detected by {risk.detected_by} · {timeAgo(risk.created_at)}</p>
                  </div>
                  <div className="flex gap-2 shrink-0">
                    <button onClick={() => resolve(risk.id)}
                      className="px-4 py-2 text-xs font-bold velocity-gradient-bg text-background rounded-xl hover:opacity-90">
                      Resolve
                    </button>
                    <button className="px-4 py-2 text-xs font-bold bg-surface-container-high ghost-border rounded-xl hover:bg-surface-container-highest">
                      Alert via Slack
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </main>
      </div>
    </div>
  );
}
