"use client";
import { useEffect, useState } from "react";
import Sidebar from "../../components/Sidebar";
import Navbar  from "../../components/Navbar";
import { teamApi } from "../../services/api";

export default function TeamPage() {
  const [data, setData] = useState(null);

  useEffect(() => {
    teamApi.list().then(({ data }) => setData(data)).catch(console.error);
  }, []);

  const team     = data?.team     || [];
  const workload = data?.workload || [];

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar title="Team" />
        <main className="flex-1 overflow-y-auto px-8 py-6 space-y-6">
          <div>
            <h1 className="text-3xl font-bold font-headline">Team Overview</h1>
            <p className="text-on-surface-variant text-sm mt-1">Real-time performance and task distribution</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {workload.map((dev) => (
              <div key={dev.id} className="bg-surface-container ghost-border rounded-2xl p-5 space-y-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full velocity-gradient-bg flex items-center justify-center text-background font-bold text-sm shrink-0">
                    {dev.name?.[0] || "D"}
                  </div>
                  <div>
                    <p className="font-semibold text-sm">{dev.name}</p>
                    <p className="text-xs text-slate-500 capitalize">{dev.role}</p>
                  </div>
                  <span className={`ml-auto text-[9px] font-bold uppercase px-2 py-0.5 rounded-full ${
                    dev.status === "overloaded" ? "bg-red-500/10 text-red-400" :
                    dev.status === "busy"       ? "bg-yellow-500/10 text-yellow-400" :
                    "bg-green-500/10 text-green-400"
                  }`}>{dev.status}</span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-center">
                  <div className="bg-surface-container-high rounded-xl py-2">
                    <p className="text-lg font-bold font-headline text-primary">{dev.open_tasks}</p>
                    <p className="text-[10px] text-slate-500">Open Tasks</p>
                  </div>
                  <div className="bg-surface-container-high rounded-xl py-2">
                    <p className="text-lg font-bold font-headline text-blue-400">{dev.velocity || 0}</p>
                    <p className="text-[10px] text-slate-500">Velocity</p>
                  </div>
                </div>
              </div>
            ))}
            {team.length === 0 && <p className="col-span-3 text-sm text-slate-500 text-center py-12">No team members found</p>}
          </div>
        </main>
      </div>
    </div>
  );
}
