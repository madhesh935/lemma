/**
 * AEGIS-OS — Workflow Event Feed
 * Real-time SSE-powered workflow notification stream
 */
import { useState, useEffect, useRef } from "react";
import { lemmaWorkflows } from "@/lib/lemma/index";
import type { WorkflowEvent, WorkflowState } from "@/types/lemma";
import { motion, AnimatePresence } from "framer-motion";
import {
  CheckCircle2, AlertTriangle, Info, XCircle,
  Loader2, ChevronRight, Clock, Activity
} from "lucide-react";

const STEP_LABELS: Record<string, string> = {
  not_started:           "Not Started",
  pod_created:           "Pod Created",
  evidence_uploaded:     "Evidence Uploaded",
  intake_running:        "Running Intake",
  intake_complete:       "Intake Complete",
  autopsy_analysis:      "Autopsy Analysis",
  digital_correlation:   "Digital Correlation",
  graph_update:          "Knowledge Graph",
  timeline_build:        "Timeline Build",
  risk_assessment:       "Risk Assessment",
  hypothesis_gen:        "Hypothesis Generation",
  investigator_review:   "⚠️ Investigator Review",
  report_generation:     "Report Generation",
  case_closed:           "Case Closed",
};

const WORKFLOW_STEPS = [
  "intake_running", "autopsy_analysis", "digital_correlation",
  "graph_update", "timeline_build", "risk_assessment",
  "hypothesis_gen", "investigator_review", "report_generation",
];

const SEV_CONFIG = {
  info:    { icon: <Info className="w-3.5 h-3.5 text-blue-400" />,    bar: "bg-blue-500" },
  success: { icon: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />, bar: "bg-emerald-500" },
  warning: { icon: <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />, bar: "bg-amber-500" },
  error:   { icon: <XCircle className="w-3.5 h-3.5 text-red-400" />,  bar: "bg-red-500" },
};

interface WorkflowFeedProps {
  podId?: string;
  maxEvents?: number;
  showProgress?: boolean;
}

export function WorkflowFeed({ podId, maxEvents = 15, showProgress = true }: WorkflowFeedProps) {
  const [events, setEvents] = useState<WorkflowEvent[]>([]);
  const [workflowState, setWorkflowState] = useState<WorkflowState | null>(null);
  const [loading, setLoading] = useState(true);
  const esRef = useRef<EventSource | null>(null);
  const feedRef = useRef<HTMLDivElement>(null);

  // Load initial snapshot
  useEffect(() => {
    lemmaWorkflows.feedSnapshot(podId)
      .then((r) => setEvents(r.events.slice(-maxEvents).reverse()))
      .catch(() => {})
      .finally(() => setLoading(false));

    if (podId) {
      lemmaWorkflows.status(podId).then(setWorkflowState).catch(() => {});
    }
  }, [podId, maxEvents]);

  // Subscribe to SSE
  useEffect(() => {
    try {
      const es = lemmaWorkflows.subscribeFeed(podId, (evt) => {
        setEvents((prev) => [evt, ...prev].slice(0, maxEvents));
        // Auto-refresh workflow state on significant events
        if (podId && ["agent_complete", "human_review_required", "workflow_approved"].includes(evt.event_type)) {
          lemmaWorkflows.status(podId).then(setWorkflowState).catch(() => {});
        }
        // Scroll to top
        feedRef.current?.scrollTo({ top: 0, behavior: "smooth" });
      });
      esRef.current = es;
    } catch {}

    return () => { esRef.current?.close(); };
  }, [podId, maxEvents]);

  const currentStepIdx = workflowState
    ? WORKFLOW_STEPS.indexOf(workflowState.current_step)
    : -1;

  return (
    <div className="flex flex-col h-full">
      {/* Workflow Progress */}
      {showProgress && workflowState && (
        <div className="mb-4 p-3 bg-white/[0.03] border border-white/5 rounded-xl">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-white/50">Workflow Progress</span>
            <span className="text-xs text-white/30">{workflowState.progress_pct}%</span>
          </div>
          {/* Progress bar */}
          <div className="h-1.5 bg-white/5 rounded-full overflow-hidden mb-3">
            <motion.div
              className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${workflowState.progress_pct}%` }}
              transition={{ duration: 0.8, ease: "easeOut" }}
            />
          </div>
          {/* Current step */}
          <div className="flex items-center gap-2">
            {workflowState.is_paused
              ? <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
              : workflowState.current_step === "case_closed"
              ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              : <Loader2 className="w-3.5 h-3.5 text-blue-400 animate-spin shrink-0" />
            }
            <span className="text-xs text-white/70 font-medium">
              {STEP_LABELS[workflowState.current_step] || workflowState.current_step}
            </span>
          </div>
          {/* Step indicators */}
          <div className="flex gap-1 mt-3">
            {WORKFLOW_STEPS.map((step, i) => (
              <div
                key={step}
                title={STEP_LABELS[step]}
                className={`flex-1 h-1 rounded-full transition-all ${
                  i < currentStepIdx ? "bg-cyan-500/60"
                  : i === currentStepIdx ? "bg-blue-400 animate-pulse"
                  : "bg-white/10"
                }`}
              />
            ))}
          </div>
        </div>
      )}

      {/* Event Feed */}
      <div className="text-xs font-medium text-white/30 uppercase tracking-wider mb-2 flex items-center gap-2">
        <Activity className="w-3 h-3" />
        Live Event Feed
        {events.length > 0 && (
          <span className="ml-auto bg-white/5 px-1.5 py-0.5 rounded text-white/20">{events.length}</span>
        )}
      </div>

      <div ref={feedRef} className="flex-1 overflow-y-auto space-y-1.5 min-h-0 scrollbar-thin">
        {loading && (
          <div className="text-center py-6">
            <Loader2 className="w-5 h-5 text-white/20 animate-spin mx-auto" />
          </div>
        )}



        <AnimatePresence>
          {events.map((evt, i) => {
            const sev = SEV_CONFIG[evt.severity as keyof typeof SEV_CONFIG] || SEV_CONFIG.info;
            return (
              <motion.div
                key={evt.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.2, delay: i === 0 ? 0 : 0 }}
                className="flex items-start gap-2.5 p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.04] hover:bg-white/[0.04] transition-colors"
              >
                <div className={`w-0.5 self-stretch rounded-full shrink-0 ${sev.bar}`} />
                <div className="flex-shrink-0 mt-0.5">{sev.icon}</div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium text-white/70 truncate">{evt.title}</div>
                  <div className="text-[11px] text-white/40 mt-0.5 leading-snug">{evt.message}</div>
                  <div className="text-[10px] text-white/20 mt-1 flex items-center gap-1">
                    <Clock className="w-2.5 h-2.5" />
                    {new Date(evt.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}
