export default function Button({ children, onClick, variant = "primary", className = "", disabled = false, type = "button" }) {
  const base = "font-bold py-2.5 px-4 rounded-xl text-sm transition-all disabled:opacity-50";
  const variants = {
    primary: "velocity-gradient-bg text-background hover:opacity-90",
    ghost: "ghost-border text-on-surface hover:bg-white/5",
    danger: "bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/20",
  };
  return (
    <button type={type} onClick={onClick} disabled={disabled} className={`${base} ${variants[variant]} ${className}`}>
      {children}
    </button>
  );
}
