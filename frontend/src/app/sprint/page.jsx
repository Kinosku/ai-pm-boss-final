"use client";
import { useEffect, useState } from "react";
import Sidebar from "../../components/Sidebar";
import Navbar  from "../../components/Navbar";
import { sprintsApi, tasksApi } from "../../services/api";
import { statusColor, capitalize, sprintProgress } from "../../utils/helpers";
import { SprintProgressBar } from "../../components/Charts";

const COLUMNS = ["backlog","todo","in_progress","in_review","blocked","done"];
const COL_LABELS = { backlog:"Backlog", todo:"To Do", in_progress:"In Progress", in_review:"In Review", blocked:"Blocked", done:"Done" };

export default function SprintPage() {
  const [sprint, setSprint] = useState(null);
  const [tasks,  setTasks]  = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    sprintsApi.active().then(async ({ data }) => {
      if (data[0]) {
        setSprint(data[0]);
        const t = await tasksApi.list({ sprint_id: data[0].id });
        setTasks(t.data);
      }
    }).finally(() => setLoading(false));
  }, []);

  const grouped = COLUMNS.reduce((acc, col) => {
    acc[col] = tasks.filter((t) => t.status === col);
    return acc;
  }, {});

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar title="Sprint Board" />
        <main className="flex-1 overflow-hidden flex flex-col px-8 py-6 gap-5">
          {sprint && (
            <div className="bg-surface-container ghost-border rounded-2xl p-5 shrink-0">
              <div className="flex items-center justify-between mb-3">
                <h2 className="font-headline font-bold text-lg">{sprint.name}</h2>
                <span className="text-xs font-mono text-primary">{sprint.health_score}/100</span>
              </div>
              <SprintProgressBar completed={sprint.points_completed} planned={sprint.points_planned} />
            </div>
          )}
          {/* Kanban */}
          <div className="flex-1 overflow-x-auto">
            <div className="flex gap-3 h-full min-w-max">
              {COLUMNS.map((col) => (
                <div key={col} className="w-64 flex flex-col bg-surface-container ghost-border rounded-2xl overflow-hidden">
                  <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-500">{COL_LABELS[col]}</span>
                    <span className="text-xs font-mono text-slate-500">{grouped[col]?.length}</span>
                  </div>
                  <div className="flex-1 overflow-y-auto p-3 space-y-2">
                    {grouped[col]?.map((t) => (
                      <div key={t.id} className="bg-surface-container-high rounded-xl p-3 ghost-border hover:bg-surface-container-highest transition-colors cursor-pointer">
                        <p className="text-xs font-medium leading-snug">{t.title}</p>
                        <div className="flex items-center justify-between mt-2">
                          <span className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded ${
                            t.priority === "high" ? "text-red-400 bg-red-400/10" : t.priority === "medium" ? "text-yellow-400 bg-yellow-400/10" : "text-green-400 bg-green-400/10"
                          }`}>{t.priority}</span>
                          {t.story_points && <span className="text-[9px] font-mono text-slate-500">{t.story_points}pt</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
