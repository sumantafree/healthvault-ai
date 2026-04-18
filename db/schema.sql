-- ============================================================
-- HealthVault AI — PostgreSQL Schema
-- Database Architect Agent
-- ============================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";   -- for full-text search

-- ============================================================
-- ENUM TYPES
-- ============================================================

CREATE TYPE gender_enum AS ENUM ('male', 'female', 'other');
CREATE TYPE blood_type_enum AS ENUM ('A+','A-','B+','B-','AB+','AB-','O+','O-','unknown');
CREATE TYPE risk_level_enum AS ENUM ('low', 'moderate', 'high', 'critical');
CREATE TYPE metric_status_enum AS ENUM ('normal', 'borderline', 'abnormal_low', 'abnormal_high');
CREATE TYPE report_type_enum AS ENUM ('blood_test', 'urine_test', 'imaging', 'prescription', 'vaccination', 'other');
CREATE TYPE reminder_frequency_enum AS ENUM ('once', 'daily', 'twice_daily', 'weekly', 'custom');
CREATE TYPE user_role_enum AS ENUM ('owner', 'member', 'viewer');

-- ============================================================
-- TABLE: users
-- Synced from Supabase Auth; extended with app-specific fields
-- ============================================================

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supabase_uid    UUID UNIQUE NOT NULL,           -- links to auth.users
    email           VARCHAR(255) UNIQUE NOT NULL,
    full_name       VARCHAR(255),
    avatar_url      TEXT,
    phone           VARCHAR(20),
    role            user_role_enum DEFAULT 'owner',
    whatsapp_number VARCHAR(20),
    timezone        VARCHAR(50) DEFAULT 'UTC',
    is_active       BOOLEAN DEFAULT TRUE,
    onboarded       BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_supabase_uid ON users(supabase_uid);
CREATE INDEX idx_users_email ON users(email);

-- ============================================================
-- TABLE: family_members
-- Each user can manage multiple family profiles
-- ============================================================

CREATE TABLE family_members (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            VARCHAR(255) NOT NULL,
    date_of_birth   DATE,
    gender          gender_enum DEFAULT 'other',
    blood_type      blood_type_enum DEFAULT 'unknown',
    height_cm       NUMERIC(5,2),
    weight_kg       NUMERIC(5,2),
    allergies       TEXT[],                         -- array of allergy strings
    chronic_conditions TEXT[],
    emergency_contact VARCHAR(255),
    avatar_url      TEXT,
    is_primary      BOOLEAN DEFAULT FALSE,          -- marks the user themselves
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_family_user_id ON family_members(user_id);

-- ============================================================
-- TABLE: health_reports
-- Uploaded documents (lab reports, prescriptions, etc.)
-- ============================================================

CREATE TABLE health_reports (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    family_member_id    UUID NOT NULL REFERENCES family_members(id) ON DELETE CASCADE,
    file_url            TEXT NOT NULL,
    file_name           VARCHAR(255) NOT NULL,
    file_size_bytes     BIGINT,
    mime_type           VARCHAR(100),
    report_type         report_type_enum DEFAULT 'other',
    report_date         DATE,
    lab_name            VARCHAR(255),
    doctor_name         VARCHAR(255),
    raw_text            TEXT,                       -- OCR extracted text
    parsed_data         JSONB,                      -- structured LLM output
    ai_summary          TEXT,                       -- LLM narrative summary
    risk_level          risk_level_enum DEFAULT 'low',
    processing_status   VARCHAR(50) DEFAULT 'pending',  -- pending|processing|done|failed
    processing_error    TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_reports_family_member ON health_reports(family_member_id);
CREATE INDEX idx_reports_user_id ON health_reports(user_id);
CREATE INDEX idx_reports_report_date ON health_reports(report_date DESC);
CREATE INDEX idx_reports_parsed_data ON health_reports USING GIN(parsed_data);

-- ============================================================
-- TABLE: health_metrics
-- Individual structured data points extracted from reports
-- ============================================================

CREATE TABLE health_metrics (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    family_member_id    UUID NOT NULL REFERENCES family_members(id) ON DELETE CASCADE,
    report_id           UUID REFERENCES health_reports(id) ON DELETE SET NULL,
    test_name           VARCHAR(255) NOT NULL,
    value               NUMERIC(12,4) NOT NULL,
    unit                VARCHAR(50),
    normal_range_min    NUMERIC(12,4),
    normal_range_max    NUMERIC(12,4),
    normal_range_text   VARCHAR(100),               -- e.g., "<5.7%" for HbA1c
    status              metric_status_enum DEFAULT 'normal',
    category            VARCHAR(100),               -- e.g., 'CBC', 'Lipid Panel', 'Thyroid'
    measured_at         TIMESTAMPTZ NOT NULL,
    notes               TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_metrics_family_member ON health_metrics(family_member_id);
CREATE INDEX idx_metrics_test_name ON health_metrics(test_name);
CREATE INDEX idx_metrics_measured_at ON health_metrics(measured_at DESC);
CREATE INDEX idx_metrics_status ON health_metrics(status);
-- Composite for trend queries
CREATE INDEX idx_metrics_member_test_date ON health_metrics(family_member_id, test_name, measured_at DESC);

-- ============================================================
-- TABLE: ai_insights
-- LLM-generated health analysis per report
-- ============================================================

CREATE TABLE ai_insights (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    family_member_id    UUID NOT NULL REFERENCES family_members(id) ON DELETE CASCADE,
    report_id           UUID REFERENCES health_reports(id) ON DELETE CASCADE,
    summary             TEXT NOT NULL,
    risk_level          risk_level_enum DEFAULT 'low',
    risk_factors        TEXT[],
    recommendations     JSONB,                      -- array of recommendation objects
    disclaimer          TEXT DEFAULT 'This analysis is for informational purposes only and does not constitute medical advice. Consult a qualified healthcare professional.',
    model_used          VARCHAR(100),
    prompt_version      VARCHAR(20),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_insights_family_member ON ai_insights(family_member_id);
CREATE INDEX idx_insights_report_id ON ai_insights(report_id);
CREATE INDEX idx_insights_risk_level ON ai_insights(risk_level);

-- ============================================================
-- TABLE: prescriptions
-- Uploaded prescription documents
-- ============================================================

CREATE TABLE prescriptions (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    family_member_id    UUID NOT NULL REFERENCES family_members(id) ON DELETE CASCADE,
    file_url            TEXT NOT NULL,
    file_name           VARCHAR(255) NOT NULL,
    doctor_name         VARCHAR(255),
    hospital_name       VARCHAR(255),
    prescribed_date     DATE,
    valid_until         DATE,
    parsed_data         JSONB,
    notes               TEXT,
    processing_status   VARCHAR(50) DEFAULT 'pending',
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_prescriptions_family ON prescriptions(family_member_id);

-- ============================================================
-- TABLE: medicines
-- Extracted from prescriptions or manually added
-- ============================================================

CREATE TABLE medicines (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    family_member_id    UUID NOT NULL REFERENCES family_members(id) ON DELETE CASCADE,
    prescription_id     UUID REFERENCES prescriptions(id) ON DELETE SET NULL,
    name                VARCHAR(255) NOT NULL,
    generic_name        VARCHAR(255),
    dosage              VARCHAR(100),               -- e.g., "500mg"
    form                VARCHAR(100),               -- tablet, syrup, injection
    frequency           VARCHAR(100),               -- e.g., "twice daily"
    instructions        TEXT,                       -- "take with food"
    start_date          DATE,
    end_date            DATE,
    is_active           BOOLEAN DEFAULT TRUE,
    refill_reminder     BOOLEAN DEFAULT FALSE,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_medicines_family ON medicines(family_member_id);
CREATE INDEX idx_medicines_active ON medicines(is_active) WHERE is_active = TRUE;

-- ============================================================
-- TABLE: reminders
-- Scheduled medicine or health check reminders
-- ============================================================

CREATE TABLE reminders (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    family_member_id    UUID NOT NULL REFERENCES family_members(id) ON DELETE CASCADE,
    medicine_id         UUID REFERENCES medicines(id) ON DELETE CASCADE,
    title               VARCHAR(255) NOT NULL,
    message             TEXT,
    reminder_time       TIME NOT NULL,
    frequency           reminder_frequency_enum DEFAULT 'daily',
    custom_cron         VARCHAR(100),
    whatsapp_number     VARCHAR(20),
    is_active           BOOLEAN DEFAULT TRUE,
    last_sent_at        TIMESTAMPTZ,
    next_send_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_reminders_user ON reminders(user_id);
CREATE INDEX idx_reminders_active ON reminders(is_active, next_send_at) WHERE is_active = TRUE;

-- ============================================================
-- TABLE: notification_logs
-- Tracks all sent WhatsApp / push notifications
-- ============================================================

CREATE TABLE notification_logs (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    family_member_id    UUID REFERENCES family_members(id) ON DELETE SET NULL,
    reminder_id         UUID REFERENCES reminders(id) ON DELETE SET NULL,
    channel             VARCHAR(50) DEFAULT 'whatsapp',  -- whatsapp | push | email
    recipient           VARCHAR(100),
    message             TEXT,
    status              VARCHAR(50) DEFAULT 'sent',      -- sent | failed | delivered
    provider_response   JSONB,
    sent_at             TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_notif_user ON notification_logs(user_id);
CREATE INDEX idx_notif_sent_at ON notification_logs(sent_at DESC);

-- ============================================================
-- TRIGGERS: auto-update updated_at columns
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_family_members_updated_at
    BEFORE UPDATE ON family_members
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_health_reports_updated_at
    BEFORE UPDATE ON health_reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_prescriptions_updated_at
    BEFORE UPDATE ON prescriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_medicines_updated_at
    BEFORE UPDATE ON medicines
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_reminders_updated_at
    BEFORE UPDATE ON reminders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- ROW LEVEL SECURITY (Supabase RLS)
-- ============================================================

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE family_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE prescriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE medicines ENABLE ROW LEVEL SECURITY;
ALTER TABLE reminders ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_logs ENABLE ROW LEVEL SECURITY;

-- Users can only read/write their own data
CREATE POLICY "users_own_data" ON users
    FOR ALL USING (supabase_uid = auth.uid());

CREATE POLICY "family_members_own_data" ON family_members
    FOR ALL USING (user_id = (SELECT id FROM users WHERE supabase_uid = auth.uid()));

CREATE POLICY "health_reports_own_data" ON health_reports
    FOR ALL USING (user_id = (SELECT id FROM users WHERE supabase_uid = auth.uid()));

CREATE POLICY "health_metrics_own_data" ON health_metrics
    FOR ALL USING (
        family_member_id IN (
            SELECT id FROM family_members
            WHERE user_id = (SELECT id FROM users WHERE supabase_uid = auth.uid())
        )
    );

CREATE POLICY "ai_insights_own_data" ON ai_insights
    FOR ALL USING (
        family_member_id IN (
            SELECT id FROM family_members
            WHERE user_id = (SELECT id FROM users WHERE supabase_uid = auth.uid())
        )
    );

CREATE POLICY "prescriptions_own_data" ON prescriptions
    FOR ALL USING (user_id = (SELECT id FROM users WHERE supabase_uid = auth.uid()));

CREATE POLICY "medicines_own_data" ON medicines
    FOR ALL USING (
        family_member_id IN (
            SELECT id FROM family_members
            WHERE user_id = (SELECT id FROM users WHERE supabase_uid = auth.uid())
        )
    );

CREATE POLICY "reminders_own_data" ON reminders
    FOR ALL USING (user_id = (SELECT id FROM users WHERE supabase_uid = auth.uid()));

CREATE POLICY "notification_logs_own_data" ON notification_logs
    FOR ALL USING (user_id = (SELECT id FROM users WHERE supabase_uid = auth.uid()));
