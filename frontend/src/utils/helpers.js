// ─── Date helpers ─────────────────────────────────────────────────────────────
export const formatDate = (dateStr) => {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
};

export const timeAgo = (dateStr) => {
  if (!dateStr) return "";
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60)  return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24)   return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
};

// ─── Status helpers ───────────────────────────────────────────────────────────
export const statusColor = (status) => ({
  todo:        "text-slate-400  bg-slate-400/10",
  in_progress: "text-blue-400   bg-blue-400/10",
  in_review:   "text-purple-400 bg-purple-400/10",
  blocked:     "text-red-400    bg-red-400/10",
  done:        "text-green-400  bg-green-400/10",
  backlog:     "text-slate-500  bg-slate-500/10",
}[status] || "text-slate-400 bg-slate-400/10");

export const priorityColor = (priority) => ({
  high:   "text-red-400   bg-red-400/10",
  medium: "text-yellow-400 bg-yellow-400/10",
  low:    "text-green-400  bg-green-400/10",
}[priority] || "text-slate-400 bg-slate-400/10");

export const severityColor = (severity) => ({
  critical: "text-red-400    bg-red-500/10    border-red-500/20",
  high:     "text-red-400    bg-red-500/10    border-red-500/20",
  medium:   "text-yellow-400 bg-yellow-500/10 border-yellow-500/20",
  low:      "text-slate-400  bg-slate-500/10  border-slate-500/20",
}[severity] || "text-slate-400 bg-slate-400/10");

export const prStatusColor = (status) => ({
  open:     "text-blue-400   bg-blue-400/10",
  in_review:"text-purple-400 bg-purple-400/10",
  approved: "text-green-400  bg-green-400/10",
  merged:   "text-primary    bg-primary/10",
  closed:   "text-slate-400  bg-slate-400/10",
}[status] || "text-slate-400 bg-slate-400/10");

// ─── String helpers ───────────────────────────────────────────────────────────
export const capitalize = (s) => s ? s.charAt(0).toUpperCase() + s.slice(1).replace(/_/g, " ") : "";
export const truncate   = (s, n = 60) => s && s.length > n ? s.slice(0, n) + "…" : s;

// ─── Sprint progress ──────────────────────────────────────────────────────────
export const sprintProgress = (completed, planned) => {
  if (!planned) return 0;
  return Math.min(Math.round((completed / planned) * 100), 100);
};

// ─── Health score color ───────────────────────────────────────────────────────
export const healthColor = (score) => {
  if (score >= 75) return "text-primary";
  if (score >= 50) return "text-yellow-400";
  return "text-red-400";
};
