/**
 * AEGIS-OS — Pod Status Panel
 * Shows Investigation Pod metadata, workflow state, and quick actions
 */
import { useState, useEffect } from "react";
import { lemmaPods, lemmaWorkflows } from "@/lib/lemma/index";
import type { Pod, WorkflowState } from "@/types/lemma";
import { motion } from "framer-motion";
import {
  Shield, Activity, CheckCircle2, AlertTriangle, Archive,
  Play, FileText, ChevronRight, Users, FolderOpen, Clock
} from "lucide-react";
import { ApprovalGate } from "./ApprovalGate";

const SEV_BADGE: Record<string, string> = {
  critical: "bg-red-500/15 text-red-300 border-red-500/20",
  high:     "bg-orange-500/15 text-orange-300 border-orange-500/20",
  medium:   "bg-amber-500/15 text-amber-300 border-amber-500/20",
  low:      "bg-blue-500/15 text-blue-300 border-blue-500/20",
};

const STATUS_BADGE: Record<string, string> = {
  active:    "bg-emerald-500/15 text-emerald-300",
  suspended: "bg-amber-500/15 text-amber-300",
  archived:  "bg-white/10 text-white/40",
  closed:    "bg-white/5 text-white/20",
};

interface PodStatusPanelProps {
  podId: string;
  onStartWorkflow?: () => void;
  onViewReport?: () => void;
}

export function PodStatusPanel({ podId, onStartWorkflow, onViewReport }: PodStatusPanelProps) {
  const [pod, setPod] = useState<Pod | null>(null);
  const [workflowState, setWorkflowState] = useState<WorkflowState | null>(null);
  const [loading, setLoading] = useState(true);
  const [showApproval, setShowApproval] = useState(false);

  useEffect(() => {
    Promise.all([
      lemmaPods.get(podId).catch(() => null),
      lemmaWorkflows.status(podId).catch(() => null),
    ]).then(([p, w]) => {
      setPod(p);
      setWorkflowState(w);
    }).finally(() => setLoading(false));
  }, [podId]);

  const handleStartWorkflow = async () => {
    try {
      await lemmaWorkflows.start(podId, { pod_id: podId });
      const state = await lemmaWorkflows.status(podId);
      setWorkflowState(state);
      onStartWorkflow?.();
    } catch (e) {
      console.error("Workflow start failed:", e);
    }
  };

  if (loading) {
    return (
      <div className="p-4 bg-white/[0.02] border border-white/5 rounded-xl animate-pulse h-48" />
    );
  }

  const isAtCheckpoint = workflowState?.is_paused && workflowState.current_step === "investigator_review";
  const isComplete = workflowState?.current_step === "case_closed";

  return (
    <div className="space-y-3">
      {/* Pod header */}
      <div className="p-4 bg-white/[0.03] border border-white/5 rounded-xl">
        <div className="flex items-start justify-between mb-3">
          <div>
            <div className="text-xs font-mono text-white/30 mb-0.5">{pod?.pod_key || podId}</div>
            <h3 className="text-sm font-bold text-white leading-tight">{pod?.name || "Investigation Pod"}</h3>
            {pod?.district && (
              <div className="text-xs text-white/30 mt-0.5">{pod.district}</div>
            )}
          </div>
          <div className="flex flex-col gap-1 items-end">
            {pod?.severity && (
              <span className={`text-[10px] px-2 py-0.5 rounded-full border font-semibold uppercase ${SEV_BADGE[pod.severity]}`}>
                {pod.severity}
              </span>
            )}
            {pod?.status && (
              <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium capitalize ${STATUS_BADGE[pod.status]}`}>
                {pod.status}
              </span>
            )}
          </div>
        </div>

        {/* Pod meta */}
        <div className="grid grid-cols-2 gap-2 mb-3">
          {[
            { icon: <Users className="w-3 h-3" />, label: "Investigators", value: pod?.investigators?.length || 0 },
            { icon: <FolderOpen className="w-3 h-3" />, label: "FIR", value: pod?.fir_number || "N/A" },
          ].map((m) => (
            <div key={m.label} className="flex items-center gap-1.5 text-xs text-white/40">
              {m.icon}
              <span>{m.label}:</span>
              <span className="text-white/60">{m.value}</span>
            </div>
          ))}
        </div>

        {/* Workflow progress */}
        {workflowState && workflowState.current_step !== "not_started" && (
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[10px] text-white/30 uppercase tracking-wider">Workflow</span>
              <span className="text-[10px] text-white/30">{workflowState.progress_pct}%</span>
            </div>
            <div className="h-1 bg-white/5 rounded-full overflow-hidden">
              <motion.div
                className={`h-full rounded-full ${isComplete ? "bg-emerald-500" : isAtCheckpoint ? "bg-amber-500" : "bg-blue-500"}`}
                initial={{ width: 0 }}
                animate={{ width: `${workflowState.progress_pct}%` }}
                transition={{ duration: 0.6 }}
              />
            </div>
            <div className="text-[10px] text-white/30 mt-1 capitalize flex items-center gap-1">
              {isAtCheckpoint ? <AlertTriangle className="w-3 h-3 text-amber-400" /> : <Activity className="w-3 h-3" />}
              {workflowState.current_step.replace(/_/g, " ")}
            </div>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="space-y-2">
        {/* Start Workflow */}
        {(!workflowState || workflowState.current_step === "not_started") && (
          <button
            onClick={handleStartWorkflow}
            className="w-full flex items-center gap-2.5 p-3 bg-blue-500/10 border border-blue-500/20
                       rounded-xl text-sm text-blue-300 hover:bg-blue-500/15 transition-all group"
          >
            <Play className="w-4 h-4" />
            <span className="flex-1 text-left font-medium">Start Investigation Workflow</span>
            <ChevronRight className="w-3.5 h-3.5 opacity-40 group-hover:opacity-70" />
          </button>
        )}

        {/* Approval Gate */}
        {isAtCheckpoint && (
          <button
            onClick={() => setShowApproval(!showApproval)}
            className="w-full flex items-center gap-2.5 p-3 bg-amber-500/10 border border-amber-500/20
                       rounded-xl text-sm text-amber-300 hover:bg-amber-500/15 transition-all animate-pulse group"
          >
            <AlertTriangle className="w-4 h-4" />
            <span className="flex-1 text-left font-medium">Review &amp; Approve →</span>
          </button>
        )}

        {/* Report viewer */}
        {isComplete && (
          <button
            onClick={onViewReport}
            className="w-full flex items-center gap-2.5 p-3 bg-emerald-500/10 border border-emerald-500/20
                       rounded-xl text-sm text-emerald-300 hover:bg-emerald-500/15 transition-all group"
          >
            <FileText className="w-4 h-4" />
            <span className="flex-1 text-left font-medium">View Final Report</span>
            <ChevronRight className="w-3.5 h-3.5 opacity-40 group-hover:opacity-70" />
          </button>
        )}
      </div>

      {/* Inline Approval Gate */}
      {showApproval && isAtCheckpoint && (
        <ApprovalGate
          podId={podId}
          podName={pod?.name}
          onApproved={() => {
            setShowApproval(false);
            lemmaWorkflows.status(podId).then(setWorkflowState).catch(() => {});
          }}
        />
      )}
    </div>
  );
}
