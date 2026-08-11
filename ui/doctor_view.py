"""
Medisynth Live – Doctor Dashboard View (Full Clinical)
Metrics, ECG, AI reasoning, prediction trends, SOAP notes, task/order management.
"""
import streamlit as st
import datetime
from ui.components import (
    render_health_gauge, create_vitals_chart, render_confidence_badge,
    render_ai_reasoning, render_detection_card, render_score_breakdown,
    render_risk_prediction, render_event_timeline, render_anomaly_score,
    create_score_history_chart, render_session_info, render_data_source_label,
    render_emergency_notification, render_medisynth_panel, PLOTLY_CONFIG,
)
from ui.shared_widgets import render_ecg_monitor, render_prediction_trend


def render_doctor_view(state: dict):
    """Full clinical dashboard for physicians."""
    score_result = state.get("score_result")
    ai_result = state.get("ai_result")
    processed = state.get("processed")
    emergency = state.get("emergency_system")
    analytics = state.get("analytics")
    synthetic = state.get("synthetic_engine")
    location = state.get("location")
    hr_history = state.get("hr_history", [])
    spo2_history = state.get("spo2_history", [])
    hr_raw = state.get("hr_raw_history", [])
    spo2_raw = state.get("spo2_raw_history", [])
    bp_sys_history = state.get("bp_sys_history", [])
    bp_dia_history = state.get("bp_dia_history", [])
    rr_history = state.get("rr_history", [])
    temp_history = state.get("temp_history", [])
    mode = state.get("mode", "normal")
    med_tracker = state.get("med_tracker")
    care_log = state.get("care_log")
    symptom_logger = state.get("symptom_logger")

    # Emergency
    if emergency and emergency.active_alert:
        render_emergency_notification(emergency.active_alert, emergency.contacts, location)
        if st.button("✕ Dismiss", key="doc_dismiss"):
            emergency.dismiss_alert()
            st.rerun()

    # ── Metrics Row ──
    if processed:
        cols = st.columns(6)
        metrics = [
            ("Heart Rate", f"{processed.clean_hr:.0f}", "bpm", "#00d4aa", hr_history),
            ("SpO₂", f"{processed.clean_spo2:.1f}", "%", "#a78bfa", spo2_history),
            ("BP", f"{processed.clean_bp_sys:.0f}/{processed.clean_bp_dia:.0f}", "mmHg", "#f472b6", bp_sys_history),
            ("Resp Rate", f"{processed.clean_rr:.0f}", "/min", "#38bdf8", rr_history),
            ("Temp", f"{processed.clean_temp:.1f}", "°C", "#fbbf24", temp_history),
            ("Score", f"{score_result.score:.0f}" if score_result else "—", "/100",
             score_result.status_color if score_result else "#7986cb", []),
        ]
        for i, (label, val, unit, color, hist) in enumerate(metrics):
            with cols[i]:
                delta = _delta(hist) if hist else ("" if not score_result else score_result.status_label)
                dc = "#ff4757" if "↑" in str(delta) else "#00d4aa" if "↓" in str(delta) else color
                st.html(f"""
                <div style="background:rgba(15,20,40,0.5);border:1px solid rgba(255,255,255,0.05);border-radius:10px;padding:10px 8px;text-align:center;">
                    <div style="color:#5c6b8a;font-size:0.52rem;font-weight:600;letter-spacing:1px;text-transform:uppercase;">{label}</div>
                    <div style="font-size:1.3rem;font-weight:800;color:{color};font-family:'JetBrains Mono',monospace;">{val}</div>
                    <div style="color:#4a5568;font-size:0.5rem;">{unit}</div>
                    <div style="color:{dc};font-size:0.55rem;font-weight:600;">{delta}</div>
                </div>""")

    # ── ECG + Score Gauge Row ──
    col_ecg, col_gauge = st.columns([2.2, 1])
    with col_ecg:
        render_ecg_monitor(hr_history, processed, height=220, show_stats=True)
    with col_gauge:
        if score_result:
            render_health_gauge(score_result.score, score_result.status_label, score_result.status_color, score_result.status_emoji)
        if analytics and len(analytics.score_all) > 3:
            fig = create_score_history_chart(analytics.score_all[-60:])
            st.plotly_chart(fig, use_container_width=True, key="doc_score_hist", config=PLOTLY_CONFIG)

    # ── Prediction Trend Analysis ──
    st.html('<div style="color:#e8eaf6;font-size:0.82rem;font-weight:700;margin:6px 0 2px;">📈 Prediction Trend Analysis</div>')
    render_prediction_trend(hr_history, spo2_history, ai_result, key_suffix="doc")

    # ── AI Engine Risk Assessment ──
    risk_pred = state.get("risk_prediction")
    if risk_pred:
        _render_risk_assessment(risk_pred, processed)

    # ── Orders: Prescribe + Assign Tasks ──
    _render_orders_panel(med_tracker, care_log)

    # ── SOAP Notes ──
    _render_soap_notes(processed, ai_result, score_result, symptom_logger)

    # ── Chart + Raw toggle ──
    show_raw = st.toggle("Show Raw vs Processed signals", key="doc_raw", value=False)
    if hr_history and spo2_history:
        fig = create_vitals_chart([], hr_history, spo2_history, hr_raw=hr_raw, spo2_raw=spo2_raw, show_raw=show_raw)
        st.plotly_chart(fig, use_container_width=True, key="doc_chart", config=PLOTLY_CONFIG)

    # ── AI Analysis + Timeline ──
    col_left, col_right = st.columns([1.5, 1.5])
    with col_left:
        if ai_result:
            render_ai_reasoning(ai_result.thinking_steps, ai_result=ai_result, score_result=score_result)
        if ai_result and ai_result.detections:
            for det in ai_result.detections:
                render_detection_card(det)
        if score_result:
            render_score_breakdown(score_result.breakdown)
    with col_right:
        if ai_result and ai_result.risk_prediction:
            render_risk_prediction(ai_result.risk_prediction)
        if ai_result:
            render_anomaly_score(ai_result.anomaly_score)
        if analytics:
            render_event_timeline(analytics.timeline, max_events=8)
        if processed:
            render_confidence_badge(processed.confidence, processed.noise_level)
        if synthetic and analytics:
            render_medisynth_panel(synthetic, analytics, mode)


# ═══════════════════════════════════════════════════════════════════════════════

def _render_orders_panel(med_tracker, care_log):
    """Doctor order panel: prescribe medications and assign tasks."""
    with st.expander("📋 Orders & Prescriptions", expanded=False):
        tab_med, tab_task = st.columns(2)

        with tab_med:
            st.html('<div style="color:#a78bfa;font-size:0.75rem;font-weight:700;margin-bottom:6px;">💊 Prescribe Medication</div>')
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Drug", key="doc_rx_name", placeholder="e.g. Atenolol")
            with c2:
                dose = st.text_input("Dosage", key="doc_rx_dose", placeholder="e.g. 25mg")
            freq = st.selectbox("Frequency", ["once_daily", "twice_daily", "three_daily", "as_needed"], key="doc_rx_freq")
            hour = st.number_input("Start hour", min_value=0, max_value=23, value=8, key="doc_rx_hr")
            if st.button("Prescribe", key="doc_prescribe"):
                if name and dose and med_tracker:
                    hours = [hour] if "once" in freq else [8, 20] if "twice" in freq else [8, 14, 20]
                    med_tracker.add_medication(name, dose, freq, hours, category="cardiac")
                    st.rerun()

        with tab_task:
            st.html('<div style="color:#00d4aa;font-size:0.75rem;font-weight:700;margin-bottom:6px;">✅ Assign Task to Caretaker</div>')
            task_title = st.text_input("Task", key="doc_task_title", placeholder="e.g. Check BP every 2 hours")
            task_hour = st.number_input("Due hour", min_value=0, max_value=23, value=datetime.datetime.now().hour + 1, key="doc_task_hr")
            if st.button("Assign Task", key="doc_assign_task"):
                if task_title and care_log:
                    care_log.add_task(task_title, task_hour, assigned_by="doctor")
                    st.rerun()

        # Current meds list
        if med_tracker and med_tracker.medications:
            st.html('<div style="color:#e8eaf6;font-size:0.72rem;font-weight:700;margin:8px 0 4px;">Current Medications:</div>')
            for med in med_tracker.medications:
                times = ", ".join([f"{h}:00" for h in med.schedule_hours])
                st.html(f'<div style="display:flex;justify-content:space-between;padding:4px 0;font-size:0.68rem;border-bottom:1px solid rgba(255,255,255,0.03);"><span style="color:#c5cae9;">💊 {med.name} {med.dosage}</span><span style="color:#7986cb;">{times}</span></div>')


def _render_soap_notes(processed, ai_result, score_result, symptom_logger):
    """Auto-populated SOAP clinical notes."""
    with st.expander("📝 SOAP Notes", expanded=False):
        # Auto-populate Objective section
        obj_lines = []
        if processed:
            obj_lines.append(f"HR: {processed.clean_hr:.0f} bpm | SpO₂: {processed.clean_spo2:.1f}%")
            obj_lines.append(f"BP: {processed.clean_bp_sys:.0f}/{processed.clean_bp_dia:.0f} mmHg | RR: {processed.clean_rr:.0f}/min | Temp: {processed.clean_temp:.1f}°C")
            obj_lines.append(f"Confidence: {processed.confidence:.0f}% | Noise: {processed.noise_level:.1f}")
        if score_result:
            obj_lines.append(f"Health Score: {score_result.score:.0f}/100 ({score_result.status_label})")
        if ai_result and ai_result.detections:
            for det in ai_result.detections:
                obj_lines.append(f"AI Detection: {det.condition} ({det.severity}, {det.confidence:.0f}%)")

        # Subjective: from symptom logger
        subj_default = ""
        if symptom_logger:
            todays = symptom_logger.get_todays_entries()
            if todays:
                subj_default = ", ".join([f"{e.icon} {e.label}" for e in todays[-5:]])

        st.text_area("**S** — Subjective (patient complaints)", value=subj_default,
                     key="soap_s", height=60, placeholder="Patient reports...")
        st.text_area("**O** — Objective (vitals & findings)", value="\n".join(obj_lines),
                     key="soap_o", height=80)
        st.text_area("**A** — Assessment", key="soap_a", height=60,
                     value=ai_result.summary if ai_result else "", placeholder="Clinical assessment...")
        st.text_area("**P** — Plan", key="soap_p", height=60,
                     placeholder="Treatment plan, orders, follow-up...")

        if st.button("📥 Export SOAP Note", key="doc_soap_export"):
            note = f"SOAP NOTE — {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            note += f"\nS: {st.session_state.get('soap_s', '')}"
            note += f"\nO: {st.session_state.get('soap_o', '')}"
            note += f"\nA: {st.session_state.get('soap_a', '')}"
            note += f"\nP: {st.session_state.get('soap_p', '')}"
            st.download_button("Download", data=note,
                file_name=f"soap_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain", key="doc_soap_dl")


def _delta(history, fmt=".1f"):
    if len(history) < 2: return ""
    d = history[-1] - history[-2]
    arrow = "↑" if d > 0 else "↓" if d < 0 else "→"
    return f"{arrow} {d:{fmt}}"


def _render_risk_assessment(risk_pred, processed):
    """AI Engine risk prediction panel — shows risk score, factors, 5-min forecasts."""
    import streamlit.components.v1 as components

    risk = risk_pred.risk_score
    level = risk_pred.risk_level
    conf = risk_pred.confidence
    factors = risk_pred.contributing_factors

    # Colors per level
    level_config = {
        "low": {"color": "#00d4aa", "bg": "rgba(0,212,170,0.06)", "border": "rgba(0,212,170,0.15)", "icon": "✅"},
        "moderate": {"color": "#fbbf24", "bg": "rgba(251,191,36,0.06)", "border": "rgba(251,191,36,0.15)", "icon": "⚠️"},
        "high": {"color": "#f97316", "bg": "rgba(249,115,22,0.06)", "border": "rgba(249,115,22,0.15)", "icon": "🔶"},
        "critical": {"color": "#ff4757", "bg": "rgba(255,71,87,0.06)", "border": "rgba(255,71,87,0.15)", "icon": "🚨"},
    }
    cfg = level_config.get(level, level_config["low"])

    # Build factors HTML
    factors_html = ""
    for f in factors[:5]:
        factors_html += f'<div style="padding:3px 0;color:#c5cae9;font-size:0.62rem;">• {f}</div>'

    # 5-min forecast
    pred_hr = risk_pred.predicted_hr_5m
    pred_spo2 = risk_pred.predicted_spo2_5m
    current_hr = processed.clean_hr if processed else 72
    current_spo2 = processed.clean_spo2 if processed else 97.5
    hr_delta = pred_hr - current_hr
    spo2_delta = pred_spo2 - current_spo2
    hr_arrow = "↑" if hr_delta > 0.5 else "↓" if hr_delta < -0.5 else "→"
    spo2_arrow = "↑" if spo2_delta > 0.5 else "↓" if spo2_delta < -0.5 else "→"

    components.html(f"""
    <div style="background:{cfg['bg']};border:1px solid {cfg['border']};border-radius:14px;
        padding:14px 16px;font-family:'Inter',sans-serif;margin:6px 0;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
            <div style="display:flex;align-items:center;gap:8px;">
                <span style="font-size:1.1rem;">{cfg['icon']}</span>
                <div>
                    <div style="color:{cfg['color']};font-size:0.65rem;font-weight:700;letter-spacing:1px;text-transform:uppercase;">
                        AI RISK ENGINE · {level.upper()}</div>
                    <div style="color:#5c6b8a;font-size:0.5rem;">Model {risk_pred.model_version} · Conf: {conf:.0f}%</div>
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:1.8rem;font-weight:900;color:{cfg['color']};line-height:1;">{risk:.0f}</div>
                <div style="color:#5c6b8a;font-size:0.45rem;">/ 100 RISK</div>
            </div>
        </div>

        <div style="width:100%;height:6px;background:rgba(255,255,255,0.04);border-radius:3px;margin:8px 0;">
            <div style="width:{min(100, risk)}%;height:100%;background:{cfg['color']};border-radius:3px;
                transition:width 0.5s ease;"></div>
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px;">
            <div>
                <div style="color:#5c6b8a;font-size:0.5rem;font-weight:600;letter-spacing:0.5px;margin-bottom:4px;">
                    CONTRIBUTING FACTORS</div>
                {factors_html}
            </div>
            <div>
                <div style="color:#5c6b8a;font-size:0.5rem;font-weight:600;letter-spacing:0.5px;margin-bottom:4px;">
                    5-MIN FORECAST</div>
                <div style="padding:6px 8px;background:rgba(255,255,255,0.02);border-radius:8px;margin-top:4px;">
                    <div style="display:flex;justify-content:space-between;font-size:0.6rem;padding:2px 0;">
                        <span style="color:#7986cb;">HR</span>
                        <span style="color:#00d4aa;font-weight:700;">{pred_hr:.0f} bpm {hr_arrow}</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;font-size:0.6rem;padding:2px 0;">
                        <span style="color:#7986cb;">SpO₂</span>
                        <span style="color:#a78bfa;font-weight:700;">{pred_spo2:.1f}% {spo2_arrow}</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """, height=220)
