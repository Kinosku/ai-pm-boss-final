"use client";
import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import Navbar  from "@/components/Navbar";
import Button  from "@/components/ui/Button";
import { settingsApi } from "@/services/api";

export default function SettingsPage() {
  const [profile, setProfile] = useState({ full_name: "", email: "", avatar_url: "" });
  const [devProfile, setDevProfile] = useState({ skills: [], github_username: "", slack_user_id: "" });
  const [saving, setSaving] = useState(false);
  const [msg, setMsg]       = useState("");

  useEffect(() => {
    settingsApi.getProfile().then(({ data }) => setProfile(data)).catch(console.error);
    settingsApi.getDeveloperProfile().then(({ data }) => {
      if (data.developer) setDevProfile(data.developer);
    }).catch(console.error);
  }, []);

  const saveProfile = async () => {
    setSaving(true);
    try {
      await settingsApi.updateProfile({ full_name: profile.full_name, avatar_url: profile.avatar_url });
      setMsg("Profile saved!");
    } catch {}
    finally { setSaving(false); setTimeout(() => setMsg(""), 3000); }
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar title="Settings" />
        <main className="flex-1 overflow-y-auto px-8 py-6">
          <div className="max-w-2xl space-y-6">
            <h1 className="text-3xl font-bold font-headline">Settings</h1>

            {/* Profile */}
            <div className="bg-surface-container ghost-border rounded-2xl p-6 space-y-4">
              <h2 className="font-bold text-base">Profile</h2>
              <div className="grid grid-cols-1 gap-3">
                {[
                  { label: "Full Name", key: "full_name", type: "text" },
                  { label: "Email",     key: "email",     type: "email", disabled: true },
                  { label: "Avatar URL",key: "avatar_url",type: "text" },
                ].map(({ label, key, type, disabled }) => (
                  <div key={key}>
                    <label className="block text-xs text-on-surface-variant mb-1">{label}</label>
                    <input type={type} disabled={disabled} value={profile[key] || ""}
                      onChange={(e) => setProfile({ ...profile, [key]: e.target.value })}
                      className="w-full bg-surface-container-lowest ghost-border rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-primary/40 disabled:opacity-40" />
                  </div>
                ))}
              </div>
              <div className="flex items-center gap-3 pt-1">
                <Button onClick={saveProfile} disabled={saving}>{saving ? "Saving…" : "Save Profile"}</Button>
                {msg && <span className="text-xs text-primary">{msg}</span>}
              </div>
            </div>

            {/* Developer profile */}
            {devProfile && (
              <div className="bg-surface-container ghost-border rounded-2xl p-6 space-y-4">
                <h2 className="font-bold text-base">Developer Profile</h2>
                <div className="grid grid-cols-1 gap-3">
                  <div>
                    <label className="block text-xs text-on-surface-variant mb-1">GitHub Username</label>
                    <input value={devProfile.github_username || ""}
                      onChange={(e) => setDevProfile({ ...devProfile, github_username: e.target.value })}
                      className="w-full bg-surface-container-lowest ghost-border rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-primary/40" />
                  </div>
                  <div>
                    <label className="block text-xs text-on-surface-variant mb-1">Slack User ID</label>
                    <input value={devProfile.slack_user_id || ""}
                      onChange={(e) => setDevProfile({ ...devProfile, slack_user_id: e.target.value })}
                      className="w-full bg-surface-container-lowest ghost-border rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-primary/40" />
                  </div>
                  <div>
                    <label className="block text-xs text-on-surface-variant mb-1">Skills (comma-separated)</label>
                    <input value={(devProfile.skills || []).join(", ")}
                      onChange={(e) => setDevProfile({ ...devProfile, skills: e.target.value.split(",").map(s=>s.trim()).filter(Boolean) })}
                      placeholder="python, fastapi, react, postgresql…"
                      className="w-full bg-surface-container-lowest ghost-border rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-primary/40" />
                  </div>
                </div>
                <Button onClick={() => settingsApi.updateDeveloperProfile(devProfile)}>Save Developer Profile</Button>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
