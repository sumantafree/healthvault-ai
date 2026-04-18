"use client";
import { useState } from "react";
import { Bell, BellOff, Clock, Plus, Trash2, MessageSquare } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Modal } from "@/components/ui/Modal";
import { PageLoader } from "@/components/ui/Spinner";
import {
  useReminders,
  useCreateReminder,
  useToggleReminder,
  useDeleteReminder,
} from "@/hooks/useReminders";
import { cn, formatRelative } from "@/lib/utils";
import type { FamilyMember, Medicine, Reminder, ReminderFrequency } from "@/types";
import { REMINDER_FREQUENCY_LABELS } from "@/types";

// ── Form schema ────────────────────────────────────────────────────────────────

const schema = z.object({
  title: z.string().min(1, "Title is required"),
  medicine_id: z.string().optional(),
  message: z.string().optional(),
  reminder_time: z.string().min(1, "Time is required"),
  frequency: z.enum(["daily", "twice_daily", "weekly", "custom"]),
  whatsapp_number: z
    .string()
    .optional()
    .refine(
      (v) => !v || /^\+?[1-9]\d{7,14}$/.test(v.replace(/\s/g, "")),
      "Enter a valid phone number with country code (e.g. +91...)"
    ),
});

type FormValues = z.infer<typeof schema>;

// ── Reminder row ──────────────────────────────────────────────────────────────

function ReminderRow({
  reminder,
  onToggle,
  onDelete,
}: {
  reminder: Reminder;
  onToggle: (id: string) => void;
  onDelete: (id: string) => void;
}) {
  const timeStr = reminder.reminder_time.slice(0, 5); // "HH:MM"
  const freqLabel = REMINDER_FREQUENCY_LABELS[reminder.frequency] ?? reminder.frequency;

  return (
    <Card className={cn("flex items-center gap-4", !reminder.is_active && "opacity-60")}>
      {/* Icon */}
      <div
        className={cn(
          "w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0",
          reminder.is_active ? "bg-blue-50" : "bg-surface-muted"
        )}
      >
        {reminder.is_active ? (
          <Bell className="w-4 h-4 text-brand-blue" />
        ) : (
          <BellOff className="w-4 h-4 text-text-muted" />
        )}
      </div>

      {/* Info */}
      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold text-text-primary truncate">{reminder.title}</p>
        <div className="flex items-center gap-2 mt-0.5 flex-wrap">
          <span className="flex items-center gap-1 text-xs text-text-muted">
            <Clock className="w-3 h-3" />
            {timeStr}
          </span>
          <span className="text-xs text-text-muted">{freqLabel}</span>
          {reminder.whatsapp_number && (
            <span className="flex items-center gap-1 text-xs text-green-600">
              <MessageSquare className="w-3 h-3" />
              WhatsApp
            </span>
          )}
          {reminder.last_sent_at && (
            <span className="text-xs text-text-muted">
              Last sent {formatRelative(reminder.last_sent_at)}
            </span>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1 flex-shrink-0">
        <button
          onClick={() => onToggle(reminder.id)}
          title={reminder.is_active ? "Pause reminder" : "Resume reminder"}
          className="p-2 rounded-lg hover:bg-surface-muted text-text-muted hover:text-text-primary transition-colors"
        >
          {reminder.is_active ? (
            <BellOff className="w-4 h-4" />
          ) : (
            <Bell className="w-4 h-4" />
          )}
        </button>
        <button
          onClick={() => {
            if (confirm("Delete this reminder?")) onDelete(reminder.id);
          }}
          className="p-2 rounded-lg hover:bg-red-50 hover:text-brand-red text-text-muted transition-colors"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </Card>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────

interface RemindersPanelProps {
  member: FamilyMember;
  medicines?: Medicine[];
}

export function RemindersPanel({ member, medicines = [] }: RemindersPanelProps) {
  const [addOpen, setAddOpen] = useState(false);

  const { data: reminders, isLoading } = useReminders(member.id);
  const create = useCreateReminder(member.id);
  const toggle = useToggleReminder(member.id);
  const remove = useDeleteReminder(member.id);

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { frequency: "daily" },
  });

  const onSubmit = async (values: FormValues) => {
    await create.mutateAsync({
      family_member_id: member.id,
      ...values,
      medicine_id: values.medicine_id || undefined,
      whatsapp_number: values.whatsapp_number || undefined,
    });
    form.reset({ frequency: "daily" });
    setAddOpen(false);
  };

  if (isLoading) return <PageLoader />;

  const active = (reminders ?? []).filter((r) => r.is_active);
  const inactive = (reminders ?? []).filter((r) => !r.is_active);

  return (
    <>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-sm font-semibold text-text-primary">Medicine Reminders</h2>
          <p className="text-xs text-text-muted mt-0.5">
            WhatsApp alerts sent automatically at the scheduled time
          </p>
        </div>
        <Button
          size="sm"
          icon={<Plus className="w-3.5 h-3.5" />}
          onClick={() => setAddOpen(true)}
        >
          Add Reminder
        </Button>
      </div>

      {/* Empty state */}
      {(reminders ?? []).length === 0 && (
        <EmptyState
          icon={<Bell className="w-10 h-10" />}
          title="No reminders yet"
          description="Set up WhatsApp alerts to never miss a medicine dose."
          action={{ label: "Add Reminder", onClick: () => setAddOpen(true) }}
        />
      )}

      {/* Active reminders */}
      {active.length > 0 && (
        <div className="space-y-2 mb-4">
          <p className="text-xs font-semibold text-text-secondary uppercase tracking-wide">
            Active ({active.length})
          </p>
          {active.map((r) => (
            <ReminderRow
              key={r.id}
              reminder={r}
              onToggle={(id) => toggle.mutate(id)}
              onDelete={(id) => remove.mutate(id)}
            />
          ))}
        </div>
      )}

      {/* Paused reminders */}
      {inactive.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold text-text-secondary uppercase tracking-wide">
            Paused ({inactive.length})
          </p>
          {inactive.map((r) => (
            <ReminderRow
              key={r.id}
              reminder={r}
              onToggle={(id) => toggle.mutate(id)}
              onDelete={(id) => remove.mutate(id)}
            />
          ))}
        </div>
      )}

      {/* Add reminder modal */}
      <Modal
        open={addOpen}
        onClose={() => {
          setAddOpen(false);
          form.reset({ frequency: "daily" });
        }}
        title="Add Medicine Reminder"
      >
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          {/* Title */}
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1">
              Reminder Title *
            </label>
            <input
              {...form.register("title")}
              placeholder="e.g. Take Metformin after breakfast"
              className="w-full text-sm border border-surface-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-blue"
            />
            {form.formState.errors.title && (
              <p className="text-xs text-brand-red mt-0.5">
                {form.formState.errors.title.message}
              </p>
            )}
          </div>

          {/* Link to medicine */}
          {medicines.length > 0 && (
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">
                Medicine (optional)
              </label>
              <select
                {...form.register("medicine_id")}
                className="w-full text-sm border border-surface-border rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-brand-blue"
              >
                <option value="">— not linked —</option>
                {medicines
                  .filter((m) => m.is_active)
                  .map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name}
                      {m.dosage ? ` (${m.dosage})` : ""}
                    </option>
                  ))}
              </select>
            </div>
          )}

          {/* Time + Frequency */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">
                Time *
              </label>
              <input
                type="time"
                {...form.register("reminder_time")}
                className="w-full text-sm border border-surface-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-blue"
              />
              {form.formState.errors.reminder_time && (
                <p className="text-xs text-brand-red mt-0.5">
                  {form.formState.errors.reminder_time.message}
                </p>
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">
                Frequency
              </label>
              <select
                {...form.register("frequency")}
                className="w-full text-sm border border-surface-border rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-brand-blue"
              >
                {(
                  ["daily", "twice_daily", "weekly", "custom"] as ReminderFrequency[]
                ).map((f) => (
                  <option key={f} value={f}>
                    {REMINDER_FREQUENCY_LABELS[f]}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* WhatsApp number */}
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1">
              WhatsApp Number
            </label>
            <input
              {...form.register("whatsapp_number")}
              placeholder="+91 98765 43210"
              className="w-full text-sm border border-surface-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-blue"
            />
            {form.formState.errors.whatsapp_number && (
              <p className="text-xs text-brand-red mt-0.5">
                {form.formState.errors.whatsapp_number.message}
              </p>
            )}
            <p className="text-xs text-text-muted mt-1">
              Include country code. Leave blank to skip WhatsApp alerts.
            </p>
          </div>

          {/* Optional message */}
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1">
              Custom Message (optional)
            </label>
            <textarea
              {...form.register("message")}
              placeholder="e.g. Take with a full glass of water"
              rows={2}
              className="w-full text-sm border border-surface-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-blue resize-none"
            />
          </div>

          <div className="flex justify-end gap-2 pt-1">
            <Button variant="secondary" type="button" onClick={() => setAddOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" loading={create.isPending}>
              Create Reminder
            </Button>
          </div>
        </form>
      </Modal>
    </>
  );
}
