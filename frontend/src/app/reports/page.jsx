"use client";

import { useState } from "react";
import Sidebar from "../../components/Sidebar";
import Navbar from "../../components/Navbar";
import { reportsApi } from "../../services/api";

export default function ReportsPage() {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const generateReport = async () => {
    setLoading(true);
    setMessage("");
    try {
      await reportsApi.generate();
      setMessage("Report generated successfully ✅");
    } catch (err) {
      console.error(err);
      setMessage("Failed to generate report ❌");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />

      <div className="flex-1">
        <Navbar title="Reports" />

        <div className="p-6">
          <h1 className="text-2xl font-bold mb-6">Project Reports</h1>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="p-4 rounded-lg bg-white/5 border border-white/10">
              <p className="text-sm text-gray-400">Velocity</p>
              <h2 className="text-xl font-bold">--</h2>
            </div>

            <div className="p-4 rounded-lg bg-white/5 border border-white/10">
              <p className="text-sm text-gray-400">Completed Tasks</p>
              <h2 className="text-xl font-bold">--</h2>
            </div>

            <div className="p-4 rounded-lg bg-white/5 border border-white/10">
              <p className="text-sm text-gray-400">Pending Tasks</p>
              <h2 className="text-xl font-bold">--</h2>
            </div>
          </div>

          {/* Generate Report Button */}
          <div className="mb-4">
            <button
              onClick={generateReport}
              disabled={loading}
              className="px-4 py-2 rounded-lg bg-primary text-black font-semibold hover:opacity-90"
            >
              {loading ? "Generating..." : "Generate AI Report"}
            </button>
          </div>

          {/* Message */}
          {message && (
            <p className="text-sm text-gray-400">{message}</p>
          )}

          {/* Placeholder Report Content */}
          <div className="mt-6 p-4 rounded-lg bg-white/5 border border-white/10">
            <h2 className="font-semibold mb-2">Latest Report</h2>
            <p className="text-sm text-gray-400">
              Your AI-generated project insights will appear here.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}