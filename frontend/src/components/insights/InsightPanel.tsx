"use client";
import { AlertCircle, Lightbulb, RefreshCw, ShieldCheck, Sparkles } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { RiskBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { useReanalyze } from "@/hooks/useInsights";
import { cn, formatRelative } from "@/lib/utils";
import type { AIInsight, Recommendation } from "@/types";

interface InsightPanelProps {
  insight: AIInsight | undefined;
  isLoading: boolean;
  reportId?: string;
  onUpload?: () => void;
}

export function InsightPanel({ insight, isLoading, reportId, onUpload }: InsightPanelProps) {
  const reanalyze = useReanalyze();

  if (isLoading) {
    return (
      <Card className="space-y-4 animate-pulse">
        <div className="flex items-center gap-3">
          <div className="h-4 w-32 skeleton" />
          <div className="h-6 w-20 skeleton rounded-full ml-auto" />
        </div>
        <div className="h-20 skeleton rounded-xl" />
        <div className="space-y-2">
          {[1, 2].map((i) => <div key={i} className="h-14 skeleton rounded-xl" />)}
        </div>
      </Card>
    );
  }

  if (!insight) {
    return (
      <Card className="h-full">
        <EmptyState
          icon={<Sparkles className="w-7 h-7" />}
          title="No AI insights yet"
          description="Upload a health report to receive personalized AI-powered health analysis."
          action={onUpload ? { label: "Upload Report", onClick: onUpload } : undefined}
        />
      </Card>
    );
  }

  const recommendations = insight.recommendations?.items ?? [];

  return (
    <Card className="space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-brand flex items-center justify-center flex-shrink-0">
            <Sparkles className="w-3.5 h-3.5 text-white" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-text-primary leading-tight">AI Health Insights</h3>
            <p className="text-[10px] text-text-muted">{formatRelative(insight.created_at)}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <RiskBadge level={insight.risk_level} />
          {reportId && (
            <Button
              variant="ghost"
              size="xs"
              icon={<RefreshCw className="w-3 h-3" />}
              loading={reanalyze.isPending}
              onClick={() => reanalyze.mutate(reportId)}
            >
              Re-analyze
            </Button>
          )}
        </div>
      </div>

      {/* Summary */}
      <div className="bg-gradient-subtle rounded-xl p-4 border border-blue-100">
        <p className="text-sm text-text-primary leading-relaxed">{insight.summary}</p>
      </div>

      {/* Risk Factors / Observations */}
      {insight.risk_factors && insight.risk_factors.length > 0 && (
        <div>
          <p className="flex items-center gap-1.5 text-[10px] font-semibold text-text-muted uppercase tracking-widest mb-3">
            <AlertCircle className="w-3 h-3 text-amber-500" />
            Observations
          </p>
          <ul className="space-y-2">
            {insight.risk_factors.map((f, i) => (
              <li key={i} className="flex items-start gap-2.5 text-sm text-text-secondary bg-amber-50/60 rounded-lg px-3 py-2.5 border border-amber-100">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 flex-shrink-0" />
                {f}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <div>
          <p className="text-[10px] font-semibold text-text-muted uppercase tracking-widest mb-3">
            Recommendations
          </p>
          <div className="space-y-2">
            {recommendations.map((rec, i) => (
              <RecommendationCard key={i} rec={rec} />
            ))}
          </div>
        </div>
      )}

      {/* Disclaimer */}
      <div className="flex items-start gap-2.5 p-3.5 bg-slate-50 rounded-xl border border-surface-border">
        <ShieldCheck className="w-4 h-4 text-slate-400 flex-shrink-0 mt-0.5" />
        <p className="text-[11px] text-text-muted leading-relaxed">{insight.disclaimer}</p>
      </div>
    </Card>
  );
}

function RecommendationCard({ rec }: { rec: Recommendation }) {
  const styles = {
    high:   { bar: "bg-red-500",    bg: "bg-red-50 border-red-100",    text: "text-red-700",   label: "High" },
    medium: { bar: "bg-amber-500",  bg: "bg-amber-50 border-amber-100", text: "text-amber-700", label: "Medium" },
    low:    { bar: "bg-emerald-500", bg: "bg-emerald-50 border-emerald-100", text: "text-emerald-700", label: "Low" },
  }[rec.priority];

  return (
    <div className={cn("rounded-xl p-3.5 border flex gap-3", styles.bg)}>
      <div className={cn("w-1 rounded-full flex-shrink-0 self-stretch", styles.bar)} />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 mb-0.5">
          <p className="text-sm font-semibold text-text-primary">{rec.title}</p>
          <span className={cn("text-[10px] font-semibold uppercase", styles.text)}>{styles.label}</span>
        </div>
        <p className="text-xs text-text-secondary leading-relaxed">{rec.description}</p>
      </div>
    </div>
  );
}
