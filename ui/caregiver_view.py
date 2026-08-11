"""
Medisynth Live – Caregiver Dashboard View (Professional Clinical)
Care log, medication admin, task checklist, vitals, prediction trends, alerts.
"""
import streamlit as st
import datetime
from ui.components import (
    render_vital_card, render_bp_card, render_health_gauge,
    create_vitals_chart, render_confidence_badge, render_risk_prediction,
    render_event_timeline, render_session_info, render_data_source_label,
    render_emergency_notification, PLOTLY_CONFIG,
)
from ui.shared_widgets import render_ecg_monitor, render_prediction_trend


def render_caregiver_view(state: dict):
    """Professional caregiver dashboard with care coordination."""
    score_result = state.get("score_result")
    ai_result = state.get("ai_result")
    processed = state.get("processed")
    emergency = state.get("emergency_system")
    analytics = state.get("analytics")
    location = state.get("location")
    hr_history = state.get("hr_history", [])
    spo2_history = state.get("spo2_history", [])
    bp_sys_history = state.get("bp_sys_history", [])
    bp_dia_history = state.get("bp_dia_history", [])
    rr_history = state.get("rr_history", [])
    temp_history = state.get("temp_history", [])
    mode = state.get("mode", "normal")
    notif_svc = state.get("notification_service")
    med_tracker = state.get("med_tracker")
    care_log = state.get("care_log")

    # Emergency banner
    if emergency and emergency.active_alert:
        render_emergency_notification(emergency.active_alert, emergency.contacts, location)
        if st.button("✕ Dismiss", key="cg_dismiss"):
            emergency.dismiss_alert()
            st.rerun()

    # ── Top Row: Score + ECG ──
    c_score, c_ecg = st.columns([0.7, 1.5])
    with c_score:
        if score_result:
            _render_score_card(score_result, ai_result)
    with c_ecg:
        render_ecg_monitor(hr_history, processed, height=220, show_stats=True)

    # ── Vitals Row: 6 metrics ──
    if processed:
        cols = st.columns(6)
        vitals = [
            ("💓", "Heart Rate", f"{processed.clean_hr:.0f}", "bpm", "#00d4aa", hr_history),
            ("🫁", "SpO₂", f"{processed.clean_spo2:.1f}", "%", "#a78bfa", spo2_history),
            ("🩸", "Systolic", f"{processed.clean_bp_sys:.0f}", "mmHg", "#f472b6", bp_sys_history),
            ("🩸", "Diastolic", f"{processed.clean_bp_dia:.0f}", "mmHg", "#ff6b9d", bp_dia_history),
            ("🌬️", "Resp Rate", f"{processed.clean_rr:.0f}", "/min", "#38bdf8", rr_history),
            ("🌡️", "Temp", f"{processed.clean_temp:.1f}", "°C", "#fbbf24", temp_history),
        ]
        for i, (icon, label, val, unit, color, hist) in enumerate(vitals):
            with cols[i]:
                delta = _delta(hist)
                dc = "#ff4757" if "↑" in delta else "#00d4aa" if "↓" in delta else "#5c6b8a"
                st.html(f"""
                <div style="background:rgba(15,20,40,0.5);border:1px solid rgba(255,255,255,0.05);border-radius:12px;padding:10px 8px;text-align:center;">
                    <div style="font-size:0.85rem;">{icon}</div>
                    <div style="color:#5c6b8a;font-size:0.55rem;font-weight:600;letter-spacing:0.5px;text-transform:uppercase;margin:2px 0;">{label}</div>
                    <div style="font-size:1.4rem;font-weight:800;color:{color};font-family:'JetBrains Mono',monospace;">{val}</div>
                    <div style="color:#4a5568;font-size:0.55rem;">{unit}</div>
                    <div style="color:{dc};font-size:0.6rem;font-weight:600;margin-top:2px;">{delta}</div>
                </div>""")

    # ── Care Log + Tasks Row ──
    col_care, col_tasks = st.columns([1.2, 1])
    with col_care:
        _render_care_log_panel(care_log, processed, score_result)
    with col_tasks:
        _render_task_panel(care_log)
        _render_med_admin_panel(med_tracker, processed)

    # ── Main: Prediction Trend + Right Panel ──
    col_main, col_side = st.columns([1.6, 1])
    with col_main:
        st.html('<div style="color:#e8eaf6;font-size:0.8rem;font-weight:700;margin:8px 0 4px;">📈 Prediction Trend Analysis</div>')
        render_prediction_trend(hr_history, spo2_history, ai_result, key_suffix="cg")
        if hr_history and spo2_history and len(hr_history) > 3:
            with st.expander("📊 Detailed Vitals Chart", expanded=False):
                fig = create_vitals_chart([], hr_history, spo2_history)
                st.plotly_chart(fig, use_container_width=True, key="cg_chart", config=PLOTLY_CONFIG)
        
        from ui.shared_widgets import render_historical_data_entry
        render_historical_data_entry(key_suffix="cg")

    with col_side:
        if ai_result:
            _render_ai_assessment(ai_result)
        if ai_result and ai_result.risk_prediction:
            render_risk_prediction(ai_result.risk_prediction)
        if emergency and emergency.alert_history:
            _render_alert_history(emergency.alert_history)
        if analytics:
            render_event_timeline(analytics.timeline, max_events=5)

    # Shift Report export
    if care_log:
        with st.expander("📋 Export Shift Report", expanded=False):
            report = care_log.generate_shift_report()
            st.code(report, language="text")
            st.download_button("📥 Download Report", data=report,
                file_name=f"shift_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain", key="cg_shift_dl")

    # Patient Location (emergency only)
    if emergency and emergency.active_alert and location and location.get("lat"):
        maps_link = f"https://www.google.com/maps?q={location['lat']},{location['lng']}"
        city = f"{location.get('city', '')} {location.get('region', '')}"
        st.html(f"""
        <div style="background:rgba(255,71,87,0.06);border:1px solid rgba(255,71,87,0.15);border-radius:12px;padding:14px;margin:8px 0;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div><span style="color:#ff4757;font-weight:700;font-size:0.85rem;">📍 Patient Location</span>
                    <div style="color:#7986cb;font-size:0.72rem;margin-top:2px;">{city} ({location['lat']:.4f}, {location['lng']:.4f})</div></div>
                <a href="{maps_link}" target="_blank" style="color:#00d4aa;font-size:0.75rem;text-decoration:none;padding:6px 12px;background:rgba(0,212,170,0.1);border-radius:8px;font-weight:600;">🗺️ Open Map</a>
            </div>
        </div>""")

    # Footer
    if analytics:
        st.html(f'<div style="text-align:center;padding:8px 0;color:#3d4a66;font-size:0.6rem;">Session {analytics.session_id} · {analytics.get_elapsed_str()} · {analytics.total_readings} readings</div>')


# ═══════════════════════════════════════════════════════════════════════════════
# ── Private Components ──
# ═══════════════════════════════════════════════════════════════════════════════

def _render_care_log_panel(care_log, processed, score_result):
    """Care activity log with quick-entry buttons."""
    if not care_log:
        return
    from modules.care_log import CARE_ACTIVITIES

    todays = care_log.get_todays_entries()

    # Header
    st.html(f"""
    <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);border-radius:14px;overflow:hidden;margin:4px 0;">
        <div style="padding:9px 14px;border-bottom:1px solid rgba(255,255,255,0.04);display:flex;justify-content:space-between;align-items:center;">
            <span style="color:#e8eaf6;font-size:0.78rem;font-weight:700;">📝 Care Log</span>
            <span style="background:rgba(0,212,170,0.1);color:#00d4aa;padding:2px 8px;border-radius:10px;font-size:0.55rem;font-weight:700;">{len(todays)} today</span>
        </div>
    </div>""")

    # Quick-entry buttons (3 columns)
    top_activities = CARE_ACTIVITIES[:6]
    cols = st.columns(3)
    for i, act in enumerate(top_activities):
        with cols[i % 3]:
            if st.button(f"{act['icon']} {act['label']}", key=f"cg_care_{act['id']}", use_container_width=True):
                care_log.log_activity(act["id"], processed=processed, score_result=score_result)
                st.rerun()

    # Add note
    with st.expander("📝 Add Observation", expanded=False):
        note = st.text_area("Notes", key="cg_care_note", height=60, placeholder="Patient observation...")
        if st.button("Save Note", key="cg_save_note"):
            if note:
                care_log.log_activity("observation", notes=note, processed=processed, score_result=score_result)
                st.rerun()

    # Recent entries
    if todays:
        entries_html = ""
        for e in reversed(todays[-5:]):
            ts = datetime.datetime.fromtimestamp(e.timestamp).strftime("%H:%M")
            note_str = f' — <span style="color:#7986cb;">{e.notes[:40]}</span>' if e.notes else ""
            vital_str = ""
            if e.hr:
                vital_str = f' <span style="color:#4a5568;font-size:0.5rem;">[HR:{e.hr:.0f}]</span>'
            entries_html += f'<div style="display:flex;justify-content:space-between;padding:4px 10px;font-size:0.65rem;border-bottom:1px solid rgba(255,255,255,0.03);"><span style="color:#c5cae9;">{e.icon} {e.label}{note_str}{vital_str}</span><span style="color:#5c6b8a;">{ts}</span></div>'
        st.html(f'<div style="background:rgba(255,255,255,0.015);border:1px solid rgba(255,255,255,0.04);border-radius:12px;overflow:hidden;margin:4px 0;">{entries_html}</div>')


def _render_task_panel(care_log):
    """Task checklist for doctor-assigned tasks."""
    if not care_log:
        return

    pending = care_log.get_pending_tasks()
    done = [t for t in care_log.tasks if t.is_done]
    now_hour = datetime.datetime.now().hour

    # Header
    overdue = [t for t in pending if t.due_hour <= now_hour]
    badge = ""
    if overdue:
        badge = f'<span style="background:rgba(255,71,87,0.15);color:#ff4757;padding:2px 8px;border-radius:10px;font-size:0.55rem;font-weight:700;margin-left:6px;">{len(overdue)} overdue</span>'

    st.html(f"""
    <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);border-radius:14px;overflow:hidden;margin:4px 0;">
        <div style="padding:9px 14px;border-bottom:1px solid rgba(255,255,255,0.04);display:flex;align-items:center;">
            <span style="color:#e8eaf6;font-size:0.78rem;font-weight:700;">✅ Tasks</span>
            <span style="color:#5c6b8a;font-size:0.55rem;margin-left:6px;">{len(done)}/{len(care_log.tasks)}</span>
            {badge}
        </div>
    </div>""")

    # Pending tasks
    for task in pending[:5]:
        is_overdue = task.due_hour <= now_hour
        color = "#ff4757" if is_overdue else "#fbbf24" if task.due_hour - now_hour <= 1 else "#5c6b8a"
        if st.button(f"○ {task.title} — {task.due_hour}:00", key=f"cg_task_{task.id}", use_container_width=True):
            care_log.complete_task(task.id)
            st.rerun()

    # Add task
    with st.expander("➕ Add Task", expanded=False):
        title = st.text_input("Task", key="cg_task_title", placeholder="e.g. Check BP")
        hour = st.number_input("Due hour (24h)", min_value=0, max_value=23, value=now_hour + 1, key="cg_task_hr")
        if st.button("Add Task", key="cg_add_task"):
            if title:
                care_log.add_task(title, hour, assigned_by="caretaker")
                st.rerun()


def _render_med_admin_panel(med_tracker, processed):
    """Medication administration panel for caretakers."""
    if not med_tracker or not med_tracker.medications:
        return

    reminders = med_tracker.get_upcoming_reminders(4)
    st.html("""
    <div style="background:rgba(167,139,250,0.04);border:1px solid rgba(167,139,250,0.12);border-radius:14px;overflow:hidden;margin:4px 0;">
        <div style="padding:9px 14px;border-bottom:1px solid rgba(167,139,250,0.08);">
            <span style="color:#a78bfa;font-size:0.78rem;font-weight:700;">💊 Medication Administration</span>
        </div>
    </div>""")

    for med in med_tracker.medications:
        overdue_for = [r for r in reminders if r.med_id == med.id and r.is_overdue]
        color = "#ff4757" if overdue_for else "#a78bfa"
        label = f"💊 Administer {med.name} ({med.dosage})"
        if overdue_for:
            label += " ⚠️ OVERDUE"
        if st.button(label, key=f"cg_admin_{med.id}", use_container_width=True):
            med_tracker.log_administration(med.id, taken_by="caretaker", processed=processed)
            st.rerun()


def _render_score_card(score_result, ai_result):
    s = score_result.score
    c = score_result.status_color
    emoji = score_result.status_emoji
    label = score_result.status_label
    if s >= 90: bg, bd = "rgba(0,212,170,0.06)", "rgba(0,212,170,0.15)"
    elif s >= 70: bg, bd = "rgba(74,222,128,0.06)", "rgba(74,222,128,0.15)"
    elif s >= 50: bg, bd = "rgba(251,191,36,0.06)", "rgba(251,191,36,0.15)"
    else: bg, bd = "rgba(255,71,87,0.06)", "rgba(255,71,87,0.15)"
    status_text = ai_result.summary if ai_result else "Analyzing..."
    det_count = len(ai_result.detections) if ai_result and ai_result.detections else 0
    det_badge = f'<span style="background:rgba(255,71,87,0.12);color:#ff4757;padding:2px 8px;border-radius:10px;font-size:0.6rem;font-weight:600;">{det_count} alert{"s" if det_count != 1 else ""}</span>' if det_count > 0 else '<span style="background:rgba(0,212,170,0.1);color:#00d4aa;padding:2px 8px;border-radius:10px;font-size:0.6rem;font-weight:600;">No alerts</span>'
    st.html(f"""
    <div style="background:{bg};border:1px solid {bd};border-radius:14px;padding:16px;text-align:center;">
        <div style="font-size:0.6rem;color:#5c6b8a;font-weight:600;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;">PATIENT STATUS</div>
        <div style="font-size:3rem;font-weight:900;color:{c};font-family:'JetBrains Mono',monospace;line-height:1;">{s:.0f}</div>
        <div style="color:#5c6b8a;font-size:0.7rem;margin:2px 0 8px;">/ 100</div>
        <div style="font-size:1.2rem;margin-bottom:4px;">{emoji} {label}</div>
        <div style="margin:6px 0;">{det_badge}</div>
        <div style="color:#7986cb;font-size:0.68rem;line-height:1.4;margin-top:6px;">{status_text[:80]}</div>
    </div>""")


def _render_ai_assessment(ai_result):
    overall = ai_result.overall_status
    if overall == "critical": bg, bd, ic, title = "rgba(255,71,87,0.06)", "rgba(255,71,87,0.18)", "🔴", "CRITICAL"
    elif overall == "monitoring": bg, bd, ic, title = "rgba(255,179,71,0.06)", "rgba(255,179,71,0.18)", "🟡", "MONITORING"
    else: bg, bd, ic, title = "rgba(0,212,170,0.05)", "rgba(0,212,170,0.12)", "🟢", "STABLE"
    dets_html = ""
    for det in (ai_result.detections or [])[:4]:
        sc = "#ff4757" if det.severity == "critical" else "#ffb347"
        dets_html += f'<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.03);font-size:0.72rem;"><span style="color:#c5cae9;">{det.condition}</span><span style="color:{sc};font-weight:600;">{det.confidence:.0f}%</span></div>'
    if not dets_html:
        dets_html = '<div style="color:#00d4aa;font-size:0.72rem;padding:4px 0;">✓ All vitals within normal range</div>'
    st.html(f"""
    <div style="background:{bg};border:1px solid {bd};border-radius:14px;padding:14px;margin:4px 0;">
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;">
            <span>{ic}</span>
            <span style="color:#e8eaf6;font-size:0.78rem;font-weight:700;">AI Assessment: {title}</span>
        </div>
        {dets_html}
        <div style="color:#7986cb;font-size:0.65rem;margin-top:6px;line-height:1.4;">{ai_result.summary}</div>
    </div>""")


def _render_alert_history(alert_history):
    entries = ""
    for alert in reversed(alert_history[-5:]):
        ts = datetime.datetime.fromtimestamp(alert.timestamp).strftime("%H:%M:%S")
        entries += f'<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.03);font-size:0.7rem;"><span style="color:#7986cb;">{ts}</span><span style="color:#ff4757;font-weight:600;">Score: {alert.health_score:.0f}</span></div>'
    st.html(f"""
    <div style="background:rgba(255,71,87,0.04);border:1px solid rgba(255,71,87,0.1);border-radius:14px;padding:14px;margin:4px 0;">
        <div style="color:#ff4757;font-size:0.72rem;font-weight:700;margin-bottom:6px;">🚨 Alert History ({len(alert_history)})</div>
        {entries}
    </div>""")


def _delta(history, fmt=".1f"):
    if len(history) < 2: return "—"
    d = history[-1] - history[-2]
    arrow = "↑" if d > 0 else "↓" if d < 0 else "→"
    return f"{arrow} {d:{fmt}}"
