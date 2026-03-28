"use client";
import { useState } from "react";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const { login, signup } = useAuth();
  const [isSignup, setIsSignup] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("employee");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (isSignup) {
        await signup(name, email, password, role);
      } else {
        await login(email, password);
      }
    } catch (err) {
const detail = err?.response?.data?.detail;
if (Array.isArray(detail)) {
  setError(detail.map(d => d.msg).join(", "));
} else {
  setError(detail || "Something went wrong. Please try again.");
}    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm">

        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl velocity-gradient-bg mb-4">
            <span style={{ fontSize: 28, color: "#06090f" }}>🤖</span>
          </div>
          <h1 className="text-3xl font-bold font-headline">
            AI PM <span className="velocity-gradient">BOSS</span>
          </h1>
          <p className="text-on-surface-variant text-sm mt-1">Autonomous Project Intelligence</p>
        </div>

        {/* Card */}
        <div className="glass-panel ghost-border rounded-2xl p-8 ambient-glow">
          <h2 className="text-lg font-semibold mb-6">
            {isSignup ? "Create your account" : "Sign in to continue"}
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            {isSignup && (
              <div>
                <label className="block text-xs font-medium text-on-surface-variant mb-1.5">Full Name</label>
                <input
                  type="text" required value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="John Doe"
                  className="w-full bg-surface-container-lowest ghost-border rounded-xl px-4 py-2.5 text-sm text-on-surface placeholder:text-slate-600 focus:outline-none focus:border-primary/50 transition-all"
                />
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-on-surface-variant mb-1.5">Email</label>
              <input
                type="email" required value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                className="w-full bg-surface-container-lowest ghost-border rounded-xl px-4 py-2.5 text-sm text-on-surface placeholder:text-slate-600 focus:outline-none focus:border-primary/50 transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-on-surface-variant mb-1.5">Password</label>
              <input
                type="password" required value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-surface-container-lowest ghost-border rounded-xl px-4 py-2.5 text-sm text-on-surface placeholder:text-slate-600 focus:outline-none focus:border-primary/50 transition-all"
              />
            </div>

            {isSignup && (
              <div>
                <label className="block text-xs font-medium text-on-surface-variant mb-2">I am a...</label>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { value: "boss", label: "Boss / PM", icon: "👔", desc: "Full project control" },
                    { value: "employee", label: "Developer", icon: "💻", desc: "My tasks & PRs" },
                  ].map(({ value, label, icon, desc }) => (
                    <button
                      key={value} type="button"
                      onClick={() => setRole(value)}
                      className={`p-3 rounded-xl border text-left transition-all ${
                        role === value
                          ? "border-primary/60 bg-primary/10"
                          : "ghost-border bg-surface-container-lowest hover:bg-surface-container"
                      }`}
                    >
                      <span className="text-xl block mb-1">{icon}</span>
                      <p className="text-xs font-bold">{label}</p>
                      <p className="text-[10px] text-on-surface-variant">{desc}</p>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {error && (
              <p className="text-red-400 text-xs bg-red-400/10 border border-red-400/20 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <button
              type="submit" disabled={loading}
              className="w-full velocity-gradient-bg text-background font-bold py-2.5 rounded-xl text-sm hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              {loading ? "Please wait…" : isSignup ? "Create Account" : "Sign In"}
            </button>
          </form>

          <p className="text-center text-xs text-on-surface-variant mt-5">
            {isSignup ? "Already have an account?" : "Don't have an account?"}{" "}
            <button
              onClick={() => { setIsSignup(!isSignup); setError(""); }}
              className="text-primary hover:underline font-semibold"
            >
              {isSignup ? "Sign In" : "Sign Up"}
            </button>
          </p>
        </div>

        <p className="text-center text-[10px] text-slate-600 mt-6">© 2025 AI PM BOSS · Quadra Elites</p>
      </div>
    </div>
  );
}
