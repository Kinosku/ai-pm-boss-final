"use client";

import Sidebar from "../../components/Sidebar";
import Navbar from "../../components/Navbar";
import NotificationsPanel from "../../components/NotificationsPanel";

export default function NotificationsPage() {
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />

      <div className="flex-1">
        <Navbar title="Notifications" />

        <div className="p-6 max-w-3xl">
          <h1 className="text-2xl font-bold mb-6">
            Notifications
          </h1>

          <NotificationsPanel />
        </div>
      </div>
    </div>
  );
}