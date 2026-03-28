"use client";

import { useEffect, useState } from "react";
import Sidebar from "../../components/Sidebar";
import Navbar from "../../components/Navbar";
import { settingsApi } from "../../services/api";

export default function SettingsPage() {
  const [profile, setProfile] = useState({
    full_name: "",
    email: "",
    role: "",
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  // 🔥 FETCH PROFILE
  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const res = await settingsApi.getProfile();
        setProfile(res.data || {});
      } catch (err) {
        console.error("Error fetching profile:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, []);

  // 🔥 HANDLE CHANGE
  const handleChange = (e) => {
    setProfile({ ...profile, [e.target.name]: e.target.value });
  };

  // 🔥 SAVE PROFILE
  const handleSave = async () => {
    setSaving(true);
    setMessage("");

    try {
      await settingsApi.updateProfile(profile);
      setMessage("Profile updated successfully ✅");
    } catch (err) {
      console.error(err);
      setMessage("Failed to update profile ❌");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />

      <div className="flex-1">
        <Navbar title="Settings" />

        <div className="p-6 max-w-xl">
          <h1 className="text-2xl font-bold mb-6">Profile Settings</h1>

          {loading ? (
            <p className="text-gray-400">Loading profile...</p>
          ) : (
            <div className="space-y-4">

              {/* Name */}
              <div>
                <label className="block text-sm mb-1">Full Name</label>
                <input
                  type="text"
                  name="full_name"
                  value={profile.full_name || ""}
                  onChange={handleChange}
                  className="w-full p-2 rounded bg-white/5 border border-white/10"
                />
              </div>

              {/* Email */}
              <div>
                <label className="block text-sm mb-1">Email</label>
                <input
                  type="email"
                  name="email"
                  value={profile.email || ""}
                  onChange={handleChange}
                  className="w-full p-2 rounded bg-white/5 border border-white/10"
                />
              </div>

              {/* Role (Read Only) */}
              <div>
                <label className="block text-sm mb-1">Role</label>
                <input
                  type="text"
                  value={profile.role || ""}
                  disabled
                  className="w-full p-2 rounded bg-gray-800 border border-white/10 text-gray-400"
                />
              </div>

              {/* Save Button */}
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-4 py-2 rounded bg-primary text-black font-semibold hover:opacity-90"
              >
                {saving ? "Saving..." : "Save Changes"}
              </button>

              {/* Message */}
              {message && (
                <p className="text-sm text-gray-400">{message}</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}