"use client";
import { useEffect, useState } from "react";
import Sidebar   from "@/components/Sidebar";
import Navbar    from "@/components/Navbar";
import TaskCard  from "@/components/TaskCard";
import Modal     from "@/components/ui/Modal";
import Button    from "@/components/ui/Button";
import { tasksApi } from "@/services/api";
import { useAuth } from "@/context/AuthContext";

const STATUSES   = ["all","todo","in_progress","in_review","blocked","done"];
const PRIORITIES = ["all","high","medium","low"];

export default function TasksPage() {
  const { isBoss }            = useAuth();
  const [tasks, setTasks]     = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter]   = useState("all");
  const [priorityFilter, setPriorityFilter] = useState("all");
  const [prdModal, setPrdModal] = useState(false);
  const [prdText, setPrdText]   = useState("");
  const [parsing, setParsing]   = useState(false);

  const load = async () => {
    setLoading(true);
    const params = {};
    if (statusFilter   !== "all") params.status   = statusFilter;
    if (priorityFilter !== "all") params.priority = priorityFilter;
    const { data } = await tasksApi.list(params);
    setTasks(data);
    setLoading(false);
  };

  useEffect(() => { load(); }, [statusFilter, priorityFilter]);

  const handleStatusChange = async (id, status) => {
    await tasksApi.update(id, { status });
    setTasks((prev) => prev.map((t) => (t.id === id ? { ...t, status } : t)));
  };

  const parsePrd = async () => {
    if (!prdText.trim()) return;
    setParsing(true);
    try {
      const { data } = await tasksApi.parsePrd({ project_id: 1, prd_text: prdText, auto_assign: true });
      setTasks((prev) => [...data, ...prev]);
      setPrdModal(false); setPrdText("");
    } catch (e) { console.error(e); }
    finally { setParsing(false); }
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar title="Tasks" />
        <main className="flex-1 overflow-y-auto px-8 py-6">

          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold font-headline">Tasks</h1>
              <p className="text-on-surface-variant text-sm mt-1">
                {isBoss ? "All project tasks" : "Your assigned tasks"} · {tasks.length} total
              </p>
            </div>
            {isBoss && (
              <Button onClick={() => setPrdModal(true)}>
                <span className="material-symbols-outlined text-[18px]">auto_awesome</span>
                Create tasks from PRD
              </Button>
            )}
          </div>

          {/* Filters */}
          <div className="flex gap-3 mb-5 flex-wrap">
            <div className="flex gap-1 bg-surface-container ghost-border rounded-xl p-1">
              {STATUSES.map((s) => (
                <button key={s} onClick={() => setStatusFilter(s)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-colors ${
                    statusFilter === s ? "bg-surface-container-high text-on-surface" : "text-slate-500 hover:text-on-surface"
                  }`}>{s.replace("_"," ")}</button>
              ))}
            </div>
            <div className="flex gap-1 bg-surface-container ghost-border rounded-xl p-1">
              {PRIORITIES.map((p) => (
                <button key={p} onClick={() => setPriorityFilter(p)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-colors ${
                    priorityFilter === p ? "bg-surface-container-high text-on-surface" : "text-slate-500 hover:text-on-surface"
                  }`}>{p}</button>
              ))}
            </div>
          </div>

          {/* Table */}
          <div className="bg-surface-container ghost-border rounded-2xl overflow-hidden">
            <div className="grid grid-cols-[auto_1fr_auto_auto_auto_auto] gap-0 px-6 py-3 border-b border-white/5">
              {["","Task","Points","Priority","Status","Due"].map((h, i) => (
                <span key={i} className="text-xs font-bold uppercase tracking-wider text-slate-500">{h}</span>
              ))}
            </div>
            {loading && <p className="text-xs text-slate-500 px-6 py-8 text-center">Loading…</p>}
            {!loading && tasks.length === 0 && (
              <p className="text-xs text-slate-500 px-6 py-8 text-center">No tasks found</p>
            )}
            {tasks.map((t) => (
              <TaskCard key={t.id} task={t} onStatusChange={handleStatusChange} />
            ))}
          </div>
        </main>
      </div>

      {/* PRD Modal */}
      <Modal open={prdModal} onClose={() => setPrdModal(false)} title="Create Tasks from PRD" width="max-w-2xl">
        <p className="text-sm text-on-surface-variant mb-4">Paste your PRD or feature description. AI will extract developer-ready tasks automatically.</p>
        <textarea value={prdText} onChange={(e) => setPrdText(e.target.value)} rows={10}
          placeholder="Paste your PRD text here…"
          className="w-full bg-surface-container-lowest ghost-border rounded-xl p-4 text-sm text-on-surface placeholder:text-slate-600 focus:outline-none focus:border-primary/40 resize-none" />
        <div className="flex justify-end gap-3 mt-4">
          <Button variant="secondary" onClick={() => setPrdModal(false)}>Cancel</Button>
          <Button onClick={parsePrd} disabled={parsing}>
            <span className="material-symbols-outlined text-[18px]">auto_awesome</span>
            {parsing ? "Extracting…" : "Extract Tasks"}
          </Button>
        </div>
      </Modal>
    </div>
  );
}
