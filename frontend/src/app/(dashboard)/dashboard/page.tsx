"use client";
import { useState } from "react";
import { Upload, Activity, AlertTriangle, TrendingUp, FileText, Users } from "lucide-react";
import { Header } from "@/components/layout/Header";
import { HealthScoreCard } from "@/components/dashboard/HealthScoreCard";
import { MetricsSummary } from "@/components/dashboard/MetricsSummary";
import { RecentReports } from "@/components/dashboard/RecentReports";
import { InsightPanel } from "@/components/insights/InsightPanel";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { ReportUpload } from "@/components/reports/ReportUpload";
import { EmptyState } from "@/components/ui/EmptyState";
import { MemberSelector } from "@/components/layout/MemberSelector";
import { useSelectedMember } from "@/hooks/useFamilyMembers";
import { useMetrics } from "@/hooks/useMetrics";
import { useLatestInsight } from "@/hooks/useInsights";
import Link from "next/link";

export default function DashboardPage() {
  const member = useSelectedMember();
  const [uploadOpen, setUploadOpen] = useState(false);

  const { healthScore, totalCount, abnormalCount, abnormalMetrics, isLoading: metricsLoading } =
    useMetrics(member?.id);
  const { data: insight, isLoading: insightLoading } = useLatestInsight(member?.id);

  if (!member) {
    return (
      <>
        <Header title="Dashboard" />
        <div className="p-4 sm:p-6 flex items-center justify-center min-h-[60vh]">
          <div className="text-center max-w-sm">
            <div className="w-16 h-16 rounded-2xl bg-gradient-subtle border border-surface-border flex items-center justify-center mx-auto mb-4">
              <Users className="w-8 h-8 text-brand-blue" />
            </div>
            <h2 className="text-lg font-bold text-text-primary mb-2">Add a family member</h2>
            <p className="text-sm text-text-secondary mb-6">
              Create a profile for yourself or a family member to start tracking health data.
            </p>
            {/* Show member selector on mobile too */}
            <div className="flex flex-col items-center gap-3 sm:hidden mb-4">
              <MemberSelector />
            </div>
            <Link href="/family">
              <Button size="md">Add Family Member</Button>
            </Link>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Header
        title={`${member.name}'s Dashboard`}
        subtitle={member.age ? `${member.age} yrs · ${member.blood_type}` : undefined}
      />

      <div className="p-4 sm:p-6 space-y-5">
        {/* ── Stats strip ── */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <StatCard
            icon={<Activity className="w-4 h-4 text-brand-blue" />}
            value={totalCount}
            label="Total Metrics"
            bg="bg-blue-50"
          />
          <StatCard
            icon={<AlertTriangle className="w-4 h-4 text-amber-500" />}
            value={abnormalCount}
            label="Need Attention"
            bg="bg-amber-50"
            highlight={abnormalCount > 0}
          />
          <StatCard
            icon={<TrendingUp className="w-4 h-4 text-emerald-600" />}
            value={`${healthScore}%`}
            label="Health Score"
            bg="bg-emerald-50"
          />
          <StatCard
            icon={<FileText className="w-4 h-4 text-violet-600" />}
            value="Reports"
            label="Lab Results"
            bg="bg-violet-50"
            action={() => setUploadOpen(true)}
          />
        </div>

        {/* ── Upload CTA strip ── */}
        <div className="flex items-center justify-between bg-gradient-subtle rounded-xl border border-blue-100 px-4 py-3">
          <p className="text-sm text-text-secondary">
            {totalCount > 0
              ? `${totalCount} metrics tracked for ${member.name}`
              : "Upload a report to start tracking health metrics"}
          </p>
          <Button
            size="sm"
            icon={<Upload className="w-3.5 h-3.5" />}
            onClick={() => setUploadOpen(true)}
          >
            <span className="hidden sm:inline">Upload Report</span>
            <span className="sm:hidden">Upload</span>
          </Button>
        </div>

        {/* ── Score + Insights ── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <HealthScoreCard
            score={healthScore}
            riskLevel={insight?.risk_level ?? "low"}
            totalMetrics={totalCount}
            abnormalCount={abnormalCount}
            loading={metricsLoading}
          />
          <div className="lg:col-span-2">
            <InsightPanel
              insight={insight}
              isLoading={insightLoading}
              onUpload={() => setUploadOpen(true)}
            />
          </div>
        </div>

        {/* ── Metrics + Reports ── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <MetricsSummary metrics={abnormalMetrics} showAbnormalOnly />
          <RecentReports memberId={member.id} onUploadClick={() => setUploadOpen(true)} />
        </div>
      </div>

      <Modal
        open={uploadOpen}
        onClose={() => setUploadOpen(false)}
        title={`Upload Report`}
        description={`For ${member.name}`}
      >
        <ReportUpload member={member} onSuccess={() => setUploadOpen(false)} />
      </Modal>
    </>
  );
}

function StatCard({
  icon, value, label, bg, highlight, action,
}: {
  icon: React.ReactNode;
  value: string | number;
  label: string;
  bg: string;
  highlight?: boolean;
  action?: () => void;
}) {
  return (
    <div
      onClick={action}
      className={`stat-card p-4 ${action ? "cursor-pointer" : ""}`}
    >
      <div className={`w-8 h-8 rounded-xl ${bg} flex items-center justify-center mb-3`}>
        {icon}
      </div>
      <p className={`text-xl font-bold tabular-nums leading-tight ${highlight ? "text-amber-600" : "text-text-primary"}`}>
        {value}
      </p>
      <p className="text-xs text-text-muted mt-0.5 font-medium">{label}</p>
    </div>
  );
}
