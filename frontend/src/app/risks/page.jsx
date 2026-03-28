"use client";

import Sidebar from "../../components/Sidebar";
import Navbar from "../../components/Navbar";

export default function RisksPage() {
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex-1">
        <Navbar title="Risk Alerts" />
        <div className="p-6">
          <p>No risks detected ✅</p>
        </div>
      </div>
    </div>
  );
}
