"use client";

import { useEffect, useState } from "react";
import { projectsApi } from "../services/api";

export default function ProjectsPage() {
  const [projects, setProjects] = useState([]);

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await projectsApi.list();
        setProjects(res.data);
      } catch (e) {
        console.error(e);
      }
    };
    fetch();
  }, []);

  return (
    <div>
      <h1>Projects</h1>
      {projects.map((p) => (
        <div key={p.id}>{p.name}</div>
      ))}
    </div>
  );
}