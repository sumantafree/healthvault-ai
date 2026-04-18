"use client";
import { Power, Trash2, Bell } from "lucide-react";
import { cn, formatDate } from "@/lib/utils";
import { StatusPill } from "@/components/ui/Badge";
import type { Medicine } from "@/types";
import { MEDICINE_FORM_ICONS } from "@/types";

interface MedicineCardProps {
  medicine: Medicine;
  onToggle: (id: string) => void;
  onDelete: (id: string) => void;
  compact?: boolean;
}

export function MedicineCard({ medicine, onToggle, onDelete, compact = false }: MedicineCardProps) {
  const formIcon = medicine.form
    ? MEDICINE_FORM_ICONS[medicine.form] ?? "💊"
    : "💊";

  const isExpired = medicine.end_date
    ? new Date(medicine.end_date) < new Date()
    : false;

  return (
    <div
      className={cn(
        "bg-white border rounded-xl transition-all",
        medicine.is_active && !isExpired
          ? "border-surface-border shadow-card"
          : "border-surface-border opacity-60",
        compact ? "p-3" : "p-4"
      )}
    >
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className={cn(
          "rounded-xl flex items-center justify-center flex-shrink-0 text-lg",
          compact ? "w-8 h-8" : "w-10 h-10",
          medicine.is_active && !isExpired ? "bg-green-50" : "bg-surface-muted"
        )}>
          {formIcon}
        </div>

        {/* Content */}
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <p className={cn("font-semibold text-text-primary truncate", compact ? "text-sm" : "text-base")}>
              {medicine.name}
            </p>
            {medicine.dosage && (
              <span className="text-xs font-medium text-text-muted bg-surface-muted px-2 py-0.5 rounded-full">
                {medicine.dosage}
              </span>
            )}
            {!medicine.is_active && <StatusPill label="Inactive" variant="default" />}
            {isExpired && medicine.is_active && <StatusPill label="Expired" variant="error" />}
          </div>

          {medicine.generic_name && (
            <p className="text-xs text-text-muted mt-0.5">{medicine.generic_name}</p>
          )}

          {!compact && (
            <div className="mt-2 space-y-1">
              {medicine.frequency && (
                <p className="text-xs text-text-secondary">
                  <span className="font-medium">Frequency:</span> {medicine.frequency}
                </p>
              )}
              {medicine.instructions && (
                <p className="text-xs text-text-secondary">
                  <span className="font-medium">Instructions:</span> {medicine.instructions}
                </p>
              )}
              {medicine.form && (
                <p className="text-xs text-text-secondary capitalize">
                  <span className="font-medium">Form:</span> {medicine.form}
                </p>
              )}
              <div className="flex gap-4 mt-1">
                {medicine.start_date && (
                  <p className="text-[11px] text-text-muted">From: {formatDate(medicine.start_date)}</p>
                )}
                {medicine.end_date && (
                  <p className={cn("text-[11px]", isExpired ? "text-brand-red" : "text-text-muted")}>
                    Until: {formatDate(medicine.end_date)}
                  </p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 flex-shrink-0">
          <button
            onClick={() => onToggle(medicine.id)}
            title={medicine.is_active ? "Mark inactive" : "Mark active"}
            className={cn(
              "p-1.5 rounded-lg transition-colors",
              medicine.is_active
                ? "text-brand-green hover:bg-green-50"
                : "text-text-muted hover:bg-surface-muted"
            )}
          >
            <Power className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => onDelete(medicine.id)}
            className="p-1.5 rounded-lg text-text-muted hover:bg-red-50 hover:text-brand-red transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
