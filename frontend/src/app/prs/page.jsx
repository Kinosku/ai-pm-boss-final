"use client";

import { useEffect, useState } from "react";
import Sidebar from "../../components/Sidebar";
import Navbar from "../../components/Navbar";
import { prsApi } from "../../services/api";

export default function PRsPage() {
  const [prs, setPrs] = useState([]);
  const [loading, setLoading] = useState(true);

  // 🔥 Fetch PRs
  useEffect(() => {
    const fetchPRs = async () => {
      try {
        const res = await prsApi.list();
        setPrs(res.data || []);
      } catch (err) {
        console.error("Error fetching PRs:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchPRs();
  }, []);

  // 🔥 Update PR status
  const updateStatus = async (id, status) => {
    try {
      await prsApi.update(id, { status });

      setPrs((prev) =>
        prev.map((pr) =>
          pr.id === id ? { ...pr, status } : pr
        )
      );
    } catch (err) {
      console.error("Error updating PR:", err);
    }
  };

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />

      <div className="flex-1">
        <Navbar title="Pull Requests" />

        <div className="p-6">
          <h1 className="text-2xl font-bold mb-6">Pull Requests</h1>

          {loading ? (
            <p className="text-gray-400">Loading PRs...</p>
          ) : prs.length === 0 ? (
            <p className="text-gray-400">No pull requests found</p>
          ) : (
            <div className="space-y-4">
              {prs.map((pr) => (
                <div
                  key={pr.id}
                  className="p-4 rounded-lg border border-white/10 bg-white/5"
                >
                  {/* Title */}
                  <h2 className="font-semibold text-lg">{pr.title}</h2>

                  {/* Description */}
                  {pr.description && (
                    <p className="text-sm text-gray-400 mt-1">
                      {pr.description}
                    </p>
                  )}

                  {/* Info */}
                  <div className="flex justify-between items-center mt-3">
                    <span className="text-xs text-gray-400">
                      Status:{" "}
                      <span className="font-semibold">
                        {pr.status || "open"}
                      </span>
                    </span>

                    {/* Actions */}
                    <div className="flex gap-2">
                      <button
                        onClick={() => updateStatus(pr.id, "approved")}
                        className="px-3 py-1 text-xs rounded bg-green-500 text-black"
                      >
                        Approve
                      </button>

                      <button
                        onClick={() =>
                          updateStatus(pr.id, "changes_requested")
                        }
                        className="px-3 py-1 text-xs rounded bg-red-500 text-black"
                      >
                        Reject
                      </button>
                    </div>
                  </div>

                  {/* Timestamp */}
                  {pr.updated_at && (
                    <p className="text-[10px] text-gray-500 mt-2">
                      Updated: {pr.updated_at}
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