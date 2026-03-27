"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "../context/AuthContext";
const BOSS_NAV = [
  { label: "Dashboard",    href: "/dashboard/boss",  icon: "dashboard" },
  { label: "Risk Alerts",  href: "/risks",            icon: "warning" },
  { label: "AI Agents",    href: "/agents",           icon: "smart_toy" },
  { label: "Reports",      href: "/reports",          icon: "assessment" },
  { label: "Team",         href: "/team",             icon: "group" },
  { label: "Sprint Board", href: "/sprint",           icon: "view_kanban" },
  { label: "Integrations", href: "/integrations",     icon: "extension" },
  { label: "Settings",     href: "/settings",         icon: "settings" },
];

const EMPLOYEE_NAV = [
  { label: "My Work",   href: "/dashboard/employee", icon: "dashboard" },
  { label: "My Tasks",  href: "/tasks",              icon: "assignment" },
  { label: "My PRs",    href: "/prs",                icon: "merge_type" },
  { label: "Team",      href: "/team",               icon: "groups" },
  { label: "Standups",  href: "/standups",           icon: "bolt" },
  { label: "Sprint",    href: "/sprint",             icon: "view_kanban" },
  { label: "Notifications", href: "/notifications",  icon: "notifications" },
  { label: "Settings",  href: "/settings",           icon: "settings" },
];

export default function Sidebar() {
  const { user, logout, isBoss } = useAuth();
  const pathname = usePathname();
  const nav = isBoss ? BOSS_NAV : EMPLOYEE_NAV;
  const accentColor = isBoss ? "#00ffb4" : "#00c8ff";

  return (
    <aside className="flex flex-col h-screen sticky top-0 left-0 border-r border-white/5 w-[220px] bg-background z-50 shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 h-16 border-b border-white/5">
        <div className="w-7 h-7 rounded-lg velocity-gradient-bg flex items-center justify-center">
          <span className="material-symbols-outlined text-background text-base" style={{ fontVariationSettings: "'FILL' 1" }}>smart_toy</span>
        </div>
        <span className="text-base font-bold font-headline velocity-gradient">AI Boss</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-0.5">
        {nav.map(({ label, href, icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link key={href} href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                active
                  ? `bg-white/5 border-r-2 font-semibold`
                  : "text-slate-400 hover:text-white hover:bg-white/[0.04]"
              }`}
              style={active ? { color: accentColor, borderColor: accentColor } : {}}
            >
              <span className="material-symbols-outlined text-[20px]">{icon}</span>
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>

      {/* User + Logout */}
      <div className="px-3 pb-4 border-t border-white/5 pt-3 space-y-1">
        <div className="flex items-center gap-2.5 px-3 py-2">
          <div className="w-7 h-7 rounded-full velocity-gradient-bg flex items-center justify-center text-background text-xs font-bold shrink-0">
            {user?.full_name?.[0] || "U"}
          </div>
          <div className="min-w-0">
            <p className="text-xs font-semibold truncate">{user?.full_name || "User"}</p>
            <p className="text-[10px] text-slate-500 capitalize">{user?.role}</p>
          </div>
        </div>
        <button onClick={logout}
          className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium text-slate-400 hover:text-white hover:bg-white/[0.04] transition-all">
          <span className="material-symbols-outlined text-[20px]">logout</span>
          <span>Logout</span>
        </button>
      </div>
    </aside>
  );
}
