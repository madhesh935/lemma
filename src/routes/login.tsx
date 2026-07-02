import { createFileRoute, redirect, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { Shield, Eye, EyeOff, Lock, User, AlertCircle, Loader2 } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";

export const Route = createFileRoute("/login")({
  component: LoginPage,
  beforeLoad: ({ context }) => {
    // Redirect to dashboard if already logged in
    // Uncomment when auth is enforced:
    // const { isAuthenticated } = useAuthStore.getState();
    // if (isAuthenticated) throw redirect({ to: "/" });
  },
});

const DEMO_ACCOUNTS = [
  { label: "Admin", email: "admin@aegis.gov", password: "Admin@aegis123", role: "admin" },
];

function LoginPage() {
  const navigate = useNavigate();
  const { login, isLoading, error, clearError } = useAuthStore();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(email, password);
      navigate({ to: "/" });
    } catch {}
  };

  const fillDemo = (acc: typeof DEMO_ACCOUNTS[0]) => {
    setEmail(acc.email);
    setPassword(acc.password);
    clearError();
  };

  return (
    <div className="min-h-screen flex bg-[#0a0e1a]">
      {/* Left panel — Branding */}
      <div className="hidden lg:flex flex-col justify-between w-[480px] bg-gradient-to-br from-[#0d1530] to-[#0a0e1a] border-r border-white/5 p-12">
        <div>
          <div className="flex items-center gap-3 mb-12">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="text-white font-bold text-lg">AEGIS-OS</div>
              <div className="text-blue-400/70 text-xs">Forensic Intelligence Platform</div>
            </div>
          </div>

          <h1 className="text-4xl font-bold text-white mb-4 leading-tight">
            AI-Powered<br />
            <span className="bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">
              Forensic Triage
            </span><br />
            Platform
          </h1>
          <p className="text-white/50 text-sm leading-relaxed">
            Multi-agent AI orchestration for digital forensic investigation.
            Powered by Lemma SDK — 8 specialized agents, 15 forensic functions.
          </p>
        </div>

        <div className="space-y-4">
          {[
            { icon: "🔬", label: "Autopsy Intelligence", desc: "AI-parsed postmortem analysis" },
            { icon: "🗺️", label: "Spatial Intelligence", desc: "GPS + CCTV movement reconstruction" },
            { icon: "⚠️", label: "Risk Assessment", desc: "Real-time threat prioritization" },
          ].map((f) => (
            <div key={f.label} className="flex items-start gap-3 p-3 rounded-lg bg-white/[0.03] border border-white/5">
              <span className="text-xl">{f.icon}</span>
              <div>
                <div className="text-white/80 text-sm font-medium">{f.label}</div>
                <div className="text-white/40 text-xs">{f.desc}</div>
              </div>
            </div>
          ))}
        </div>

        <div className="text-white/20 text-xs">
          v3.0.0 · Lemma SDK · Gappy AI Hackathon 2026
        </div>
      </div>

      {/* Right panel — Login form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="flex items-center gap-3 mb-8 lg:hidden">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div className="text-white font-bold text-xl">AEGIS-OS</div>
          </div>

          <div className="mb-8">
            <h2 className="text-2xl font-bold text-white mb-1">Sign in</h2>
            <p className="text-white/40 text-sm">Access the forensic intelligence platform</p>
          </div>

          {/* Demo accounts removed as requested */}

          <form onSubmit={handleLogin} className="space-y-4">
            {/* Email */}
            <div>
              <label className="block text-sm text-white/50 mb-1.5">Email Address</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="officer@aegis.gov"
                  required
                  className="w-full pl-10 pr-4 py-3 bg-white/[0.05] border border-white/10 rounded-xl
                             text-white placeholder-white/20 text-sm
                             focus:outline-none focus:border-blue-500/50 focus:bg-white/[0.07]
                             transition-all"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm text-white/50 mb-1.5">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full pl-10 pr-12 py-3 bg-white/[0.05] border border-white/10 rounded-xl
                             text-white placeholder-white/20 text-sm
                             focus:outline-none focus:border-blue-500/50 focus:bg-white/[0.07]
                             transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
                <span className="text-red-300 text-sm">{error}</span>
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 px-4 bg-gradient-to-r from-blue-600 to-cyan-600 text-white font-semibold
                         rounded-xl hover:from-blue-500 hover:to-cyan-500 transition-all
                         disabled:opacity-50 disabled:cursor-not-allowed
                         flex items-center justify-center gap-2 text-sm"
            >
              {isLoading ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Authenticating...</>
              ) : (
                <>
                  <Shield className="w-4 h-4" />
                  Sign In to AEGIS-OS
                </>
              )}
            </button>
          </form>

          <div className="mt-8 p-4 bg-amber-500/5 border border-amber-500/10 rounded-xl">
            <p className="text-amber-300/60 text-xs leading-relaxed">
              <span className="font-semibold">⚠️ Authorized Personnel Only.</span>{" "}
              Unauthorized access to this system is a criminal offense under the IT Act 2000.
              All sessions are logged and monitored.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
