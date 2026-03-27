import clsx from "clsx";

export default function Button({ children, variant = "primary", size = "md", className = "", ...props }) {
  const base = "inline-flex items-center justify-center gap-2 font-bold rounded-xl transition-all duration-150 disabled:opacity-50";
  const variants = {
    primary:  "velocity-gradient-bg text-background hover:opacity-90",
    secondary:"bg-surface-container ghost-border text-on-surface hover:bg-surface-container-high",
    ghost:    "text-slate-400 hover:text-white hover:bg-white/[0.04]",
    danger:   "bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20",
  };
  const sizes = {
    sm: "px-3 py-1.5 text-xs",
    md: "px-4 py-2 text-sm",
    lg: "px-6 py-2.5 text-sm",
  };
  return (
    <button className={clsx(base, variants[variant], sizes[size], className)} {...props}>
      {children}
    </button>
  );
}
