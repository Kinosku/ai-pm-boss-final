"use client";
import { useAuth } from "../context/AuthContext";
import Link from "next/link";

export default function Navbar({ title }) {
  const { user } = useAuth();

  return (
    <header className="h-14 flex items-center justify-between px-6 border-b border-white/5 bg-background/80 backdrop-blur shrink-0">
      <h2 className="font-headline font-bold text-base">{title}</h2>
      <div className="flex items-center gap-3">
        <Link href="/notifications" className="text-on-surface-variant hover:text-on-surface transition-colors text-lg">🔔</Link>
        <div className="w-7 h-7 rounded-full velocity-gradient-bg flex items-center justify-center text-background font-bold text-xs">
          {user?.name?.[0]?.toUpperCase() || "U"}
        </div>
      </div>
    </header>
  );
}
