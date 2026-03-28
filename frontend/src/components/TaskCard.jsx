"use client";

export default function TaskCard({ task }) {
  return (
    <div className="p-4 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 transition">
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
  );
}