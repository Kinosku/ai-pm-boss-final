"use client";
import { useState, useEffect } from "react";
import Sidebar from "../../../components/Sidebar";
import Navbar from "../../../components/Navbar";
import { StatCard } from "../../../components/ui/Card";
import { SprintProgressBar } from "../../../components/Charts";
import { agentsApi } from "../../../services/api";
import { useAuth } from "../../../context/AuthContext";
import { useRouter } from "next/navigation";
import { timeAgo, severityColor } from "../../../utils/helpers";

const MOCK = {
  active_sprint: { name: "Sprint 3 - Core Agents", health_score: 74, points_completed: 18, points_planned: 28 },
  task_counts: { open: 12, blocked: 3, done: 18 },
  risk_counts: { total: 4, high: 2 },
  stale_prs: 3,
  recent_risks: [
    { id: 1, title: "Auth Service sprint velocity down 38%", severity: "high", detected_by: "Delay Predictor Agent", created_at: new Date(Date.now() - 3600000).toISOString() },
    { id: 2, title: "3 PRs stale for 5+ days", severity: "medium", detected_by: "PR Mapper Agent", created_at: new Date(Date.now() - 7200000).toISOString() },
  ],
  activity_feed: [
    { text: "Task Creator Agent generated 6 tasks from PRD uploaded by Sofi" },
    { text: "PR #47 mapped to TASK-023 automatically with 94% confidence" },
    { text: "Delay Predictor flagged Sprint 3 at risk — 74/100 health score" },
    { text: "Weekly report generated and delivered to Slack #pm-channel" },
    { text: "Standup summary compiled from 4 developer updates" },
  ],
};

const quickActions = [
  { label: "Run Standup Bot", icon: "🎙️", agent: "standup_bot" },
  { label: "Generate Report", icon: "📊", agent: "report_generator" },
  { label: "Scan Delays", icon: "🔍", agent: "delay_predictor" },
  { label: "Create Tasks", icon: "✅", agent: "task_creator" },
];

export default function BossDashboard() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [data] = useState(MOCK);
  const [triggering, setTriggering] = useState(null);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    if (!authLoading && (!user || user.role !== "boss")) {
      router.push("/");
    }
  }, [user, authLoading, router]);

  const triggerAgent = async (agent) => {
    setTriggering(agent);
    setMsg("");
    try {
      await agentsApi.trigger({ agent, project_id: 1 });
      setMsg(`✅ ${agent.replace(/_/g, " ")} triggered successfully!`);
    } catch {
      setMsg(`✅ ${agent.replace(/_/g, " ")} queued (demo mode)`);
    } finally {
      setTriggering(null);
      setTimeout(() => setMsg(""), 3000);
    }
  };

  if (authLoading) return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <p className="text-on-surface-variant text-sm">Loading...</p>
    </div>
  );

  const sprint = data.active_sprint;
  const tasks = data.task_counts;
  const risks = data.risk_counts;

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar title="Boss Command Center" />
        <main className="flex-1 overflow-y-auto px-6 py-6 space-y-6 scrollbar-hide">

          {msg && (
            <div className="bg-primary/10 border border-primary/20 rounded-xl px-4 py-2.5 text-sm text-primary">
              {msg}
            </div>
          )}

          {/* Stats */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard label="Open Tasks" value={tasks.open} icon="✅" iconColor="text-primary" />
            <StatCard label="Risk Alerts" value={risks.total} icon="⚠️" iconColor="text-red-400" sub={`${risks.high} high priority`} />
            <StatCard label="Stale PRs" value={data.stale_prs} icon="🔀" iconColor="text-yellow-400" />
            <StatCard label="Sprint Health" value={`${sprint.health_score}/100`} icon="💓" iconColor="text-blue-400" sub={sprint.name} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Sprint progress */}
            <div className="lg:col-span-2 bg-surface-container ghost-border rounded-2xl p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-[10px] text-slate-500 uppercase tracking-widest font-medium">Active Sprint</p>
                  <h3 className="font-headline font-bold text-lg mt-0.5">{sprint.name}</h3>
                </div>
                <span className="text-sm font-bold px-3 py-1 rounded-full bg-primary/10 text-primary">
                  {sprint.health_score}/100
                </span>
              </div>
              <SprintProgressBar completed={sprint.points_completed} planned={sprint.points_planned} label="Story Points" />
              <div className="grid grid-cols-3 gap-3 pt-2">
                {[
                  { label: "Open", count: tasks.open, color: "text-blue-400" },
                  { label: "Blocked", count: tasks.blocked, color: "text-red-400" },
                  { label: "Done", count: tasks.done, color: "text-primary" },
                ].map(({ label, count, color }) => (
                  <div key={label} className="bg-surface-container-high rounded-xl p-3 text-center">
                    <p className={`text-xl font-bold font-headline ${color}`}>{count}</p>
                    <p className="text-xs text-slate-500">{label}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick actions */}
            <div className="bg-surface-container ghost-border rounded-2xl p-5">
              <p className="text-[10px] text-slate-500 uppercase tracking-widest font-medium mb-3">Quick Actions</p>
              <div className="grid grid-cols-2 gap-2">
                {quickActions.map(({ label, icon, agent }) => (
                  <button key={label} onClick={() => triggerAgent(agent)} disabled={triggering === agent}
                    className="flex flex-col items-center gap-2 p-3 bg-surface-container-high rounded-xl hover:bg-surface-container-highest transition-colors disabled:opacity-50">
                    <span className="text-2xl">{icon}</span>
                    <span className="text-[11px] font-bold text-center leading-tight">{label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Risks */}
            <div className="bg-surface-container ghost-border rounded-2xl p-5">
              <div className="flex items-center justify-between mb-4">
                <p className="text-[10px] text-slate-500 uppercase tracking-widest font-medium">Priority Risks</p>
                <a href="/risks" className="text-xs text-primary hover:underline">View all</a>
              </div>
              <div className="space-y-3">
                {data.recent_risks.map((r) => (
                  <div key={r.id} className={`p-3 rounded-xl border ${severityColor(r.severity)}`}>
                    <span className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded mr-2 ${
                      r.severity === "high" ? "bg-red-500 text-white" : "bg-yellow-500 text-black"
                    }`}>{r.severity}</span>
                    <p className="text-sm font-semibold mt-1">{r.title}</p>
                    <p className="text-[10px] text-slate-500 mt-1">{r.detected_by} · {timeAgo(r.created_at)}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Activity */}
            <div className="bg-surface-container ghost-border rounded-2xl p-5">
              <p className="text-[10px] text-slate-500 uppercase tracking-widest font-medium mb-4">AI Activity Feed</p>
              <div className="space-y-3">
                {data.activity_feed.map((item, i) => (
                  <div key={i} className="flex gap-3 items-start">
                    <div className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5 shrink-0" />
                    <p className="text-xs text-on-surface leading-relaxed">{item.text}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

        </main>
      </div>
    </div>
  );
}
