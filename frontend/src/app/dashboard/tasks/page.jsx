"use client";
import { useEffect, useState } from "react";
import { tasksApi } from "../../services/api";

export default function TasksPage() {
  const [tasks, setTasks] = useState([]);

  useEffect(() => {
    const fetchTasks = async () => {
      try {
        const res = await tasksApi.list();
        setTasks(res.data || []);
      } catch (e) {
        console.error("Error fetching tasks:", e);
      }
    };

    fetchTasks();
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-xl font-bold mb-4">Tasks</h1>

      {tasks.length === 0 ? (
        <p>No tasks found</p>
      ) : (
        tasks.map((t) => (
          <div
            key={t.id}
            className="p-3 mb-2 border rounded-lg bg-gray-50"
          >
            {t.title}
          </div>
        ))
      )}
    </div>
  );
}