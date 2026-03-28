export const capitalize = (str) => {
  if (!str) return "";
  return str.charAt(0).toUpperCase() + str.slice(1).replace(/_/g, " ");
};

export const timeAgo = (dateStr) => {
  if (!dateStr) return "";
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
};

export const formatDate = (dateStr) => {
  if (!dateStr) return "";
  return new Date(dateStr).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
};

export const statusColor = (status) => {
  const map = {
    todo: "bg-slate-700 text-slate-300",
    in_progress: "bg-blue-500/20 text-blue-400",
    done: "bg-green-500/20 text-green-400",
    blocked: "bg-red-500/20 text-red-400",
  };
  return map[status] || "bg-slate-700 text-slate-300";
};

export const priorityColor = (priority) => {
  const map = {
    high: "text-red-400",
    medium: "text-yellow-400",
    low: "text-green-400",
  };
  return map[priority] || "text-slate-400";
};

export const severityColor = (severity) => {
  const map = {
    critical: "border-red-500/30 bg-red-500/5",
    high: "border-red-400/30 bg-red-400/5",
    medium: "border-yellow-400/30 bg-yellow-400/5",
    low: "border-green-400/30 bg-green-400/5",
  };
  return map[severity] || "border-white/10 bg-white/5";
};

export const prStatusColor = (status) => {
  const map = {
    open: "bg-green-500/20 text-green-400",
    merged: "bg-purple-500/20 text-purple-400",
    closed: "bg-red-500/20 text-red-400",
    draft: "bg-slate-500/20 text-slate-400",
  };
  return map[status] || "bg-slate-700 text-slate-300";
};
