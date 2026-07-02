/**
 * AEGIS-OS Lemma SDK Client
 * All API calls to the Lemma SDK backend endpoints.
 */
import type {
  Pod, CreatePodInput, FileRecord, AgentJob, AgentInfo,
  WorkflowState, WorkflowEvent, Report, ReportType,
  AuthUser, TokenResponse, CopilotResponse, DashboardStats,
  RiskScore, Hypothesis, TimelineEvent, Person,
} from "@/types/lemma";

const BASE = "/api/v2";

// ─── Token management ─────────────────────────────────────────────────────────
let _accessToken: string | null = null;

export const setAccessToken = (token: string) => { _accessToken = token; };
export const getAccessToken = () => _accessToken;
export const clearTokens = () => { _accessToken = null; };

// ─── HTTP helpers ─────────────────────────────────────────────────────────────
async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> || {}),
  };
  if (_accessToken) {
    headers["Authorization"] = `Bearer ${_accessToken}`;
  }
  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const err = await res.json();
      detail = err.detail || detail;
    } catch {}
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

async function uploadRequest<T>(path: string, formData: FormData): Promise<T> {
  const headers: Record<string, string> = {};
  if (_accessToken) headers["Authorization"] = `Bearer ${_accessToken}`;
  const res = await fetch(`${BASE}${path}`, { method: "POST", headers, body: formData });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try { const err = await res.json(); detail = err.detail || detail; } catch {}
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}


// ─── AUTH ─────────────────────────────────────────────────────────────────────
export const lemmaAuth = {
  login: (email: string, password: string) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  refresh: (refresh_token: string) =>
    request<{ access_token: string }>("/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token }),
    }),

  me: () => request<AuthUser>("/auth/me"),

  logout: () => request<void>("/auth/logout", { method: "POST" }),

  createUser: (data: { email: string; password: string; full_name: string; role: string }) =>
    request<AuthUser>("/auth/users", { method: "POST", body: JSON.stringify(data) }),

  listUsers: () => request<AuthUser[]>("/auth/users"),
};


// ─── PODS ─────────────────────────────────────────────────────────────────────
export const lemmaPods = {
  create: (data: CreatePodInput) =>
    request<Pod>("/pods", { method: "POST", body: JSON.stringify(data) }),

  list: () => request<{ pods: Pod[]; total: number }>("/pods"),

  get: (podId: string) => request<Pod>(`/pods/${podId}`),

  update: (podId: string, data: Partial<Pod>) =>
    request<Pod>(`/pods/${podId}`, { method: "PATCH", body: JSON.stringify(data) }),

  archive: (podId: string) =>
    request<{ message: string }>(`/pods/${podId}/archive`, { method: "POST" }),

  notifications: (podId: string) =>
    request<{ notifications: WorkflowEvent[] }>(`/pods/${podId}/notifications`),

  stats: () => request<DashboardStats>("/pods/stats/summary"),
};


// ─── EVIDENCE FILES ───────────────────────────────────────────────────────────
export const lemmaFiles = {
  upload: (podId: string, files: File[]) => {
    const form = new FormData();
    files.forEach((f) => form.append("files", f));
    return uploadRequest<{ uploaded: FileRecord[]; errors: unknown[]; total_uploaded: number }>(
      `/pods/${podId}/files`,
      form,
    );
  },

  list: (podId: string) =>
    request<{ files: FileRecord[]; stats: Record<string, unknown> }>(`/pods/${podId}/files`),

  get: (podId: string, fileId: string) =>
    request<FileRecord>(`/pods/${podId}/files/${fileId}`),

  downloadUrl: (podId: string, fileId: string) =>
    `${BASE}/pods/${podId}/files/${fileId}/download`,

  delete: (podId: string, fileId: string) =>
    request<void>(`/pods/${podId}/files/${fileId}`, { method: "DELETE" }),
};


// ─── AGENTS ───────────────────────────────────────────────────────────────────
export const lemmaAgents = {
  list: () => request<{ agents: AgentInfo[] }>("/agents/list"),

  invoke: (agentName: string, podId: string, context: Record<string, unknown> = {}, asyncMode = true) =>
    request<AgentJob>("/agents/invoke", {
      method: "POST",
      body: JSON.stringify({ agent_name: agentName, pod_id: podId, context, async_mode: asyncMode }),
    }),

  jobStatus: (jobId: string) => request<AgentJob>(`/agents/status/${jobId}`),

  history: (podId: string) => request<{ jobs: AgentJob[] }>(`/agents/history/${podId}`),
};


// ─── WORKFLOWS ────────────────────────────────────────────────────────────────
export const lemmaWorkflows = {
  start: (podId: string, context: Record<string, unknown> = {}) =>
    request<{ message: string }>("/workflows/start", {
      method: "POST",
      body: JSON.stringify({ pod_id: podId, context }),
    }),

  status: (podId: string) => request<WorkflowState>(`/workflows/${podId}/status`),

  approve: (podId: string, reportType: ReportType = "investigator") =>
    request<{ message: string }>(`/workflows/${podId}/approve`, {
      method: "POST",
      body: JSON.stringify({ report_type: reportType }),
    }),

  feedSnapshot: (podId?: string) => {
    const qs = podId ? `?pod_id=${podId}` : "";
    return request<{ events: WorkflowEvent[] }>(`/workflows/feed/snapshot${qs}`);
  },

  /** Subscribe to SSE event feed */
  subscribeFeed: (
    podId?: string,
    onEvent?: (event: WorkflowEvent) => void,
  ): EventSource => {
    const qs = podId ? `?pod_id=${podId}` : "";
    const url = `${BASE}/workflows/feed${qs}`;
    const es = new EventSource(url);
    es.onmessage = (e) => {
      try {
        const data: WorkflowEvent = JSON.parse(e.data);
        onEvent?.(data);
      } catch {}
    };
    return es;
  },
};


// ─── COPILOT ──────────────────────────────────────────────────────────────────
export const lemmaCopilot = {
  chat: (message: string, podId?: string, sessionId?: string, context: Record<string, unknown> = {}) =>
    request<CopilotResponse>("/copilot/chat", {
      method: "POST",
      body: JSON.stringify({ message, pod_id: podId, session_id: sessionId, context }),
    }),

  history: (sessionId: string) =>
    request<{ messages: Array<{ role: string; content: string }> }>(`/copilot/history/${sessionId}`),

  clearSession: (sessionId: string) =>
    request<void>(`/copilot/session/${sessionId}`, { method: "DELETE" }),

  routingMap: () => request<{ routing_rules: Array<{ pattern: string; routes_to: string }> }>("/copilot/routing-map"),
};


// ─── Legacy API (preserved from lib/api.ts) ───────────────────────────────────
export { fetchStats } from "@/lib/api";
