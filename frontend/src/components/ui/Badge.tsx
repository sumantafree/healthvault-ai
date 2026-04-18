import { cn } from "@/lib/utils";
import type { RiskLevel, MetricStatus } from "@/types";
import { RISK_CONFIG, METRIC_STATUS_CONFIG } from "@/types";

export function RiskBadge({ level }: { level: RiskLevel }) {
  const cfg = RISK_CONFIG[level];
  const dot = {
    low:      "bg-emerald-500",
    moderate: "bg-amber-500",
    high:     "bg-red-500",
    critical: "bg-red-700",
  }[level];
  return (
    <span className={cn(
      "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border",
      cfg.bg, cfg.color, cfg.border
    )}>
      <span className={cn("w-1.5 h-1.5 rounded-full", dot)} />
      {cfg.label}
    </span>
  );
}

export function MetricStatusBadge({ status }: { status: MetricStatus }) {
  const cfg = METRIC_STATUS_CONFIG[status];
  const bgMap: Record<MetricStatus, string> = {
    normal:        "bg-emerald-50 text-emerald-700",
    borderline:    "bg-amber-50 text-amber-700",
    abnormal_low:  "bg-red-50 text-red-600",
    abnormal_high: "bg-red-50 text-red-600",
  };
  return (
    <span className={cn(
      "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold",
      bgMap[status]
    )}>
      <span className={cn("w-1.5 h-1.5 rounded-full flex-shrink-0", cfg.dot)} />
      {cfg.label}
    </span>
  );
}

export function StatusPill({
  label,
  variant,
  dot = false,
}: {
  label: string;
  variant: "default" | "success" | "warning" | "error" | "info" | "purple";
  dot?: boolean;
}) {
  const styles = {
    default: "bg-slate-100 text-slate-600",
    success: "bg-emerald-50 text-emerald-700",
    warning: "bg-amber-50 text-amber-700",
    error:   "bg-red-50 text-red-600",
    info:    "bg-blue-50 text-blue-700",
    purple:  "bg-violet-50 text-violet-700",
  };
  const dots = {
    default: "bg-slate-400",
    success: "bg-emerald-500",
    warning: "bg-amber-500",
    error:   "bg-red-500",
    info:    "bg-blue-500",
    purple:  "bg-violet-500",
  };
  return (
    <span className={cn("inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium", styles[variant])}>
      {dot && <span className={cn("w-1.5 h-1.5 rounded-full flex-shrink-0", dots[variant])} />}
      {label}
    </span>
  );
}
