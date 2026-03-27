"use client";
import { useState, useEffect } from "react";
import Sidebar from "../../../components/Sidebar";
import Navbar from "../../../components/Navbar";
import { StatCard } from "../../../components/ui/Card";
import { dashboardApi, agentsApi } from "../../../services/api";
import { severityColor, timeAgo, capitalize } from "../../../utils/helpers";
import { SprintProgressBar } from "../../../components/Charts";
export default function BossDashboard() {
  const [data, setData]     = useState(null);
  const [loading, setLoading] = useState(true);

useEffect(() => {
  const fetchData = async () => {
    try {
      const res = await dashboardApi.boss();
      setData(res.data);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  };

  fetchData();
}, []);
  const sprint   = data?.active_sprint   || {};
  const tasks    = data?.task_counts     || {};
  const risks    = data?.risk_counts     || {};

  const quickActions = [
    { label: "Run Standup\nBot",       icon: "record_voice_over", agent: "standup_bot" },
    { label: "Generate\nReport",       icon: "analytics",         agent: "report_generator" },
    { label: "Sync Jira\nTasks",       icon: "sync",              agent: null },
    { label: "Create tasks\nfrom PRD", icon: "task_alt",          agent: "task_creator" },
  ];

  const triggerAgent = async (agent) => {
    if (!agent) return;
    try { await agentsApi.trigger({ project_id: 1, agent }); }
    catch (e) { console.error(e); }
  };
if (loading) return <div>Loading...</div>;
if (!data) return <div>No data</div>;
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar title="Boss Command Center" />
        <main className="flex-1 overflow-y-auto px-8 py-6 space-y-6">

          {/* Stat cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard label="Open Tasks"   value={tasks.open}   icon="task_alt"  iconColor="text-primary" />
            <StatCard label="Risk Alerts"  value={risks.total}  icon="warning"   iconColor="text-red-400"
              sub={`${risks.high || 0} high priority`} />
            <StatCard label="Stale PRs"    value={data?.stale_prs ?? "—"} icon="merge_type" iconColor="text-yellow-400" />
            <StatCard label="Sprint Health" value={sprint.health_score != null ? `${sprint.health_score}` : "—"}
              icon="monitor_heart" iconColor="text-blue-400" sub={sprint.name} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Sprint progress */}
            <div className="lg:col-span-2 bg-surface-container ghost-border rounded-2xl p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-widest font-medium">Active Sprint</p>
                  <h3 className="font-headline font-bold text-lg mt-0.5">{sprint.name || "No active sprint"}</h3>
                </div>
                {sprint.health_score != null && (
                  <span className={`text-sm font-bold px-3 py-1 rounded-full bg-primary/10 text-primary`}>
                    {sprint.health_score}/100
                  </span>
                )}
              </div>
              {sprint.points_planned > 0 && (
                <SprintProgressBar
                  completed={sprint.points_completed}
                  planned={sprint.points_planned}
                  label="Story Points"
                />
              )}
              {/* Task breakdown */}
              <div className="grid grid-cols-3 gap-3 pt-2">
                {[
                  { label: "Open",    count: tasks.open,    color: "text-blue-400" },
                  { label: "Blocked", count: tasks.blocked, color: "text-red-400" },
                  { label: "Done",    count: tasks.done,    color: "text-primary" },
                ].map(({ label, count, color }) => (
                  <div key={label} className="bg-surface-container-high rounded-xl p-3 text-center">
                    <p className={`text-xl font-bold font-headline ${color}`}>{count ?? 0}</p>
                    <p className="text-xs text-slate-500">{label}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick actions */}
            <div className="bg-surface-container ghost-border rounded-2xl p-5">
              <p className="text-xs text-slate-500 uppercase tracking-widest font-medium mb-3">Quick Actions</p>
              <div className="grid grid-cols-2 gap-2">
                {quickActions.map(({ label, icon, agent }) => (
                  <button key={label} onClick={() => triggerAgent(agent)}
                    className="flex flex-col items-center gap-1.5 p-3 bg-surface-container-high rounded-xl hover:bg-surface-container-highest transition-colors group">
                    <span className="material-symbols-outlined text-[22px] text-primary group-hover:scale-110 transition-transform"
                      style={{ fontVariationSettings: "'FILL' 1" }}>{icon}</span>
                    <span className="text-[11px] font-bold text-center leading-tight whitespace-pre-line">{label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Risk alerts preview + Activity feed */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Priority risks */}
            <div className="bg-surface-container ghost-border rounded-2xl p-5">
              <div className="flex items-center justify-between mb-4">
                <p className="text-xs text-slate-500 uppercase tracking-widest font-medium">Priority Risks</p>
                <a href="/risks" className="text-xs text-primary hover:underline">View all</a>
              </div>
              <div className="space-y-3">
                {(data?.recent_risks || []).map((r) => (
                  <div key={r.id} className={`p-3 rounded-xl border ${severityColor(r.severity)}`}>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-[9px] font-bold uppercase tracking-widest px-1.5 py-0.5 rounded ${
                        r.severity === "high" || r.severity === "critical" ? "bg-red-500 text-black" : "bg-yellow-500 text-black"
                      }`}>⚠️ {r.severity}</span>
                    </div>
                    <p className="text-sm font-semibold leading-snug">{r.title}</p>
                    <p className="text-[10px] text-slate-500 mt-1">{r.detected_by} · {timeAgo(r.created_at)}</p>
                  </div>
                ))}
                {(!data?.recent_risks?.length) && (
                  <p className="text-xs text-slate-500 text-center py-4">No active risks 🎉</p>
                )}
              </div>
            </div>

            {/* Activity feed */}
            <div className="bg-surface-container ghost-border rounded-2xl p-5">
              <p className="text-xs text-slate-500 uppercase tracking-widest font-medium mb-4">AI Activity Feed</p>
              <div className="space-y-3">
                {(data?.activity_feed || []).map((item, i) => (
                  <div key={i} className="flex gap-3 items-start">
                    <div className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5 shrink-0" />
                    <p className="text-xs text-on-surface leading-relaxed">{item.text}</p>
                  </div>
                ))}
                {(!data?.activity_feed?.length) && (
                  <p className="text-xs text-slate-500 text-center py-4">No recent activity</p>
                )}
              </div>
            </div>
          </div>

        </main>
      </div>
    </div>
  );
}
