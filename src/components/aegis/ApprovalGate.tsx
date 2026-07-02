/**
 * AEGIS-OS — Human Approval Gate
 * Critical checkpoint requiring investigator sign-off before report generation
 */
import { useState } from "react";
import { lemmaWorkflows } from "@/lib/lemma/index";
import type { ReportType } from "@/types/lemma";
import { motion } from "framer-motion";
import { AlertTriangle, Shield, CheckCircle2, FileText, Loader2, ChevronDown } from "lucide-react";

const REPORT_TYPES: { value: ReportType; label: string; desc: string }[] = [
  { value: "executive",      label: "Executive Summary",    desc: "High-level brief for senior officers" },
  { value: "investigator",   label: "Investigator Report",  desc: "Full technical report with evidence chain" },
  { value: "court",          label: "Court-Ready Summary",  desc: "Legal proceedings document (requires legal review)" },
  { value: "evidence_index", label: "Evidence Index",       desc: "Full evidence catalogue with hashes" },
];

interface ApprovalGateProps {
  podId: string;
  podName?: string;
  onApproved?: () => void;
  className?: string;
}

export function ApprovalGate({ podId, podName, onApproved, className = "" }: ApprovalGateProps) {
  const [reportType, setReportType] = useState<ReportType>("investigator");
  const [showTypeMenu, setShowTypeMenu] = useState(false);
  const [approving, setApproving] = useState(false);
  const [approved, setApproved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmCheck, setConfirmCheck] = useState(false);

  const selected = REPORT_TYPES.find((r) => r.value === reportType)!;

  const handleApprove = async () => {
    if (!confirmCheck) {
      setError("Please confirm you have reviewed all findings before approving.");
      return;
    }
    setApproving(true);
    setError(null);
    try {
      await lemmaWorkflows.approve(podId, reportType);
      setApproved(true);
      onApproved?.();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setApproving(false);
    }
  };

  if (approved) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className={`p-5 bg-emerald-500/10 border border-emerald-500/20 rounded-xl ${className}`}
      >
        <div className="flex items-center gap-3">
          <CheckCircle2 className="w-6 h-6 text-emerald-400" />
          <div>
            <div className="font-semibold text-emerald-300">Approved — Generating Report</div>
            <div className="text-sm text-emerald-300/60 mt-0.5">
              {selected.label} is being generated. You will be notified when ready.
            </div>
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`p-5 bg-amber-500/5 border border-amber-500/20 rounded-xl ${className}`}
    >
      {/* Header */}
      <div className="flex items-start gap-3 mb-4">
        <div className="w-9 h-9 rounded-lg bg-amber-500/10 flex items-center justify-center shrink-0">
          <AlertTriangle className="w-4.5 h-4.5 text-amber-400" />
        </div>
        <div>
          <h3 className="font-semibold text-white text-sm">Investigator Review Required</h3>
          <p className="text-xs text-white/40 mt-0.5 leading-relaxed">
            Automated analysis is complete for{" "}
            <span className="text-white/60">{podName || podId}</span>.
            Review all findings before approving report generation.
          </p>
        </div>
      </div>

      {/* Review checklist */}
      <div className="mb-4 space-y-1.5">
        {[
          "Reviewed all evidence items and OCR extractions",
          "Verified timeline events and resolved conflicts",
          "Assessed all generated hypotheses",
          "Confirmed risk score and anomaly flags",
          "Checked knowledge graph for accuracy",
        ].map((item, i) => (
          <div key={i} className="flex items-center gap-2 text-xs text-white/40">
            <CheckCircle2 className="w-3 h-3 text-white/20 shrink-0" />
            {item}
          </div>
        ))}
      </div>

      {/* Report type selector */}
      <div className="mb-4">
        <label className="block text-xs text-white/40 mb-1.5">Report Type</label>
        <div className="relative">
          <button
            onClick={() => setShowTypeMenu(!showTypeMenu)}
            className="w-full flex items-center justify-between px-3 py-2.5 bg-white/5 border border-white/10
                       rounded-lg text-sm text-white hover:border-white/20 transition-all"
          >
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-white/30" />
              {selected.label}
            </div>
            <ChevronDown className={`w-4 h-4 text-white/30 transition-transform ${showTypeMenu ? "rotate-180" : ""}`} />
          </button>
          {showTypeMenu && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-[#0d1530] border border-white/10 rounded-lg overflow-hidden z-20 shadow-xl">
              {REPORT_TYPES.map((rt) => (
                <button
                  key={rt.value}
                  onClick={() => { setReportType(rt.value); setShowTypeMenu(false); }}
                  className={`w-full text-left px-3 py-2.5 hover:bg-white/5 transition-colors ${
                    rt.value === reportType ? "bg-blue-500/10" : ""
                  }`}
                >
                  <div className="text-sm text-white/80">{rt.label}</div>
                  <div className="text-xs text-white/30">{rt.desc}</div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Confirmation checkbox */}
      <label className="flex items-start gap-2.5 mb-4 cursor-pointer group">
        <div
          onClick={() => setConfirmCheck(!confirmCheck)}
          className={`w-4 h-4 rounded border mt-0.5 flex items-center justify-center shrink-0 transition-all cursor-pointer ${
            confirmCheck
              ? "bg-blue-500 border-blue-500"
              : "border-white/20 bg-white/5 group-hover:border-white/40"
          }`}
        >
          {confirmCheck && <CheckCircle2 className="w-3 h-3 text-white" />}
        </div>
        <span className="text-xs text-white/50 leading-relaxed select-none">
          I confirm that I have reviewed all AI-generated findings and they are consistent with my investigation.
          I understand this will generate a <strong className="text-white/70">{selected.label}</strong> requiring final approval.
        </span>
      </label>

      {/* Error */}
      {error && (
        <div className="mb-3 p-2.5 bg-red-500/10 border border-red-500/20 rounded-lg text-xs text-red-300">
          {error}
        </div>
      )}

      {/* Approve button */}
      <button
        onClick={handleApprove}
        disabled={approving}
        className="w-full py-2.5 px-4 bg-gradient-to-r from-amber-600 to-orange-600 text-white font-semibold
                   rounded-lg hover:from-amber-500 hover:to-orange-500 transition-all text-sm
                   disabled:opacity-50 disabled:cursor-not-allowed
                   flex items-center justify-center gap-2"
      >
        {approving ? (
          <><Loader2 className="w-4 h-4 animate-spin" /> Approving…</>
        ) : (
          <><Shield className="w-4 h-4" /> Approve &amp; Generate Report</>
        )}
      </button>

      <div className="mt-3 text-center text-[10px] text-white/20">
        This action is logged. Your badge number and timestamp will be recorded.
      </div>
    </motion.div>
  );
}
