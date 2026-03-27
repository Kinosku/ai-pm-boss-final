"use client";
import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";
import Navbar  from "../components/Navbar";
import Modal   from "../components/ui/Modal";
import Button  from "../components/ui/Button";
import { integrationsApi } from "../services/api";

const PROVIDERS = [
  { id: "github", name: "GitHub",  icon: "code",      desc: "Sync PRs, commits, and branches in real-time" },
  { id: "jira",   name: "Jira",    icon: "assignment", desc: "Sync tickets, sprints, and velocity data" },
  { id: "slack",  name: "Slack",   icon: "forum",      desc: "Receive standup alerts and report summaries" },
];

export default function IntegrationsPage() {
  const [integrations, setIntegrations] = useState([]);
  const [modal, setModal] = useState(null);  // provider id
  const [form, setForm]   = useState({});
  const [saving, setSaving] = useState(false);
  const PROJECT_ID = 1;

  useEffect(() => {
    integrationsApi.list({ project_id: PROJECT_ID })
      .then(({ data }) => setIntegrations(data))
      .catch(console.error);
  }, []);

  const statusOf = (id) => integrations.find((i) => i.provider === id)?.status;
  const isConnected = (id) => statusOf(id) === "connected";

  const connect = async () => {
    setSaving(true);
    try {
      await integrationsApi.connect({ project_id: PROJECT_ID, provider: modal, ...form });
      const { data } = await integrationsApi.list({ project_id: PROJECT_ID });
      setIntegrations(data);
      setModal(null); setForm({});
    } catch (e) { console.error(e); }
    finally { setSaving(false); }
  };

  const disconnect = async (id) => {
    const intg = integrations.find((i) => i.provider === id);
    if (!intg) return;
    await integrationsApi.disconnect(intg.id);
    const { data } = await integrationsApi.list({ project_id: PROJECT_ID });
    setIntegrations(data);
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar title="Integrations" />
        <main className="flex-1 overflow-y-auto px-8 py-6">
          <div className="mb-8">
            <h1 className="text-3xl font-bold font-headline">System <span className="velocity-gradient">Integrations</span></h1>
            <p className="text-on-surface-variant mt-1">Connect your tools to power real-time AI decisions</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {PROVIDERS.map(({ id, name, icon, desc }) => {
              const connected = isConnected(id);
              return (
                <div key={id} className="bg-surface-container ghost-border rounded-2xl p-6 flex flex-col gap-4">
                  <div className="flex items-center justify-between">
                    <div className="w-10 h-10 bg-surface-container-high rounded-xl flex items-center justify-center">
                      <span className="material-symbols-outlined text-primary text-[22px]">{icon}</span>
                    </div>
                    <span className={`text-[10px] font-mono font-bold uppercase px-2 py-1 rounded-full ${
                      connected ? "bg-primary/10 text-primary" : "bg-surface-container-high text-slate-500"
                    }`}>{connected ? "CONNECTED" : "NOT CONNECTED"}</span>
                  </div>
                  <div>
                    <h3 className="font-bold text-lg">{name}</h3>
                    <p className="text-sm text-on-surface-variant mt-0.5">{desc}</p>
                  </div>
                  <div className="flex gap-2 mt-auto">
                    {connected ? (
                      <>
                        <Button variant="secondary" size="sm" className="flex-1"
                          onClick={() => { const intg = integrations.find((i)=>i.provider===id); if(intg) integrationsApi.sync(intg.id); }}>
                          Sync Now
                        </Button>
                        <Button variant="danger" size="sm" onClick={() => disconnect(id)}>Disconnect</Button>
                      </>
                    ) : (
                      <Button size="sm" className="flex-1" onClick={() => { setModal(id); setForm({}); }}>
                        Connect {name}
                      </Button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </main>
      </div>

      {/* Connect Modal */}
      <Modal open={!!modal} onClose={() => setModal(null)} title={`Connect ${modal ? PROVIDERS.find(p=>p.id===modal)?.name : ""}`}>
        <div className="space-y-3">
          {modal === "github" && <>
            <input placeholder="Repository (e.g. org/repo)" value={form.github_repo || ""} onChange={(e)=>setForm({...form,github_repo:e.target.value})}
              className="w-full bg-surface-container-lowest ghost-border rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-primary/40" />
            <input placeholder="GitHub Token" type="password" value={form.github_token || ""} onChange={(e)=>setForm({...form,github_token:e.target.value})}
              className="w-full bg-surface-container-lowest ghost-border rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-primary/40" />
          </>}
          {modal === "slack" && <>
            <input placeholder="Slack Channel ID (e.g. C01234567)" value={form.slack_channel_id || ""} onChange={(e)=>setForm({...form,slack_channel_id:e.target.value})}
              className="w-full bg-surface-container-lowest ghost-border rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-primary/40" />
            <input placeholder="Bot Token (xoxb-...)" type="password" value={form.slack_bot_token || ""} onChange={(e)=>setForm({...form,slack_bot_token:e.target.value})}
              className="w-full bg-surface-container-lowest ghost-border rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-primary/40" />
          </>}
          {modal === "jira" && <>
            <input placeholder="Jira Base URL" value={form.jira_base_url || ""} onChange={(e)=>setForm({...form,jira_base_url:e.target.value})}
              className="w-full bg-surface-container-lowest ghost-border rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-primary/40" />
            <input placeholder="Project Key (e.g. PROJ)" value={form.jira_project_key || ""} onChange={(e)=>setForm({...form,jira_project_key:e.target.value})}
              className="w-full bg-surface-container-lowest ghost-border rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-primary/40" />
            <input placeholder="API Token" type="password" value={form.jira_api_token || ""} onChange={(e)=>setForm({...form,jira_api_token:e.target.value})}
              className="w-full bg-surface-container-lowest ghost-border rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-primary/40" />
          </>}
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" onClick={()=>setModal(null)}>Cancel</Button>
            <Button onClick={connect} disabled={saving}>{saving ? "Connecting…" : "Connect"}</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
