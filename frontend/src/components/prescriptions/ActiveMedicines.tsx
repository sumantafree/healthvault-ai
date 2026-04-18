"use client";
import { Pill } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { MedicineCard } from "./MedicineCard";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageLoader } from "@/components/ui/Spinner";
import { useActiveMedicines, useToggleMedicine, useDeleteMedicine } from "@/hooks/useMedicines";
import { toast } from "sonner";

interface ActiveMedicinesProps {
  memberId: string;
  onAddClick?: () => void;
}

export function ActiveMedicines({ memberId, onAddClick }: ActiveMedicinesProps) {
  const { data: medicines, isLoading } = useActiveMedicines(memberId);
  const toggle = useToggleMedicine(memberId);
  const remove = useDeleteMedicine(memberId);

  const handleDelete = (id: string) => {
    if (!confirm("Remove this medicine?")) return;
    remove.mutate(id);
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Active Medicines</CardTitle>
        {medicines && medicines.length > 0 && (
          <span className="text-xs font-semibold text-brand-blue bg-blue-50 px-2 py-0.5 rounded-full">
            {medicines.length}
          </span>
        )}
      </CardHeader>

      {isLoading ? (
        <PageLoader />
      ) : !medicines || medicines.length === 0 ? (
        <EmptyState
          icon={<Pill className="w-8 h-8" />}
          title="No active medicines"
          description="Upload a prescription to auto-extract medicines, or add one manually."
          action={onAddClick ? { label: "Add Medicine", onClick: onAddClick } : undefined}
        />
      ) : (
        <div className="space-y-2">
          {medicines.map((m) => (
            <MedicineCard
              key={m.id}
              medicine={m}
              onToggle={(id) => toggle.mutate(id)}
              onDelete={handleDelete}
              compact
            />
          ))}
        </div>
      )}
    </Card>
  );
}
