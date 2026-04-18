"use client";
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  FileText, Upload, Trash2, RefreshCw,
  CheckCircle, Clock, Loader2, XCircle, Plus, Pill,
} from "lucide-react";
import { toast } from "sonner";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Header } from "@/components/layout/Header";
import { PrescriptionUpload } from "@/components/prescriptions/PrescriptionUpload";
import { MedicineCard } from "@/components/prescriptions/MedicineCard";
import { ActiveMedicines } from "@/components/prescriptions/ActiveMedicines";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageLoader } from "@/components/ui/Spinner";
import { useSelectedMember } from "@/hooks/useFamilyMembers";
import { usePrescriptions, useDeletePrescription, useReprocessPrescription } from "@/hooks/usePrescriptions";
import { useMedicines, useToggleMedicine, useDeleteMedicine, useCreateMedicine } from "@/hooks/useMedicines";
import { formatDate, formatRelative, cn } from "@/lib/utils";
import type { Prescription, ProcessingStatus, MedicineForm, MedicineCreate } from "@/types";
import { PROCESSING_STATUS_CONFIG, MEDICINE_FORM_ICONS } from "@/types";
import { RemindersPanel } from "@/components/prescriptions/RemindersPanel";

// ── Status icon map ───────────────────────────────────────────────────────────

const StatusIcon: Record<ProcessingStatus, React.ReactNode> = {
  pending:    <Clock className="w-3.5 h-3.5 text-slate-400" />,
  processing: <Loader2 className="w-3.5 h-3.5 text-blue-500 animate-spin" />,
  done:       <CheckCircle className="w-3.5 h-3.5 text-green-500" />,
  failed:     <XCircle className="w-3.5 h-3.5 text-red-500" />,
};

// ── Add medicine form schema ───────────────────────────────────────────────────

const addMedicineSchema = z.object({
  name: z.string().min(1, "Name is required"),
  dosage: z.string().optional(),
  form: z.enum(["tablet","capsule","syrup","injection","cream","drops","inhaler","other"]).optional(),
  frequency: z.string().optional(),
  instructions: z.string().optional(),
  start_date: z.string().optional(),
  end_date: z.string().optional(),
});

type AddMedicineForm = z.infer<typeof addMedicineSchema>;

// ── Page ──────────────────────────────────────────────────────────────────────

export default function PrescriptionsPage() {
  const member = useSelectedMember();
  const [uploadOpen, setUploadOpen] = useState(false);
  const [addMedOpen, setAddMedOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<"prescriptions" | "medicines" | "reminders">("prescriptions");

  const { data: prescriptions, isLoading: prescLoading } = usePrescriptions(member?.id);
  const { data: medicines, isLoading: medsLoading } = useMedicines(member?.id);
  const deletePrescription = useDeletePrescription(member?.id);
  const reprocess = useReprocessPrescription(member?.id);
  const toggleMed = useToggleMedicine(member?.id);
  const deleteMed = useDeleteMedicine(member?.id);
  const createMed = useCreateMedicine(member?.id);

  const form = useForm<AddMedicineForm>({ resolver: zodResolver(addMedicineSchema) });

  const onAddMedicine = async (data: AddMedicineForm) => {
    if (!member) return;
    try {
      await createMed.mutateAsync({ family_member_id: member.id, ...data } as MedicineCreate);
      form.reset();
      setAddMedOpen(false);
    } catch (e: any) {
      toast.error(e.message);
    }
  };

  if (!member) return <><Header title="Prescriptions" /></>;

  const TABS = [
    { key: "prescriptions", label: "Prescriptions", count: prescriptions?.length },
    { key: "medicines",     label: "All Medicines",  count: medicines?.length },
    { key: "reminders",     label: "Reminders",      count: undefined },
  ] as const;

  return (
    <>
      <Header title="Prescriptions & Medicines" subtitle={member.name} />
      <div className="p-6 space-y-5">

        {/* Actions bar */}
        <div className="flex items-center justify-between">
          {/* Tabs */}
          <div className="flex gap-1 p-1 bg-surface-muted rounded-xl">
            {TABS.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors",
                  activeTab === tab.key
                    ? "bg-white text-text-primary shadow-card"
                    : "text-text-secondary hover:text-text-primary"
                )}
              >
                {tab.label}
                {tab.count !== undefined && (
                  <span className={cn("text-xs px-1.5 py-0.5 rounded-full font-semibold",
                    activeTab === tab.key ? "bg-brand-blue text-white" : "bg-surface-border text-text-muted"
                  )}>
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </div>

          <div className="flex gap-2">
            {activeTab === "medicines" && (
              <Button variant="secondary" size="sm" icon={<Plus className="w-3.5 h-3.5" />} onClick={() => setAddMedOpen(true)}>
                Add Manually
              </Button>
            )}
            <Button size="sm" icon={<Upload className="w-3.5 h-3.5" />} onClick={() => setUploadOpen(true)}>
              Upload Prescription
            </Button>
          </div>
        </div>

        {/* Active medicines summary always visible at top */}
        <ActiveMedicines memberId={member.id} onAddClick={() => setAddMedOpen(true)} />

        {/* Tab content */}
        {activeTab === "prescriptions" && (
          <PrescriptionsTab
            prescriptions={prescriptions ?? []}
            isLoading={prescLoading}
            onUpload={() => setUploadOpen(true)}
            onDelete={(id) => deletePrescription.mutate(id)}
            onReprocess={(id) => reprocess.mutate(id)}
          />
        )}

        {activeTab === "medicines" && (
          <MedicinesTab
            medicines={medicines ?? []}
            isLoading={medsLoading}
            onToggle={(id) => toggleMed.mutate(id)}
            onDelete={(id) => {
              if (!confirm("Remove this medicine?")) return;
              deleteMed.mutate(id);
            }}
            onAdd={() => setAddMedOpen(true)}
          />
        )}

        {activeTab === "reminders" && (
          <RemindersPanel member={member} medicines={medicines ?? []} />
        )}
      </div>

      {/* Upload modal */}
      <Modal open={uploadOpen} onClose={() => setUploadOpen(false)} title={`Upload Prescription for ${member.name}`}>
        <PrescriptionUpload member={member} onSuccess={() => setUploadOpen(false)} />
      </Modal>

      {/* Add medicine modal */}
      <Modal open={addMedOpen} onClose={() => setAddMedOpen(false)} title="Add Medicine Manually">
        <form onSubmit={form.handleSubmit(onAddMedicine)} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="col-span-2">
              <label className="block text-xs font-medium text-text-secondary mb-1">Medicine Name *</label>
              <input {...form.register("name")} placeholder="e.g. Paracetamol"
                className="w-full text-sm border border-surface-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-blue" />
              {form.formState.errors.name && (
                <p className="text-xs text-brand-red mt-0.5">{form.formState.errors.name.message}</p>
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">Dosage</label>
              <input {...form.register("dosage")} placeholder="e.g. 500mg"
                className="w-full text-sm border border-surface-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-blue" />
            </div>

            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">Form</label>
              <select {...form.register("form")}
                className="w-full text-sm border border-surface-border rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-brand-blue">
                <option value="">Select form</option>
                {(["tablet","capsule","syrup","injection","cream","drops","inhaler","other"] as MedicineForm[]).map((f) => (
                  <option key={f} value={f}>{MEDICINE_FORM_ICONS[f]} {f.charAt(0).toUpperCase() + f.slice(1)}</option>
                ))}
              </select>
            </div>

            <div className="col-span-2">
              <label className="block text-xs font-medium text-text-secondary mb-1">Frequency</label>
              <input {...form.register("frequency")} placeholder="e.g. Twice daily, Every 8 hours"
                className="w-full text-sm border border-surface-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-blue" />
            </div>

            <div className="col-span-2">
              <label className="block text-xs font-medium text-text-secondary mb-1">Instructions</label>
              <input {...form.register("instructions")} placeholder="e.g. Take with food, Before meals"
                className="w-full text-sm border border-surface-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-blue" />
            </div>

            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">Start Date</label>
              <input type="date" {...form.register("start_date")}
                className="w-full text-sm border border-surface-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-blue" />
            </div>

            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">End Date</label>
              <input type="date" {...form.register("end_date")}
                className="w-full text-sm border border-surface-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-blue" />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" type="button" onClick={() => setAddMedOpen(false)}>Cancel</Button>
            <Button type="submit" loading={createMed.isPending}>Add Medicine</Button>
          </div>
        </form>
      </Modal>
    </>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────

function PrescriptionsTab({
  prescriptions, isLoading, onUpload, onDelete, onReprocess,
}: {
  prescriptions: Prescription[];
  isLoading: boolean;
  onUpload: () => void;
  onDelete: (id: string) => void;
  onReprocess: (id: string) => void;
}) {
  if (isLoading) return <PageLoader />;

  if (prescriptions.length === 0) {
    return (
      <EmptyState
        icon={<FileText className="w-10 h-10" />}
        title="No prescriptions yet"
        description="Upload a prescription to automatically extract medicines and dosages."
        action={{ label: "Upload Prescription", onClick: onUpload }}
      />
    );
  }

  return (
    <div className="space-y-3">
      {prescriptions.map((p) => (
        <PrescriptionRow key={p.id} prescription={p} onDelete={onDelete} onReprocess={onReprocess} />
      ))}
    </div>
  );
}

function PrescriptionRow({
  prescription: p, onDelete, onReprocess,
}: {
  prescription: Prescription;
  onDelete: (id: string) => void;
  onReprocess: (id: string) => void;
}) {
  const statusCfg = PROCESSING_STATUS_CONFIG[p.processing_status];
  const medCount = p.parsed_data?.medicine_count ?? 0;

  return (
    <Card className="flex items-center gap-4">
      <div className="w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center flex-shrink-0">
        <FileText className="w-5 h-5 text-brand-green" />
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 flex-wrap">
          <p className="text-sm font-semibold text-text-primary truncate">{p.file_name}</p>
          {p.processing_status === "done" && medCount > 0 && (
            <span className="text-xs font-medium text-green-700 bg-green-50 px-2 py-0.5 rounded-full">
              {medCount} medicine{medCount !== 1 ? "s" : ""} extracted
            </span>
          )}
        </div>
        <div className="flex items-center gap-3 mt-0.5 flex-wrap">
          <span className={cn("text-xs font-medium", statusCfg.color)}>{statusCfg.label}</span>
          {p.doctor_name && <span className="text-xs text-text-muted">{p.doctor_name}</span>}
          {p.hospital_name && <span className="text-xs text-text-muted">{p.hospital_name}</span>}
          {p.prescribed_date && <span className="text-xs text-text-muted">{formatDate(p.prescribed_date)}</span>}
          <span className="text-xs text-text-muted">{formatRelative(p.created_at)}</span>
        </div>
      </div>

      <div className="flex items-center gap-1.5 flex-shrink-0">
        {p.processing_status === "failed" && (
          <Button variant="ghost" size="sm" icon={<RefreshCw className="w-3.5 h-3.5" />} onClick={() => onReprocess(p.id)}>
            Retry
          </Button>
        )}
        <button
          onClick={() => {
            if (confirm("Delete this prescription and its extracted medicines?")) onDelete(p.id);
          }}
          className="p-2 rounded-lg hover:bg-red-50 hover:text-brand-red text-text-muted transition-colors"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </Card>
  );
}

function MedicinesTab({
  medicines, isLoading, onToggle, onDelete, onAdd,
}: {
  medicines: import("@/types").Medicine[];
  isLoading: boolean;
  onToggle: (id: string) => void;
  onDelete: (id: string) => void;
  onAdd: () => void;
}) {
  if (isLoading) return <PageLoader />;

  if (medicines.length === 0) {
    return (
      <EmptyState
        icon={<Pill className="w-10 h-10" />}
        title="No medicines yet"
        description="Add medicines manually or upload a prescription for AI extraction."
        action={{ label: "Add Medicine", onClick: onAdd }}
      />
    );
  }

  const active = medicines.filter((m) => m.is_active);
  const inactive = medicines.filter((m) => !m.is_active);

  return (
    <div className="space-y-5">
      {active.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-text-secondary mb-3">Active ({active.length})</h2>
          <div className="space-y-2">
            {active.map((m) => (
              <MedicineCard key={m.id} medicine={m} onToggle={onToggle} onDelete={onDelete} />
            ))}
          </div>
        </div>
      )}
      {inactive.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-text-secondary mb-3">Inactive ({inactive.length})</h2>
          <div className="space-y-2">
            {inactive.map((m) => (
              <MedicineCard key={m.id} medicine={m} onToggle={onToggle} onDelete={onDelete} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
