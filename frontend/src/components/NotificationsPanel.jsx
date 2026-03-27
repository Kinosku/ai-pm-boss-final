"use client";
import { useEffect, useState } from "react";
import { notificationsApi } from "../services/api";
import { timeAgo } from "../utils/helpers";

const typeIcon = {
  risk_alert:    { icon: "warning",        color: "text-red-400    bg-red-400/10" },
  agent_action:  { icon: "smart_toy",      color: "text-primary    bg-primary/10" },
  pr_update:     { icon: "merge_type",     color: "text-blue-400   bg-blue-400/10" },
  report_ready:  { icon: "assessment",     color: "text-purple-400 bg-purple-400/10" },
  task_assigned: { icon: "task_alt",       color: "text-green-400  bg-green-400/10" },
  blocker:       { icon: "block",          color: "text-red-400    bg-red-400/10" },
  system:        { icon: "info",           color: "text-slate-400  bg-slate-400/10" },
};

export default function NotificationsPanel({ limit = 5 }) {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const { data } = await notificationsApi.list({ limit });
      setNotifications(data);
    } catch {}
    finally { setLoading(false); }
  };

  const markRead = async (id) => {
    await notificationsApi.markRead(id);
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
    );
  };

  useEffect(() => { load(); }, []);

  if (loading) return <div className="text-xs text-slate-500 px-4 py-6 text-center">Loading…</div>;

  return (
    <div className="divide-y divide-white/5">
      {notifications.length === 0 && (
        <p className="text-xs text-slate-500 px-4 py-6 text-center">No notifications</p>
      )}
      {notifications.map((n) => {
        const { icon, color } = typeIcon[n.type] || typeIcon.system;
        return (
          <div key={n.id}
            className={`flex gap-3 px-4 py-4 transition-colors hover:bg-white/[0.02] ${!n.is_read ? "bg-white/[0.015]" : ""}`}>
            {/* Icon */}
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${color}`}>
              <span className="material-symbols-outlined text-[16px]" style={{ fontVariationSettings: "'FILL' 1" }}>{icon}</span>
            </div>
            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-2">
                <p className={`text-sm font-medium leading-snug ${n.is_read ? "text-on-surface-variant" : "text-on-surface"}`}>
                  {n.title}
                </p>
                {!n.is_read && (
                  <button onClick={() => markRead(n.id)}
                    className="shrink-0 w-1.5 h-1.5 rounded-full bg-primary mt-1.5" />
                )}
              </div>
              {n.message && <p className="text-xs text-slate-500 mt-0.5 truncate">{n.message}</p>}
              <div className="flex items-center gap-3 mt-1.5">
                <span className="text-[10px] text-slate-600">{timeAgo(n.created_at)}</span>
                {n.action_url && (
                  <a href={n.action_url}
                    className="text-[10px] font-bold text-primary hover:underline">{n.action_label || "View"}</a>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
