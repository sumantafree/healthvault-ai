"use client";
import { Heart, TrendingUp, ShieldCheck, Bell, Activity, FileSearch, Users } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";

const FEATURES = [
  { icon: Activity,    text: "AI-powered health report analysis",   sub: "Upload PDFs & images, get instant insights" },
  { icon: TrendingUp,  text: "Track metrics over time",             sub: "Visualize trends across all your test results" },
  { icon: Bell,        text: "WhatsApp medicine reminders",         sub: "Never miss a dose with smart alerts" },
  { icon: Users,       text: "Full family health management",       sub: "One place for everyone in the household" },
];

const STATS = [
  { value: "50+", label: "Metrics tracked" },
  { value: "AI", label: "Powered analysis" },
  { value: "256-bit", label: "SSL encrypted" },
];

export default function LoginPage() {
  const { signInWithGoogle, loading } = useAuth();

  return (
    <div className="min-h-screen flex">
      {/* ── Left panel — brand / features (hidden on mobile) ── */}
      <div className="hidden lg:flex lg:w-1/2 xl:w-3/5 bg-gradient-brand relative overflow-hidden flex-col justify-between p-10">
        {/* Background decoration */}
        <div className="absolute inset-0 bg-grid opacity-10" />
        <div className="absolute -top-32 -left-32 w-96 h-96 rounded-full bg-white/10 blur-3xl" />
        <div className="absolute -bottom-32 -right-32 w-96 h-96 rounded-full bg-white/10 blur-3xl" />

        {/* Logo */}
        <div className="relative z-10 flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-white/20 backdrop-blur-sm border border-white/30 flex items-center justify-center">
            <Heart className="w-5 h-5 text-white" />
          </div>
          <div>
            <p className="text-white font-bold text-lg leading-tight">HealthVault AI</p>
            <p className="text-white/60 text-xs">Family Health Intelligence</p>
          </div>
        </div>

        {/* Main copy */}
        <div className="relative z-10 flex-1 flex flex-col justify-center py-12">
          <h1 className="text-4xl xl:text-5xl font-bold text-white leading-tight mb-4 text-balance">
            Your family's health,<br />intelligently managed.
          </h1>
          <p className="text-white/75 text-lg leading-relaxed mb-10 max-w-md">
            Upload lab reports, track metrics over time, and receive AI-powered insights — all in one secure platform.
          </p>

          {/* Feature list */}
          <div className="space-y-4">
            {FEATURES.map(({ icon: Icon, text, sub }) => (
              <div key={text} className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-xl bg-white/15 border border-white/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Icon className="w-4 h-4 text-white" />
                </div>
                <div>
                  <p className="text-white font-medium text-sm">{text}</p>
                  <p className="text-white/55 text-xs mt-0.5">{sub}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Stats bar */}
        <div className="relative z-10 flex gap-6">
          {STATS.map(({ value, label }) => (
            <div key={label}>
              <p className="text-white text-xl font-bold">{value}</p>
              <p className="text-white/55 text-xs">{label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ── Right panel — auth card ── */}
      <div className="flex-1 flex items-center justify-center p-6 bg-surface-subtle">
        <div className="w-full max-w-sm">
          {/* Mobile logo */}
          <div className="flex flex-col items-center mb-8 lg:hidden">
            <div className="w-14 h-14 rounded-2xl bg-gradient-brand flex items-center justify-center shadow-lg mb-4">
              <Heart className="w-7 h-7 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-text-primary">HealthVault AI</h1>
            <p className="text-sm text-text-secondary mt-1 text-center">Family Health Intelligence Platform</p>
          </div>

          {/* Card */}
          <div className="bg-white rounded-2xl shadow-card-hover border border-surface-border p-8">
            <div className="mb-6">
              <h2 className="text-xl font-bold text-text-primary">Welcome back</h2>
              <p className="text-sm text-text-secondary mt-1">Sign in to access your health dashboard.</p>
            </div>

            {/* Google button */}
            <button
              onClick={signInWithGoogle}
              disabled={loading}
              className="w-full flex items-center justify-center gap-3 h-12 px-5 rounded-xl border border-surface-border bg-white hover:bg-surface-subtle active:scale-98 transition-all shadow-xs text-sm font-medium text-text-primary disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {loading ? (
                <div className="w-5 h-5 rounded-full border-2 border-surface-border border-t-brand-blue animate-spin" />
              ) : (
                <svg viewBox="0 0 24 24" className="w-5 h-5 flex-shrink-0">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                </svg>
              )}
              Continue with Google
            </button>

            {/* Divider */}
            <div className="flex items-center gap-3 my-6">
              <div className="flex-1 h-px bg-surface-border" />
              <span className="text-xs text-text-muted">Secured by Supabase Auth</span>
              <div className="flex-1 h-px bg-surface-border" />
            </div>

            {/* Trust badges */}
            <div className="flex items-center justify-center gap-4">
              <div className="flex items-center gap-1.5 text-xs text-text-muted">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                HIPAA-ready
              </div>
              <div className="w-px h-3 bg-surface-border" />
              <div className="flex items-center gap-1.5 text-xs text-text-muted">
                <FileSearch className="w-3.5 h-3.5 text-blue-500" />
                End-to-end encrypted
              </div>
            </div>
          </div>

          <p className="text-center text-[11px] text-text-muted mt-5 leading-relaxed">
            By signing in you agree to our{" "}
            <span className="underline underline-offset-2 cursor-pointer">Terms of Service</span>
            {" "}and{" "}
            <span className="underline underline-offset-2 cursor-pointer">Privacy Policy</span>.
          </p>
        </div>
      </div>
    </div>
  );
}
