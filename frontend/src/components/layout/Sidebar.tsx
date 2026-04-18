"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, FileText, TrendingUp, Lightbulb,
  Users, LogOut, Heart, Pill, X, Activity,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import { useSidebarStore } from "@/store/sidebar";

const NAV_ITEMS = [
  { href: "/dashboard",     label: "Dashboard",   icon: LayoutDashboard, color: "text-blue-500"   },
  { href: "/reports",       label: "Reports",     icon: FileText,        color: "text-violet-500" },
  { href: "/metrics",       label: "Trends",      icon: TrendingUp,      color: "text-teal-500"   },
  { href: "/insights",      label: "AI Insights", icon: Lightbulb,       color: "text-amber-500"  },
  { href: "/prescriptions", label: "Medicines",   icon: Pill,            color: "text-green-500"  },
  { href: "/family",        label: "Family",      icon: Users,           color: "text-pink-500"   },
];

function SidebarContent({ onClose }: { onClose?: () => void }) {
  const pathname = usePathname();
  const { signOut, user } = useAuth();

  return (
    <div className="flex flex-col h-full">
      {/* ── Brand ── */}
      <div className="flex items-center justify-between px-5 py-5">
        <Link href="/dashboard" className="flex items-center gap-3" onClick={onClose}>
          <div className="w-9 h-9 rounded-xl bg-gradient-brand flex items-center justify-center shadow-sm flex-shrink-0">
            <Heart className="w-4.5 h-4.5 text-white" style={{ width: 18, height: 18 }} />
          </div>
          <div>
            <p className="text-sm font-bold text-text-primary leading-tight">HealthVault</p>
            <p className="text-[10px] text-text-muted font-medium">AI Platform</p>
          </div>
        </Link>
        {/* Mobile close button */}
        {onClose && (
          <button
            onClick={onClose}
            className="lg:hidden p-1.5 rounded-lg hover:bg-surface-muted text-text-muted"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* ── Divider ── */}
      <div className="mx-4 h-px bg-surface-border" />

      {/* ── Nav ── */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto scrollbar-none">
        <p className="text-[10px] font-semibold text-text-muted uppercase tracking-widest px-3 mb-3">
          Navigation
        </p>
        {NAV_ITEMS.map(({ href, label, icon: Icon, color }) => {
          const active = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              onClick={onClose}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150",
                active
                  ? "nav-active"
                  : "text-text-secondary hover:bg-surface-muted hover:text-text-primary"
              )}
            >
              <span className={cn(
                "flex items-center justify-center w-7 h-7 rounded-lg transition-colors",
                active ? "bg-white/20" : "bg-surface-muted"
              )}>
                <Icon className={cn("w-3.5 h-3.5", active ? "text-white" : color)} />
              </span>
              {label}
            </Link>
          );
        })}
      </nav>

      {/* ── Footer ── */}
      <div className="p-3 border-t border-surface-border space-y-1">
        {/* User info */}
        {user && (
          <div className="flex items-center gap-2.5 px-3 py-2.5 rounded-xl bg-surface-subtle border border-surface-border mb-2">
            <div className="w-7 h-7 rounded-full bg-gradient-brand flex items-center justify-center flex-shrink-0">
              <span className="text-[10px] font-bold text-white">
                {(user.user_metadata?.full_name ?? user.email ?? "U").charAt(0).toUpperCase()}
              </span>
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold text-text-primary truncate leading-tight">
                {user.user_metadata?.full_name ?? "User"}
              </p>
              <p className="text-[10px] text-text-muted truncate">{user.email}</p>
            </div>
          </div>
        )}
        <button
          onClick={signOut}
          className="flex items-center gap-2.5 w-full px-3 py-2.5 rounded-xl text-sm font-medium text-text-secondary hover:bg-red-50 hover:text-red-600 transition-colors"
        >
          <span className="flex items-center justify-center w-7 h-7 rounded-lg bg-surface-muted">
            <LogOut className="w-3.5 h-3.5" />
          </span>
          Sign Out
        </button>
      </div>
    </div>
  );
}

export function Sidebar() {
  const { open, close } = useSidebarStore();

  return (
    <>
      {/* Desktop sidebar — always visible */}
      <aside className="hidden lg:flex fixed left-0 top-0 h-full w-[260px] bg-white border-r border-surface-border flex-col z-40">
        <SidebarContent />
      </aside>

      {/* Mobile overlay */}
      {open && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/40 backdrop-blur-sm animate-fade-in"
            onClick={close}
          />
          {/* Drawer */}
          <aside className="relative w-[260px] bg-white h-full shadow-modal flex flex-col animate-slide-in">
            <SidebarContent onClose={close} />
          </aside>
        </div>
      )}
    </>
  );
}
