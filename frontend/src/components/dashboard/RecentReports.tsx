"use client";
import { FileText, Clock, CheckCircle, XCircle, Loader2, FileUp } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { RiskBadge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { reportsApi } from "@/lib/api/reports";
import { formatRelative, cn } from "@/lib/utils";
import type { HealthReport, ProcessingStatus } from "@/types";

const STATUS_CONFIG: Record<ProcessingStatus, {
  icon: React.ReactNode;
  label: string;
  color: string;
  bg: string;
}> = {
  pending:    { icon: <Clock className="w-3 h-3" />,             label: "Queued",    color: "text-slate-500",  bg: "bg-slate-100"  },
  processing: { icon: <Loader2 className="w-3 h-3 animate-spin" />, label: "Analyzing", color: "text-blue-600",  bg: "bg-blue-50"    },
  done:       { icon: <CheckCircle className="w-3 h-3" />,       label: "Complete",  color: "text-emerald-600", bg: "bg-emerald-50" },
  failed:     { icon: <XCircle className="w-3 h-3" />,           label: "Failed",    color: "text-red-600",   bg: "bg-red-50"     },
};

interface RecentReportsProps {
  memberId: string;
  onUploadClick?: () => void;
}

export function RecentReports({ memberId, onUploadClick }: RecentReportsProps) {
  const { data, isLoading } = useQuery({
    queryKey: ["reports", memberId],
    queryFn: () => reportsApi.list(memberId, 1),
    enabled: !!memberId,
    staleTime: 60_000,
  });

  const reports = data?.items ?? [];

  return (
    <Card>
      <CardHeader
        action={
          onUploadClick && (
            <button
              onClick={onUploadClick}
              className="text-xs font-medium text-brand-blue hover:text-blue-700 transition-colors"
            >
              + Upload
            </button>
          )
        }
      >
        <CardTitle>Recent Reports</CardTitle>
      </CardHeader>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-14 skeleton rounded-xl" />
          ))}
        </div>
      ) : reports.length === 0 ? (
        <EmptyState
          compact
          icon={<FileUp className="w-6 h-6" />}
          title="No reports yet"
          description="Upload your first lab report for AI analysis."
          action={onUploadClick ? { label: "Upload Report", onClick: onUploadClick } : undefined}
        />
      ) : (
        <div className="divide-y divide-surface-border">
          {reports.slice(0, 5).map((r) => (
            <ReportRow key={r.id} report={r} />
          ))}
        </div>
      )}
    </Card>
  );
}

function ReportRow({ report }: { report: HealthReport }) {
  const cfg = STATUS_CONFIG[report.processing_status];

  return (
    <div className="flex items-center gap-3 py-3 first:pt-0 last:pb-0">
      {/* Icon */}
      <div className="w-9 h-9 rounded-xl bg-gradient-subtle flex items-center justify-center flex-shrink-0 border border-surface-border">
        <FileText className="w-4 h-4 text-brand-blue" />
      </div>

      {/* Info */}
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-text-primary truncate leading-tight">{report.file_name}</p>
        <p className="text-[11px] text-text-muted mt-0.5">{formatRelative(report.created_at)}</p>
      </div>

      {/* Status */}
      <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
        {report.processing_status === "done" && <RiskBadge level={report.risk_level} />}
        <span className={cn(
          "inline-flex items-center gap-1 text-[10px] font-medium px-1.5 py-0.5 rounded-full",
          cfg.color, cfg.bg
        )}>
          {cfg.icon}
          {cfg.label}
        </span>
      </div>
    </div>
  );
}
