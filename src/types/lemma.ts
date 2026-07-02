/**
 * AEGIS-OS Lemma SDK Types
 * TypeScript definitions for all Lemma entities
 */

// ─── Core Lemma Types ───────────────────────────────────────────────────────
export type PodStatus = "active" | "suspended" | "archived" | "closed";
export type Severity = "low" | "medium" | "high" | "critical";
export type UserRole = "admin" | "lead_investigator" | "investigator" | "viewer";
export type AgentStatus = "ready" | "running" | "completed" | "failed" | "idle";
export type WorkflowStep =
  | "pod_created" | "evidence_uploaded" | "intake_running" | "intake_complete"
  | "autopsy_analysis" | "digital_correlation" | "graph_update"
  | "timeline_build" | "risk_assessment" | "hypothesis_gen"
  | "investigator_review" | "report_generation" | "case_closed" | "not_started";
export type EvidenceType =
  | "autopsy_report" | "witness_statement" | "image" | "crime_scene_photo"
  | "gps_log" | "call_detail_record" | "cctv_video" | "phone_metadata"
  | "medical_report" | "pdf" | "json_data" | "csv_data" | "video" | "other";
export type ReportType = "executive" | "investigator" | "court" | "evidence_index";

// ─── Investigation Pod ───────────────────────────────────────────────────────
export interface Pod {
  pod_id: string;
  pod_key: string;           // e.g. "CASE-2026-001"
  name: string;
  description?: string;
  status: PodStatus;
  severity: Severity;
  district?: string;
  fir_number?: string;
  investigators: string[];
  created_at: string;
  updated_at: string;
  closed_at?: string;
  recent_notifications?: WorkflowEvent[];
}

export interface CreatePodInput {
  name: string;
  description?: string;
  severity?: Severity;
  district?: string;
  fir_number?: string;
  pod_key?: string;
}

// ─── Evidence Files ──────────────────────────────────────────────────────────
export interface FileRecord {
  file_id: string;
  pod_id: string;
  original_name: string;
  file_hash: string;
  file_size: number;
  mime_type: string;
  evidence_type: EvidenceType;
  uploaded_by?: string;
  uploaded_at: string;
  is_processed: boolean;
  chain_of_custody: CustodyEntry[];
  metadata: Record<string, unknown>;
  priority_score?: number;
  ai_classification?: string;
  ai_summary?: string;
}

export interface CustodyEntry {
  timestamp: string;
  action: string;
  user_id?: string;
  agent_name?: string;
  notes: string;
}

// ─── Persons ─────────────────────────────────────────────────────────────────
export interface Person {
  id: string;
  pod_id: string;
  person_code?: string;
  full_name: string;
  role: "victim" | "suspect" | "witness" | "unknown";
  age?: number;
  gender?: string;
  risk_level: string;
  notes?: string;
}

// ─── Timeline Events ─────────────────────────────────────────────────────────
export interface TimelineEvent {
  id?: string;
  timestamp?: string;
  timestamp_iso?: string;
  event_type: string;
  title: string;
  description?: string;
  location_name?: string;
  latitude?: number;
  longitude?: number;
  confidence: number;
  is_conflicting?: boolean;
  source_evidence_id?: string;
  persons_involved?: string[];
}

// ─── Hypotheses ───────────────────────────────────────────────────────────────
export interface Hypothesis {
  hypothesis_number: number;
  title: string;
  description: string;
  confidence_score: number;
  supporting_evidence_ids: string[];
  contradicting_evidence_ids: string[];
  additional_evidence_needed: string[];
  reasoning?: string;
}

// ─── Risk Score ───────────────────────────────────────────────────────────────
export interface RiskScore {
  overall_score: number;
  urgency_level: "low" | "medium" | "high" | "critical";
  factors: Record<string, number>;
  anomalies: Array<{ type: string; detail: string }>;
  inconsistencies: string[];
  recommendations: string[];
}

// ─── Agent ────────────────────────────────────────────────────────────────────
export interface AgentInfo {
  name: string;
  description: string;
  version: string;
  status: AgentStatus;
}

export interface AgentJob {
  job_id: string;
  agent_name: string;
  pod_id: string;
  status: "pending" | "running" | "completed" | "failed";
  output?: Record<string, unknown>;
  error?: string;
  duration_seconds?: number;
  started_by?: string;
}

// ─── Workflow ─────────────────────────────────────────────────────────────────
export interface WorkflowState {
  pod_id: string;
  current_step: WorkflowStep;
  is_paused: boolean;
  step_history: WorkflowStepRecord[];
  progress_pct: number;
}

export interface WorkflowStepRecord {
  step: string;
  success: boolean;
  data?: Record<string, unknown>;
  error?: string;
  timestamp: string;
}

export interface WorkflowEvent {
  id: string;
  event_type: string;
  title: string;
  message: string;
  pod_id?: string;
  severity: "info" | "success" | "warning" | "error";
  metadata: Record<string, unknown>;
  timestamp: string;
  read: boolean;
}

// ─── Report ───────────────────────────────────────────────────────────────────
export interface Report {
  id?: string;
  report_type: ReportType;
  title: string;
  content_markdown?: string;
  content_json?: Record<string, unknown>;
  status: "draft" | "pending_approval" | "approved" | "finalized";
  approved_by?: string;
  generated_at: string;
  generated_by: string;
}

// ─── Auth ─────────────────────────────────────────────────────────────────────
export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  department?: string;
  badge_number?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: AuthUser;
}

// ─── Copilot ──────────────────────────────────────────────────────────────────
export interface CopilotMessage {
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
  agents_consulted?: string[];
}

export interface CopilotResponse {
  response: string;
  agent_used: string;
  agents_consulted: string[];
  session_id: string;
  confidence: number;
  sources: string[];
}

// ─── Dashboard Stats ──────────────────────────────────────────────────────────
export interface DashboardStats {
  total: number;
  active: number;
  archived: number;
  high_risk: number;
  critical: number;
  by_severity: Record<Severity, number>;
}
