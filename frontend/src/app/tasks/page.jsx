"use client";

import { useEffect, useState } from "react";
import Sidebar from "../../components/Sidebar";
import Navbar from "../../components/Navbar";
import { tasksApi } from "../../services/api";

export default function TasksPage() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTasks = async () => {
      try {
        const res = await tasksApi.list();
        setTasks(res.data || []);
      } catch (err) {
        console.error("Error fetching tasks:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchTasks();
  }, []);

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />

      <div className="flex-1">
        <Navbar title="My Tasks" />

        <div className="p-6">
          <h1 className="text-2xl font-bold mb-4">My Tasks</h1>

          {loading ? (
            <p className="text-sm text-gray-400">Loading tasks...</p>
          ) : tasks.length === 0 ? (
            <p className="text-sm text-gray-400">No tasks available</p>
          ) : (
            <div className="space-y-3">
              {tasks.map((task) => (
                <div
                  key={task.id}
                  className="p-4 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 transition"
                >
                  <h2 className="font-semibold text-lg">{task.title}</h2>

                  {task.description && (
                    <p className="text-sm text-gray-400 mt-1">
                      {task.description}
                    </p>
                  )}

                  <div className="flex gap-3 mt-3 text-xs text-gray-400">
                    <span>📌 {task.status || "todo"}</span>
                    <span>⚡ {task.priority || "medium"}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}