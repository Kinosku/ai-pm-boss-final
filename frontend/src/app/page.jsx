"use client";
import { useState } from "react";
import { useAuth } from "@/context/AuthContext";

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [error, setError]       = useState("");
  const [loading, setLoading]   = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError(""); setLoading(true);
    try { await login(email, password); }
    catch { setError("Invalid credentials. Please try again."); }
    finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl velocity-gradient-bg mb-4">
            <span className="material-symbols-outlined text-background text-2xl" style={{ fontVariationSettings: "'FILL' 1" }}>smart_toy</span>
          </div>
          <h1 className="text-2xl font-bold font-headline">
            AI PM <span className="velocity-gradient">BOSS</span>
          </h1>
          <p className="text-on-surface-variant text-sm mt-1">Autonomous Project Intelligence</p>
        </div>

        {/* Card */}
        <div className="glass-panel ghost-border rounded-2xl p-8 ambient-glow">
          <h2 className="text-lg font-semibold mb-6">Sign in to continue</h2>
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-on-surface-variant mb-1.5">Email</label>
              <input
                type="email" required value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                className="w-full bg-surface-container-lowest ghost-border rounded-xl px-4 py-2.5 text-sm text-on-surface placeholder:text-slate-600 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/30 transition-all"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-on-surface-variant mb-1.5">Password</label>
              <input
                type="password" required value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-surface-container-lowest ghost-border rounded-xl px-4 py-2.5 text-sm text-on-surface placeholder:text-slate-600 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/30 transition-all"
              />
            </div>
            {error && <p className="text-red-400 text-xs">{error}</p>}
            <button
              type="submit" disabled={loading}
              className="w-full velocity-gradient-bg text-background font-bold py-2.5 rounded-xl text-sm hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              {loading ? "Signing in…" : "Sign In"}
            </button>
          </form>

          {/* Role info */}
          <div className="mt-6 pt-6 border-t border-white/5 grid grid-cols-2 gap-3">
            {[
              { role: "Boss", icon: "manage_accounts", desc: "Full project control" },
              { role: "Employee", icon: "code", desc: "My tasks & PRs" },
            ].map(({ role, icon, desc }) => (
              <div key={role} className="bg-surface-container rounded-xl p-3 text-center">
                <span className="material-symbols-outlined text-primary text-xl block mb-1">{icon}</span>
                <p className="text-xs font-semibold">{role}</p>
                <p className="text-[10px] text-on-surface-variant">{desc}</p>
              </div>
            ))}
          </div>
        </div>
        <p className="text-center text-[10px] text-slate-600 mt-6">© 2024 AI PM BOSS GLOBAL</p>
      </div>
    </div>
  );
}
