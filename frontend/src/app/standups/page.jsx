"use client";

import { useEffect, useState } from "react";
import Sidebar from "../../components/Sidebar";
import Navbar from "../../components/Navbar";
import { standupsApi } from "../../services/api";

export default function StandupsPage() {
  const [text, setText] = useState("");
  const [standups, setStandups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  // 🔥 Fetch previous standups
  useEffect(() => {
    const fetchStandups = async () => {
      try {
        const res = await standupsApi.list();
        setStandups(res.data || []);
      } catch (err) {
        console.error("Error fetching standups:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchStandups();
  }, []);

  // 🔥 Submit standup
  const handleSubmit = async () => {
    if (!text.trim()) return;

    setSubmitting(true);

    try {
      const res = await standupsApi.submit({ text });

      const newEntry = res.data || {
        text,
        created_at: new Date().toISOString(),
      };

      setStandups([newEntry, ...standups]);
      setText("");
    } catch (err) {
      console.error("Error submitting standup:", err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />

      <div className="flex-1">
        <Navbar title="Standups" />

        <div className="p-6 max-w-3xl">
          <h1 className="text-2xl font-bold mb-6">Daily Standup</h1>

          {/* Input */}
          <div className="mb-6">
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="What did you do today? Any blockers?"
              className="w-full p-3 rounded-lg bg-white/5 border border-white/10"
              rows={4}
            />

            <button
              onClick={handleSubmit}
              disabled={submitting}
              className="mt-3 px-4 py-2 rounded bg-primary text-black font-semibold"
            >
              {submitting ? "Submitting..." : "Submit Standup"}
            </button>
          </div>

          {/* History */}
          <h2 className="text-lg font-semibold mb-3">Previous Updates</h2>

          {loading ? (
            <p className="text-gray-400">Loading...</p>
          ) : standups.length === 0 ? (
            <p className="text-gray-400">No standups yet</p>
          ) : (
            <div className="space-y-3">
              {standups.map((s, i) => (
                <div
                  key={i}
                  className="p-3 rounded-lg border border-white/10 bg-white/5"
                >
                  <p className="text-sm">{s.text}</p>

                  {s.created_at && (
                    <p className="text-xs text-gray-500 mt-2">
                      {new Date(s.created_at).toLocaleString()}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}