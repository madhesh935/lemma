import { Link } from "@tanstack/react-router";
import { cases, type Severity } from "@/data/data";
import { ChevronRight, ShieldAlert, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { lemmaPods } from "@/lib/lemma/index";
import type { Pod } from "@/types/lemma";

const sevColor: Record<Severity, string> = {
  low:      "bg-success/15 text-success border-success/30",
  medium:   "bg-warn/15 text-warn border-warn/30",
  high:     "bg-danger/15 text-danger border-danger/30",
  critical: "bg-danger/25 text-danger border-danger/50 animate-pulse-ring-danger",
};

export function CaseTable() {
  const [pods, setPods] = useState<Pod[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    lemmaPods.list()
      .then((r) => {
        if (r.pods && r.pods.length > 0) {
          setPods(r.pods);
        } else {
          setPods([]);
        }
      })
      .catch(() => {
        setPods([]);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  // Use dynamic backend pods if available, fallback to mock data otherwise
  const displayCases = pods.length > 0 
    ? pods.map((p) => ({
        id: p.pod_id,
        fir: p.pod_key,
        title: p.name,
        district: p.district || "Chennai",
        status: p.status === "active" ? "Active" : "Closed",
        severity: (p.severity as Severity) || "medium",
        aiConfidence: p.pod_id === "C-2041" ? 87 : 70, // contextual mock conf
        flagged: p.severity === "critical" || p.severity === "high",
        officer: p.investigators?.[0] || "Insp. R. Karthik",
        type: "Homicide",
      }))
    : cases;

  return (
    <div className="glass overflow-hidden rounded-xl">
      <div className="flex items-center justify-between border-b border-border/40 px-4 py-3">
        <div className="text-[11px] uppercase tracking-widest text-muted-foreground">Active Investigations</div>
        <div className="text-[10px] text-muted-foreground flex items-center gap-2">
          {loading ? (
            <span className="flex items-center gap-1.5 text-xs text-[#00C8FF]">
              <Loader2 className="w-3 h-3 animate-spin" /> Fetching Live API...
            </span>
          ) : pods.length > 0 ? (
            <span className="text-[#00D084] font-semibold">● Live API connected ({displayCases.length} cases)</span>
          ) : (
            <span className="text-white/40">{displayCases.length} cases · offline mode</span>
          )}
        </div>
      </div>
      <table className="w-full text-sm">
        <thead className="text-left text-[11px] uppercase tracking-wider text-muted-foreground">
          <tr className="[&>th]:px-4 [&>th]:py-2.5 [&>th]:font-medium">
            <th>Case</th><th>District</th><th>Type</th><th>Severity</th><th>AI Conf.</th><th>Officer</th><th></th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border/40">
          {displayCases.map((c) => (
            <tr key={c.id} className="group transition hover:bg-primary/5">
              <td className="px-4 py-3">
                <div className="flex items-center gap-2 font-medium">
                  {c.flagged && <ShieldAlert className="h-3.5 w-3.5 text-danger" />}
                  {c.title}
                </div>
                <div className="text-[11px] text-muted-foreground">{c.id} · {c.fir}</div>
              </td>
              <td className="px-4 py-3 text-muted-foreground">{c.district}</td>
              <td className="px-4 py-3 text-muted-foreground">{c.type}</td>
              <td className="px-4 py-3">
                <span className={`rounded-md border px-2 py-0.5 text-[10px] uppercase tracking-wider ${sevColor[c.severity as Severity] || "border-white/10"}`}>{c.severity}</span>
              </td>
              <td className="px-4 py-3">
                <div className="flex items-center gap-2">
                  <div className="h-1.5 w-20 overflow-hidden rounded bg-secondary">
                    <div className="h-full bg-gradient-to-r from-primary to-neon-2" style={{ width: `${c.aiConfidence}%` }} />
                  </div>
                  <span className="font-mono text-xs">{c.aiConfidence}%</span>
                </div>
              </td>
              <td className="px-4 py-3 text-muted-foreground">{c.officer}</td>
              <td className="px-4 py-3 text-right">
                <Link
                  to="/cases/$caseId"
                  params={{ caseId: c.id }}
                  className="inline-flex items-center gap-1 rounded-md border border-border/60 bg-secondary/40 px-2 py-1 text-[11px] text-muted-foreground transition group-hover:border-primary/60 group-hover:text-primary"
                >
                  Open <ChevronRight className="h-3 w-3" />
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
