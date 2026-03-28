"use client";
import { useAuth } from "../context/AuthContext";
import { usePathname } from "next/navigation";
import Link from "next/link";

const bossLinks = [
  { href: "/dashboard/boss", icon: "🏠", label: "Dashboard" },
  { href: "/projects", icon: "📁", label: "Projects" },
  { href: "/tasks", icon: "✅", label: "Tasks" },
  { href: "/sprint", icon: "🏃", label: "Sprints" },
  { href: "/risks", icon: "⚠️", label: "Risk Alerts" },
  { href: "/reports", icon: "📊", label: "Reports" },
  { href: "/standups", icon: "🎙️", label: "Standups" },
  { href: "/team", icon: "👥", label: "Team" },
  { href: "/prs", icon: "🔀", label: "Pull Requests" },
  { href: "/notifications", icon: "🔔", label: "Notifications" },
  { href: "/integrations", icon: "🔌", label: "Integrations" },
  { href: "/settings", icon: "⚙️", label: "Settings" },
];

const employeeLinks = [
  { href: "/dashboard/employee", icon: "🏠", label: "My Dashboard" },
  { href: "/tasks", icon: "✅", label: "My Tasks" },
  { href: "/prs", icon: "🔀", label: "My PRs" },
  { href: "/standups", icon: "🎙️", label: "Standups" },
  { href: "/sprint", icon: "🏃", label: "Sprint" },
  { href: "/notifications", icon: "🔔", label: "Notifications" },
  { href: "/integrations", icon: "🔌", label: "Integrations" },
  { href: "/settings", icon: "⚙️", label: "Settings" },
];

export default function Sidebar() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const links = user?.role === "boss" ? bossLinks : employeeLinks;

  return (
    <aside className="w-56 h-screen flex flex-col bg-surface-container ghost-border border-r border-white/5 shrink-0">
      <div className="px-5 py-5 border-b border-white/5">
        <h1 className="text-lg font-bold font-headline">
          AI PM <span className="velocity-gradient">BOSS</span>
        </h1>
        <p className="text-[10px] text-on-surface-variant mt-0.5 capitalize">
          {user?.role || "user"} · {user?.name || ""}
        </p>
      </div>

      <nav className="flex-1 overflow-y-auto py-3 scrollbar-hide">
        {links.map(({ href, icon, label }) => {
          const active = pathname === href;
          return (
            <Link key={href} href={href}
              className={`flex items-center gap-3 px-4 py-2.5 mx-2 rounded-xl text-sm transition-all ${
                active
                  ? "bg-primary/10 text-primary font-semibold"
                  : "text-on-surface-variant hover:bg-white/5 hover:text-on-surface"
              }`}
            >
              <span className="text-base">{icon}</span>
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="px-4 py-4 border-t border-white/5">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 rounded-full velocity-gradient-bg flex items-center justify-center text-background font-bold text-sm">
            {user?.name?.[0]?.toUpperCase() || "U"}
          </div>
          <div className="min-w-0">
            <p className="text-xs font-semibold truncate">{user?.name || "User"}</p>
            <p className="text-[10px] text-on-surface-variant truncate">{user?.email || ""}</p>
          </div>
        </div>
        <button onClick={logout}
          className="w-full text-xs text-red-400 hover:text-red-300 hover:bg-red-400/10 py-2 rounded-xl transition-all">
          Sign Out
        </button>
      </div>
    </aside>
  );
}
