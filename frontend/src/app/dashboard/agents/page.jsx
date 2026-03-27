"use client";

import { useEffect, useState } from "react";
import { agentsApi } from "../services/api";

export default function AgentsPage() {
  const [agents, setAgents] = useState([]);

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await agentsApi.list();
        setAgents(res.data);
      } catch (e) {
        console.error(e);
      }
    };
    fetch();
  }, []);

  return (
    <div>
      <h1>Agents</h1>
      {agents.map((a, i) => (
        <div key={i}>{a.name}</div>
      ))}
    </div>
  );
}