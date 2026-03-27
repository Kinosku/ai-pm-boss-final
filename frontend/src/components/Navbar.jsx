"use client";
import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { notificationsApi } from "../services/api";

export default function Navbar({ title }) {
  const { user } = useAuth();
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    notificationsApi.count()
      .then(({ data }) => setUnread(data.unread || 0))
      .catch(() => {});
  }, []);

  return (
    <header className="flex justify-between items-center px-8 w-full sticky top-0 z-40 bg-background/80 backdrop-blur-xl h-16 border-b border-white/5 shrink-0">
      {/* Title */}
      <h2 className="font-headline font-bold text-lg text-on-surface">{title}</h2>

      {/* Right actions */}
      <div className="flex items-center gap-3">
        {/* Search */}
        <div className="relative hidden md:block">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 text-[18px]">search</span>
          <input
            placeholder="Global search…"
            className="bg-surface-container-lowest ghost-border rounded-full pl-9 pr-4 py-1.5 text-xs w-56 focus:outline-none focus:border-primary/40 transition-colors"
          />
        </div>

        {/* Notifications bell */}
        <a href="/notifications" className="relative p-2 rounded-lg hover:bg-white/5 transition-colors">
          <span className="material-symbols-outlined text-[20px] text-slate-400">notifications</span>
          {unread > 0 && (
            <span className="absolute top-1.5 right-1.5 w-4 h-4 rounded-full bg-red-500 text-[9px] font-bold text-white flex items-center justify-center">
              {unread > 9 ? "9+" : unread}
            </span>
          )}
        </a>

        {/* Avatar */}
        <div className="w-8 h-8 rounded-full velocity-gradient-bg flex items-center justify-center text-background text-xs font-bold">
          {user?.full_name?.[0] || "U"}
        </div>
      </div>
    </header>
  );
}
