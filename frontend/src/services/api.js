import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

const api = axios.create({ baseURL: API_URL });

api.interceptors.request.use((config) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});


export const authApi = {
  login: (data) => api.post("/auth/login", data),
  register: (data) => api.post("/auth/register", data),
  me: () => api.get("/auth/me"),
};

export const dashboardApi = {
  boss: () => api.get("/dashboard/boss"),
  employee: () => api.get("/dashboard/employee"),
};

export const projectsApi = {
  list: () => api.get("/projects"),
  create: (data) => api.post("/projects", data),
  get: (id) => api.get(`/projects/${id}`),
  update: (id, data) => api.patch(`/projects/${id}`, data),
  delete: (id) => api.delete(`/projects/${id}`),
};

export const tasksApi = {
  list: (projectId) => api.get(`/tasks/project/${projectId}`),
  all: () => api.get("/tasks"),
  create: (data) => api.post("/tasks", data),
  update: (id, data) => api.patch(`/tasks/${id}`, data),
  delete: (id) => api.delete(`/tasks/${id}`),
  my: () => api.get("/tasks/my"),
};

export const sprintsApi = {
  list: () => api.get("/sprints"),
  create: (data) => api.post("/sprints", data),
  get: (id) => api.get(`/sprints/${id}`),
  update: (id, data) => api.patch(`/sprints/${id}`, data),
};

export const agentsApi = {
  trigger: (data) => api.post("/agents/trigger", data),
  createTasks: (data) => api.post("/agents/create-tasks", data),
  predictDelay: (data) => api.post("/agents/predict-delay", data),
  generateReport: (data) => api.post("/agents/generate-report", data),
  standup: (data) => api.post("/agents/standup", data),
};

export const standupsApi = {
  list: () => api.get("/standups"),
  submit: (data) => api.post("/standups", data),
  today: () => api.get("/standups/today"),
};

export const reportsApi = {
  list: () => api.get("/reports"),
  generate: (data) => api.post("/reports/generate", data),
};

export const teamApi = {
  list: () => api.get("/team"),
  get: (id) => api.get(`/team/${id}`),
};

export const notificationsApi = {
  list: () => api.get("/notifications"),
  markRead: (id) => api.patch(`/notifications/${id}/read`),
  markAllRead: () => api.patch("/notifications/read-all"),
};
export const integrationsApi = {
  list: () => api.get("/integrations"),
  connect: (data) => api.post("/integrations/connect", data),
  disconnect: (type) => api.delete(`/integrations/${type}`),
};

export const riskApi = {
  list: () => api.get("/risks"),
  resolve: (id) => api.patch(`/risks/${id}/resolve`),
};

export const pullRequestsApi = {
  list: () => api.get("/pull-requests"),
  my: () => api.get("/pull-requests/my"),
};


export { api };
