"use client";
export default function Modal({ open, onClose, title, children }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-surface-container ghost-border rounded-2xl p-6 w-full max-w-md z-10">
        <div className="flex items-center justify-between mb-5">
          <h3 className="font-headline font-bold text-lg">{title}</h3>
          <button onClick={onClose} className="text-on-surface-variant hover:text-on-surface text-xl">✕</button>
        </div>
        {children}
      </div>
    </div>
  );
}
