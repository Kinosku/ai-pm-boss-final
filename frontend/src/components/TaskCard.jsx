"use client";
import { statusColor, priorityColor, formatDate, capitalize } from "@/utils/helpers";

export default function TaskCard({ task, onStatusChange }) {
  const statuses = ["todo", "in_progress", "in_review", "blocked", "done"];

  return (
    <div className="flex items-center gap-4 px-6 py-4 border-b border-white/5 hover:bg-white/[0.02] transition-colors group">
      {/* Priority dot */}
      <span className={`w-2 h-2 rounded-full shrink-0 ${
        task.priority === "high" ? "bg-red-400" :
        task.priority === "medium" ? "bg-yellow-400" : "bg-green-400"
      }`} />

      {/* Jira key */}
      {task.jira_key && (
        <span className="font-mono text-xs text-on-surface-variant shrink-0">{task.jira_key}</span>
      )}

      {/* Title */}
      <p className="flex-1 text-sm font-medium text-on-surface truncate">{task.title}</p>

      {/* Story points */}
      {task.story_points && (
        <span className="text-xs font-mono text-slate-500 shrink-0">{task.story_points}pts</span>
      )}

      {/* Priority badge */}
      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase shrink-0 ${priorityColor(task.priority)}`}>
        {task.priority}
      </span>

      {/* Status */}
      <select
        value={task.status}
        onChange={(e) => onStatusChange?.(task.id, e.target.value)}
        className={`text-[11px] font-bold px-2 py-1 rounded-lg border-0 cursor-pointer shrink-0 ${statusColor(task.status)} bg-transparent`}
      >
        {statuses.map((s) => (
          <option key={s} value={s}>{capitalize(s)}</option>
        ))}
      </select>

      {/* Due date */}
      <span className="text-xs text-slate-500 shrink-0 hidden lg:block">{formatDate(task.due_date)}</span>
    </div>
  );
}
