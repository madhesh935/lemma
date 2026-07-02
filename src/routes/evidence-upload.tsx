import { createFileRoute } from "@tanstack/react-router";
import { useState, useCallback, useEffect } from "react";
import { 
  Upload, FileText, Image as ImageIcon, Video, Map, Phone, Eye, 
  CheckCircle2, AlertCircle, X, Loader2, Shield,
  Activity, Fingerprint, Lock, Cpu, Link as LinkIcon, Database,
  Search, ChevronDown, FolderOpen, ArrowRight, UploadCloud, Hourglass, PlayCircle, CheckCircle
} from "lucide-react";
import type { FileRecord, Pod } from "@/types/lemma";
import { Shell } from "@/components/aegis/Shell";
import { StatCard } from "@/components/aegis/StatCard";
import { motion, AnimatePresence } from "framer-motion";
import { lemmaFiles, lemmaPods, lemmaWorkflows } from "@/lib/lemma/index";

export const Route = createFileRoute("/evidence-upload")({
  component: EvidenceUploadPage,
});

const EVIDENCE_TYPES = [
  { id: "cctv_video", icon: <Video className="w-4 h-4" />, label: "CCTV Footage", desc: "Timestamp extraction & object tracking", formats: "MP4, AVI" },
  { id: "autopsy_report", icon: <FileText className="w-4 h-4" />, label: "Autopsy Report", desc: "NLP parsing & PMI estimation", formats: "PDF, DOCX" },
  { id: "witness_statement", icon: <Eye className="w-4 h-4" />, label: "Witness Statement", desc: "Entity & sentiment analysis", formats: "TXT, PDF" },
  { id: "gps_log", icon: <Map className="w-4 h-4" />, label: "GPS Track", desc: "Geospatial path reconstruction", formats: "GPX, JSON" },
  { id: "image", icon: <ImageIcon className="w-4 h-4" />, label: "Crime Scene Image", desc: "EXIF parsing & object detection", formats: "JPG, PNG" },
  { id: "call_detail_record", icon: <Phone className="w-4 h-4" />, label: "Call Detail Records", desc: "Network graph generation", formats: "CSV, XLSX" },
];

function EvidenceUploadPage() {
  const [pods, setPods] = useState<Pod[]>([]);
  const [selectedPodId, setSelectedPodId] = useState("");
  const [searchPod, setSearchPod] = useState("");
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  
  const [files, setFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploaded, setUploaded] = useState<FileRecord[]>([]);
  const [errors, setErrors] = useState<string[]>([]);

  useEffect(() => {
    lemmaPods.list().then(r => {
      setPods(r.pods);
      if (r.pods.length > 0) {
        setSelectedPodId(r.pods[0].pod_id);
      }
    }).catch(() => {});
  }, []);

  const filteredPods = pods.filter(p => 
    p.pod_key.toLowerCase().includes(searchPod.toLowerCase()) || 
    p.name.toLowerCase().includes(searchPod.toLowerCase())
  );

  const selectedPod = pods.find(p => p.pod_id === selectedPodId);

  const addFiles = useCallback((newFiles: FileList | null) => {
    if (!newFiles) return;
    setFiles((prev) => [...prev, ...Array.from(newFiles)]);
  }, []);

  const removeFile = (i: number) => setFiles((p) => p.filter((_, idx) => idx !== i));

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    addFiles(e.dataTransfer.files);
  };

  const handleUpload = async () => {
    if (!selectedPodId || files.length === 0) return;
    setUploading(true);
    setErrors([]);
    try {
      const resp = await lemmaFiles.upload(selectedPodId, files);
      setUploaded((prev) => [...prev, ...resp.uploaded]);
      resp.errors.forEach((e: unknown) => {
        if (typeof e === "object" && e !== null && "error" in e) {
          setErrors((prev) => [...prev, (e as { error: string }).error]);
        }
      });
      lemmaWorkflows.start(selectedPodId).catch(console.error);
      setFiles([]);
    } catch (e) {
      setErrors([String((e as Error).message)]);
    } finally {
      setUploading(false);
    }
  };

  return (
    <Shell>
      <div className="max-w-[1600px] mx-auto p-8 space-y-6 text-white font-sans">
        
        {/* Header */}
        <div className="flex flex-col items-start mb-2">
          <div className="flex items-center gap-2 mb-3">
            <Shield className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-semibold text-white/70 uppercase tracking-wider">Secure Data Ingestion</h2>
            <span className="text-xs text-white/20 ml-auto flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Upload Node Active
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white mb-1">
            Evidence Upload
          </h1>
          <p className="text-sm text-white/50 max-w-3xl">
            Upload forensic evidence into an Investigation Pod with secure chain-of-custody tracking and AI-powered preprocessing.
          </p>
        </div>

        {/* Row 1: Target Pod & Stats */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-8">
            <div className="bg-[#0D1528] border border-[rgba(0,180,255,0.22)] rounded-[18px] p-5 h-full flex flex-col justify-center relative overflow-visible shadow-[0_0_15px_rgba(0,180,255,0.05)]">
              <label className="block text-xs font-bold text-white/50 uppercase tracking-widest mb-3">
                Target Investigation Pod
              </label>
              <div className="relative">
                <div 
                  onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                  className={`w-full px-4 py-3 bg-[#070B17] border rounded-xl flex items-center justify-between cursor-pointer transition-all ${
                    isDropdownOpen || selectedPodId ? 'border-cyan-500/50 shadow-[0_0_10px_rgba(0,180,255,0.2)]' : 'border-white/10 hover:border-white/20'
                  }`}
                >
                  {selectedPod ? (
                    <div className="flex items-center gap-3">
                      <FolderOpen className="w-5 h-5 text-cyan-400" />
                      <div>
                        <div className="text-sm font-semibold text-white">{selectedPod.name}</div>
                        <div className="text-xs font-mono text-cyan-400/60">{selectedPod.pod_key}</div>
                      </div>
                    </div>
                  ) : (
                    <span className="text-white/40 text-sm">Select an active investigation pod...</span>
                  )}
                  <ChevronDown className={`w-5 h-5 text-white/30 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`} />
                </div>

                <AnimatePresence>
                  {isDropdownOpen && (
                    <motion.div 
                      initial={{ opacity: 0, y: -5 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -5 }}
                      className="absolute top-full left-0 right-0 mt-2 bg-[#0D1528] border border-[rgba(0,180,255,0.22)] rounded-xl overflow-hidden z-50 shadow-2xl"
                    >
                      <div className="p-2 border-b border-white/5 flex items-center gap-2 bg-[#070B17]">
                        <Search className="w-4 h-4 text-white/30 ml-2" />
                        <input 
                          type="text"
                          placeholder="Search pods..."
                          value={searchPod}
                          onChange={(e) => setSearchPod(e.target.value)}
                          className="w-full bg-transparent border-none outline-none text-sm text-white placeholder:text-white/30 py-1.5"
                        />
                      </div>
                      <div className="max-h-60 overflow-y-auto">
                        {filteredPods.length === 0 ? (
                          <div className="p-4 text-center text-sm text-white/30">No pods found.</div>
                        ) : (
                          filteredPods.map(p => (
                            <button
                              key={p.pod_id}
                              onClick={() => { setSelectedPodId(p.pod_id); setIsDropdownOpen(false); setSearchPod(""); }}
                              className="w-full text-left p-3 hover:bg-white/[0.03] flex items-center gap-3 border-b border-white/5 last:border-0 transition-colors"
                            >
                              <FolderOpen className="w-4 h-4 text-cyan-400/50" />
                              <div>
                                <div className="text-sm font-medium text-white/90">{p.name}</div>
                                <div className="text-xs font-mono text-white/40">{p.pod_key}</div>
                              </div>
                            </button>
                          ))
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>
          </div>
          
          <div className="lg:col-span-4 grid grid-cols-2 gap-4">
            <StatCard label="Today's Uploads" value={14} icon={UploadCloud} tone="neon-2" sub="across pods" trend="+2 since yesterday" />
            <StatCard label="Chain of Custody" value={89} icon={LinkIcon} tone="success" sub="verified hashes" trend="0 breaches" />
          </div>
        </div>

        {/* Row 2: Upload Area & Evidence Types */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-8 space-y-6">
            
            <div className="bg-[#0D1528] border border-[rgba(0,180,255,0.22)] rounded-[18px] p-6 shadow-[0_0_15px_rgba(0,180,255,0.05)]">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">Upload Evidence</h3>
                <span className="flex items-center gap-1.5 text-xs text-[#00D084] bg-[#00D084]/10 px-2 py-1 rounded-md border border-[#00D084]/20 font-medium">
                  <Shield className="w-3 h-3" /> Chain of Custody Active
                </span>
              </div>

              <div
                onDrop={handleDrop}
                onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                onDragLeave={() => setIsDragging(false)}
                onClick={() => document.getElementById("file-input")?.click()}
                className={`relative border border-dashed rounded-[14px] p-12 text-center transition-all cursor-pointer overflow-hidden group
                  ${isDragging
                    ? "border-[#00C8FF] bg-[#00C8FF]/10 shadow-[0_0_20px_rgba(0,200,255,0.15)]"
                    : "border-[rgba(0,180,255,0.4)] bg-[#070B17] hover:border-[#00C8FF] hover:bg-white/[0.02]"
                  }`}
              >
                <div className="relative z-10 flex flex-col items-center">
                  <div className="w-12 h-12 mb-4 rounded-full bg-[#0D1528] border border-white/10 flex items-center justify-center group-hover:border-[#00C8FF]/50 group-hover:shadow-[0_0_15px_rgba(0,200,255,0.2)] transition-all">
                    <Upload className={`w-5 h-5 ${isDragging ? "text-[#00C8FF]" : "text-white/50 group-hover:text-[#00C8FF]"}`} />
                  </div>
                  <h3 className="text-base font-semibold text-white mb-1">Drag & Drop files here</h3>
                  <p className="text-white/40 text-sm mb-4">or click to browse your local file system</p>
                  <p className="text-[10px] text-white/30 uppercase tracking-widest font-mono">Max file size: 500MB</p>
                </div>
                <input id="file-input" type="file" multiple className="hidden" onChange={(e) => addFiles(e.target.files)} />
              </div>

              {/* Upload Queue & Results */}
              <AnimatePresence>
                {(files.length > 0 || uploaded.length > 0 || errors.length > 0) && (
                  <motion.div 
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    className="mt-6 space-y-4"
                  >
                    {errors.map((e, i) => (
                      <div key={i} className="flex items-center gap-3 p-3 bg-[#FF4D6D]/10 border border-[#FF4D6D]/30 rounded-xl text-[#FF4D6D] text-sm">
                        <AlertCircle className="w-4 h-4 shrink-0" /> {e}
                      </div>
                    ))}

                    <div className="space-y-2">
                      {uploaded.map((r) => (
                        <div key={r.file_id} className="flex items-start gap-4 p-3 bg-[#00D084]/10 border border-[#00D084]/20 rounded-xl">
                          <CheckCircle2 className="w-5 h-5 text-[#00D084] mt-0.5" />
                          <div className="flex-1 min-w-0">
                            <div className="text-sm font-semibold text-white truncate">{r.original_name}</div>
                            <div className="flex items-center gap-3 mt-1 text-[11px] font-mono text-[#00D084]/70">
                              <span className="uppercase">{r.evidence_type.replace(/_/g, " ")}</span>
                              <span><Fingerprint className="w-3 h-3 inline mr-1"/> {r.file_hash.slice(0, 16)}…</span>
                            </div>
                          </div>
                        </div>
                      ))}
                      
                      {files.map((f, i) => (
                        <div key={i} className="flex items-center gap-4 p-3 bg-[#070B17] border border-white/10 rounded-xl group hover:border-white/20 transition-all">
                          <div className="w-8 h-8 rounded bg-white/5 border border-white/10 flex items-center justify-center text-white/50 font-mono text-[10px]">
                            {f.name.split(".").pop()?.toUpperCase() || "FILE"}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="text-sm font-medium text-white/90 truncate">{f.name}</div>
                            <div className="text-[11px] text-white/40 mt-0.5">
                              {f.size > 1024 * 1024 ? `${(f.size / 1024 / 1024).toFixed(1)} MB` : `${Math.round(f.size / 1024)} KB`}
                            </div>
                          </div>
                          <button onClick={() => removeFile(i)} className="p-1.5 rounded hover:bg-white/10 text-white/30 hover:text-white transition-all">
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                    </div>

                    {files.length > 0 && (
                      <button
                        onClick={handleUpload}
                        disabled={uploading || !selectedPodId}
                        className="w-full py-3 mt-2 bg-[#0D1528] border border-[rgba(0,180,255,0.4)] hover:bg-[#00C8FF]/10 text-white font-medium rounded-xl transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-[#0D1528] hover:shadow-[0_0_15px_rgba(0,200,255,0.2)]"
                      >
                        {uploading ? (
                          <><Loader2 className="w-4 h-4 animate-spin text-[#00C8FF]" /> Ingesting...</>
                        ) : !selectedPodId ? (
                          <>
                            <AlertCircle className="w-4 h-4 text-red-400" />
                            Select a Pod to Commit
                          </>
                        ) : (
                          <>
                            <Database className="w-4 h-4 text-[#00C8FF]" /> 
                            Commit {files.length} File{files.length > 1 ? 's' : ''} to Pod
                          </>
                        )}
                      </button>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>

          <div className="lg:col-span-4 space-y-4">
            <h3 className="text-xs font-bold text-white/50 uppercase tracking-widest px-1">Supported Evidence Types</h3>
            <div className="flex flex-col gap-3">
              {EVIDENCE_TYPES.map((type) => (
                <div key={type.id} className="bg-[#0D1528] border border-[rgba(0,180,255,0.15)] rounded-xl p-4 flex items-start gap-3 hover:border-[rgba(0,180,255,0.4)] hover:bg-white/[0.02] transition-all group shadow-sm">
                  <div className="p-2 rounded bg-[#070B17] border border-white/5 text-[#00C8FF] group-hover:shadow-[0_0_10px_rgba(0,200,255,0.2)] transition-all">
                    {type.icon}
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-white/90">{type.label}</div>
                    <div className="text-[11px] text-white/50 mt-1">{type.desc}</div>
                    <div className="text-[10px] font-mono text-[#00C8FF]/50 mt-2 uppercase tracking-wider">{type.formats}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Bottom: Pipeline Horizontal */}
        <div className="bg-[#0D1528] border border-[rgba(0,180,255,0.22)] rounded-[18px] p-5 shadow-[0_0_15px_rgba(0,180,255,0.05)] overflow-hidden relative">
          <h3 className="text-xs font-bold text-white/50 uppercase tracking-widest mb-6">Processing Pipeline</h3>
          <div className="flex items-center justify-between relative px-4">
            <div className="absolute left-10 right-10 top-1/2 -translate-y-1/2 h-px bg-white/10 z-0" />
            <div className="absolute left-10 right-1/2 top-1/2 -translate-y-1/2 h-px bg-[#00C8FF]/50 shadow-[0_0_10px_#00C8FF] z-0" />
            
            {[
              { icon: Upload, label: "Upload" },
              { icon: Fingerprint, label: "Hash Gen" },
              { icon: FileText, label: "OCR" },
              { icon: Cpu, label: "Extraction" },
              { icon: Database, label: "Knowledge" },
              { icon: CheckCircle, label: "Ready" }
            ].map((step, i) => (
              <div key={i} className="relative z-10 flex flex-col items-center gap-3">
                <div className={`w-8 h-8 rounded-full border flex items-center justify-center bg-[#0D1528] ${i < 3 ? 'border-[#00C8FF] text-[#00C8FF] shadow-[0_0_10px_rgba(0,200,255,0.2)]' : 'border-white/20 text-white/30'}`}>
                  <step.icon className="w-3.5 h-3.5" />
                </div>
                <span className={`text-[10px] font-bold uppercase tracking-widest ${i < 3 ? 'text-white' : 'text-white/30'}`}>{step.label}</span>
              </div>
            ))}
          </div>
        </div>

      </div>
    </Shell>
  );
}
