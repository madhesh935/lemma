/**
 * AEGIS-OS — Agent Status Grid
 * Shows live status of all 8 Lemma agents
 */
import { useState, useEffect } from "react";
import { lemmaAgents } from "@/lib/lemma/index";
import type { AgentInfo, AgentJob } from "@/types/lemma";
import { Bot, CheckCircle2, Loader2, XCircle, Clock, Zap } from "lucide-react";
import { motion } from "framer-motion";

const AGENT_META: Record<string, { emoji: string; color: string; desc: string }> = {
  evidence_intake:       { emoji: "📁", color: "from-blue-500/20 to-blue-600/10 border-blue-500/20",   desc: "OCR · Entity Extraction · Classification" },
  autopsy_intelligence:  { emoji: "🔬", color: "from-red-500/20 to-red-600/10 border-red-500/20",     desc: "Autopsy Parse · PMI Estimation" },
  digital_correlation:   { emoji: "📡", color: "from-cyan-500/20 to-cyan-600/10 border-cyan-500/20",  desc: "GPS · CDR · CCTV Fusion" },
  timeline_reconstruction:{ emoji: "⏱️", color: "from-purple-500/20 to-purple-600/10 border-purple-500/20", desc: "Chronology · Conflict Detection" },
  knowledge_graph:       { emoji: "🕸️", color: "from-green-500/20 to-green-600/10 border-green-500/20", desc: "Neo4j · Relationship Mapping" },
  hypothesis:            { emoji: "💡", color: "from-yellow-500/20 to-yellow-600/10 border-yellow-500/20", desc: "Multi-Hypothesis Generation" },
  risk_assessment:       { emoji: "⚠️", color: "from-orange-500/20 to-orange-600/10 border-orange-500/20", desc: "Scoring · Anomaly Detection" },
  report:                { emoji: "📋", color: "from-indigo-500/20 to-indigo-600/10 border-indigo-500/20", desc: "Report Generation · Approval" },
};

const STATUS_CONFIG = {
  ready:     { icon: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />, label: "Ready",    badge: "bg-emerald-400/10 text-emerald-400" },
  running:   { icon: <Loader2 className="w-3.5 h-3.5 text-blue-400 animate-spin" />, label: "Running", badge: "bg-blue-400/10 text-blue-400" },
  completed: { icon: <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" />, label: "Done",    badge: "bg-cyan-400/10 text-cyan-400" },
  failed:    { icon: <XCircle className="w-3.5 h-3.5 text-red-400" />, label: "Failed",   badge: "bg-red-400/10 text-red-400" },
  idle:      { icon: <Clock className="w-3.5 h-3.5 text-white/20" />, label: "Idle",     badge: "bg-white/5 text-white/30" },
};

interface AgentStatusGridProps {
  podId?: string;
  compact?: boolean;
}

export function AgentStatusGrid({ podId, compact = false }: AgentStatusGridProps) {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [jobs, setJobs] = useState<AgentJob[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    lemmaAgents.list()
      .then((r) => setAgents(r.agents))
      .catch(() => {
        // Offline fallback — show default agents
        setAgents(Object.keys(AGENT_META).map((name) => ({
          name,
          description: AGENT_META[name].desc,
          version: "1.0.0",
          status: "idle" as const,
        })));
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!podId) return;
    lemmaAgents.history(podId).then((r) => setJobs(r.jobs)).catch(() => {});
  }, [podId]);

  // Merge agent list with latest job statuses
  const agentStatuses = agents.map((a) => {
    const latestJob = jobs
      .filter((j) => j.agent_name === a.name)
      .sort((x, y) => (y.job_id > x.job_id ? 1 : -1))[0];
    const status = latestJob?.status === "running" ? "running"
      : latestJob?.status === "completed" ? "completed"
      : latestJob?.status === "failed" ? "failed"
      : "idle";
    return { ...a, jobStatus: status, lastJob: latestJob };
  });

  if (loading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="h-20 rounded-xl bg-white/[0.03] border border-white/5 animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className={compact ? "grid grid-cols-4 gap-2" : "grid grid-cols-2 lg:grid-cols-4 gap-3"}>
      {agentStatuses.map((agent, i) => {
        const meta = AGENT_META[agent.name] || { emoji: "🤖", color: "from-white/5 to-white/5 border-white/10", desc: "" };
        const statusCfg = STATUS_CONFIG[agent.jobStatus as keyof typeof STATUS_CONFIG] || STATUS_CONFIG.idle;

        return (
          <motion.div
            key={agent.name}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.04 }}
            className={`p-3 rounded-xl border bg-gradient-to-br ${meta.color} transition-all hover:scale-[1.02] cursor-default`}
          >
            <div className="flex items-start justify-between mb-2">
              <span className="text-xl">{meta.emoji}</span>
              <span className={`flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-medium ${statusCfg.badge}`}>
                {statusCfg.icon}
                {statusCfg.label}
              </span>
            </div>
            <div className="text-xs font-semibold text-white/80 leading-tight mb-0.5">
              {agent.name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
            </div>
            {!compact && (
              <div className="text-[10px] text-white/30 leading-snug">{meta.desc}</div>
            )}
            {agent.lastJob?.duration_seconds && (
              <div className="flex items-center gap-1 mt-1.5 text-[10px] text-white/20">
                <Zap className="w-2.5 h-2.5" />
                {agent.lastJob.duration_seconds.toFixed(1)}s
              </div>
            )}
          </motion.div>
        );
      })}
    </div>
  );
}
