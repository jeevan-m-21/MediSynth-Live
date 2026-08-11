"""
Medisynth Live – Main Application
AI-Powered Preventive Health Monitoring System

Uses @st.fragment for auto-refreshing dashboard — eliminates duplication by
only re-rendering the dashboard fragment instead of the entire page.
"""

import streamlit as st
import time

import config
from modules.simulation_engine import SimulationEngine
from modules.synthetic_engine import SyntheticEngine
from modules.preprocessing import PreprocessingPipeline
from modules.ai_detection import AIDetectionEngine
from modules.baseline_engine import BaselineEngine
from modules.health_score import HealthScoreEngine
from modules.emergency_system import EmergencySystem
from modules.analytics_engine import AnalyticsEngine
from modules.notification_service import NotificationService
from modules.location_service import request_location, build_maps_link
from modules.hospital_finder import find_nearby_hospitals, format_hospitals_for_message
from modules.sound_alerts import play_alert
from modules.ml_anomaly_model import MLAnomalyDetector
from modules.sos_emergency import get_sos_overlay_html
from modules.medication_tracker import MedicationTracker
from modules.symptom_logger import SymptomLogger
from modules.care_log import CareLog

from ui.styles import inject_css
from ui.simulation_panel import render_simulation_panel
from ui.patient_view import render_patient_view
from ui.caregiver_view import render_caregiver_view
from ui.doctor_view import render_doctor_view
from ui.components import render_status_banner
from ui.patient_selector import render_patient_selector, render_user_badge
from backend.models.database import init_db, seed_demo_users
from backend.auth.middleware import init_auth, is_authenticated, require_auth, get_user_role

# ── Page Config ──
st.set_page_config(
    page_title="Medisynth Live – AI Health Monitoring",
    page_icon="🫀",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

# ── Initialize Database & Auth (once) ──
if "db_initialized" not in st.session_state:
    init_db()
    seed_demo_users()
    st.session_state["db_initialized"] = True
init_auth()

# ── Auth Gate — show login if not authenticated ──
require_auth()


# ── Initialize ──
def init_state():
    defaults = {
        "sim_engine": SimulationEngine(),
        "synthetic_engine": SyntheticEngine(),
        "preprocessing": PreprocessingPipeline(),
        "ai_engine": AIDetectionEngine(),
        "baseline_engine": BaselineEngine(),
        "score_engine": HealthScoreEngine(),
        "emergency_system": EmergencySystem(),
        "analytics": AnalyticsEngine(),
        "notification_service": NotificationService(),
        "ml_model": MLAnomalyDetector(),
        "med_tracker": MedicationTracker(),
        "symptom_logger": SymptomLogger(),
        "care_log": CareLog(),
        "role": "Patient",
        "last_update": 0.0,
        "tick_count": 0,
        "baseline_started": False,
        "hr_history": [],
        "spo2_history": [],
        "hr_raw_history": [],
        "spo2_raw_history": [],
        "bp_sys_history": [],
        "bp_dia_history": [],
        "rr_history": [],
        "temp_history": [],
        "timestamps": [],
        "processed": None,
        "ai_result": None,
        "score_result": None,
        "deviation": None,
        "sound_muted": False,
        "prev_status": "stable",
        "auto_notified_alert_ts": 0,
        "patient_name": "Patient",  # Configurable patient name
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    if "location" not in st.session_state:
        request_location()

def switch_patient_context(new_patient_id: str, new_patient_name: str):
    """Save current patient's simulation context and load the new one."""
    if "patient_contexts" not in st.session_state:
        st.session_state["patient_contexts"] = {}
        
    current_id = st.session_state.get("selected_patient_id")
    if current_id == new_patient_id:
        return
    
    # Keys that belong to a patient's specific simulation instance
    context_keys = [
        "sim_engine", "synthetic_engine", "preprocessing", "ai_engine",
        "baseline_engine", "score_engine", "analytics",
        "ml_model", "med_tracker", "symptom_logger", "care_log",
        "last_update", "tick_count", "baseline_started", "hr_history",
        "spo2_history", "hr_raw_history", "spo2_raw_history", "bp_sys_history",
        "bp_dia_history", "rr_history", "temp_history", "timestamps",
        "processed", "ai_result", "score_result", "deviation",
        "prev_status", "auto_notified_alert_ts"
    ]
    
    # Save old context
    if current_id:
        old_context = {}
        for k in context_keys:
            if k in st.session_state:
                old_context[k] = st.session_state[k]
        st.session_state["patient_contexts"][current_id] = old_context
        
    # Set active ID
    st.session_state["selected_patient_id"] = new_patient_id
    st.session_state["selected_patient_name"] = new_patient_name
    st.session_state["patient_name"] = new_patient_name
    
    # Load new context or clear for fresh init
    if new_patient_id in st.session_state["patient_contexts"]:
        for k, v in st.session_state["patient_contexts"][new_patient_id].items():
            st.session_state[k] = v
    else:
        for k in context_keys:
            if k in st.session_state:
                del st.session_state[k]
        init_state()

init_state()


# ── Map auth role → dashboard role ──
_auth_role = get_user_role()
_role_map = {"patient": "Patient", "doctor": "Doctor", "caregiver": "Caregiver"}
if _auth_role in _role_map:
    st.session_state.role = _role_map[_auth_role]

# ── Sidebar ──
with st.sidebar:
    render_user_badge()
    if _auth_role in ("doctor", "caregiver"):
        render_patient_selector()
    render_simulation_panel(
        st.session_state.sim_engine,
        st.session_state.synthetic_engine,
        st.session_state.emergency_system,
        st.session_state.notification_service,
    )


# ── Detailed Alert Message Builder ──
def _build_detailed_alert(patient_name, score_result, processed, ai_result, maps_link):
    """Build a comprehensive emergency message with full vitals and AI analysis."""
    lines = []
    lines.append("MEDISYNTH LIVE - EMERGENCY ALERT")
    lines.append(f"Patient: {patient_name}")
    lines.append("")

    # Health score
    lines.append(f"Health Score: {score_result.score:.0f}/100 ({score_result.status_label})")
    lines.append("")

    # All 5 vitals
    lines.append("--- VITAL SIGNS ---")
    lines.append(f"Heart Rate: {processed.clean_hr:.0f} bpm")
    lines.append(f"SpO2: {processed.clean_spo2:.1f}%")
    lines.append(f"Blood Pressure: {processed.clean_bp_sys:.0f}/{processed.clean_bp_dia:.0f} mmHg")
    lines.append(f"Respiratory Rate: {processed.clean_rr:.0f} breaths/min")
    lines.append(f"Temperature: {processed.clean_temp:.1f} C")
    lines.append(f"Data Confidence: {processed.confidence:.0f}%")
    lines.append("")

    # AI detections
    if ai_result.detections:
        lines.append("--- AI DETECTIONS ---")
        for det in ai_result.detections:
            dur = f" [{det.duration_s:.0f}s]" if det.duration_s > 0 else ""
            lines.append(f"[{det.severity.upper()}] {det.condition}{dur} (conf: {det.confidence:.0f}%)")
            if det.evidence:
                lines.append(f"  -> {det.evidence[0]}")
        lines.append("")

    # Anomaly + Risk
    anomaly_pct = round(ai_result.anomaly_score * 100)
    lines.append(f"Anomaly Score: {anomaly_pct}%")
    if ai_result.risk_prediction:
        rp = ai_result.risk_prediction
        lines.append(f"3-Min Forecast: {rp.trend_direction} (score: {rp.predicted_score:.0f})")
        if rp.time_to_critical_s:
            lines.append(f"Time to Critical: {rp.time_to_critical_s:.0f}s")
    lines.append("")

    # Nearby hospitals (if location available)
    loc = st.session_state.get("location")
    if loc and loc.get("lat"):
        try:
            hospitals = find_nearby_hospitals(loc["lat"], loc["lng"], radius_km=5, max_results=3)
            if hospitals:
                hosp_text = format_hospitals_for_message(hospitals, max_count=3)
                lines.append(hosp_text)
                lines.append("")
                # Store in session for UI display
                st.session_state["nearby_hospitals"] = hospitals
        except Exception:
            pass

    # Summary
    lines.append(f"AI Summary: {ai_result.summary}")

    return "\n".join(lines)


# ── Data Processing Function ──
def process_tick():
    """Run one simulation tick: generate → preprocess → analyze → score → alert."""
    now = time.time()
    if (now - st.session_state.last_update) < (config.UPDATE_INTERVAL_S * 0.8):
        return

    st.session_state.last_update = now
    st.session_state.tick_count += 1

    sim = st.session_state.sim_engine
    synth = st.session_state.synthetic_engine
    preproc = st.session_state.preprocessing
    ai = st.session_state.ai_engine
    baseline = st.session_state.baseline_engine
    scorer = st.session_state.score_engine
    emerg = st.session_state.emergency_system
    analytics = st.session_state.analytics
    notif = st.session_state.notification_service

    if sim.mode != analytics.current_mode:
        analytics.record_mode_change(sim.mode)

    if not st.session_state.baseline_started:
        baseline.start_capture()
        st.session_state.baseline_started = True

    # Generate
    reading = None
    if synth.is_active():
        reading = synth.generate_reading(
            base_hr=sim._prev_hr, base_spo2=sim._prev_spo2,
            base_bp_sys=sim._prev_bp_sys, base_bp_dia=sim._prev_bp_dia,
            base_rr=sim._prev_rr, base_temp=sim._prev_temp,
        )
    if not reading:
        reading = sim.generate_reading()

    st.session_state.hr_raw_history.append(reading.heart_rate)
    st.session_state.spo2_raw_history.append(reading.spo2)

    processed = preproc.process(
        reading.heart_rate, reading.spo2,
        reading.bp_systolic, reading.bp_diastolic,
        reading.respiratory_rate, reading.temperature,
    )
    st.session_state.processed = processed

    st.session_state.hr_history.append(processed.clean_hr)
    st.session_state.spo2_history.append(processed.clean_spo2)
    st.session_state.bp_sys_history.append(processed.clean_bp_sys)
    st.session_state.bp_dia_history.append(processed.clean_bp_dia)
    st.session_state.rr_history.append(processed.clean_rr)
    st.session_state.temp_history.append(processed.clean_temp)
    st.session_state.timestamps.append(reading.timestamp)

    max_pts = config.HISTORY_MAX_POINTS
    for key in ["hr_history", "spo2_history", "hr_raw_history", "spo2_raw_history",
                "bp_sys_history", "bp_dia_history", "rr_history", "temp_history", "timestamps"]:
        if len(st.session_state[key]) > max_pts:
            st.session_state[key] = st.session_state[key][-max_pts:]

    if baseline.is_capturing:
        baseline.add_sample(processed.clean_hr, processed.clean_spo2)
    st.session_state.deviation = baseline.compute_deviation(processed.clean_hr, processed.clean_spo2)

    bl_hr = baseline.baseline.hr_mean if baseline.has_baseline() else None
    bl_spo2 = baseline.baseline.spo2_mean if baseline.has_baseline() else None

    ai_result = ai.analyze(
        processed.clean_hr, processed.clean_spo2,
        bp_sys=processed.clean_bp_sys, bp_dia=processed.clean_bp_dia,
        rr=processed.clean_rr, temp=processed.clean_temp,
        baseline_hr=bl_hr, baseline_spo2=bl_spo2,
        confidence=processed.confidence,
        mode=st.session_state.sim_engine.mode,
    )
    st.session_state.ai_result = ai_result

    score_result = scorer.compute(
        processed.clean_hr, processed.clean_spo2,
        bp_sys=processed.clean_bp_sys, bp_dia=processed.clean_bp_dia,
        rr=processed.clean_rr, temp=processed.clean_temp,
        baseline_hr=bl_hr, baseline_spo2=bl_spo2,
        confidence=processed.confidence,
        mode=st.session_state.sim_engine.mode,
    )
    st.session_state.score_result = score_result

    # ML Anomaly Detection (Isolation Forest)
    ml = st.session_state.ml_model
    is_normal = ai_result.overall_status in ("stable", "normal")
    ml_result = ml.update_and_predict(
        processed.clean_hr, processed.clean_spo2,
        bp_sys=processed.clean_bp_sys, bp_dia=processed.clean_bp_dia,
        rr=processed.clean_rr, temp=processed.clean_temp,
        is_normal_context=is_normal,
    )
    st.session_state.ml_result = ml_result

    # AI Engine Risk Prediction (plug-in style)
    if "risk_predictor" not in st.session_state:
        from ai_engine.predict import RiskPredictor
        st.session_state["risk_predictor"] = RiskPredictor()
    risk_pred = st.session_state.risk_predictor
    risk_result = risk_pred.predict(
        hr_history=list(st.session_state.hr_history),
        spo2_history=list(st.session_state.spo2_history),
        bp_sys=processed.clean_bp_sys, bp_dia=processed.clean_bp_dia,
        rr=processed.clean_rr, temp=processed.clean_temp,
        health_score=score_result.score,
    )
    st.session_state.risk_prediction = risk_result

    analytics.record_reading(
        processed.clean_hr, processed.clean_spo2,
        processed.clean_bp_sys, processed.clean_bp_dia,
        processed.clean_rr, processed.clean_temp,
        score_result.score,
    )
    for det in ai_result.detections:
        analytics.record_detection(det.condition, det.severity, det.evidence[0] if det.evidence else "")

    # AUTO-EMERGENCY
    if emerg.should_trigger_alert(score_result.score, ai_result.overall_status):
        loc = st.session_state.get("location")
        alert = emerg.trigger_alert(
            score_result.score, processed.clean_hr, processed.clean_spo2,
            ai_result.overall_status, location=loc,
        )
        analytics.record_alert(score_result.score)
        maps_link = build_maps_link(loc["lat"], loc["lng"]) if loc and loc.get("lat") else alert.google_maps_link
        emerg.notify_contacts()

        # Build detailed AI emergency message
        patient_name = st.session_state.get("patient_name", "Patient")
        detailed_msg = _build_detailed_alert(
            patient_name, score_result, processed, ai_result, maps_link
        )

        # Send notification SYNCHRONOUSLY (not async) to ensure it completes
        if emerg.contacts and (now - st.session_state.auto_notified_alert_ts > 30):
            print(f"[MEDISYNTH] ALERT: Sending emergency to {len(emerg.contacts)} contacts...")
            results = notif.send_to_all_contacts(
                emerg.contacts, detailed_msg, maps_link,
                patient_name=patient_name,
            )
            for r in results:
                status = "SUCCESS" if r.success else f"FAIL: {r.error}"
                print(f"[MEDISYNTH] -> {r.recipient} via {r.provider}: {status}")
            st.session_state.auto_notified_alert_ts = now
        emerg.confirm_alert()

        # Trigger SOS overlay for critical emergencies
        st.session_state.sos_active = True
        st.session_state.sos_data = {
            "patient_name": patient_name,
            "hr": processed.clean_hr,
            "spo2": processed.clean_spo2,
            "bp_sys": processed.clean_bp_sys,
            "bp_dia": processed.clean_bp_dia,
            "health_score": score_result.score,
            "ai_status": ai_result.summary,
        }

    if ai_result.overall_status != st.session_state.prev_status:
        if not st.session_state.sound_muted:
            if ai_result.overall_status == "critical":
                play_alert("critical")
            elif ai_result.overall_status == "monitoring":
                play_alert("warning")
        # Auto-dismiss SOS when patient stabilizes
        if ai_result.overall_status in ("stable", "normal", "monitoring") and st.session_state.get("sos_active"):
            st.session_state.sos_active = False
        st.session_state.prev_status = ai_result.overall_status


# ── Auto-refreshing Dashboard Fragment ──
@st.fragment(run_every=1.0)
def dashboard_fragment():
    """This fragment auto-reruns every 1s, re-rendering ONLY itself — not the full page."""
    # Process new data
    process_tick()

    # Status
    overall = st.session_state.ai_result.overall_status if st.session_state.ai_result else "stable"
    render_status_banner(overall)

    # Title bar — compact
    st.html(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
        <div>
            <span style="font-size:1.3rem; font-weight:800; color:#e8eaf6;">Medisynth Live</span>
            <span style="font-size:0.75rem; color:#7986cb; margin-left:10px;">{st.session_state.role} Dashboard</span>
        </div>
        <div style="font-size:0.7rem; color:#4a5568;">
            Tick #{st.session_state.tick_count} • {st.session_state.sim_engine.mode.upper()}
        </div>
    </div>
    """)

    # Baseline progress — compact
    if st.session_state.baseline_engine.is_capturing:
        p = st.session_state.baseline_engine.get_capture_progress()
        st.html(f"""
        <div style="background:rgba(0,212,170,0.06); border:1px solid rgba(0,212,170,0.15);
            border-radius:8px; padding:6px 14px; margin-bottom:6px; font-size:0.72rem; color:#00d4aa;">
            ⏳ Learning your baseline... {p*100:.0f}%
            <div style="width:100%; height:3px; background:rgba(255,255,255,0.04); border-radius:2px; margin-top:3px;">
                <div style="width:{p*100}%; height:100%; background:#00d4aa; border-radius:2px;"></div>
            </div>
        </div>
        """)

    # Build state
    view_state = {
        "score_result": st.session_state.get("score_result"),
        "ai_result": st.session_state.get("ai_result"),
        "processed": st.session_state.get("processed"),
        "baseline_engine": st.session_state.baseline_engine,
        "deviation": st.session_state.get("deviation"),
        "emergency_system": st.session_state.emergency_system,
        "analytics": st.session_state.analytics,
        "notification_service": st.session_state.notification_service,
        "hr_history": list(st.session_state.hr_history),
        "spo2_history": list(st.session_state.spo2_history),
        "hr_raw_history": list(st.session_state.hr_raw_history),
        "spo2_raw_history": list(st.session_state.spo2_raw_history),
        "bp_sys_history": list(st.session_state.bp_sys_history),
        "bp_dia_history": list(st.session_state.bp_dia_history),
        "rr_history": list(st.session_state.rr_history),
        "temp_history": list(st.session_state.temp_history),
        "mode": st.session_state.sim_engine.mode,
        "synthetic_engine": st.session_state.synthetic_engine,
        "location": st.session_state.get("location"),
        "ml_result": st.session_state.get("ml_result"),
        "med_tracker": st.session_state.get("med_tracker"),
        "symptom_logger": st.session_state.get("symptom_logger"),
        "care_log": st.session_state.get("care_log"),
        "risk_prediction": st.session_state.get("risk_prediction"),
    }

    # ── SOS Emergency Overlay (only when active — no gap when dismissed) ──
    if st.session_state.get("sos_active") and st.session_state.get("sos_data"):
        import streamlit.components.v1 as _sos_comp
        d = st.session_state.sos_data
        sos_html = get_sos_overlay_html(
            patient_name=d["patient_name"],
            hr=d["hr"], spo2=d["spo2"],
            bp_sys=d["bp_sys"], bp_dia=d["bp_dia"],
            health_score=d["health_score"],
            ai_status=d["ai_status"],
        )
        _sos_comp.html(sos_html, height=480, scrolling=False)

    # Render the correct view
    role = st.session_state.role
    if role == "Patient":
        render_patient_view(view_state)
    elif role == "Caregiver":
        render_caregiver_view(view_state)
    elif role == "Doctor":
        render_doctor_view(view_state)

    # ── Browser Notifications (JavaScript) ──
    notif = st.session_state.notification_service
    browser_alerts = notif.get_pending_browser_alerts()
    for alert in browser_alerts:
        title = alert["title"].replace("'", "\\'").replace('"', '\\"')
        body = alert["body"].replace("'", "\\'").replace('"', '\\"')
        st.html(f"""
        <script>
        (function() {{
            if ('Notification' in window) {{
                if (Notification.permission === 'granted') {{
                    new Notification('{title}', {{
                        body: '{body}',
                        icon: '🚨',
                        requireInteraction: true
                    }});
                }} else if (Notification.permission !== 'denied') {{
                    Notification.requestPermission().then(function(p) {{
                        if (p === 'granted') {{
                            new Notification('{title}', {{body: '{body}'}});
                        }}
                    }});
                }}
            }}
        }})();
        </script>
        """)

    # ── WhatsApp Compose Links ──
    wa_links = notif.get_pending_whatsapp_links()
    if wa_links:
        st.html("""
        <div style="background:rgba(37,211,102,0.08); border:1px solid rgba(37,211,102,0.3);
            border-radius:12px; padding:12px; margin:8px 0;">
            <div style="color:#25d366; font-weight:700; font-size:0.85rem; margin-bottom:6px;">
                💬 Quick WhatsApp Alert (tap to send)
            </div>
        """)
        for link in wa_links:
            st.html(f"""
            <a href="{link}" target="_blank" style="display:inline-block; background:#25d366;
                color:white; padding:8px 16px; border-radius:8px; text-decoration:none;
                font-weight:600; font-size:0.8rem; margin:4px 4px 4px 0;">
                📲 Send via WhatsApp
            </a>
            """)
        st.html("</div>")


# Run the fragment
dashboard_fragment()

# ── Data Export (OUTSIDE fragment — download_button breaks inside @st.fragment) ──
analytics = st.session_state.get("analytics")
if analytics and analytics.total_readings > 0:
    st.html('<div class="section-header" style="margin-top:12px;">DATA EXPORT</div>')
    e1, e2 = st.columns(2)
    with e1:
        csv_data = analytics.generate_csv()
        st.download_button("📥 Download CSV", data=csv_data,
            file_name=f"medisynth_{analytics.session_id}.csv",
            mime="text/csv", key="main_csv_dl")
    with e2:
        html_data = analytics.generate_html_report()
        st.download_button("📋 Download Report", data=html_data,
            file_name=f"report_{analytics.session_id}.html",
            mime="text/html", key="main_html_dl")

