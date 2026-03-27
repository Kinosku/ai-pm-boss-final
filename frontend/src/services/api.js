import axios from "axios";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({ baseURL: `${BASE}/api` });

// Attach JWT on every request
api.interceptors.request.use((config) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto-logout on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.href = "/";
    }
    return Promise.reject(err);
  }
);

// ─── Auth ─────────────────────────────────────────────────────────────────────
export const authApi = {
  login:    (d)  => api.post("/auth/login", d),
  register: (d)  => api.post("/auth/register", d),
  me:       ()   => api.get("/auth/me"),
};

// ─── Dashboard ────────────────────────────────────────────────────────────────
export const dashboardApi = {
  boss:     ()   => api.get("/dashboard/boss"),
  employee: ()   => api.get("/dashboard/employee"),
};

// ─── Projects ─────────────────────────────────────────────────────────────────
export const projectsApi = {
  list:   ()    => api.get("/projects"),
  get:    (id)  => api.get(`/projects/${id}`),
  create: (d)   => api.post("/projects", d),
  update: (id, d) => api.patch(`/projects/${id}`, d),
  delete: (id)  => api.delete(`/projects/${id}`),
};

// ─── Tasks ────────────────────────────────────────────────────────────────────
export const tasksApi = {
  list:     (p)   => api.get("/tasks", { params: p }),
  get:      (id)  => api.get(`/tasks/${id}`),
  create:   (d)   => api.post("/tasks", d),
  update:   (id, d) => api.patch(`/tasks/${id}`, d),
  delete:   (id)  => api.delete(`/tasks/${id}`),
  parsePrd: (d)   => api.post("/tasks/parse-prd", d),
};

// ─── Sprints ──────────────────────────────────────────────────────────────────
export const sprintsApi = {
  list:     (p)   => api.get("/sprints", { params: p }),
  active:   (p)   => api.get("/sprints/active", { params: p }),
  get:      (id)  => api.get(`/sprints/${id}`),
  stats:    (id)  => api.get(`/sprints/${id}/stats`),
  create:   (d)   => api.post("/sprints", d),
  update:   (id, d) => api.patch(`/sprints/${id}`, d),
  start:    (id)  => api.post(`/sprints/${id}/start`),
  complete: (id)  => api.post(`/sprints/${id}/complete`),
};

// ─── Pull Requests ────────────────────────────────────────────────────────────
export const prsApi = {
  list:   (p)   => api.get("/pull-requests", { params: p }),
  my:     ()    => api.get("/pull-requests/my"),
  stale:  (p)   => api.get("/pull-requests/stale/list", { params: p }),
  get:    (id)  => api.get(`/pull-requests/${id}`),
  update: (id, d) => api.patch(`/pull-requests/${id}`, d),
};

// ─── Risks ────────────────────────────────────────────────────────────────────
export const risksApi = {
  list:    (p)  => api.get("/risks", { params: p }),
  counts:  (p)  => api.get("/risks/counts", { params: p }),
  analyze: (d)  => api.post("/risks/analyze", d),
  get:     (id) => api.get(`/risks/${id}`),
  update:  (id, d) => api.patch(`/risks/${id}`, d),
  resolve: (id) => api.post(`/risks/${id}/resolve`),
};

// ─── Standups ─────────────────────────────────────────────────────────────────
export const standupsApi = {
  list:            (p) => api.get("/standups", { params: p }),
  submit:          (d) => api.post("/standups", d),
  generateSummary: (d) => api.post("/standups/generate-summary", d),
};

// ─── Reports ──────────────────────────────────────────────────────────────────
export const reportsApi = {
  generate:  (p)   => api.post("/reports/generate", null, { params: p }),
  velocity:  (id)  => api.get(`/reports/velocity/${id}`),
  summary:   (id)  => api.get(`/reports/summary/${id}`),
};

// ─── Team ─────────────────────────────────────────────────────────────────────
export const teamApi = {
  list:     (p)   => api.get("/team", { params: p }),
  get:      (id)  => api.get(`/team/${id}`),
  workload: (p)   => api.get("/team/workload/summary", { params: p }),
};

// ─── Notifications ────────────────────────────────────────────────────────────
export const notificationsApi = {
  list:        (p)  => api.get("/notifications", { params: p }),
  count:       ()   => api.get("/notifications/count"),
  markRead:    (id) => api.patch(`/notifications/${id}/read`),
  markAllRead: ()   => api.post("/notifications/mark-all-read"),
};

// ─── Integrations ─────────────────────────────────────────────────────────────
export const integrationsApi = {
  list:       (p)   => api.get("/integrations", { params: p }),
  connect:    (d)   => api.post("/integrations/connect", d),
  disconnect: (id)  => api.post(`/integrations/${id}/disconnect`),
  sync:       (id)  => api.post(`/integrations/${id}/sync`),
};

// ─── Agents ───────────────────────────────────────────────────────────────────
export const agentsApi = {
  list:           ()    => api.get("/agents"),
  status:         (n,p) => api.get(`/agents/${n}/status`, { params: { project_id: p } }),
  trigger:        (d)   => api.post("/agents/trigger", d),
  runStandup:     (p)   => api.post("/agents/run-standup", null, { params: p }),
  generateReport: (p)   => api.post("/agents/generate-report", null, { params: p }),
};

// ─── Settings ─────────────────────────────────────────────────────────────────
export const settingsApi = {
  getProfile:           ()  => api.get("/settings/profile"),
  updateProfile:        (d) => api.patch("/settings/profile", d),
  getDeveloperProfile:  ()  => api.get("/settings/developer-profile"),
  updateDeveloperProfile:(d)=> api.patch("/settings/developer-profile", d),
};
