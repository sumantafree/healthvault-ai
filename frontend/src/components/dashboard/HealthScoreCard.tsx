"use client";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { RiskBadge } from "@/components/ui/Badge";
import type { RiskLevel } from "@/types";
import { cn } from "@/lib/utils";

interface HealthScoreCardProps {
  score: number;
  riskLevel: RiskLevel;
  totalMetrics: number;
  abnormalCount: number;
  loading?: boolean;
}

export function HealthScoreCard({ score, riskLevel, totalMetrics, abnormalCount, loading }: HealthScoreCardProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-card border border-surface-border shadow-card p-5 space-y-4">
        <div className="h-3 w-20 skeleton" />
        <div className="flex justify-center">
          <div className="w-32 h-32 rounded-full skeleton" />
        </div>
        <div className="h-3 w-28 skeleton mx-auto" />
      </div>
    );
  }

  const normalCount = totalMetrics - abnormalCount;
  const pct = totalMetrics === 0 ? 0 : score;

  // Ring geometry
  const r = 44;
  const cx = 56;
  const cy = 56;
  const circ = 2 * Math.PI * r;
  const offset = circ - (pct / 100) * circ;

  const strokeColor = pct >= 80 ? "#22C55E" : pct >= 60 ? "#F59E0B" : "#EF4444";
  const scoreColor  = pct >= 80 ? "text-emerald-600" : pct >= 60 ? "text-amber-600" : "text-red-500";

  const TrendIcon = abnormalCount === 0 ? TrendingUp : abnormalCount > 3 ? TrendingDown : Minus;
  const trendColor = abnormalCount === 0 ? "text-emerald-500" : abnormalCount > 3 ? "text-red-500" : "text-amber-500";

  return (
    <div className="bg-white rounded-card border border-surface-border shadow-card p-5 flex flex-col items-center text-center">
      {/* Title */}
      <div className="flex items-center justify-between w-full mb-5">
        <p className="text-xs font-semibold text-text-muted uppercase tracking-widest">Health Score</p>
        <RiskBadge level={riskLevel} />
      </div>

      {/* Circular ring */}
      <div className="relative w-32 h-32 mb-5">
        {/* Gradient defs */}
        <svg className="absolute inset-0 w-full h-full" viewBox="0 0 112 112">
          <defs>
            <linearGradient id="scoreGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor={strokeColor} />
              <stop offset="100%" stopColor={strokeColor} stopOpacity="0.7" />
            </linearGradient>
          </defs>
          {/* Track */}
          <circle cx={cx} cy={cy} r={r} fill="none" stroke="#F1F5F9" strokeWidth="8" />
          {/* Progress */}
          <circle
            cx={cx} cy={cy} r={r}
            fill="none"
            stroke="url(#scoreGrad)"
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circ}
            strokeDashoffset={offset}
            transform={`rotate(-90 ${cx} ${cy})`}
            className="transition-all duration-1000 ease-out"
          />
        </svg>
        {/* Center label */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={cn("text-3xl font-bold leading-none tabular-nums", scoreColor)}>
            {totalMetrics === 0 ? "—" : pct}
          </span>
          <span className="text-[10px] text-text-muted font-medium mt-0.5">out of 100</span>
        </div>
      </div>

      {/* Trend */}
      <div className={cn("flex items-center gap-1.5 text-xs font-medium mb-5", trendColor)}>
        <TrendIcon className="w-3.5 h-3.5" />
        {abnormalCount === 0 ? "All values normal" : `${abnormalCount} value${abnormalCount !== 1 ? "s" : ""} need attention`}
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 gap-3 w-full">
        <div className="bg-surface-subtle rounded-xl p-3 text-center border border-surface-border">
          <p className="text-2xl font-bold text-text-primary tabular-nums">{totalMetrics}</p>
          <p className="text-[10px] text-text-muted font-medium mt-0.5">Total Tests</p>
        </div>
        <div className={cn(
          "rounded-xl p-3 text-center border",
          abnormalCount > 0 ? "bg-red-50 border-red-100" : "bg-emerald-50 border-emerald-100"
        )}>
          <p className={cn("text-2xl font-bold tabular-nums", abnormalCount > 0 ? "text-red-600" : "text-emerald-600")}>
            {abnormalCount}
          </p>
          <p className={cn("text-[10px] font-medium mt-0.5", abnormalCount > 0 ? "text-red-400" : "text-emerald-400")}>
            Abnormal
          </p>
        </div>
      </div>
    </div>
  );
}
