"use client";
import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import Navbar  from "@/components/Navbar";
import Button  from "@/components/ui/Button";
import { standupsApi } from "@/services/api";
import { timeAgo } from "@/utils/helpers";

export default function StandupsPage() {
  const [standups, setStandups]   = useState([]);
  const [form, setForm]           = useState({ done: "", doing: "", blocked: "" });
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    standupsApi.list({ is_summary: true }).then(({ data }) => setStandups(data)).catch(console.error);
  }, []);

  const submit = async () => {
    setSubmitting(true);
    try {
      await standupsApi.submit({
        project_id:   1,
        standup_date: new Date().toISOString(),
        done:    form.done.split("\n").filter(Boolean),
        doing:   form.doing.split("\n").filter(Boolean),
        blocked: form.blocked.split("\n").filter(Boolean),
      });
      setSubmitted(true); setForm({ done: "", doing: "", blocked: "" });
    } catch (e) { console.error(e); }
    finally { setSubmitting(false); }
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar title="Standups" />
        <main className="flex-1 overflow-y-auto px-8 py-6 space-y-6">
          <h1 className="text-3xl font-bold font-headline">Standup Summary</h1>

          {/* Submit form */}
          {!submitted ? (
            <div className="bg-surface-container ghost-border rounded-2xl p-6 space-y-4 max-w-xl">
              <h2 className="font-bold">Today's Update</h2>
              {[
                { label: "✅ Done (yesterday)", key: "done",    placeholder: "What did you complete?" },
                { label: "🚀 Doing (today)",    key: "doing",   placeholder: "What are you working on?" },
                { label: "🚨 Blocked",          key: "blocked", placeholder: "Any blockers? (leave empty if none)" },
              ].map(({ label, key, placeholder }) => (
                <div key={key}>
                  <label className="block text-xs font-medium text-on-surface-variant mb-1">{label}</label>
                  <textarea rows={2} value={form[key]} onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                    placeholder={placeholder}
                    className="w-full bg-surface-container-lowest ghost-border rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-primary/40 resize-none" />
                </div>
              ))}
              <Button onClick={submit} disabled={submitting}>{submitting ? "Submitting…" : "Submit Standup"}</Button>
            </div>
          ) : (
            <div className="bg-primary/5 border border-primary/20 rounded-2xl p-5 max-w-xl flex items-center gap-3">
              <span className="material-symbols-outlined text-primary text-2xl" style={{ fontVariationSettings: "'FILL' 1" }}>check_circle</span>
              <p className="text-sm font-semibold">Standup submitted! Thanks 🎉</p>
            </div>
          )}

          {/* Summaries */}
          <div className="space-y-4">
            <h2 className="font-bold text-base">Recent Summaries</h2>
            {standups.map((s) => (
              <div key={s.id} className="bg-surface-container ghost-border rounded-2xl p-5">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs text-slate-500">{timeAgo(s.standup_date)}</span>
                  {s.slack_channel && <span className="font-mono text-[10px] bg-surface-container-high text-secondary px-2 py-0.5 rounded">{s.slack_channel}</span>}
                </div>
                <p className="text-sm whitespace-pre-line text-on-surface">{s.summary_text}</p>
                {s.blockers_json?.length > 0 && (
                  <div className="mt-3 space-y-1">
                    {s.blockers_json.map((b, i) => (
                      <div key={i} className="bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2 text-xs text-red-400">
                        🚨 {b.developer}: {b.blocker}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </main>
      </div>
    </div>
  );
}
