"""
Medisynth Live – Premium UI Components
Animated SVG health gauge, sparkline mini-charts, risk prediction panel,
vital cards, AI reasoning, and emergency alert components.
"""

import streamlit as st
import plotly.graph_objects as go
from typing import List, Optional
import math
import time


def _html(content: str):
    """Render HTML content reliably."""
    st.html(content)


# ──────────────────────────── Animated SVG Health Gauge ────────────────────────

def render_health_gauge(score: float, status_label: str, color: str, emoji: str):
    """Render a circular SVG health gauge with animated arc."""
    pct = max(0, min(100, score))
    radius = 70
    circumference = 2 * math.pi * radius
    dash = circumference * pct / 100
    gap = circumference - dash

    # Gradient colors based on score
    if pct >= 90:
        arc_color, glow = "#00d4aa", "rgba(0,212,170,0.3)"
    elif pct >= 75:
        arc_color, glow = "#4ade80", "rgba(74,222,128,0.3)"
    elif pct >= 60:
        arc_color, glow = "#fbbf24", "rgba(251,191,36,0.3)"
    elif pct >= 40:
        arc_color, glow = "#f97316", "rgba(249,115,22,0.3)"
    else:
        arc_color, glow = "#ff4757", "rgba(255,71,87,0.3)"

    _html(f"""
    <div style="text-align:center; padding:16px 0;">
        <div style="font-size:0.8rem; font-weight:600; text-transform:uppercase;
            letter-spacing:2px; color:#7986cb; margin-bottom:8px;">AI HEALTH SCORE</div>
        <svg width="200" height="200" viewBox="0 0 200 200" style="filter:drop-shadow(0 0 12px {glow});">
            <!-- Background circle -->
            <circle cx="100" cy="100" r="{radius}" fill="none"
                stroke="rgba(255,255,255,0.06)" stroke-width="10"/>
            <!-- Animated arc -->
            <circle cx="100" cy="100" r="{radius}" fill="none"
                stroke="{arc_color}" stroke-width="10" stroke-linecap="round"
                stroke-dasharray="{dash:.1f} {gap:.1f}"
                transform="rotate(-90 100 100)"
                style="transition: stroke-dasharray 1s cubic-bezier(0.4,0,0.2,1);">
                <animate attributeName="stroke-dasharray"
                    from="0 {circumference}" to="{dash:.1f} {gap:.1f}"
                    dur="1.2s" fill="freeze" />
            </circle>
            <!-- Score text -->
            <text x="100" y="90" text-anchor="middle" font-size="48"
                font-weight="900" fill="{arc_color}" font-family="Inter,sans-serif">{pct:.0f}</text>
            <text x="100" y="115" text-anchor="middle" font-size="12"
                font-weight="500" fill="#7986cb" font-family="Inter,sans-serif">/ 100</text>
        </svg>
        <div style="margin-top:4px;">
            <span style="background:rgba(255,255,255,0.06); padding:6px 16px; border-radius:20px;
                font-weight:600; font-size:1rem; color:{arc_color};">
                {emoji} {status_label}
            </span>
        </div>
    </div>
    """)


# ──────────────────────────── Sparkline Mini-Chart ────────────────────────────

def render_sparkline(data: List[float], color: str = "#00d4aa", height: int = 30, width: int = 120):
    """Render a tiny inline SVG sparkline chart."""
    if len(data) < 2:
        return ""
    recent = data[-20:]
    n = len(recent)
    mn, mx = min(recent), max(recent)
    rng = mx - mn if mx != mn else 1

    points = []
    for i, v in enumerate(recent):
        x = (i / (n - 1)) * width
        y = height - ((v - mn) / rng) * (height - 4) - 2
        points.append(f"{x:.1f},{y:.1f}")

    polyline = " ".join(points)
    last_y = height - ((recent[-1] - mn) / rng) * (height - 4) - 2

    return f"""
    <svg width="{width}" height="{height}" style="display:inline-block; vertical-align:middle;">
        <polyline points="{polyline}" fill="none" stroke="{color}" stroke-width="1.5"
            stroke-linejoin="round" stroke-linecap="round" opacity="0.7"/>
        <circle cx="{width}" cy="{last_y:.1f}" r="2.5" fill="{color}"/>
    </svg>
    """


# ──────────────────────────── Vital Card with Sparkline ───────────────────────

def render_vital_card(label: str, value: float, unit: str, icon: str = "💓",
                      color: str = "#00d4aa", trend: str = "→ Stable",
                      sparkline_data: List[float] = None):
    """Render a premium vital card with optional sparkline."""
    spark_svg = render_sparkline(sparkline_data, color) if sparkline_data and len(sparkline_data) > 2 else ""

    _html(f"""
    <div class="vital-card">
        <div class="vital-label">{icon} {label}</div>
        <div class="vital-value">{value:.1f}</div>
        <div class="vital-unit">{unit}</div>
        <div style="color:{color}; font-size:0.75rem; font-weight:500; margin-top:4px;">{trend}</div>
        {f'<div style="margin-top:8px;">{spark_svg}</div>' if spark_svg else ''}
    </div>
    """)


# ──────────────────────────── BP Card (Special) ──────────────────────────────

def render_bp_card(sys: float, dia: float, sparkline_data: List[float] = None):
    """Render a blood pressure card with systolic/diastolic."""
    color = "#f472b6"
    if sys > 140 or dia > 90:
        color = "#ff4757"
    elif sys < 90:
        color = "#ffb347"

    spark_svg = render_sparkline(sparkline_data, color) if sparkline_data and len(sparkline_data) > 2 else ""

    _html(f"""
    <div class="vital-card">
        <div class="vital-label">🩸 Blood Pressure</div>
        <div style="font-size:2.2rem; font-weight:800; color:{color}; line-height:1.1;">
            {sys:.0f}<span style="font-size:1.2rem; color:#7986cb;">/</span>{dia:.0f}
        </div>
        <div class="vital-unit">mmHg</div>
        {f'<div style="margin-top:8px;">{spark_svg}</div>' if spark_svg else ''}
    </div>
    """)


# ──────────────────────────── Risk Prediction Panel ──────────────────────────

def render_risk_prediction(prediction):
    """Render the 3-minute risk prediction panel."""
    if not prediction:
        return

    dir_color = {"improving": "#00d4aa", "stable": "#7986cb", "deteriorating": "#ff4757"}
    dir_icon = {"improving": "↗", "stable": "→", "deteriorating": "↘"}
    color = dir_color.get(prediction.trend_direction, "#7986cb")
    icon = dir_icon.get(prediction.trend_direction, "→")

    ttc_html = ""
    if prediction.time_to_critical_s:
        mins = prediction.time_to_critical_s / 60
        ttc_html = f"""
        <div style="color:#ff4757; font-weight:700; margin-top:8px; padding:8px;
            background:rgba(255,71,87,0.1); border-radius:8px; font-size:0.85rem;">
            Time to critical: {mins:.1f} min
        </div>"""

    _html(f"""
    <div class="glass-card" style="border-color:rgba(124,58,237,0.2);">
        <div class="section-header">3-Min Risk Prediction</div>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <div>
                <div style="color:#7986cb; font-size:0.75rem;">TREND</div>
                <div style="color:{color}; font-weight:700; font-size:1.1rem;">
                    {icon} {prediction.trend_direction.upper()}
                </div>
            </div>
            <div style="text-align:right;">
                <div style="color:#7986cb; font-size:0.75rem;">CONFIDENCE</div>
                <div style="color:#e8eaf6; font-weight:600;">{prediction.confidence:.0f}%</div>
            </div>
        </div>
        <div style="display:flex; gap:16px; font-size:0.85rem; color:#c5cae9;">
            <div>Predicted HR: <strong>{prediction.predicted_hr:.0f}</strong> bpm</div>
            <div>Predicted SpO2: <strong>{prediction.predicted_spo2:.1f}</strong>%</div>
        </div>
        <div style="font-size:0.8rem; color:#7986cb; margin-top:4px;">
            HR Range: {prediction.hr_lower:.0f} - {prediction.hr_upper:.0f} bpm
        </div>
        {ttc_html}
    </div>
    """)


def render_prediction_window(ai_result, score_result=None, processed=None):
    """Render PREDICTIVE HEALTH INTELLIGENCE panel matching reference design."""
    if not ai_result:
        return

    rp = ai_result.risk_prediction
    detections = ai_result.detections or []
    anomaly = ai_result.anomaly_score
    current_score = score_result.score if score_result else 100

    # Compute 3 time horizon predictions
    if rp:
        trend = rp.trend_direction
        pred_5 = max(0, min(100, rp.predicted_score * 0.6 + current_score * 0.4))
        pred_10 = rp.predicted_score
        pred_15 = max(0, min(100, rp.predicted_score * 1.3 - current_score * 0.3))
        conf_5 = min(95, rp.confidence + 10)
        conf_10 = rp.confidence
        conf_15 = max(20, rp.confidence - 15)
    else:
        trend = "stable"
        pred_5 = current_score
        pred_10 = current_score
        pred_15 = current_score
        conf_5 = 70
        conf_10 = 50
        conf_15 = 30

    def _status(score):
        if score >= 80: return ("#00d4aa", "STABLE")
        if score >= 60: return ("#fbbf24", "CAUTION")
        if score >= 40: return ("#f97316", "WARNING")
        return ("#ff4757", "CRITICAL")

    trend_icons = {"improving": "↗", "stable": "■", "deteriorating": "↘"}
    trend_colors = {"improving": "#00d4aa", "stable": "#7986cb", "deteriorating": "#ff4757"}
    t_icon = trend_icons.get(trend, "■")
    t_color = trend_colors.get(trend, "#7986cb")

    # Build 3 horizon cards
    horizons = [
        ("NEXT 5 MIN", pred_5, conf_5),
        ("NEXT 10 MIN", pred_10, conf_10),
        ("NEXT 15 MIN", pred_15, conf_15),
    ]
    cards_html = ""
    for label, score, conf in horizons:
        color, status = _status(score)
        cards_html += f"""
        <div style="flex:1; text-align:center; padding:10px 6px;
            background:rgba(15,20,40,0.6); border:1px solid rgba(255,255,255,0.05);
            border-radius:10px;">
            <div style="font-size:0.55rem; color:#5c6b8a; font-weight:600;
                letter-spacing:1px; margin-bottom:6px;">{label}</div>
            <div style="font-size:1.8rem; font-weight:900; color:{color};
                font-family:'JetBrains Mono',monospace; line-height:1;">{score:.0f}%</div>
            <div style="font-size:0.55rem; color:{color}; font-weight:700;
                letter-spacing:0.5px; margin:4px 0;">{status}</div>
            <div style="display:flex; justify-content:center; gap:4px; align-items:center;">
                <span style="color:{t_color}; font-size:0.6rem; font-weight:600;">{t_icon}</span>
                <span style="color:#5c6b8a; font-size:0.55rem;">{trend}</span>
            </div>
            <div style="color:#4a5568; font-size:0.5rem; margin-top:2px;">Conf: {conf:.0f}%</div>
        </div>"""

    # Risk category bars
    hr_val = processed.clean_hr if processed else 72
    spo2_val = processed.clean_spo2 if processed else 97
    bp_val = processed.clean_bp_sys if processed else 120

    stress = min(100, max(0, (hr_val - 60) / 1.2 + max(0, bp_val - 130) * 0.8))
    oxy = min(100, max(0, (98 - spo2_val) * 8))
    fatigue = min(100, max(0, anomaly * 100 * 1.2 + max(0, hr_val - 80) * 0.3))
    emerg = min(100, sum(30 for d in detections if d.severity == "critical") +
                     sum(10 for d in detections if d.severity == "warning"))
    abnormal = min(100, max(0, abs(hr_val - 72) * 0.8 + anomaly * 40))

    categories = [
        ("Stress Escalation", stress, "#f97316" if stress > 40 else "#fbbf24" if stress > 20 else "#00d4aa"),
        ("Oxygen Instability", oxy, "#ff4757" if oxy > 40 else "#fbbf24" if oxy > 15 else "#00d4aa"),
        ("Fatigue Probability", fatigue, "#f97316" if fatigue > 50 else "#fbbf24" if fatigue > 25 else "#00d4aa"),
        ("Emergency Risk", emerg, "#ff4757" if emerg > 30 else "#fbbf24" if emerg > 10 else "#00d4aa"),
        ("Abnormal Heart", abnormal, "#f97316" if abnormal > 40 else "#fbbf24" if abnormal > 20 else "#00d4aa"),
    ]

    bars_html = ""
    for cat_name, cat_val, cat_color in categories:
        bar_w = min(100, max(2, cat_val))
        bars_html += f"""
        <div style="margin-bottom:6px;">
            <div style="display:flex; justify-content:space-between; font-size:0.62rem; margin-bottom:2px;">
                <span style="color:#8e99b0;">{cat_name}</span>
                <span style="color:{cat_color}; font-weight:700;
                    font-family:'JetBrains Mono',monospace;">{cat_val:.0f}%</span>
            </div>
            <div style="height:4px; background:rgba(255,255,255,0.04); border-radius:2px; overflow:hidden;">
                <div style="width:{bar_w:.0f}%; height:100%; background:{cat_color};
                    border-radius:2px; transition:width 0.5s ease;"></div>
            </div>
        </div>"""

    # Summary footer
    overall_color, overall_status = _status(pred_10)
    if trend == "deteriorating" and pred_10 < 60:
        footer_text = f"Moderate stress escalation risk detected ({stress:.0f}%)."
        footer_sub = "Elevated health risk detected in projections. Close monitoring advised."
    elif trend == "deteriorating":
        footer_text = f"Gradual deterioration trend detected. Projected score: {pred_10:.0f}%."
        footer_sub = "Monitor closely for signs of clinical escalation."
    elif any(d.severity == "critical" for d in detections):
        footer_text = f"Critical condition detected. Emergency risk at {emerg:.0f}%."
        footer_sub = "Immediate clinical assessment recommended."
    else:
        footer_text = f"Vital signs projected to remain stable. Score: {pred_10:.0f}%."
        footer_sub = "No elevated risk detected. Continue routine monitoring."

    _html(f"""
    <div style="background:rgba(10,14,30,0.8); border:1px solid rgba(255,255,255,0.06);
        border-radius:14px; overflow:hidden;">
        <div style="display:flex; align-items:center; gap:8px;
            padding:12px 16px; border-bottom:1px solid rgba(255,255,255,0.04);">
            <div style="font-size:0.8rem;">🔮</div>
            <div style="color:#c5cae9; font-size:0.7rem; font-weight:700;
                letter-spacing:1.5px;">PREDICTIVE HEALTH INTELLIGENCE</div>
        </div>
        <div style="display:flex; gap:8px; padding:12px 16px;">{cards_html}</div>
        <div style="padding:6px 16px 10px;">{bars_html}</div>
        <div style="padding:8px 16px 12px; border-top:1px solid rgba(255,255,255,0.03);">
            <div style="color:{overall_color}; font-size:0.7rem; font-weight:600; margin-bottom:4px;">
                ⚡ {footer_text}
            </div>
            <div style="color:#5c6b8a; font-size:0.65rem; font-style:italic;">{footer_sub}</div>
        </div>
    </div>
    """)


# ──────────────────────────── ML Anomaly Model Panel ─────────────────────────

def render_ml_model_panel(ml_result=None):
    """Render the ML Isolation Forest anomaly detection panel."""
    if ml_result is None:
        return

    status = ml_result.model_status
    score = ml_result.anomaly_score
    conf = ml_result.model_confidence
    progress = ml_result.training_progress
    samples = ml_result.samples_seen
    is_anomaly = ml_result.is_anomaly
    features = ml_result.top_features

    # Status colors
    if status == "training":
        badge_color = "#7c3aed"
        badge_text = "TRAINING"
        score_color = "#7986cb"
    elif is_anomaly:
        badge_color = "#ff4757"
        badge_text = "ANOMALY DETECTED"
        score_color = "#ff4757"
    else:
        badge_color = "#00d4aa"
        badge_text = "NORMAL"
        score_color = "#00d4aa"

    # Training progress bar (during training)
    training_html = ""
    if status == "training":
        pct = progress * 100
        training_html = f"""
        <div style="margin:12px 0;">
            <div style="display:flex; justify-content:space-between; font-size:0.6rem; margin-bottom:4px;">
                <span style="color:#7986cb;">Learning normal patterns...</span>
                <span style="color:#a78bfa; font-weight:700;">{pct:.0f}%</span>
            </div>
            <div style="height:6px; background:rgba(255,255,255,0.04); border-radius:3px; overflow:hidden;">
                <div style="width:{pct:.0f}%; height:100%; background:linear-gradient(90deg,#7c3aed,#a78bfa);
                    border-radius:3px; transition:width 0.5s ease;"></div>
            </div>
            <div style="color:#5c6b8a; font-size:0.55rem; margin-top:4px;">
                {samples} / 30 samples required for model initialization
            </div>
        </div>"""
    else:
        # Anomaly score gauge
        score_pct = min(100, score * 100)
        gauge_color = "#00d4aa" if score < 0.3 else "#ffb347" if score < 0.6 else "#ff4757"

        # Feature contribution
        features_html = ""
        if features:
            items = "".join([f'<span style="background:{gauge_color}15; color:{gauge_color}; '
                           f'padding:2px 8px; border-radius:10px; font-size:0.55rem; '
                           f'font-weight:600;">{f}</span>' for f in features])
            features_html = f"""
            <div style="margin-top:8px;">
                <div style="color:#7986cb; font-size:0.5rem; letter-spacing:1px; margin-bottom:4px;">
                    TOP CONTRIBUTING FEATURES
                </div>
                <div style="display:flex; flex-wrap:wrap; gap:4px;">{items}</div>
            </div>"""

        training_html = f"""
        <div style="margin:10px 0;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <div>
                    <div style="font-size:1.8rem; font-weight:900; color:{score_color};
                        font-family:'JetBrains Mono',monospace; line-height:1;">{score:.3f}</div>
                    <div style="color:#5c6b8a; font-size:0.5rem; letter-spacing:1px;">ANOMALY SCORE</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:1.1rem; font-weight:700; color:#e8eaf6;
                        font-family:'JetBrains Mono',monospace;">{conf:.0f}%</div>
                    <div style="color:#5c6b8a; font-size:0.5rem;">MODEL CONFIDENCE</div>
                </div>
            </div>
            <div style="height:6px; background:rgba(255,255,255,0.04); border-radius:3px; overflow:hidden;">
                <div style="width:{score_pct:.0f}%; height:100%; background:{gauge_color};
                    border-radius:3px; transition:width 0.5s ease;"></div>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:0.5rem; color:#5c6b8a; margin-top:2px;">
                <span>Normal</span><span>Anomalous</span>
            </div>
            {features_html}
        </div>
        <div style="display:flex; gap:12px; margin-top:8px;">
            <div style="flex:1; text-align:center; padding:6px; background:rgba(255,255,255,0.02); border-radius:6px;">
                <div style="color:#a78bfa; font-size:0.85rem; font-weight:700;
                    font-family:'JetBrains Mono',monospace;">{samples}</div>
                <div style="color:#5c6b8a; font-size:0.45rem; letter-spacing:1px;">SAMPLES SEEN</div>
            </div>
            <div style="flex:1; text-align:center; padding:6px; background:rgba(255,255,255,0.02); border-radius:6px;">
                <div style="color:#a78bfa; font-size:0.85rem; font-weight:700;">IF</div>
                <div style="color:#5c6b8a; font-size:0.45rem; letter-spacing:1px;">ALGORITHM</div>
            </div>
            <div style="flex:1; text-align:center; padding:6px; background:rgba(255,255,255,0.02); border-radius:6px;">
                <div style="color:#a78bfa; font-size:0.85rem; font-weight:700;">100</div>
                <div style="color:#5c6b8a; font-size:0.45rem; letter-spacing:1px;">ESTIMATORS</div>
            </div>
        </div>"""

    _html(f"""
    <div class="glass-card" style="padding:14px; border:1px solid rgba(124,58,237,0.2);">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <div style="display:flex; align-items:center; gap:8px;">
                <div style="width:8px; height:8px; border-radius:50%; background:{badge_color};
                    {"animation:pulse 1.5s infinite;" if status == "training" else ""}"></div>
                <div style="color:#e8eaf6; font-size:0.7rem; font-weight:800; letter-spacing:1.5px;">
                    ML ANOMALY MODEL
                </div>
            </div>
            <div style="background:{badge_color}18; color:{badge_color}; padding:3px 10px;
                border-radius:10px; font-size:0.55rem; font-weight:700; letter-spacing:0.5px;">
                {badge_text}
            </div>
        </div>
        <div style="color:#5c6b8a; font-size:0.55rem; border-bottom:1px solid rgba(255,255,255,0.04);
            padding-bottom:6px; margin-bottom:6px;">
            Isolation Forest · Unsupervised · Online Learning · 6-feature input vector
        </div>
        {training_html}
    </div>
    """)


# ──────────────────────────── Session Timer ──────────────────────────────────

def render_session_info(session_id: str, elapsed_str: str, readings: int):
    """Render session info bar."""
    _html(f"""
    <div style="display:flex; justify-content:space-between; align-items:center;
        padding:8px 16px; background:rgba(15,20,40,0.4); border-radius:10px;
        margin-bottom:12px; font-size:0.75rem; color:#7986cb;">
        <div>🔬 Session: <strong style="color:#a78bfa;">{session_id}</strong></div>
        <div>⏱️ {elapsed_str}</div>
        <div>📊 {readings} readings</div>
    </div>
    """)


# ──────────────────────────── AI Reasoning Panel ─────────────────────────────

def render_ai_reasoning(thinking_steps: list, ai_result=None, processed=None,
                         baseline_engine=None, score_result=None):
    """Production-grade AI Reasoning Panel — matches reference design."""

    # ── Determine overall status ──
    overall = "stable"
    n_warnings = 0
    n_critical = 0
    for step in thinking_steps:
        if step.severity == "critical":
            n_critical += 1
        elif step.severity in ("warning", "monitoring"):
            n_warnings += 1
    if n_critical > 0:
        overall = "critical"
    elif n_warnings > 0:
        overall = "monitoring"

    # Risk label config
    risk_config = {
        "stable": ("#00d4aa", "Normal"),
        "monitoring": ("#ffb347", "Warning"),
        "critical": ("#ff4757", "Critical Risk"),
    }
    risk_color, risk_label = risk_config.get(overall, risk_config["stable"])

    # Confidence
    conf = 0
    if ai_result and ai_result.risk_prediction:
        conf = ai_result.risk_prediction.confidence
    elif score_result:
        conf = min(95, 60 + len(thinking_steps) * 3)
    else:
        conf = 50

    # ── Summary verdict text ──
    summary = ai_result.summary if ai_result else "Analyzing..."

    # ── Build reasoning bullets (only substantial steps) ──
    bullets_html = ""
    for step in thinking_steps:
        if step.severity == "critical":
            bullet_color = "#ff4757"
        elif step.severity in ("warning", "monitoring"):
            bullet_color = "#ffb347"
        else:
            bullet_color = "#8e99b0"

        # Split on " — " for detail
        msg = step.message
        if " — " in msg:
            parts = msg.split(" — ", 1)
            msg_html = f'<span style="color:#c5cae9;">{parts[0]}</span> — <span style="color:{bullet_color};">{parts[1]}</span>'
        else:
            msg_html = f'<span style="color:{bullet_color};">{msg}</span>'

        bullets_html += f"""
        <div style="display:flex; gap:8px; padding:4px 0; font-size:0.7rem; line-height:1.5;">
            <div style="color:{bullet_color}; flex-shrink:0; margin-top:2px;">▸</div>
            <div>{msg_html}</div>
        </div>"""

    # ── Detection tags ──
    tags_html = ""
    if ai_result and ai_result.detections:
        tags = ""
        for det in ai_result.detections:
            det_color = "#ff4757" if det.severity == "critical" else "#ffb347"
            tags += f"""<span style="display:inline-block; padding:4px 12px; margin:3px 4px 3px 0;
                background:rgba(15,20,40,0.6); border:1px solid {det_color}40;
                border-radius:16px; font-size:0.65rem; color:{det_color};
                font-weight:600;">{det.condition}</span>"""
        tags_html = f'<div style="margin:10px 0 8px;">{tags}</div>'

    # ── Recommendation box ──
    rec_html = ""
    if ai_result and ai_result.detections:
        # Collect unique recommendations
        recs = []
        for det in ai_result.detections[:3]:
            if det.recommendation and det.recommendation not in recs:
                recs.append(det.recommendation)
        if recs:
            rec_text = " ".join(recs)
            rec_html = f"""
            <div style="background:rgba(251,191,36,0.08); border:1px solid rgba(251,191,36,0.2);
                border-radius:10px; padding:10px 12px; margin-top:6px;">
                <div style="color:#fbbf24; font-size:0.72rem; line-height:1.5;">
                    <span style="font-size:0.8rem;">💡</span> {rec_text}
                </div>
            </div>"""
    else:
        rec_html = """
        <div style="background:rgba(0,212,170,0.05); border:1px solid rgba(0,212,170,0.15);
            border-radius:10px; padding:10px 12px; margin-top:6px;">
            <div style="color:#00d4aa; font-size:0.72rem; line-height:1.5;">
                <span style="font-size:0.8rem;">✓</span> All vitals within normal parameters. No clinical intervention required.
            </div>
        </div>"""

    # ── Final assembly ──
    _html(f"""
    <div style="background:rgba(10,14,30,0.8); border:1px solid rgba(255,255,255,0.06);
        border-radius:14px; overflow:hidden;">

        <!-- Header bar -->
        <div style="display:flex; justify-content:space-between; align-items:center;
            padding:12px 16px; border-bottom:1px solid rgba(255,255,255,0.04);">
            <div style="display:flex; align-items:center; gap:8px;">
                <div style="width:8px; height:8px; border-radius:50%; background:{risk_color};
                    animation:pulse 2s infinite;"></div>
                <div style="color:#c5cae9; font-size:0.7rem; font-weight:700;
                    letter-spacing:1.5px;">AI REASONING</div>
            </div>
            <div style="display:flex; gap:8px; align-items:center;">
                <div style="padding:3px 10px; border-radius:6px;
                    border:1px solid rgba(255,255,255,0.1); background:rgba(255,255,255,0.03);
                    font-size:0.6rem; color:#c5cae9; font-weight:600;">
                    Confidence: <span style="color:#e8eaf6;">{conf:.0f}%</span>
                </div>
                <div style="padding:3px 10px; border-radius:6px;
                    background:{risk_color}18; border:1px solid {risk_color}40;
                    font-size:0.6rem; color:{risk_color}; font-weight:700;">
                    {risk_label}
                </div>
            </div>
        </div>

        <!-- Summary -->
        <div style="padding:12px 16px 6px; color:#c5cae9; font-size:0.78rem;
            line-height:1.5; border-bottom:1px solid rgba(255,255,255,0.03);">
            {summary}
        </div>

        <!-- Reasoning steps -->
        <div style="padding:8px 16px; max-height:280px; overflow-y:auto;">
            {bullets_html}
        </div>

        <!-- Detection tags -->
        <div style="padding:0 16px;">
            {tags_html}
        </div>

        <!-- Recommendation -->
        <div style="padding:4px 16px 14px;">
            {rec_html}
        </div>
    </div>
    """)


# ──────────────────────────── Detection Cards ────────────────────────────────

def render_detection_card(detection):
    """Render a single AI detection result."""
    sev_colors = {"critical": "#ff4757", "warning": "#ffb347", "info": "#00d4aa"}
    color = sev_colors.get(detection.severity, "#7986cb")

    evidence_html = "".join(f"<div style='color:#c5cae9; font-size:0.8rem;'>• {e}</div>" for e in detection.evidence)

    _html(f"""
    <div style="padding:12px; margin-bottom:8px; background:rgba(255,255,255,0.02);
        border-left:3px solid {color}; border-radius:0 10px 10px 0;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div style="color:{color}; font-weight:700; font-size:0.9rem;">
                ⚠️ {detection.condition}
                <span style="font-size:0.7rem; color:#7986cb; margin-left:8px;">
                    ({detection.severity.upper()})
                </span>
            </div>
            <div style="color:#7986cb; font-size:0.75rem;">
                Confidence: {detection.confidence:.0f}%
            </div>
        </div>
        {evidence_html}
        <div style="color:#a78bfa; font-size:0.8rem; margin-top:4px; font-style:italic;">
            → {detection.recommendation}
        </div>
    </div>
    """)


# ──────────────────────────── Score Breakdown ────────────────────────────────

def render_score_breakdown(breakdown: list):
    """Render health score breakdown items."""
    items_html = ""
    for item in breakdown:
        ded_color = "#ff4757" if item.deduction > 0 else "#00d4aa"
        ded_text = f"-{item.deduction:.1f}" if item.deduction > 0 else "✓ 0"
        weight_pct = f"{item.weight * 100:.0f}%"
        items_html += f"""
        <div class="breakdown-item">
            <div class="breakdown-label">
                {item.icon} {item.category}
                <span style="color:#4a5568; font-size:0.7rem; margin-left:4px;">({weight_pct})</span>
            </div>
            <div class="breakdown-deduction {'deduction-negative' if item.deduction > 0 else 'deduction-zero'}">
                {ded_text}
            </div>
        </div>"""

    _html(f"""
    <div class="glass-card">
        <div class="section-header">❓ WHY THIS SCORE?</div>
        {items_html}
    </div>
    """)


# ──────────────────────────── Status Banner ──────────────────────────────────

def render_status_banner(status: str):
    """Render system status banner."""
    status_map = {
        "stable": ("🟢", "SYSTEM STATUS: STABLE", "status-stable"),
        "monitoring": ("🟡", "SYSTEM STATUS: MONITORING", "status-monitoring"),
        "critical": ("🔴", "SYSTEM STATUS: CRITICAL", "status-critical"),
    }
    emoji, text, css_class = status_map.get(status, status_map["stable"])
    _html(f"""
    <div class="status-banner {css_class}">
        <span style="font-size:1.2rem;">{emoji}</span>
        <strong>{text}</strong>
        <span style="font-size:0.8rem; opacity:0.7;">• Medisynth Live Active</span>
    </div>
    """)


# ──────────────────────────── Emergency Alert Card ───────────────────────────

def render_alert_card(alert, contacts, key_notify, key_confirm, key_dismiss):
    """Render emergency alert with 3-step workflow."""
    step = alert.step
    step1 = "✓ Alert User" if step >= 1 else "○ Alert User"
    step2 = "✓ Notify Contacts" if step >= 2 else "○ Notify Contacts"
    step3 = "✓ Confirmed" if step >= 3 else "○ Confirmed"

    step1_color = "#00d4aa" if step >= 1 else "#7986cb"
    step2_color = "#00d4aa" if step >= 2 else "#7986cb"
    step3_color = "#00d4aa" if step >= 3 else "#7986cb"

    _html(f"""
    <div class="alert-card">
        <div class="alert-title">🚨 Emergency Alert Active</div>
        <div style="color:#c5cae9; font-size:0.85rem; margin-bottom:12px;">
            Health Score: <strong style="color:#ff4757;">{alert.health_score:.0f}</strong> |
            HR: <strong>{alert.heart_rate:.0f}</strong> bpm |
            SpO₂: <strong>{alert.spo2:.1f}</strong>%
        </div>
        <div style="display:flex; gap:16px; font-size:0.85rem; margin-bottom:12px;">
            <span style="color:{step1_color}; font-weight:600;">{step1}</span>
            <span style="color:{step2_color}; font-weight:600;">{step2}</span>
            <span style="color:{step3_color}; font-weight:600;">{step3}</span>
        </div>
    </div>
    """)

    col1, col2 = st.columns(2)
    if step == 1:
        with col1:
            if st.button("📤 Notify Emergency Contacts", key=key_notify):
                return "notify"
    elif step == 2:
        with col1:
            if st.button("✓ Confirm Alert Sent", key=key_confirm):
                return "confirm"

    if step < 3:
        with col2:
            if st.button("✕ Dismiss Alert", key=key_dismiss):
                return "dismiss"

    if step >= 3:
        _html("""
            <div style="color:#00d4aa; font-size:0.9rem; padding:8px 0;">
                ✓ Alert confirmed and contacts notified
            </div>
        """)

    return None


# ──────────────────────────── Nearby Hospitals ───────────────────────────────

def render_nearby_hospitals(hospitals: list, patient_location=None):
    """Render nearby hospitals panel with distance, directions, and contact info."""
    if not hospitals:
        return

    items_html = ""
    for i, h in enumerate(hospitals):
        dist_txt = f"{h.distance_km:.1f} km" if h.distance_km > 0 else ""
        phone_html = f'<div style="color:#7986cb; font-size:0.6rem;">Tel: {h.phone}</div>' if h.phone else ""
        addr_html = f'<div style="color:#5c6b8a; font-size:0.58rem; margin-top:1px;">{h.address}</div>' if h.address else ""
        emerg_badge = '<span style="color:#ff4757; font-size:0.5rem; font-weight:700; background:rgba(255,71,87,0.12); padding:1px 5px; border-radius:3px; margin-left:6px;">EMERGENCY</span>' if h.emergency else ""

        # Determine color based on distance
        if h.distance_km <= 1:
            dist_color = "#00d4aa"
        elif h.distance_km <= 3:
            dist_color = "#ffb347"
        else:
            dist_color = "#7986cb"

        items_html += f"""
        <div style="display:flex; gap:10px; padding:8px 6px; border-bottom:1px solid rgba(255,255,255,0.04);
            animation:fadeSlideIn 0.4s ease-out;">
            <div style="width:28px; height:28px; border-radius:8px; background:rgba(255,71,87,0.1);
                display:flex; align-items:center; justify-content:center; flex-shrink:0;
                font-size:0.9rem; border:1px solid rgba(255,71,87,0.15);">
                🏥
            </div>
            <div style="flex:1; min-width:0;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div style="color:#e8eaf6; font-weight:600; font-size:0.75rem; white-space:nowrap;
                        overflow:hidden; text-overflow:ellipsis; max-width:70%;">
                        {h.name}{emerg_badge}
                    </div>
                    <div style="color:{dist_color}; font-size:0.65rem; font-weight:700;
                        font-family:'JetBrains Mono',monospace; flex-shrink:0;">
                        {dist_txt}
                    </div>
                </div>
                {addr_html}
                {phone_html}
                <div style="margin-top:3px;">
                    <a href="{h.directions_url}" target="_blank"
                       style="color:#a78bfa; font-size:0.6rem; text-decoration:none;
                       font-weight:600; letter-spacing:0.5px;">
                        Get Directions →
                    </a>
                </div>
            </div>
        </div>"""

    # Google Maps search fallback link
    search_url = ""
    if patient_location and patient_location.get("lat"):
        search_url = f"https://www.google.com/maps/search/hospital/@{patient_location['lat']},{patient_location['lng']},14z"

    search_html = ""
    if search_url:
        search_html = f"""
        <div style="text-align:center; padding:6px 0 2px;">
            <a href="{search_url}" target="_blank"
               style="color:#00d4aa; font-size:0.65rem; text-decoration:none; font-weight:600;">
                Search More Hospitals on Maps →
            </a>
        </div>"""

    _html(f"""
    <div class="glass-card" style="padding:14px; border:1px solid rgba(255,71,87,0.12);">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <div class="section-header" style="margin:0;">NEARBY HOSPITALS</div>
            <div style="color:#7986cb; font-size:0.55rem; font-weight:600; letter-spacing:1px;">
                AI LOCATED
            </div>
        </div>
        <div style="max-height:300px; overflow-y:auto;">
            {items_html}
        </div>
        {search_html}
    </div>
    """)


# ──────────────────────────── Confidence Badge ───────────────────────────────

def render_confidence_badge(confidence: float, noise: float = 0):
    """Render data confidence badge."""
    color = "#00d4aa" if confidence >= 85 else "#ffb347" if confidence >= 60 else "#ff4757"
    level = "High" if confidence >= 85 else "Medium" if confidence >= 60 else "Low"
    _html(f"""
    <div class="glass-card">
        <div class="section-header">📡 Data Reliability</div>
        <div style="text-align:center;">
            <div style="font-size:2rem; font-weight:800; color:{color};">{confidence:.0f}%</div>
            <div style="color:#7986cb; font-size:0.8rem;">({level})</div>
        </div>
        {f'<div style="color:#4a5568; font-size:0.75rem; text-align:center; margin-top:4px;">Noise: {noise:.3f}</div>' if noise > 0 else ''}
    </div>
    """)


# ──────────────────────────── Anomaly Score Indicator ────────────────────────

def render_anomaly_score(score: float):
    """Render the composite anomaly score as a horizontal bar."""
    pct = score * 100
    color = "#00d4aa" if pct < 20 else "#ffb347" if pct < 50 else "#ff4757"
    label = "Normal" if pct < 20 else "Elevated" if pct < 50 else "High"
    _html(f"""
    <div class="glass-card">
        <div class="section-header">🎯 Anomaly Score</div>
        <div style="display:flex; align-items:center; gap:12px;">
            <div style="flex:1;">
                <div style="width:100%; height:8px; background:rgba(255,255,255,0.06); border-radius:4px; overflow:hidden;">
                    <div style="width:{pct:.0f}%; height:100%; background:{color}; border-radius:4px;
                        transition:width 0.8s ease;"></div>
                </div>
            </div>
            <div style="color:{color}; font-weight:700; font-size:0.9rem; min-width:60px; text-align:right;">
                {pct:.0f}% {label}
            </div>
        </div>
    </div>
    """)


# ──────────────────────────── Event Timeline ─────────────────────────────────

def render_event_timeline(events: list, max_events: int = 8):
    """Render a vertical event timeline."""
    if not events:
        _html("""
        <div class="glass-card">
            <div class="section-header">📋 Event Timeline</div>
            <div style="color:#7986cb; font-size:0.85rem;">No events yet</div>
        </div>
        """)
        return

    import datetime
    items_html = ""
    for ev in reversed(events[-max_events:]):
        ts = datetime.datetime.fromtimestamp(ev.timestamp).strftime("%H:%M:%S")
        sev_colors = {"critical": "#ff4757", "warning": "#ffb347", "info": "#00d4aa"}
        color = sev_colors.get(ev.severity, "#7986cb")
        type_icons = {"detection": "⚠️", "mode_change": "🔄", "alert": "🚨", "baseline": "📊"}
        icon = type_icons.get(ev.event_type, "•")

        items_html += f"""
        <div style="display:flex; gap:10px; padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.04);
            font-size:0.8rem; animation:fadeSlideIn 0.3s ease-out;">
            <div style="color:#4a5568; min-width:55px; font-family:'JetBrains Mono',monospace;">{ts}</div>
            <div style="color:{color}; min-width:20px;">{icon}</div>
            <div style="color:#c5cae9; flex:1;">{ev.title}</div>
        </div>"""

    _html(f"""
    <div class="glass-card">
        <div class="section-header">📋 Event Timeline</div>
        {items_html}
    </div>
    """)


# ──────────────────────────── Anomaly History ─────────────────────────────────

def render_anomaly_history(timeline_events: list, max_items: int = 50):
    """Render chronological anomaly history — shows all abnormalities detected over time."""
    import datetime

    # Filter to only anomaly/detection events (not mode changes)
    anomalies = [e for e in timeline_events
                 if e.event_type in ("detection", "alert")]

    if not anomalies:
        _html("""
        <div class="glass-card">
            <div class="section-header">ANOMALY HISTORY</div>
            <div style="color:#00d4aa; font-size:0.8rem; text-align:center; padding:12px;">
                No anomalies detected yet. System is monitoring...
            </div>
        </div>
        """)
        return

    # Group by minute blocks
    now = time.time() if anomalies else 0
    recent = anomalies[-max_items:]

    # Stats bar
    total = len(anomalies)
    critical_count = sum(1 for a in anomalies if a.severity == "critical")
    warning_count = sum(1 for a in anomalies if a.severity == "warning")
    info_count = total - critical_count - warning_count

    stats_html = f"""
    <div style="display:flex; gap:12px; margin-bottom:10px; padding:8px 10px;
        background:rgba(255,255,255,0.02); border-radius:8px; font-size:0.65rem;">
        <div style="flex:1; text-align:center;">
            <div style="color:#c5cae9; font-weight:700; font-size:0.95rem;">{total}</div>
            <div style="color:#5c6b8a; letter-spacing:0.5px;">TOTAL</div>
        </div>
        <div style="flex:1; text-align:center;">
            <div style="color:#ff4757; font-weight:700; font-size:0.95rem;">{critical_count}</div>
            <div style="color:#5c6b8a; letter-spacing:0.5px;">CRITICAL</div>
        </div>
        <div style="flex:1; text-align:center;">
            <div style="color:#ffb347; font-weight:700; font-size:0.95rem;">{warning_count}</div>
            <div style="color:#5c6b8a; letter-spacing:0.5px;">WARNING</div>
        </div>
        <div style="flex:1; text-align:center;">
            <div style="color:#00d4aa; font-weight:700; font-size:0.95rem;">{info_count}</div>
            <div style="color:#5c6b8a; letter-spacing:0.5px;">INFO</div>
        </div>
    </div>"""

    # Build timeline entries
    entries_html = ""
    prev_minute = None
    for i, ev in enumerate(reversed(recent)):
        ts_dt = datetime.datetime.fromtimestamp(ev.timestamp)
        ts_str = ts_dt.strftime("%H:%M:%S")
        minute_str = ts_dt.strftime("%H:%M")
        elapsed = now - ev.timestamp
        ago_str = _format_ago(elapsed)

        # Minute separator
        if minute_str != prev_minute:
            entries_html += f"""
            <div style="color:#4a5568; font-size:0.55rem; font-weight:600;
                letter-spacing:1.5px; padding:6px 0 2px; margin-top:4px;
                border-top:1px solid rgba(255,255,255,0.04);">
                {minute_str}
            </div>"""
            prev_minute = minute_str

        # Severity config
        sev_config = {
            "critical": ("#ff4757", "rgba(255,71,87,0.06)", "CRIT"),
            "warning": ("#ffb347", "rgba(255,179,71,0.04)", "WARN"),
            "info": ("#00d4aa", "rgba(0,212,170,0.03)", "INFO"),
        }
        color, bg, badge = sev_config.get(ev.severity, ("#7986cb", "rgba(0,0,0,0)", "INFO"))

        # Icon based on event type
        type_icons = {"detection": "!", "alert": "!!"}
        icon_char = type_icons.get(ev.event_type, ".")

        # Dot connector line
        is_last = (i == len(recent) - 1)
        line_style = "transparent" if is_last else color

        entries_html += f"""
        <div style="display:flex; gap:8px; font-size:0.75rem; min-height:32px;">
            <div style="display:flex; flex-direction:column; align-items:center; width:14px; flex-shrink:0;">
                <div style="width:8px; height:8px; border-radius:50%; background:{color};
                    box-shadow:0 0 6px {color}40; flex-shrink:0;"></div>
                <div style="width:1px; flex:1; background:{line_style};"></div>
            </div>
            <div style="flex:1; padding-bottom:6px; background:{bg}; border-radius:6px;
                padding:5px 8px; margin-bottom:2px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div style="color:{color}; font-weight:600; font-size:0.72rem;">
                        {ev.title}
                    </div>
                    <div style="display:flex; gap:6px; align-items:center;">
                        <span style="color:{color}; font-size:0.5rem; font-weight:700;
                            background:{color}15; padding:1px 5px; border-radius:3px;
                            letter-spacing:0.5px;">{badge}</span>
                        <span style="color:#4a5568; font-size:0.6rem;
                            font-family:'JetBrains Mono',monospace;">{ts_str}</span>
                    </div>
                </div>
                <div style="color:#5c6b8a; font-size:0.6rem; margin-top:1px;">
                    {ev.detail if ev.detail else ''} <span style="color:#3d4a66;">({ago_str})</span>
                </div>
            </div>
        </div>"""

    _html(f"""
    <div class="glass-card" style="padding:14px;">
        <div class="section-header">ANOMALY HISTORY</div>
        {stats_html}
        <div style="max-height:380px; overflow-y:auto; scroll-behavior:smooth;
            padding-right:4px;">
            {entries_html}
        </div>
    </div>
    """)


def _format_ago(seconds: float) -> str:
    """Format elapsed seconds into human-readable 'ago' string."""
    if seconds < 5:
        return "just now"
    if seconds < 60:
        return f"{int(seconds)}s ago"
    mins = int(seconds / 60)
    if mins < 60:
        return f"{mins}m ago"
    hrs = int(mins / 60)
    return f"{hrs}h {mins % 60}m ago"


# ──────────────────────────── Vitals Chart ───────────────────────────────────

def create_vitals_chart(timestamps: list, hr_data: list, spo2_data: list,
                        hr_raw: list = None, spo2_raw: list = None,
                        show_raw: bool = False) -> go.Figure:
    """Create premium Plotly chart for vital signs — smooth, responsive, production-grade."""
    fig = go.Figure()

    x_labels = list(range(len(hr_data)))

    if show_raw and hr_raw:
        fig.add_trace(go.Scatter(
            x=x_labels, y=hr_raw, mode='lines', name='HR (Raw)',
            line=dict(color='rgba(255, 179, 71, 0.25)', width=1, dash='dot'),
            hovertemplate='HR Raw: %{y:.1f} bpm<extra></extra>',
        ))
    if show_raw and spo2_raw:
        fig.add_trace(go.Scatter(
            x=x_labels, y=spo2_raw, mode='lines', name='SpO2 (Raw)',
            line=dict(color='rgba(167, 139, 250, 0.25)', width=1, dash='dot'),
            yaxis='y2',
            hovertemplate='SpO2 Raw: %{y:.1f}%<extra></extra>',
        ))

    # Processed HR — smooth spline with gradient fill
    fig.add_trace(go.Scatter(
        x=x_labels, y=hr_data, mode='lines', name='Heart Rate',
        line=dict(color='#00d4aa', width=2.5, shape='spline', smoothing=1.3),
        fill='tozeroy',
        fillcolor='rgba(0, 212, 170, 0.04)',
        hovertemplate='HR: %{y:.1f} bpm<extra></extra>',
    ))

    # Processed SpO2 — smooth spline
    fig.add_trace(go.Scatter(
        x=x_labels, y=spo2_data, mode='lines', name='SpO2',
        line=dict(color='#a78bfa', width=2.5, shape='spline', smoothing=1.3),
        yaxis='y2',
        hovertemplate='SpO2: %{y:.1f}%<extra></extra>',
    ))

    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(10,14,26,0)',
        plot_bgcolor='rgba(15,20,40,0.6)',
        font=dict(family='Inter, sans-serif', color='#7986cb', size=11),
        height=320,
        margin=dict(l=48, r=48, t=25, b=25),
        legend=dict(
            orientation='h', yanchor='top', y=1.12, xanchor='center', x=0.5,
            bgcolor='rgba(10,14,26,0.85)', font=dict(size=10),
            bordercolor='rgba(255,255,255,0.04)', borderwidth=1,
        ),
        xaxis=dict(
            showgrid=False, zeroline=False,
            showticklabels=False,
        ),
        yaxis=dict(
            title=dict(text='Heart Rate (bpm)', font=dict(color='#00d4aa', size=10)),
            showgrid=True, gridcolor='rgba(255,255,255,0.025)',
            zeroline=False, tickfont=dict(color='#00d4aa', size=10),
        ),
        yaxis2=dict(
            title=dict(text='SpO2 (%)', font=dict(color='#a78bfa', size=10)),
            overlaying='y', side='right',
            showgrid=False, zeroline=False,
            tickfont=dict(color='#a78bfa', size=10),
            range=[78, 102],
        ),
        hovermode='x unified',
        # Performance: disable transitions for real-time updates
        transition=dict(duration=0),
    )

    # Disable animation for faster rendering
    fig.update_traces(
        connectgaps=True,
    )

    return fig


def create_score_history_chart(scores: list) -> go.Figure:
    """Create a small health score trend chart."""
    fig = go.Figure()
    x = list(range(len(scores)))

    # Color gradient based on score
    colors = ['#ff4757' if s < 40 else '#f97316' if s < 60 else '#fbbf24' if s < 75 else '#4ade80' if s < 90 else '#00d4aa' for s in scores]

    fig.add_trace(go.Scatter(
        x=x, y=scores, mode='lines+markers',
        line=dict(color='#a78bfa', width=2, shape='spline'),
        marker=dict(size=3, color=colors),
        fill='tozeroy', fillcolor='rgba(167,139,250,0.05)',
        hovertemplate='Score: %{y:.0f}<extra></extra>',
    ))

    # Critical threshold line
    fig.add_hline(y=40, line=dict(color='rgba(255,71,87,0.3)', width=1, dash='dash'))

    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='#0a0e1a',
        plot_bgcolor='#0f1428',
        font=dict(family='Inter, sans-serif', color='#7986cb', size=10),
        height=180,
        margin=dict(l=40, r=20, t=10, b=20),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(range=[0, 105], showgrid=True, gridcolor='rgba(255,255,255,0.03)',
                   zeroline=False, tickfont=dict(color='#7986cb')),
        showlegend=False,
    )
    return fig


# Plotly config: disable built-in fullscreen (broken with st.fragment), keep zoom/pan
PLOTLY_CONFIG = {
    'displayModeBar': True,
    'modeBarButtonsToRemove': ['autoScale2d', 'lasso2d', 'select2d'],
    'displaylogo': False,
    'responsive': True,
}


def create_prediction_chart(hr_data: list, spo2_data: list,
                            risk_pred=None) -> go.Figure:
    """Create prediction trend chart with actual data, trendline, and confidence bounds."""
    import numpy as np

    fig = go.Figure()
    n = len(hr_data)
    if n < 5:
        return fig

    x_actual = list(range(n))

    # Actual HR
    fig.add_trace(go.Scatter(
        x=x_actual, y=hr_data[-60:], mode='lines', name='HR Actual',
        line=dict(color='#00d4aa', width=2, shape='spline', smoothing=1.3),
        hovertemplate='HR: %{y:.0f} bpm<extra></extra>',
    ))

    # Actual SpO2
    fig.add_trace(go.Scatter(
        x=x_actual, y=spo2_data[-60:], mode='lines', name='SpO2 Actual',
        line=dict(color='#a78bfa', width=2, shape='spline', smoothing=1.3),
        yaxis='y2',
        hovertemplate='SpO2: %{y:.1f}%<extra></extra>',
    ))

    # Compute trendlines and predictions
    recent_hr = np.array(hr_data[-20:]) if len(hr_data) >= 20 else np.array(hr_data)
    recent_spo2 = np.array(spo2_data[-20:]) if len(spo2_data) >= 20 else np.array(spo2_data)
    x_fit = np.arange(len(recent_hr))

    if len(recent_hr) >= 5:
        hr_coeffs = np.polyfit(x_fit, recent_hr, 1)
        spo2_coeffs = np.polyfit(x_fit, recent_spo2, 1)

        # HR residuals for confidence bounds
        hr_residuals = recent_hr - np.polyval(hr_coeffs, x_fit)
        hr_std = np.std(hr_residuals) if len(hr_residuals) > 1 else 5

        # Prediction: extend 30 points (~1 min ahead)
        pred_points = 30
        x_pred = np.arange(n, n + pred_points)
        x_pred_fit = np.arange(len(recent_hr), len(recent_hr) + pred_points)
        hr_pred = np.clip(hr_coeffs[0] * x_pred_fit + hr_coeffs[1], 30, 220)
        spo2_pred = np.clip(spo2_coeffs[0] * x_pred_fit + spo2_coeffs[1], 70, 100)

        # Confidence bounds (widen with distance)
        conf_multiplier = np.linspace(1, 2.5, pred_points)
        hr_upper = hr_pred + 2 * hr_std * conf_multiplier
        hr_lower = hr_pred - 2 * hr_std * conf_multiplier

        # HR prediction line
        fig.add_trace(go.Scatter(
            x=x_pred.tolist(), y=hr_pred.tolist(), mode='lines', name='HR Predicted',
            line=dict(color='#00d4aa', width=2, dash='dash'),
            hovertemplate='HR Pred: %{y:.0f} bpm<extra></extra>',
        ))

        # HR confidence band
        fig.add_trace(go.Scatter(
            x=x_pred.tolist() + x_pred.tolist()[::-1],
            y=hr_upper.tolist() + hr_lower.tolist()[::-1],
            fill='toself', fillcolor='rgba(0,212,170,0.08)',
            line=dict(color='rgba(0,0,0,0)'),
            name='HR 95% CI', showlegend=True,
            hoverinfo='skip',
        ))

        # SpO2 prediction line
        fig.add_trace(go.Scatter(
            x=x_pred.tolist(), y=spo2_pred.tolist(), mode='lines', name='SpO2 Predicted',
            line=dict(color='#a78bfa', width=2, dash='dash'),
            yaxis='y2',
            hovertemplate='SpO2 Pred: %{y:.1f}%<extra></extra>',
        ))

        # Trend direction annotation
        hr_slope = hr_coeffs[0]
        if hr_slope > 0.3:
            trend_txt = "HR RISING"
            trend_color = "#ff4757"
        elif hr_slope < -0.3:
            trend_txt = "HR FALLING"
            trend_color = "#ffb347"
        else:
            trend_txt = "HR STABLE"
            trend_color = "#00d4aa"

        fig.add_annotation(
            x=n + pred_points // 2, y=hr_pred[pred_points // 2],
            text=trend_txt, showarrow=False,
            font=dict(color=trend_color, size=10, family='JetBrains Mono'),
            bgcolor='rgba(10,14,26,0.8)', bordercolor=trend_color,
            borderwidth=1, borderpad=4,
        )

    # Add vertical "now" line
    fig.add_vline(x=n - 1, line=dict(color='rgba(255,255,255,0.15)', width=1, dash='dot'))
    fig.add_annotation(x=n - 1, y=1.02, yref='paper', text='NOW', showarrow=False,
                       font=dict(color='#7986cb', size=9), bgcolor='rgba(10,14,26,0.8)')

    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(10,14,26,0)',
        plot_bgcolor='rgba(15,20,40,0.6)',
        font=dict(family='Inter, sans-serif', color='#7986cb', size=10),
        height=280,
        margin=dict(l=48, r=48, t=30, b=25),
        legend=dict(
            orientation='h', yanchor='top', y=1.15, xanchor='center', x=0.5,
            bgcolor='rgba(10,14,26,0.85)', font=dict(size=9),
        ),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(
            title=dict(text='HR (bpm)', font=dict(color='#00d4aa', size=10)),
            showgrid=True, gridcolor='rgba(255,255,255,0.025)',
            zeroline=False, tickfont=dict(color='#00d4aa', size=9),
        ),
        yaxis2=dict(
            title=dict(text='SpO2 (%)', font=dict(color='#a78bfa', size=10)),
            overlaying='y', side='right',
            showgrid=False, zeroline=False,
            tickfont=dict(color='#a78bfa', size=9),
            range=[78, 102],
        ),
        hovermode='x unified',
        transition=dict(duration=0),
    )
    return fig


# ──────────────────────────── Medisynth Engine Panel ─────────────────────────

def render_medisynth_panel(synthetic_engine, analytics, mode: str):
    """Render the Medisynth AI Engine dedicated panel."""
    is_training = synthetic_engine.is_training_mode
    active = synthetic_engine.get_active_scenario_info()
    scenario_name = active.name if active else "—"
    total_readings = analytics.total_readings if analytics else 0

    phase_label = "Synthetic Training" if is_training else "Live Monitoring"
    phase_color = "#a78bfa" if is_training else "#00d4aa"
    phase_icon = "🧬" if is_training else "📡"

    edge_cases = "YES" if (active or is_training) else "NO"
    edge_color = "#fbbf24" if edge_cases == "YES" else "#7986cb"

    _html(f"""
    <div class="glass-card" style="border-color:rgba(124,58,237,0.2);">
        <div class="section-header">🧬 MEDISYNTH AI ENGINE</div>

        <div style="display:flex; justify-content:space-between; margin-bottom:12px;">
            <div>
                <div style="color:#7986cb; font-size:0.65rem; text-transform:uppercase; letter-spacing:1px;">PHASE</div>
                <div style="color:{phase_color}; font-weight:700; font-size:0.95rem;">
                    {phase_icon} {phase_label}
                </div>
            </div>
            <div style="text-align:right;">
                <div style="color:#7986cb; font-size:0.65rem; text-transform:uppercase; letter-spacing:1px;">SCENARIO</div>
                <div style="color:#e8eaf6; font-weight:600; font-size:0.9rem;">{scenario_name}</div>
            </div>
        </div>

        <div style="display:flex; gap:12px; margin-bottom:10px;">
            <div style="flex:1; background:rgba(255,255,255,0.03); border-radius:8px; padding:10px; text-align:center;">
                <div style="color:#e8eaf6; font-size:1.3rem; font-weight:800;
                    font-family:'JetBrains Mono',monospace;">{total_readings}</div>
                <div style="color:#7986cb; font-size:0.65rem; text-transform:uppercase;">Samples Generated</div>
            </div>
            <div style="flex:1; background:rgba(255,255,255,0.03); border-radius:8px; padding:10px; text-align:center;">
                <div style="color:{edge_color}; font-size:1.3rem; font-weight:800;">{edge_cases}</div>
                <div style="color:#7986cb; font-size:0.65rem; text-transform:uppercase;">Edge Cases Injected</div>
            </div>
        </div>

        <div style="display:flex; gap:8px; font-size:0.7rem;">
            <div style="flex:1; padding:6px 8px; border-radius:6px;
                background:{'rgba(167,139,250,0.15)' if is_training else 'rgba(255,255,255,0.03)'};
                border:1px solid {'rgba(167,139,250,0.3)' if is_training else 'transparent'};
                color:{'#a78bfa' if is_training else '#4a5568'}; text-align:center; font-weight:600;">
                🧬 Training Phase<br><span style="font-size:0.6rem;">Synthetic Data (Medisynth)</span>
            </div>
            <div style="flex:1; padding:6px 8px; border-radius:6px;
                background:{'rgba(0,212,170,0.15)' if not is_training else 'rgba(255,255,255,0.03)'};
                border:1px solid {'rgba(0,212,170,0.3)' if not is_training else 'transparent'};
                color:{'#00d4aa' if not is_training else '#4a5568'}; text-align:center; font-weight:600;">
                📡 Live Phase<br><span style="font-size:0.6rem;">Streaming Wearable Data</span>
            </div>
        </div>
    </div>
    """)


# ──────────────────────────── Data Source Label ───────────────────────────────

def render_data_source_label(mode: str):
    """Render the 'Physiologically simulated data' badge."""
    _html(f"""
    <div style="display:flex; align-items:center; gap:8px; padding:4px 12px;
        background:rgba(124,58,237,0.08); border:1px solid rgba(124,58,237,0.15);
        border-radius:8px; margin-bottom:8px; font-size:0.7rem; color:#a78bfa;">
        <span>🧬</span>
        <span>Physiologically simulated data (not random) — Mode: <strong>{mode.upper()}</strong></span>
        <span style="margin-left:auto; font-size:0.6rem; color:#7986cb;">2s intervals</span>
    </div>
    """)


# ──────────────────────────── Enhanced Emergency Notification ────────────────

def render_emergency_notification(alert, contacts, location=None):
    """Render emergency notification with REAL location."""
    import datetime
    ts = datetime.datetime.fromtimestamp(alert.timestamp).strftime("%H:%M:%S")

    contacts_html = ""
    for c in contacts:
        contacts_html += f"""
        <div style="display:flex; align-items:center; gap:10px; padding:8px 0;
            border-bottom:1px solid rgba(255,255,255,0.04); font-size:0.8rem;">
            <span style="color:#00d4aa; font-size:1rem;">✔</span>
            <div style="flex:1;">
                <div style="color:#e8eaf6; font-weight:600;">{c.name}</div>
                <div style="color:#7986cb; font-size:0.7rem;">{c.phone} • {c.relationship}</div>
            </div>
            <div style="color:#00d4aa; font-size:0.7rem; font-weight:600;">✔ Notified</div>
        </div>"""

    if not contacts:
        contacts_html = '<div style="color:#ffb347; font-size:0.8rem; padding:8px 0;">⚠️ No contacts. Add in sidebar.</div>'

    # REAL location
    if location and location.get("lat") and location["lat"] != 0:
        maps_link = f"https://www.google.com/maps?q={location['lat']},{location['lng']}"
        city = f"{location.get('city','')} {location.get('region','')}, {location.get('country','')}".strip()
        loc_html = f'📍 <a href="{maps_link}" target="_blank" style="color:#00d4aa; text-decoration:underline;">Open Map</a> — {city} ({location["lat"]:.4f}, {location["lng"]:.4f})'
    elif alert.google_maps_link:
        loc_html = f'📍 <a href="{alert.google_maps_link}" target="_blank" style="color:#00d4aa;">{alert.google_maps_link}</a>'
    else:
        loc_html = '<span style="color:#ffb347;">📍 Acquiring location...</span>'

    _html(f"""
    <div style="background:rgba(255,71,87,0.06); border:1px solid rgba(255,71,87,0.2);
        border-radius:16px; padding:20px; margin:8px 0; animation:pulse-critical 2s infinite;">
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:12px;">
            <span style="font-size:1.3rem;">🚨</span>
            <span style="color:#ff4757; font-size:1rem; font-weight:700;">EMERGENCY ALERT DISPATCHED</span>
            <span style="margin-left:auto; color:#7986cb; font-size:0.75rem;">{ts}</span>
        </div>
        <div style="background:rgba(0,0,0,0.2); border-radius:10px; padding:12px; margin-bottom:12px;
            font-family:'JetBrains Mono',monospace; font-size:0.8rem; color:#e8eaf6; line-height:1.7;">
            🔴 MEDISYNTH LIVE EMERGENCY<br><br>
            Health Score: <strong style="color:#ff4757;">{alert.health_score:.0f}/100</strong><br>
            Heart Rate: <strong>{alert.heart_rate:.0f} bpm</strong><br>
            SpO₂: <strong>{alert.spo2:.1f}%</strong><br>
            Risk: <strong style="color:#ff4757;">{alert.risk_level.upper()}</strong><br><br>
            {loc_html}
        </div>
        <div style="font-size:0.7rem; font-weight:600; color:#7986cb; text-transform:uppercase;
            letter-spacing:1px; margin-bottom:6px;">CONTACTS NOTIFIED</div>
        {contacts_html}
    </div>
    """)


# ──────────────────────────── Business Model Panel ───────────────────────────

def render_business_model():
    """Render the business model / pricing panel."""
    _html("""
    <div class="glass-card" style="border-color:rgba(0,212,170,0.15);">
        <div class="section-header">💰 BUSINESS MODEL</div>

        <div style="display:flex; gap:10px; flex-wrap:wrap;">

            <div style="flex:1; min-width:140px; background:rgba(0,212,170,0.06);
                border:1px solid rgba(0,212,170,0.15); border-radius:12px; padding:14px;">
                <div style="color:#00d4aa; font-weight:700; font-size:0.85rem; margin-bottom:6px;">
                    👤 Consumer Plan
                </div>
                <div style="color:#e8eaf6; font-size:1.3rem; font-weight:800;">$9.99<span style="font-size:0.7rem; color:#7986cb;">/mo</span></div>
                <div style="color:#7986cb; font-size:0.7rem; line-height:1.5; margin-top:6px;">
                    Real-time monitoring<br>
                    AI health score<br>
                    Emergency alerts<br>
                    Personal baseline
                </div>
            </div>

            <div style="flex:1; min-width:140px; background:rgba(124,58,237,0.06);
                border:1px solid rgba(124,58,237,0.15); border-radius:12px; padding:14px;
                position:relative; overflow:hidden;">
                <div style="position:absolute; top:8px; right:8px; background:#7c3aed;
                    color:white; font-size:0.55rem; padding:2px 6px; border-radius:4px;
                    font-weight:700;">POPULAR</div>
                <div style="color:#a78bfa; font-weight:700; font-size:0.85rem; margin-bottom:6px;">
                    🏗️ API Access
                </div>
                <div style="color:#e8eaf6; font-size:1.3rem; font-weight:800;">$499<span style="font-size:0.7rem; color:#7986cb;">/mo</span></div>
                <div style="color:#7986cb; font-size:0.7rem; line-height:1.5; margin-top:6px;">
                    Wearable SDK integration<br>
                    Bulk synthetic data<br>
                    Custom AI models<br>
                    10K API calls/mo
                </div>
            </div>

            <div style="flex:1; min-width:140px; background:rgba(255,179,71,0.06);
                border:1px solid rgba(255,179,71,0.15); border-radius:12px; padding:14px;">
                <div style="color:#ffb347; font-weight:700; font-size:0.85rem; margin-bottom:6px;">
                    🏥 Hospital License
                </div>
                <div style="color:#e8eaf6; font-size:1.3rem; font-weight:800;">Custom</div>
                <div style="color:#7986cb; font-size:0.7rem; line-height:1.5; margin-top:6px;">
                    Multi-patient dashboard<br>
                    EHR integration<br>
                    Clinical analytics<br>
                    Dedicated support
                </div>
            </div>

        </div>
    </div>
    """)
