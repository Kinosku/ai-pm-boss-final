"use client";

import { useEffect, useState } from "react";
import Sidebar from "../../components/Sidebar";
import Navbar from "../../components/Navbar";
import { teamApi } from "../../services/api";

export default function TeamPage() {
  const [team, setTeam] = useState([]);
  const [loading, setLoading] = useState(true);

  // 🔥 Fetch team
  useEffect(() => {
    const fetchTeam = async () => {
      try {
        const res = await teamApi.list();
        setTeam(res.data || []);
      } catch (err) {
        console.error("Error fetching team:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchTeam();
  }, []);

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />

      <div className="flex-1">
        <Navbar title="Team" />

        <div className="p-6">
          <h1 className="text-2xl font-bold mb-6">Team Members</h1>

          {loading ? (
            <p className="text-gray-400">Loading team...</p>
          ) : team.length === 0 ? (
            <p className="text-gray-400">No team members found</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {team.map((member) => (
                <div
                  key={member.id}
                  className="p-4 rounded-lg border border-white/10 bg-white/5"
                >
                  {/* Name */}
                  <h2 className="font-semibold text-lg">
                    {member.full_name}
                  </h2>

                  {/* Email */}
                  <p className="text-sm text-gray-400">
                    {member.email}
                  </p>

                  {/* Role */}
                  <div className="mt-2">
                    <span
                      className={`text-xs px-2 py-1 rounded ${
                        member.role === "boss"
                          ? "bg-yellow-400 text-black"
                          : "bg-blue-400 text-black"
                      }`}
                    >
                      {member.role}
                    </span>
                  </div>

                  {/* Workload */}
                  <div className="mt-3">
                    <p className="text-xs text-gray-400 mb-1">
                      Workload
                    </p>
                    <div className="w-full h-2 bg-white/10 rounded">
                      <div
                        className="h-2 bg-primary rounded"
                        style={{
                          width: `${member.workload || 40}%`,
                        }}
                      />
                    </div>
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