// HealthVault AI — Shared TypeScript Types
// Mirror the FastAPI Pydantic schemas

// ── Enums ──────────────────────────────────────────────────────────────────────

export type RiskLevel = "low" | "moderate" | "high" | "critical";
export type MetricStatus = "normal" | "borderline" | "abnormal_low" | "abnormal_high";
export type ProcessingStatus = "pending" | "processing" | "done" | "failed";
export type ReportType = "blood_test" | "urine_test" | "imaging" | "prescription" | "vaccination" | "other";
export type Gender = "male" | "female" | "other";
export type BloodType = "A+" | "A-" | "B+" | "B-" | "AB+" | "AB-" | "O+" | "O-" | "unknown";

// ── User ───────────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  role: string;
  onboarded: boolean;
}

// ── Family Member ──────────────────────────────────────────────────────────────

export interface FamilyMember {
  id: string;
  user_id: string;
  name: string;
  date_of_birth: string | null;
  gender: Gender;
  blood_type: BloodType;
  height_cm: number | null;
  weight_kg: number | null;
  allergies: string[] | null;
  chronic_conditions: string[] | null;
  emergency_contact: string | null;
  avatar_url: string | null;
  is_primary: boolean;
  age: number | null;
  bmi: number | null;
  created_at: string;
  updated_at: string;
}

export interface FamilyMemberCreate {
  name: string;
  date_of_birth?: string;
  gender?: Gender;
  blood_type?: BloodType;
  height_cm?: number;
  weight_kg?: number;
  allergies?: string[];
  chronic_conditions?: string[];
  emergency_contact?: string;
  is_primary?: boolean;
}

// ── Health Report ──────────────────────────────────────────────────────────────

export interface HealthReport {
  id: string;
  user_id: string;
  family_member_id: string;
  file_url: string;
  file_name: string;
  file_size_bytes: number | null;
  mime_type: string | null;
  report_type: ReportType;
  report_date: string | null;
  lab_name: string | null;
  doctor_name: string | null;
  ai_summary: string | null;
  risk_level: RiskLevel;
  processing_status: ProcessingStatus;
  created_at: string;
  updated_at: string;
}

export interface HealthReportList {
  items: HealthReport[];
  total: number;
  page: number;
  per_page: number;
}

// ── Health Metric ──────────────────────────────────────────────────────────────

export interface HealthMetric {
  id: string;
  family_member_id: string;
  report_id: string | null;
  test_name: string;
  value: number;
  unit: string | null;
  normal_range_min: number | null;
  normal_range_max: number | null;
  normal_range_text: string | null;
  status: MetricStatus;
  category: string | null;
  measured_at: string;
  notes: string | null;
  is_abnormal: boolean;
  created_at: string;
}

export interface MetricTrend {
  test_name: string;
  unit: string | null;
  normal_range_min: number | null;
  normal_range_max: number | null;
  data_points: {
    measured_at: string;
    value: number;
    status: MetricStatus;
  }[];
}

// ── AI Insight ─────────────────────────────────────────────────────────────────

export interface Recommendation {
  title: string;
  description: string;
  priority: "low" | "medium" | "high";
}

export interface AIInsight {
  id: string;
  family_member_id: string;
  report_id: string | null;
  summary: string;
  risk_level: RiskLevel;
  risk_factors: string[] | null;
  recommendations: { items: Recommendation[] } | null;
  disclaimer: string;
  model_used: string | null;
  created_at: string;
}

// ── UI Helpers ─────────────────────────────────────────────────────────────────

export const RISK_CONFIG: Record<RiskLevel, { label: string; color: string; bg: string; border: string }> = {
  low:      { label: "Low Risk",      color: "text-green-700",  bg: "bg-green-50",  border: "border-green-200" },
  moderate: { label: "Moderate Risk", color: "text-yellow-700", bg: "bg-yellow-50", border: "border-yellow-200" },
  high:     { label: "High Risk",     color: "text-red-700",    bg: "bg-red-50",    border: "border-red-200" },
  critical: { label: "Critical",      color: "text-red-900",    bg: "bg-red-100",   border: "border-red-400" },
};

export const METRIC_STATUS_CONFIG: Record<MetricStatus, { label: string; color: string; dot: string }> = {
  normal:       { label: "Normal",        color: "text-green-600",  dot: "bg-green-500"  },
  borderline:   { label: "Borderline",    color: "text-yellow-600", dot: "bg-yellow-500" },
  abnormal_low: { label: "Below Normal",  color: "text-red-600",    dot: "bg-red-500"    },
  abnormal_high:{ label: "Above Normal",  color: "text-red-600",    dot: "bg-red-500"    },
};

export const PROCESSING_STATUS_CONFIG: Record<ProcessingStatus, { label: string; color: string }> = {
  pending:    { label: "Queued",      color: "text-slate-500"  },
  processing: { label: "Analyzing",   color: "text-blue-600"   },
  done:       { label: "Complete",    color: "text-green-600"  },
  failed:     { label: "Failed",      color: "text-red-600"    },
};

// ── Prescription ───────────────────────────────────────────────────────────────

export interface Prescription {
  id: string;
  user_id: string;
  family_member_id: string;
  file_url: string;
  file_name: string;
  doctor_name: string | null;
  hospital_name: string | null;
  prescribed_date: string | null;
  valid_until: string | null;
  parsed_data: {
    medicines: ExtractedMedicine[];
    medicine_count: number;
    prompt_version: string;
  } | null;
  notes: string | null;
  processing_status: ProcessingStatus;
  created_at: string;
  updated_at: string;
}

export interface ExtractedMedicine {
  name: string;
  generic_name: string | null;
  dosage: string | null;
  form: string | null;
  frequency: string | null;
  instructions: string | null;
  duration_days: number | null;
}

// ── Medicine ───────────────────────────────────────────────────────────────────

export type MedicineForm = "tablet" | "capsule" | "syrup" | "injection" | "cream" | "drops" | "inhaler" | "other";

export interface Medicine {
  id: string;
  family_member_id: string;
  prescription_id: string | null;
  name: string;
  generic_name: string | null;
  dosage: string | null;
  form: MedicineForm | null;
  frequency: string | null;
  instructions: string | null;
  start_date: string | null;
  end_date: string | null;
  is_active: boolean;
  refill_reminder: boolean;
  created_at: string;
  updated_at: string;
}

export interface MedicineCreate {
  family_member_id: string;
  prescription_id?: string;
  name: string;
  generic_name?: string;
  dosage?: string;
  form?: MedicineForm;
  frequency?: string;
  instructions?: string;
  start_date?: string;
  end_date?: string;
  refill_reminder?: boolean;
}

export const MEDICINE_FORM_ICONS: Record<MedicineForm, string> = {
  tablet:   "💊",
  capsule:  "💊",
  syrup:    "🧴",
  injection:"💉",
  cream:    "🧴",
  drops:    "💧",
  inhaler:  "🫁",
  other:    "💊",
};

// ── Reminder ───────────────────────────────────────────────────────────────────

export type ReminderFrequency = "daily" | "twice_daily" | "weekly" | "custom";

export interface Reminder {
  id: string;
  user_id: string;
  family_member_id: string;
  medicine_id: string | null;
  title: string;
  message: string | null;
  reminder_time: string; // "HH:MM:SS"
  frequency: ReminderFrequency;
  whatsapp_number: string | null;
  is_active: boolean;
  last_sent_at: string | null;
  next_send_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReminderCreate {
  family_member_id: string;
  medicine_id?: string;
  title: string;
  message?: string;
  reminder_time: string; // "HH:MM"
  frequency: ReminderFrequency;
  whatsapp_number?: string;
}

export const REMINDER_FREQUENCY_LABELS: Record<ReminderFrequency, string> = {
  daily:       "Once daily",
  twice_daily: "Twice daily",
  weekly:      "Weekly",
  custom:      "Custom schedule",
};
