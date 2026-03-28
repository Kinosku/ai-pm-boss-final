"use client";

import { useEffect, useState } from "react";
import { notificationsApi } from "../services/api";

export default function NotificationsPanel() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        const res = await notificationsApi.list();
        setNotifications(res.data || []);
      } catch (err) {
        console.error("Error fetching notifications:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchNotifications();
  }, []);

  const markAsRead = (id) => {
    setNotifications((prev) =>
      prev.map((n) =>
        n.id === id ? { ...n, read: true } : n
      )
    );
  };

  return (
    <div className="space-y-3">
      {loading ? (
        <p className="text-gray-400">Loading notifications...</p>
      ) : notifications.length === 0 ? (
        <p className="text-gray-400">No notifications</p>
      ) : (
        notifications.map((n) => (
          <div
            key={n.id}
            className={`p-3 rounded-lg border ${
              n.read
                ? "bg-white/5 border-white/10"
                : "bg-blue-500/10 border-blue-400"
            }`}
          >
            {/* Message */}
            <p className="text-sm">{n.message}</p>

            {/* Time */}
            <p className="text-xs text-gray-500 mt-1">
              {n.created_at
                ? new Date(n.created_at).toLocaleString()
                : "recent"}
            </p>

            {/* Action */}
            {!n.read && (
              <button
                onClick={() => markAsRead(n.id)}
                className="text-xs text-blue-400 mt-2"
              >
                Mark as read
              </button>
            )}
          </div>
        ))
      )}
    </div>
  );
}