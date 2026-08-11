"""
Medisynth Live – Global Configuration
Central configuration for thresholds, weights, simulation parameters, and design tokens.
"""

# ──────────────────────────── Simulation Parameters ────────────────────────────
UPDATE_INTERVAL_MS = 2000  # Data generation interval in milliseconds
UPDATE_INTERVAL_S = UPDATE_INTERVAL_MS / 1000
BASELINE_CAPTURE_DURATION_S = 30  # Seconds to capture baseline
HISTORY_MAX_POINTS = 150  # Max data points to retain in history

# ──────────────────────────── Normal Mode Ranges ───────────────────────────────
NORMAL_HR_MIN = 62
NORMAL_HR_MAX = 78
NORMAL_HR_BASE = 70
NORMAL_SPO2_MIN = 96
NORMAL_SPO2_MAX = 99
NORMAL_SPO2_BASE = 97.5
NORMAL_BP_SYS_BASE = 120
NORMAL_BP_DIA_BASE = 80
NORMAL_RR_BASE = 16
NORMAL_TEMP_BASE = 36.8

# ──────────────────────────── Stress Mode Ranges ───────────────────────────────
STRESS_HR_MIN = 85
STRESS_HR_MAX = 115
STRESS_HR_TARGET = 105
STRESS_SPO2_MIN = 93
STRESS_SPO2_MAX = 97
STRESS_BP_SYS_TARGET = 145
STRESS_BP_DIA_TARGET = 92
STRESS_RR_TARGET = 22
STRESS_TEMP_TARGET = 37.2
STRESS_RAMP_DURATION_S = 30  # Time to reach peak stress

# ──────────────────────────── Critical Mode Ranges ─────────────────────────────
CRITICAL_HR_MIN = 120
CRITICAL_HR_MAX = 165
CRITICAL_SPO2_MIN = 82
CRITICAL_SPO2_MAX = 91
CRITICAL_BP_SYS_TARGET = 180
CRITICAL_BP_DIA_TARGET = 110
CRITICAL_RR_TARGET = 30
CRITICAL_TEMP_TARGET = 38.8
CRITICAL_HR_ERRATIC_AMPLITUDE = 15  # Additional erratic swing

# ──────────────────────────── Sleep Mode Ranges ────────────────────────────────
SLEEP_HR_BASE = 58
SLEEP_SPO2_BASE = 97.0
SLEEP_BP_SYS_BASE = 105
SLEEP_BP_DIA_BASE = 68
SLEEP_RR_BASE = 12
SLEEP_TEMP_BASE = 36.3

# ──────────────────────────── Exercise Mode Ranges ─────────────────────────────
EXERCISE_HR_TARGET = 155
EXERCISE_SPO2_BASE = 96.5
EXERCISE_BP_SYS_TARGET = 165
EXERCISE_BP_DIA_TARGET = 85
EXERCISE_RR_TARGET = 28
EXERCISE_TEMP_TARGET = 38.2
EXERCISE_RAMP_DURATION_S = 20

# ──────────────────────────── Recovery Mode Ranges ─────────────────────────────
RECOVERY_HR_START = 140
RECOVERY_DECAY_HALF_LIFE_S = 30  # HR halves deviation in this many seconds

# ──────────────────────────── Detection Thresholds ─────────────────────────────
TACHYCARDIA_HR_THRESHOLD = 100
BRADYCARDIA_HR_THRESHOLD = 50
HYPOXIA_SPO2_THRESHOLD = 92
HYPERTENSION_SYS_THRESHOLD = 140
HYPERTENSION_DIA_THRESHOLD = 90
HYPOTENSION_SYS_THRESHOLD = 90
HYPOTENSION_DIA_THRESHOLD = 60
TACHYPNEA_RR_THRESHOLD = 24
BRADYPNEA_RR_THRESHOLD = 10
FEVER_TEMP_THRESHOLD = 38.0
HYPOTHERMIA_TEMP_THRESHOLD = 35.5
SUSTAINED_DURATION_S = 10  # Seconds condition must persist
HYPOXIA_SUSTAINED_S = 6
TREND_SLOPE_THRESHOLD = 2.0  # bpm per reading — rapid change
DEVIATION_WARNING_PCT = 15  # Baseline deviation warning
DEVIATION_CRITICAL_PCT = 30  # Baseline deviation critical

# Arrhythmia detection
HRV_IRREGULARITY_THRESHOLD = 0.25  # CV of RR-intervals
ARRHYTHMIA_WINDOW = 10  # Number of readings to analyze

# Multi-vital correlation (shock detection)
SHOCK_HR_MIN = 110
SHOCK_SYS_MAX = 90
SHOCK_SPO2_MAX = 93

# ──────────────────────────── Health Score Weights ─────────────────────────────
SCORE_WEIGHT_HR = 0.25
SCORE_WEIGHT_SPO2 = 0.20
SCORE_WEIGHT_BP = 0.15
SCORE_WEIGHT_RR = 0.10
SCORE_WEIGHT_TEMP = 0.05
SCORE_WEIGHT_DEVIATION = 0.15
SCORE_WEIGHT_CONFIDENCE = 0.05
SCORE_WEIGHT_TREND = 0.05

# Health Score deduction ranges (max deduction per category)
SCORE_HR_MAX_DEDUCTION = 25
SCORE_SPO2_MAX_DEDUCTION = 30
SCORE_BP_MAX_DEDUCTION = 20
SCORE_RR_MAX_DEDUCTION = 15
SCORE_TEMP_MAX_DEDUCTION = 15
SCORE_DEVIATION_MAX_DEDUCTION = 20
SCORE_CONFIDENCE_MAX_DEDUCTION = 10
SCORE_TREND_MAX_DEDUCTION = 10

# Health Score status thresholds
SCORE_EXCELLENT_MIN = 90
SCORE_GOOD_MIN = 75
SCORE_MILD_RISK_MIN = 60
SCORE_MODERATE_RISK_MIN = 40
# Below 40 = Critical

# ──────────────────────────── Emergency Thresholds ─────────────────────────────
EMERGENCY_SCORE_THRESHOLD = 40  # Score below this triggers emergency
ALERT_COOLDOWN_S = 30  # Minimum seconds between alerts

# ──────────────────────────── Preprocessing ────────────────────────────────────
SMOOTHING_WINDOW = 5  # Moving average window size
OUTLIER_Z_THRESHOLD = 3.0  # Z-score threshold for outlier rejection
MIN_CONFIDENCE = 10  # Minimum confidence score (%)

# ──────────────────────────── Risk Prediction ──────────────────────────────────
PREDICTION_HORIZON_S = 180  # 3-minute forward prediction
PREDICTION_MIN_POINTS = 10  # Min data points for prediction

# ──────────────────────────── Design Tokens ────────────────────────────────────
COLORS = {
    "bg_primary": "#0a0e1a",
    "bg_secondary": "#0f1428",
    "bg_card": "rgba(255, 255, 255, 0.04)",
    "bg_card_hover": "rgba(255, 255, 255, 0.07)",
    "accent_primary": "#00d4aa",
    "accent_secondary": "#7c3aed",
    "accent_gradient_start": "#00d4aa",
    "accent_gradient_end": "#7c3aed",
    "warning": "#ffb347",
    "critical": "#ff4757",
    "success": "#00d4aa",
    "text_primary": "#e8eaf6",
    "text_secondary": "#7986cb",
    "text_muted": "#4a5568",
    "border": "rgba(255, 255, 255, 0.06)",
    "shadow": "rgba(0, 0, 0, 0.3)",
    "glass_bg": "rgba(15, 20, 40, 0.8)",
    "glass_border": "rgba(255, 255, 255, 0.08)",
    # Status colors
    "status_stable": "#00d4aa",
    "status_monitoring": "#ffb347",
    "status_critical": "#ff4757",
    # Score gradient
    "score_excellent": "#00d4aa",
    "score_good": "#4ade80",
    "score_mild": "#fbbf24",
    "score_moderate": "#f97316",
    "score_critical": "#ff4757",
    # Vital sign colors
    "vital_hr": "#00d4aa",
    "vital_spo2": "#a78bfa",
    "vital_bp": "#f472b6",
    "vital_rr": "#38bdf8",
    "vital_temp": "#fbbf24",
}

FONTS = {
    "primary": "'Inter', sans-serif",
    "mono": "'JetBrains Mono', 'Fira Code', monospace",
}

# ──────────────────────────── Status Labels ────────────────────────────────────
STATUS_LABELS = {
    "stable": {"emoji": "🟢", "label": "Stable", "color": COLORS["status_stable"]},
    "monitoring": {"emoji": "🟡", "label": "Monitoring", "color": COLORS["status_monitoring"]},
    "critical": {"emoji": "🔴", "label": "Critical", "color": COLORS["status_critical"]},
}

SCORE_STATUS_MAP = {
    "excellent": {"label": "Excellent", "color": COLORS["score_excellent"], "emoji": "💚"},
    "good": {"label": "Good", "color": COLORS["score_good"], "emoji": "💙"},
    "mild_risk": {"label": "Mild Risk", "color": COLORS["score_mild"], "emoji": "💛"},
    "moderate_risk": {"label": "Moderate Risk", "color": COLORS["score_moderate"], "emoji": "🧡"},
    "critical": {"label": "Critical", "color": COLORS["score_critical"], "emoji": "❤️‍🔥"},
}

# ──────────────────────────── Mode Definitions ─────────────────────────────────
SIMULATION_MODES = {
    "normal": {"label": "Normal", "icon": "💚", "description": "Stable vital signs"},
    "stress": {"label": "Stress", "icon": "💛", "description": "Gradual cardiac stress simulation"},
    "critical": {"label": "Critical Event", "icon": "🔴", "description": "Heart attack / severe event simulation"},
    "sleep": {"label": "Sleep", "icon": "🌙", "description": "Resting / sleep state vitals"},
    "exercise": {"label": "Exercise", "icon": "🏃", "description": "Physical activity simulation"},
    "recovery": {"label": "Recovery", "icon": "🔄", "description": "Post-exertion recovery decay"},
}

# ──────────────────────────── Notification Service ──────────────────────────────
# Configure ONE of the following providers via environment variables:
#
# Option 1: Twilio SMS (industry standard)
#   TWILIO_ACCOUNT_SID=your_sid
#   TWILIO_AUTH_TOKEN=your_token
#   TWILIO_PHONE_NUMBER=+1234567890
#
# Option 2: CallMeBot WhatsApp (free, requires registration)
#   CALLMEBOT_API_KEY=your_key
#   Register: https://www.callmebot.com/blog/free-api-whatsapp-messages/
#
# Option 3: Email SMTP (free via Gmail App Password)
#   SMTP_EMAIL=your_email@gmail.com
#   SMTP_PASSWORD=your_app_password
#   SMTP_HOST=smtp.gmail.com  (default)
#   SMTP_PORT=587  (default)
#
# Option 4: Textbelt (1 free SMS/day, zero config — default fallback)
#
NOTIFICATION_COOLDOWN_S = 60  # Min seconds between notifications to same contact
AUTO_EMERGENCY_ENABLED = True  # Auto-send notifications on critical alerts

