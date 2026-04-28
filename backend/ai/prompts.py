"""
HealthVault AI — Prompt Library
Versioned, structured prompts for OCR post-processing and health report analysis.

Design principles:
  - No diagnosis language — observation only
  - Always produce valid JSON
  - Version-tagged for rollback capability
"""

PROMPT_VERSION = "1.2"

# ── SYSTEM PROMPTS ─────────────────────────────────────────────────────────────

SYSTEM_REPORT_PARSER = """You are a medical data extraction assistant for HealthVault AI.
Your job is to extract structured health data from lab reports, blood tests, and medical documents.

STRICT RULES:
1. Extract ONLY data explicitly present in the text — never infer or fabricate values.
2. Do NOT provide diagnoses, prognoses, or medical opinions.
3. Return ONLY valid JSON matching the schema exactly.
4. If a field is not found, use null.
5. All numeric values must be numbers (not strings).
6. Normalize test names to common English terms (e.g., "Hb" → "Hemoglobin").
"""

SYSTEM_INSIGHTS = """You are a health data analyst assistant for HealthVault AI.
You analyze structured health metrics and provide informational summaries.

STRICT RULES:
1. You are NOT a doctor. You do NOT diagnose any condition.
2. Use language like "values appear elevated", "within reference range", "may warrant attention".
3. Base ALL observations only on the data provided — never speculate.
4. Always include the disclaimer in your output exactly as provided.
5. Return ONLY valid JSON matching the schema exactly.
6. Risk levels: "low" (all normal), "moderate" (borderline/mildly abnormal),
   "high" (significantly abnormal), "critical" (severely out of range).
"""

# ── USER PROMPTS ───────────────────────────────────────────────────────────────

def build_parser_prompt(raw_text: str, report_type: str = "blood_test") -> str:
    return f"""Extract all health metrics from the following medical report text.
Report type hint: {report_type}

REPORT TEXT:
\"\"\"
{raw_text[:6000]}
\"\"\"

Return a JSON object with EXACTLY this structure:
{{
  "report_date": "YYYY-MM-DD or null",
  "lab_name": "string or null",
  "doctor_name": "string or null",
  "report_type": "blood_test|urine_test|imaging|other",
  "metrics": [
    {{
      "test_name": "Full test name",
      "value": 0.0,
      "unit": "unit string or null",
      "normal_range_min": 0.0 or null,
      "normal_range_max": 0.0 or null,
      "normal_range_text": "e.g. 4.0-11.0 or null",
      "status": "normal|borderline|abnormal_low|abnormal_high",
      "category": "CBC|Lipid Panel|Thyroid|Liver|Kidney|Diabetes|Urine|Electrolytes|Other"
    }}
  ]
}}

Status determination:
- "normal": value within normal range
- "borderline": within 10% outside normal range
- "abnormal_low": value below normal range by more than 10%
- "abnormal_high": value above normal range by more than 10%

If no metrics are found, return {{"metrics": [], "report_date": null, "lab_name": null, "doctor_name": null, "report_type": "{report_type}"}}
"""


def build_insights_prompt(
    metrics: list[dict],
    member_context: dict,
    disclaimer: str,
) -> str:
    import json
    from datetime import date, datetime
    from decimal import Decimal

    def _default(o):
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, (date, datetime)):
            return o.isoformat()
        return str(o)

    metrics_json = json.dumps(metrics, indent=2, default=_default)
    context_json = json.dumps(member_context, indent=2, default=_default)

    return f"""Analyze the following health metrics for a patient and provide an informational health summary.

PATIENT CONTEXT:
{context_json}

HEALTH METRICS:
{metrics_json}

Return a JSON object with EXACTLY this structure:
{{
  "summary": "2-4 sentence narrative summary of the health data. Objective, non-diagnostic language only.",
  "risk_level": "low|moderate|high|critical",
  "risk_factors": ["list", "of", "specific", "observations", "for", "abnormal", "values"],
  "recommendations": [
    {{
      "title": "short title",
      "description": "actionable suggestion (e.g. consult a doctor, retest in X weeks, lifestyle change)",
      "priority": "low|medium|high"
    }}
  ],
  "disclaimer": "{disclaimer}"
}}

Risk level guidelines:
- "low": all metrics within normal range
- "moderate": 1-2 borderline or mildly abnormal values
- "high": 3+ abnormal values or 1-2 significantly abnormal values
- "critical": any value severely out of range requiring immediate attention

Always end recommendations with one item: {{"title": "Consult Your Doctor", "description": "Share this report with your healthcare provider for professional evaluation.", "priority": "high"}}
"""


def build_ocr_cleanup_prompt(raw_ocr: str) -> str:
    """Used to clean noisy OCR output before parsing."""
    return f"""Clean and structure the following raw OCR text from a medical report.
Fix obvious OCR errors (e.g., "0" vs "O", broken line spacing, garbled numbers).
Preserve all numeric values exactly — do not change any numbers.
Return only the cleaned text, no commentary.

RAW OCR TEXT:
{raw_ocr[:4000]}
"""


# ── PRESCRIPTION PROMPTS ──────────────────────────────────────────────────────

SYSTEM_PRESCRIPTION_PARSER = """You are a medical data extraction assistant for HealthVault AI.
Your job is to extract structured medicine information from doctor prescriptions.

STRICT RULES:
1. Extract ONLY data explicitly present in the text — never infer or fabricate.
2. Do NOT provide medical advice or dosage recommendations beyond what is written.
3. Return ONLY valid JSON matching the schema exactly.
4. If a field is not found, use null.
5. Normalize medicine names to their common English names.
"""


def build_prescription_parser_prompt(raw_text: str) -> str:
    return f"""Extract all prescription information from the following text.

PRESCRIPTION TEXT:
\"\"\"
{raw_text[:5000]}
\"\"\"

Return a JSON object with EXACTLY this structure:
{{
  "doctor_name": "string or null",
  "hospital_name": "string or null",
  "prescribed_date": "YYYY-MM-DD or null",
  "valid_until": "YYYY-MM-DD or null",
  "medicines": [
    {{
      "name": "Brand/common medicine name",
      "generic_name": "Generic name or null",
      "dosage": "e.g. 500mg, 10ml, null",
      "form": "tablet|capsule|syrup|injection|cream|drops|inhaler|other or null",
      "frequency": "e.g. once daily, twice daily, every 8 hours or null",
      "instructions": "e.g. take with food, before meals or null",
      "duration_days": integer or null
    }}
  ]
}}

If no medicines are found, return {{"medicines": [], "doctor_name": null, "hospital_name": null, "prescribed_date": null, "valid_until": null}}
"""
