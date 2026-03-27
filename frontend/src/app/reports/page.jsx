"use client";
import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";
import Navbar  from "../components/Navbar";
import { VelocityChart } from "../components/Charts";
import { StatCard } from "../components/ui/Card";
import Button from "../components/ui/Button";
import { reportsApi } from "../services/api";

export default function ReportsPage() {
  const [summary,   setSummary]  = useState(null);
  const [velocity,  setVelocity] = useState([]);
  const [generating, setGenerating] = useState(false);
  const [lastReport, setLastReport] = useState(null);
  const PROJECT_ID = 1;

  useEffect(() => {
    Promise.all([reportsApi.summary(PROJECT_ID), reportsApi.velocity(PROJECT_ID)])
      .then(([s, v]) => { setSummary(s.data); setVelocity(v.data); })
      .catch(console.error);
  }, []);

  const generate = async (type) => {
    setGenerating(true);
    try {
      const { data } = await reportsApi.generate({ project_id: PROJECT_ID, report_type: type });
      setLastReport(data);
    } catch (e) { console.error(e); }
    finally { setGenerating(false); }
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar title="Reports & Analytics" />
        <main className="flex-1 overflow-y-auto px-8 py-6 space-y-6">

          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold font-headline">Reports & Analytics</h1>
              <p className="text-on-surface-variant text-sm mt-1">AI-generated insights and velocity tracking</p>
            </div>
            <div className="flex gap-2">
              {["weekly","sprint","executive"].map((t) => (
                <Button key={t} variant="secondary" size="sm" onClick={() => generate(t)} disabled={generating}>
                  {capitalize(t)}
                </Button>
              ))}
              <Button onClick={() => generate("weekly")} disabled={generating}>
                <span className="material-symbols-outlined text-[18px]">analytics</span>
                {generating ? "Generating…" : "Generate Report"}
              </Button>
            </div>
          </div>

          {/* Stats */}
          {summary && (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard label="Completed Tasks" value={summary.completed_tasks} icon="task_alt"   iconColor="text-primary" />
              <StatCard label="PRs Merged"      value={summary.prs_merged}      icon="merge_type" iconColor="text-blue-400" />
              <StatCard label="Blocked Tasks"   value={summary.blocked_tasks}   icon="block"      iconColor="text-red-400" />
              <StatCard label="Open Risks"      value={summary.open_risks}      icon="warning"    iconColor="text-yellow-400" />
            </div>
          )}

          {/* Velocity chart */}
          <div className="bg-surface-container ghost-border rounded-2xl p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="font-bold text-lg">Sprint Velocity</h3>
                <p className="text-xs text-on-surface-variant font-mono">Last {velocity.length} Sprints · Story Points</p>
              </div>
              <span className="text-[10px] font-bold uppercase tracking-widest bg-primary/10 text-primary px-3 py-1 rounded-lg">Live Metric</span>
            </div>
            <VelocityChart data={velocity} />
          </div>

          {/* Last generated report */}
          {lastReport && (
            <div className="bg-surface-container ghost-border rounded-2xl p-5 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-lg capitalize">{lastReport.report_type} Report</h3>
                <span className="text-xs text-slate-500">{lastReport.generated_at} · {lastReport.generated_by}</span>
              </div>
              <p className="text-sm text-on-surface-variant italic">"{lastReport.executive_summary}"</p>
              {lastReport.key_achievements?.length > 0 && (
                <div>
                  <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Key Achievements</p>
                  <ul className="space-y-1">
                    {lastReport.key_achievements.map((a, i) => (
                      <li key={i} className="text-sm flex gap-2"><span className="text-primary">✓</span>{a}</li>
                    ))}
                  </ul>
                </div>
              )}
              {lastReport.next_period_priorities?.length > 0 && (
                <div>
                  <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Next Priorities</p>
                  <ul className="space-y-1">
                    {lastReport.next_period_priorities.map((p, i) => (
                      <li key={i} className="text-sm flex gap-2"><span className="text-blue-400">→</span>{p}</li>
                    ))}
                  </ul>
                </div>
              )}
              {lastReport.health_score != null && (
                <div className="flex items-center gap-2 pt-2 border-t border-white/5">
                  <span className="text-xs text-slate-500">Sprint Health:</span>
                  <span className={`font-bold text-sm ${lastReport.health_score >= 75 ? "text-primary" : lastReport.health_score >= 50 ? "text-yellow-400" : "text-red-400"}`}>
                    {lastReport.health_score}/100
                  </span>
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

function capitalize(s) { return s.charAt(0).toUpperCase() + s.slice(1); }
