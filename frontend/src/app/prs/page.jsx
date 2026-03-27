"use client";
import { useEffect, useState } from "react";
import Sidebar from "../../components/Sidebar";
import Navbar from "../../components/Navbar";
import { prsApi } from "../../services/api";
import { prStatusColor, timeAgo, capitalize } from "../../utils/helpers";
import { useAuth } from "../../context/AuthContext";

export default function PRsPage() {
  const { isBoss }        = useAuth();
  const [prs, setPrs]     = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fn = isBoss ? prsApi.list({}) : prsApi.my();
    fn.then(({ data }) => setPrs(data)).finally(() => setLoading(false));
  }, [isBoss]);

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar title="Pull Requests" />
        <main className="flex-1 overflow-y-auto px-8 py-6">
          <div className="mb-6">
            <h1 className="text-3xl font-bold font-headline">My PRs & Reviews</h1>
            <p className="text-on-surface-variant text-sm mt-1">Track contributions, reviews, and deployment status</p>
          </div>

          <div className="bg-surface-container ghost-border rounded-2xl overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/5">
                  {["PR","Title","Branch","Status","Review","Stale","Opened"].map((h) => (
                    <th key={h} className="px-5 py-3 text-left text-xs font-bold uppercase tracking-wider text-slate-500">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {loading && (
                  <tr><td colSpan={7} className="text-center text-slate-500 text-sm py-8">Loading…</td></tr>
                )}
                {!loading && prs.length === 0 && (
                  <tr><td colSpan={7} className="text-center text-slate-500 text-sm py-8">No PRs found</td></tr>
                )}
                {prs.map((pr) => (
                  <tr key={pr.id} className="hover:bg-white/[0.02] transition-colors">
                    <td className="px-5 py-3.5 text-sm font-mono text-on-surface-variant">#{pr.github_pr_number}</td>
                    <td className="px-5 py-3.5">
                      <a href={pr.github_url} target="_blank" rel="noopener noreferrer"
                        className="text-sm font-medium text-on-surface hover:text-primary transition-colors line-clamp-1">
                        {pr.title}
                      </a>
                    </td>
                    <td className="px-5 py-3.5 text-xs font-mono text-slate-500">{pr.head_branch || "—"}</td>
                    <td className="px-5 py-3.5">
                      <span className={`text-[10px] font-bold px-2 py-1 rounded-full ${prStatusColor(pr.status)}`}>
                        {capitalize(pr.status)}
                      </span>
                    </td>
                    <td className="px-5 py-3.5">
                      <span className={`text-[10px] font-bold px-2 py-1 rounded-full ${
                        pr.review_status === "approved" ? "text-green-400 bg-green-400/10" :
                        pr.review_status === "changes_requested" ? "text-red-400 bg-red-400/10" :
                        "text-slate-400 bg-slate-400/10"
                      }`}>{capitalize(pr.review_status || "pending")}</span>
                    </td>
                    <td className="px-5 py-3.5">
                      {pr.is_stale && <span className="text-[10px] font-bold text-yellow-400 bg-yellow-400/10 px-2 py-1 rounded-full">Stale</span>}
                    </td>
                    <td className="px-5 py-3.5 text-xs text-slate-500">{timeAgo(pr.opened_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </main>
      </div>
    </div>
  );
}
