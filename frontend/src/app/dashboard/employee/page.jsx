"use client";
import { useEffect, useState } from "react";
import Sidebar  from "@/components/Sidebar";
import Navbar   from "@/components/Navbar";
import { StatCard } from "@/components/ui/Card";
import { dashboardApi, standupsApi } from "@/services/api";
import { statusColor, priorityColor, prStatusColor, capitalize, formatDate } from "@/utils/helpers";

export default function EmployeeDashboard() {
  const [data, setData]     = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    dashboardApi.employee()
      .then(({ data }) => setData(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const dev    = data?.developer     || {};
  const tasks  = data?.my_tasks      || [];
  const prs    = data?.my_prs        || [];
  const counts = data?.task_counts   || {};

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar title="My Work" />
        <main className="flex-1 overflow-y-auto px-8 py-6 space-y-6">

          {/* Stats */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard label="Open Tasks"   value={dev.open_tasks}  icon="task_alt"     iconColor="text-primary" />
            <StatCard label="In Progress"  value={counts.in_progress ?? 0} icon="pending" iconColor="text-blue-400" />
            <StatCard label="Blocked"      value={counts.blocked ?? 0}  icon="block"    iconColor="text-red-400" />
            <StatCard label="Velocity"     value={dev.velocity ? `${dev.velocity}pts` : "—"} icon="bolt" iconColor="text-yellow-400" />
          </div>

          {/* Standup banner */}
          {!data?.standup_submitted_today && (
            <div className="flex items-center justify-between bg-primary/5 border border-primary/20 rounded-2xl px-5 py-4">
              <div className="flex items-center gap-3">
                <span className="material-symbols-outlined text-primary text-2xl" style={{ fontVariationSettings: "'FILL' 1" }}>record_voice_over</span>
                <div>
                  <p className="text-sm font-bold">Submit your standup!</p>
                  <p className="text-xs text-on-surface-variant">You haven't submitted today's update yet.</p>
                </div>
              </div>
              <a href="/standups" className="velocity-gradient-bg text-background font-bold px-4 py-2 rounded-xl text-xs hover:opacity-90 transition-opacity">
                Submit Now
              </a>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* My Tasks */}
            <div className="bg-surface-container ghost-border rounded-2xl overflow-hidden">
              <div className="flex items-center justify-between px-5 py-4 border-b border-white/5">
                <p className="font-headline font-bold">My Tasks</p>
                <a href="/tasks" className="text-xs text-primary hover:underline">View all</a>
              </div>
              <div className="divide-y divide-white/5">
                {tasks.slice(0, 6).map((t) => (
                  <div key={t.id} className="flex items-center gap-3 px-5 py-3 hover:bg-white/[0.02]">
                    <span className={`w-2 h-2 rounded-full shrink-0 ${
                      t.priority === "high" ? "bg-red-400" : t.priority === "medium" ? "bg-yellow-400" : "bg-green-400"
                    }`} />
                    <p className="flex-1 text-sm truncate">{t.title}</p>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${statusColor(t.status)}`}>
                      {capitalize(t.status)}
                    </span>
                    {t.due_date && <span className="text-[10px] text-slate-500 hidden lg:block">{formatDate(t.due_date)}</span>}
                  </div>
                ))}
                {tasks.length === 0 && <p className="text-xs text-slate-500 text-center py-6">No tasks assigned 🎉</p>}
              </div>
            </div>

            {/* My PRs */}
            <div className="bg-surface-container ghost-border rounded-2xl overflow-hidden">
              <div className="flex items-center justify-between px-5 py-4 border-b border-white/5">
                <p className="font-headline font-bold">My PRs</p>
                <a href="/prs" className="text-xs text-primary hover:underline">View all</a>
              </div>
              <div className="divide-y divide-white/5">
                {prs.map((pr) => (
                  <div key={pr.id} className="flex items-center gap-3 px-5 py-3 hover:bg-white/[0.02]">
                    <span className="material-symbols-outlined text-[16px] text-slate-500">merge_type</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm truncate">#{pr.pr_number} {pr.title}</p>
                      {pr.is_stale && <p className="text-[10px] text-yellow-400">Stale · needs review</p>}
                    </div>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${prStatusColor(pr.status)}`}>
                      {capitalize(pr.status)}
                    </span>
                  </div>
                ))}
                {prs.length === 0 && <p className="text-xs text-slate-500 text-center py-6">No open PRs</p>}
              </div>
            </div>
          </div>

        </main>
      </div>
    </div>
  );
}
