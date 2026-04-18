"use client";
import { Header } from "@/components/layout/Header";
import { InsightPanel } from "@/components/insights/InsightPanel";
import { PageLoader } from "@/components/ui/Spinner";
import { useSelectedMember } from "@/hooks/useFamilyMembers";
import { useInsights } from "@/hooks/useInsights";
import { formatDate } from "@/lib/utils";
import { RiskBadge } from "@/components/ui/Badge";

export default function InsightsPage() {
  const member = useSelectedMember();
  const { data: insights, isLoading } = useInsights(member?.id);

  if (!member) return <><Header title="AI Insights" /></>;
  if (isLoading) return <><Header title="AI Insights" /><PageLoader /></>;

  const latest = insights?.[0];
  const previous = insights?.slice(1) ?? [];

  return (
    <>
      <Header title="AI Insights" subtitle={member.name} />
      <div className="p-6 space-y-6">
        <InsightPanel insight={latest} isLoading={isLoading} reportId={latest?.report_id ?? undefined} />

        {previous.length > 0 && (
          <div>
            <h2 className="text-sm font-semibold text-text-secondary mb-3">Previous Analyses</h2>
            <div className="space-y-3">
              {previous.map((ins) => (
                <div key={ins.id} className="bg-white border border-surface-border rounded-xl p-4">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-xs text-text-muted">{formatDate(ins.created_at)}</p>
                    <RiskBadge level={ins.risk_level} />
                  </div>
                  <p className="text-sm text-text-secondary line-clamp-3">{ins.summary}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
