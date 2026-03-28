"use client";

import { useEffect, useState } from "react";
import Sidebar from "../../components/Sidebar";
import Navbar from "../../components/Navbar";
import { tasksApi } from "../../services/api";

const columns = [
  { key: "todo", label: "To Do" },
  { key: "in_progress", label: "In Progress" },
  { key: "in_review", label: "In Review" },
  { key: "done", label: "Done" },
];

export default function SprintPage() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);

  // 🔥 Fetch tasks
  useEffect(() => {
    const fetchTasks = async () => {
      try {
        const res = await tasksApi.list();
        setTasks(res.data || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchTasks();
  }, []);

  // 🔥 Move task between columns
  const moveTask = async (task, newStatus) => {
    try {
      await tasksApi.update(task.id, { status: newStatus });

      setTasks((prev) =>
        prev.map((t) =>
          t.id === task.id ? { ...t, status: newStatus } : t
        )
      );
    } catch (err) {
      console.error(err);
    }
  };

  // 🔥 Group tasks
  const grouped = columns.reduce((acc, col) => {
    acc[col.key] = tasks.filter((t) => t.status === col.key);
    return acc;
  }, {});

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />

      <div className="flex-1">
        <Navbar title="Sprint Board" />

        <div className="p-6">
          <h1 className="text-2xl font-bold mb-6">Sprint Board</h1>

          {loading ? (
            <p className="text-gray-400">Loading tasks...</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {columns.map((col) => (
                <div
                  key={col.key}
                  className="bg-white/5 border border-white/10 rounded-lg p-3"
                >
                  <h2 className="font-semibold mb-3">{col.label}</h2>

                  <div className="space-y-2">
                    {grouped[col.key]?.map((task) => (
                      <div
                        key={task.id}
                        className="p-3 rounded bg-white/10 text-sm"
                      >
                        <p className="font-medium">{task.title}</p>

                        <div className="flex gap-2 mt-2 flex-wrap">
                          {columns.map((c) =>
                            c.key !== task.status ? (
                              <button
                                key={c.key}
                                onClick={() => moveTask(task, c.key)}
                                className="text-xs px-2 py-1 bg-primary rounded text-black"
                              >
                                Move to {c.label}
                              </button>
                            ) : null
                          )}
                        </div>
                      </div>
                    ))}
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