"use client";
import Sidebar from "@/components/Sidebar";
import Navbar  from "@/components/Navbar";
import NotificationsPanel from "@/components/NotificationsPanel";
import { notificationsApi } from "@/services/api";
import Button from "@/components/ui/Button";

export default function NotificationsPage() {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar title="Notifications" />
        <main className="flex-1 overflow-y-auto px-8 py-6">
          <div className="max-w-2xl mx-auto">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h1 className="text-3xl font-bold font-headline">
                  System <span className="velocity-gradient">Notifications</span>
                </h1>
                <p className="text-on-surface-variant text-sm mt-1">AI alerts, agent actions, and updates</p>
              </div>
              <Button variant="secondary" size="sm"
                onClick={() => notificationsApi.markAllRead().then(() => window.location.reload())}>
                Mark all read
              </Button>
            </div>
            <div className="bg-surface-container ghost-border rounded-2xl overflow-hidden">
              <NotificationsPanel limit={50} />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
