"use client";
import { useState, useEffect } from "react";
import Sidebar from "../../../components/Sidebar";
import Navbar from "../../../components/Navbar";
import { StatCard } from "../../../components/ui/Card";
import { useAuth } from "../../../context/AuthContext";
import { useRouter } from "next/navigation";
import { statusColor, prStatusColor, capitalize, formatDate } from "../../../utils/helpers";

const MOCK = {
  developer: { name: "Alex Dev", open_tasks: 5, velocity: 12 },
  task_counts: { in_progress: 2, blocked: 1, done: 8 },
  standup_submitted_today: false,
  my_tasks: [
    { id: 1, title: "Build JWT authentication module", status: "in_progress", priority: "high", due_date: new Date(Date.now() + 86400000 * 2).toISOString() },
    { id: 2, title: "Write unit tests for task creator agent", status: "todo", priority: "medium", due_date: new Date(Date.now() + 86400000 * 4).toISOString() },
    { id: 3, title: "Fix PR mapper confidence threshold", status: "in_progress", priority: "high" },
    { id: 4, title: "Setup Redis caching layer", status: "blocked", priority: "high" },
    { id: 5, title: "Update API documentation", status: "todo", priority: "low" },
  ],
  my_prs: [
    { id: 1, pr_number: 47, title: "feat: add JWT login endpoint with token refresh", status: "open", is_stale: false },
    { id: 2, pr_number: 43, title: "fix: resolve celery worker connection timeout", status: "merged", is_stale: false },
    { id: 3, pr_number: 39, title: "chore: update dependencies and fix security patches", status: "open", is_stale: true },
  ],
  integrations: [
    { id: 1, name: "GitHub", icon: "🐙", connected: true, description: "Pull requests and commits synced" },
    { id: 2, name: "Slack", icon: "💬", connected: false, description: "Team messaging and notifications" },
    { id: 3, name: "Jira", icon: "🔷", connected: false, description: "Issue tracking and sprint management" },
  ],
};

export default function EmployeeDashboard() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [data] = useState(MOCK);
  const [integrations, setIntegrations] = useState(MOCK.integrations);

  useEffect(() => {
    if (!authLoading && (!user || user.role !== "employee")) {
      router.push("/");
    }
  }, [user, authLoading, router]);

  const toggleIntegration = (id) => {
    setIntegrations((prev) =>
      prev.map((i) => i.id === id ? { ...i, connected: !i.connected } : i)
    );
  };

  if (authLoading) return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <p className="text-on-surface-variant text-sm">Loading...</p>
    </div>
  );

  const tasks = data.my_tasks;
  const prs = data.my_prs;
  const counts = data.task_counts;

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar title="My Work" />
        <main className="flex-1 overflow-y-auto px-6 py-6 space-y-6 scrollbar-hide">

          {/* Stats */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard label="Open Tasks" value={data.developer.open_tasks} icon="✅" iconColor="text-primary" />
            <StatCard label="In Progress" value={counts.in_progress} icon="⏳" iconColor="text-blue-400" />
            <StatCard label="Blocked" value={counts.blocked} icon="🚫" iconColor="text-red-400" />
            <StatCard label="Velocity" value={`${data.developer.velocity}pts`} icon="⚡" iconColor="text-yellow-400" />
          </div>

          {/* Standup banner */}
          {!data.standup_submitted_today && (
            <div className="flex items-center justify-between bg-primary/5 border border-primary/20 rounded-2xl px-5 py-4">
              <div className="flex items-center gap-3">
                <span className="text-2xl">🎙️</span>
                <div>
                  <p className="text-sm font-bold">Submit your standup!</p>
                  <p className="text-xs text-on-surface-variant">You haven't submitted today's update yet.</p>
                </div>
              </div>
              <a href="/standups"
                className="velocity-gradient-bg text-background font-bold px-4 py-2 rounded-xl text-xs hover:opacity-90 transition-opacity">
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
                {tasks.map((t) => (
                  <div key={t.id} className="flex items-center gap-3 px-5 py-3 hover:bg-white/[0.02]">
                    <span className={`w-2 h-2 rounded-full shrink-0 ${
                      t.priority === "high" ? "bg-red-400" : t.priority === "medium" ? "bg-yellow-400" : "bg-green-400"
                    }`} />
                    <p className="flex-1 text-sm truncate">{t.title}</p>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${statusColor(t.status)}`}>
                      {capitalize(t.status)}
                    </span>
                    {t.due_date && (
                      <span className="text-[10px] text-slate-500 hidden lg:block">{formatDate(t.due_date)}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* My PRs */}
            <div className="bg-surface-container ghost-border rounded-2xl overflow-hidden">
              <div className="flex items-center justify-between px-5 py-4 border-b border-white/5">
                <p className="font-headline font-bold">My Pull Requests</p>
                <a href="/prs" className="text-xs text-primary hover:underline">View all</a>
              </div>
              <div className="divide-y divide-white/5">
                {prs.map((pr) => (
                  <div key={pr.id} className="flex items-center gap-3 px-5 py-3 hover:bg-white/[0.02]">
                    <span className="text-base">🔀</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm truncate">#{pr.pr_number} {pr.title}</p>
                      {pr.is_stale && <p className="text-[10px] text-yellow-400">⚠️ Stale · needs review</p>}
                    </div>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${prStatusColor(pr.status)}`}>
                      {capitalize(pr.status)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Integrations */}
          <div className="bg-surface-container ghost-border rounded-2xl overflow-hidden">
            <div className="px-5 py-4 border-b border-white/5">
              <p className="font-headline font-bold">My Integrations</p>
              <p className="text-xs text-on-surface-variant mt-0.5">Connect your tools to sync work automatically</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-white/5">
              {integrations.map((integration) => (
                <div key={integration.id} className="p-5 flex items-center gap-4">
                  <span className="text-3xl">{integration.icon}</span>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-sm">{integration.name}</p>
                    <p className="text-[11px] text-on-surface-variant truncate">{integration.description}</p>
                    <span className={`inline-block text-[10px] font-bold mt-1 px-2 py-0.5 rounded-full ${
                      integration.connected
                        ? "bg-primary/20 text-primary"
                        : "bg-slate-700 text-slate-400"
                    }`}>
                      {integration.connected ? "✅ Connected" : "Not connected"}
                    </span>
                  </div>
                  <button
                    onClick={() => toggleIntegration(integration.id)}
                    className={`text-xs font-bold px-3 py-1.5 rounded-lg transition-all ${
                      integration.connected
                        ? "bg-red-500/20 text-red-400 hover:bg-red-500/30"
                        : "velocity-gradient-bg text-background hover:opacity-90"
                    }`}
                  >
                    {integration.connected ? "Disconnect" : "Connect"}
                  </button>
                </div>
              ))}
            </div>
          </div>

        </main>
      </div>
    </div>
  );
}
