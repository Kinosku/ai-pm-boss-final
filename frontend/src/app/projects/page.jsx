"use client";
import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import Navbar  from "@/components/Navbar";
import Modal   from "@/components/ui/Modal";
import Button  from "@/components/ui/Button";
import { projectsApi } from "@/services/api";

export default function ProjectsPage() {
  const [projects, setProjects] = useState([]);
  const [modal, setModal]       = useState(false);
  const [form, setForm]         = useState({ name: "", description: "", github_repo: "", slack_channel: "" });
  const [saving, setSaving]     = useState(false);

  const load = () => projectsApi.list().then(({ data }) => setProjects(data)).catch(console.error);
  useEffect(() => { load(); }, []);

  const create = async () => {
    setSaving(true);
    try { await projectsApi.create(form); setModal(false); setForm({ name:"", description:"", github_repo:"", slack_channel:"" }); load(); }
    catch (e) { console.error(e); }
    finally { setSaving(false); }
  };

  const STATUS_COLOR = { active: "text-primary bg-primary/10", on_hold: "text-yellow-400 bg-yellow-400/10", completed: "text-slate-400 bg-slate-400/10" };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar title="Projects" />
        <main className="flex-1 overflow-y-auto px-8 py-6 space-y-6">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold font-headline">Projects</h1>
            <Button onClick={() => setModal(true)}>
              <span className="material-symbols-outlined text-[18px]">add</span>New Project
            </Button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((p) => (
              <div key={p.id} className="bg-surface-container ghost-border rounded-2xl p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="font-bold">{p.name}</h3>
                  <span className={`text-[9px] font-bold uppercase px-2 py-0.5 rounded-full ${STATUS_COLOR[p.status] || "text-slate-400 bg-slate-400/10"}`}>{p.status}</span>
                </div>
                {p.description && <p className="text-xs text-on-surface-variant line-clamp-2">{p.description}</p>}
                <div className="flex gap-2 text-[10px] text-slate-500 flex-wrap">
                  {p.github_repo   && <span>🐙 {p.github_repo}</span>}
                  {p.slack_channel && <span>💬 {p.slack_channel}</span>}
                  {p.jira_project  && <span>📋 {p.jira_project}</span>}
                </div>
              </div>
            ))}
            {projects.length === 0 && <p className="col-span-3 text-sm text-slate-500 text-center py-12">No projects yet</p>}
          </div>
        </main>
      </div>
      <Modal open={modal} onClose={() => setModal(false)} title="New Project">
        <div className="space-y-3">
          {[
            { label: "Project Name *", key: "name",          placeholder: "My Awesome Project" },
            { label: "Description",    key: "description",   placeholder: "Brief description…" },
            { label: "GitHub Repo",    key: "github_repo",   placeholder: "org/repo-name" },
            { label: "Slack Channel",  key: "slack_channel", placeholder: "#dev-team" },
          ].map(({ label, key, placeholder }) => (
            <div key={key}>
              <label className="block text-xs text-on-surface-variant mb-1">{label}</label>
              <input value={form[key]} onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                placeholder={placeholder}
                className="w-full bg-surface-container-lowest ghost-border rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-primary/40" />
            </div>
          ))}
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" onClick={() => setModal(false)}>Cancel</Button>
            <Button onClick={create} disabled={saving || !form.name}>{saving ? "Creating…" : "Create Project"}</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
