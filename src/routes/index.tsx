import { createFileRoute } from "@tanstack/react-router";
import { Shell } from "@/components/aegis/Shell";
import { StatCard } from "@/components/aegis/StatCard";
import { RiskMap } from "@/components/aegis/RiskMap";
import { LiveFeed } from "@/components/aegis/LiveFeed";
import { CaseTable } from "@/components/aegis/CaseTable";
import { AgentStatusGrid } from "@/components/aegis/AgentStatusGrid";
import {
  FolderOpen, ShieldAlert, Stethoscope, Sparkles, AlertTriangle, FileQuestion, Bot
} from "lucide-react";
import { useEffect, useState } from "react";
import { fetchStats, type StatsResponse } from "@/lib/api";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "AEGIS-OS — Forensic Command Center" },
      { name: "description", content: "AI-powered forensic triage & Lemma SDK multi-agent investigation platform." },
    ],
  }),
  component: Index,
});

function Index() {
  const [stats, setStats] = useState<StatsResponse | null>(null);

  useEffect(() => {
    fetchStats()
      .then(setStats)
      .catch(() => { /* backend offline — keep static values */ });
  }, []);

  return (
    <Shell>
      <div className="space-y-5 p-5">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold tracking-wider text-white uppercase">Command Dashboard</h1>
          <div className="text-xs text-white/30 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Lemma SDK · 8 Agents Active
          </div>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-6">
          <StatCard label="Active Cases"     value={stats?.active_cases     ?? 142} icon={FolderOpen}    sub="↑ 8 today"     trend="+5.2% vs week" />
          <StatCard label="High Risk Cases"  value={stats?.high_risk        ?? 37}  icon={ShieldAlert}   tone="danger"  sub="3 critical"   trend="2 escalated" />
          <StatCard label="Total Autopsies"  value={stats?.total_autopsies  ?? 19}  icon={Stethoscope}   tone="warn"    sub="in dataset"   trend="avg 36h" />
          <StatCard label="AI Flagged"       value={stats?.ai_flagged       ?? 26}  icon={Sparkles}      tone="neon-2"  sub="auto-tagged"  trend="confidence ↑" />
          <StatCard label="Contradictions"   value={stats?.contradictions   ?? 58}  icon={AlertTriangle} tone="danger"  sub="across cases" trend="3 new today" />
          <StatCard label="Missing Evidence" value={stats?.missing_evidence ?? 11}  icon={FileQuestion}  tone="warn"    sub="DNA / CCTV"   trend="2 requested" />
        </div>

        {/* Maps + Feed */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <div className="lg:col-span-2"><RiskMap /></div>
          <LiveFeed />
        </div>

        {/* Lemma SDK — Agent Status */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Bot className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-semibold text-white/70 uppercase tracking-wider">AI Agent Fleet</h2>
            <span className="text-xs text-white/20 ml-auto">Lemma SDK v1.0.0 · 8 Agents · 15 Functions</span>
          </div>
          <AgentStatusGrid />
        </div>

        {/* Case Table */}
        <div>
          <CaseTable />
        </div>
      </div>
    </Shell>
  );
}

