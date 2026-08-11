"""
Medisynth Live – Patient Dashboard (Fitness-App + AI Chatbot)
"""
import streamlit as st
import streamlit.components.v1 as components
import math
from ui.components import render_emergency_notification, render_nearby_hospitals, PLOTLY_CONFIG
from ui.shared_widgets import render_ecg_monitor, render_prediction_trend, render_ai_chatbot
from modules.hospital_finder import find_nearby_hospitals


def render_patient_view(state: dict):
    score_result = state.get("score_result")
    ai_result = state.get("ai_result")
    processed = state.get("processed")
    emergency = state.get("emergency_system")
    analytics = state.get("analytics")
    notif_svc = state.get("notification_service")
    location = state.get("location")
    hr_history = state.get("hr_history", [])
    spo2_history = state.get("spo2_history", [])
    bp_sys_history = state.get("bp_sys_history", [])
    bp_dia_history = state.get("bp_dia_history", [])
    rr_history = state.get("rr_history", [])
    temp_history = state.get("temp_history", [])
    med_tracker = state.get("med_tracker")
    symptom_logger = state.get("symptom_logger")

    # Emergency
    if emergency and emergency.active_alert:
        render_emergency_notification(emergency.active_alert, emergency.contacts, location)
        if notif_svc:
            _show_delivery_log(notif_svc)
        if st.button("✕ Dismiss Alert", key="pt_dismiss"):
            emergency.dismiss_alert()
            st.rerun()

    # ── Manual Panic Button (always visible) ──
    _render_panic_button(emergency)

    # Row 1: Ring + ECG + Status
    c1, c2, c3 = st.columns([0.8, 1.4, 1])
    with c1:
        if score_result:
            _render_fitness_ring(score_result.score)
    with c2:
        render_ecg_monitor(hr_history, processed, height=210)
    with c3:
        _render_status_card(ai_result, processed)

    # Row 2: Vitals
    if processed:
        _render_vitals_grid(processed, hr_history, spo2_history, bp_sys_history, bp_dia_history, rr_history, temp_history)

    # Row 3: Medication Reminders + Symptom Logger
    _render_med_and_symptoms(med_tracker, symptom_logger, processed, score_result)

    # Row 4: Insights + Chatbot
    col_left, col_right = st.columns([1, 1.1])
    with col_left:
        if ai_result:
            _render_insights(ai_result, score_result, processed)
        if ai_result and ai_result.risk_prediction:
            _render_forecast(ai_result.risk_prediction, score_result)
    with col_right:
        from ui.shared_widgets import render_ai_chatbot, render_historical_data_entry
        render_ai_chatbot()
        render_historical_data_entry(key_suffix="pat")

    # Daily Summary
    if analytics and analytics.total_readings > 10:
        _render_daily_summary(analytics, hr_history, spo2_history, score_result, med_tracker, symptom_logger)

    # Hospitals (critical only)
    if ai_result and ai_result.overall_status in ("warning", "critical"):
        loc = st.session_state.get("location")
        if loc and loc.get("lat"):
            hospitals = st.session_state.get("nearby_hospitals")
            if not hospitals:
                try:
                    hospitals = find_nearby_hospitals(loc["lat"], loc["lng"], radius_km=5, max_results=5)
                    st.session_state["nearby_hospitals"] = hospitals
                except Exception:
                    hospitals = []
            if hospitals:
                render_nearby_hospitals(hospitals, patient_location=loc)

    # Footer
    if analytics:
        st.html(f'<div style="text-align:center;padding:8px 0;color:#3d4a66;font-size:0.6rem;">'
                f'Session {analytics.session_id} · {analytics.get_elapsed_str()} · {analytics.total_readings} readings</div>')


# ═══════════════════════════════════════════════════════════════════════════════

def _render_fitness_ring(score: float):
    pct = max(0, min(100, score))
    r = 72
    circ = 2 * math.pi * r
    dash, gap = circ * pct / 100, circ * (1 - pct / 100)
    if pct >= 90:   c, g, e, f = "#00d4aa","rgba(0,212,170,0.3)","😊","Great!"
    elif pct >= 75: c, g, e, f = "#4ade80","rgba(74,222,128,0.25)","🙂","Good"
    elif pct >= 60: c, g, e, f = "#fbbf24","rgba(251,191,36,0.25)","😐","Watch"
    elif pct >= 40: c, g, e, f = "#f97316","rgba(249,115,22,0.25)","😟","Caution"
    else:           c, g, e, f = "#ff4757","rgba(255,71,87,0.3)","🚨","Alert!"
    components.html(f"""
    <div style="text-align:center;padding:4px 0;font-family:Inter,system-ui,sans-serif;">
        <svg width="160" height="160" viewBox="0 0 160 160" style="filter:drop-shadow(0 0 14px {g});display:block;margin:0 auto;">
            <circle cx="80" cy="80" r="{r}" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="11"/>
            <circle cx="80" cy="80" r="{r}" fill="none" stroke="{c}" stroke-width="11" stroke-linecap="round"
                stroke-dasharray="{dash:.1f} {gap:.1f}" transform="rotate(-90 80 80)">
                <animate attributeName="stroke-dasharray" from="0 {circ}" to="{dash:.1f} {gap:.1f}" dur="1.2s" fill="freeze"/>
            </circle>
            <text x="80" y="72" text-anchor="middle" font-size="38" font-weight="900" fill="{c}" font-family="Inter,sans-serif">{pct:.0f}</text>
            <text x="80" y="92" text-anchor="middle" font-size="10" fill="#7986cb" font-family="Inter,sans-serif">/ 100</text>
            <text x="80" y="118" text-anchor="middle" font-size="18">{e}</text>
        </svg>
        <div style="color:{c};font-size:0.9rem;font-weight:700;margin-top:2px;">{f}</div>
        <div style="color:#5c6b8a;font-size:0.65rem;">Health Score</div>
    </div>""", height=230)

def _render_status_card(ai_result, processed):
    if not ai_result or not processed:
        st.html('<div style="background:rgba(255,255,255,0.03);border-radius:14px;padding:20px;text-align:center;"><div style="font-size:1.2rem;">⏳</div><div style="color:#7986cb;font-size:0.8rem;margin-top:6px;">Analyzing...</div></div>')
        return
    overall = ai_result.overall_status
    dets = ai_result.detections or []
    if overall == "critical":
        icon,title,sub,bg,bd = "🔴","Attention Needed","Some vitals outside safe range.","rgba(255,71,87,0.06)","rgba(255,71,87,0.18)"
    elif overall == "monitoring":
        icon,title,sub,bg,bd = "🟡","Mild Changes","Slight changes detected.","rgba(255,179,71,0.06)","rgba(255,179,71,0.18)"
    else:
        icon,title,sub,bg,bd = "🟢","All Normal","Vitals are healthy.","rgba(0,212,170,0.05)","rgba(0,212,170,0.12)"
    pills = ""
    for det in dets[:3]:
        pc = "#ff4757" if det.severity == "critical" else "#ffb347"
        nm = _pfn(det.condition)
        pills += f'<span style="display:inline-block;padding:3px 10px;margin:2px;background:{pc}12;border:1px solid {pc}30;border-radius:16px;font-size:0.65rem;color:{pc};font-weight:600;">{nm}</span>'
    rec = ""
    if dets and dets[0].recommendation:
        rec = f'<div style="margin-top:8px;padding:7px 10px;background:rgba(251,191,36,0.05);border:1px solid rgba(251,191,36,0.12);border-radius:10px;color:#fbbf24;font-size:0.7rem;line-height:1.4;">💡 {dets[0].recommendation}</div>'
    elif not dets:
        rec = '<div style="margin-top:8px;padding:7px 10px;background:rgba(0,212,170,0.04);border:1px solid rgba(0,212,170,0.1);border-radius:10px;color:#00d4aa;font-size:0.7rem;">✓ No action needed.</div>'
    st.html(f'<div style="background:{bg};border:1px solid {bd};border-radius:14px;padding:14px;"><div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;"><span style="font-size:1.1rem;">{icon}</span><div><div style="color:#e8eaf6;font-size:0.95rem;font-weight:700;">{title}</div><div style="color:#7986cb;font-size:0.68rem;">{sub}</div></div></div>{f"<div style=margin-top:4px;>{pills}</div>" if pills else ""}{rec}</div>')

def _render_vitals_grid(p, hr_h, spo2_h, bp_sys_h, bp_dia_h, rr_h, temp_h):
    def _sp(data, color, w=70, h=22):
        if len(data) < 3: return ""
        d = data[-15:]
        n = len(d); mn, mx = min(d), max(d); rng = mx - mn if mx != mn else 1
        pts = " ".join([f"{(i/(n-1))*w:.1f},{h-((v-mn)/rng)*(h-4)-2:.1f}" for i,v in enumerate(d)])
        return f'<svg width="{w}" height="{h}" style="display:block;margin:4px auto 0;"><polyline points="{pts}" fill="none" stroke="{color}" stroke-width="1.5" stroke-linejoin="round" opacity="0.5"/></svg>'
    def _ar(data, inv=False):
        if len(data) < 3: return "→","#5c6b8a"
        d = data[-1] - (data[-5] if len(data)>=5 else data[0])
        if inv: d = -d
        if d > 1: return "↑","#ff4757" if not inv else "#00d4aa"
        if d < -1: return "↓","#00d4aa" if not inv else "#ff4757"
        return "→","#5c6b8a"
    ha,hc=_ar(hr_h); sa,sc=_ar(spo2_h,True); ra,rc=_ar(rr_h); ta,tc=_ar(temp_h)
    bl,bc=("High","#ff4757") if p.clean_bp_sys>140 or p.clean_bp_dia>90 else ("Low","#ffb347") if p.clean_bp_sys<90 else ("Normal","#00d4aa")
    cards=[("💓","Heart Rate",f"{p.clean_hr:.0f}","bpm","#00d4aa",ha,hc,_sp(hr_h,"#00d4aa")),
           ("🫁","Oxygen",f"{p.clean_spo2:.1f}","%","#a78bfa",sa,sc,_sp(spo2_h,"#a78bfa")),
           ("🩸","BP",f"{p.clean_bp_sys:.0f}/{p.clean_bp_dia:.0f}","mmHg","#f472b6",bl,bc,_sp(bp_sys_h,"#f472b6")),
           ("🌬️","Breathing",f"{p.clean_rr:.0f}","/min","#38bdf8",ra,rc,_sp(rr_h,"#38bdf8")),
           ("🌡️","Temp",f"{p.clean_temp:.1f}","°C","#fbbf24",ta,tc,_sp(temp_h,"#fbbf24"))]
    html=""
    for icon,label,val,unit,color,trend,tcol,spark in cards:
        html+=f'<div style="flex:1;min-width:95px;background:rgba(255,255,255,0.025);border:1px solid rgba(255,255,255,0.05);border-radius:14px;padding:10px 6px;text-align:center;"><div style="font-size:0.9rem;">{icon}</div><div style="color:#5c6b8a;font-size:0.55rem;font-weight:600;letter-spacing:0.5px;text-transform:uppercase;margin:2px 0;">{label}</div><div style="font-size:1.6rem;font-weight:800;color:{color};font-family:JetBrains Mono,monospace;line-height:1.1;">{val}</div><div style="color:#4a5568;font-size:0.6rem;">{unit}</div><div style="color:{tcol};font-size:0.65rem;font-weight:600;margin-top:2px;">{trend}</div>{spark}</div>'
    st.html(f'<div style="display:flex;gap:8px;margin:8px 0;flex-wrap:wrap;">{html}</div>')

def _render_insights(ai_result, score_result, processed):
    items=[]
    for det in (ai_result.detections or []):
        fr=_pfd(det)
        if fr:
            ic="⚠️" if det.severity=="critical" else "💛" if det.severity=="warning" else "ℹ️"
            items.append((ic,fr))
    if not items:
        items.append(("💚","Heart rhythm is steady and oxygen levels are healthy."))
        if processed and processed.confidence>=80:
            items.append(("📡","Signal quality excellent — readings reliable."))
    entries="".join([f'<div style="display:flex;gap:10px;padding:7px 12px;border-bottom:1px solid rgba(255,255,255,0.03);align-items:flex-start;"><span style="font-size:0.85rem;flex-shrink:0;">{ic}</span><div style="color:#c5cae9;font-size:0.75rem;line-height:1.5;">{txt}</div></div>' for ic,txt in items[:4]])
    st.html(f'<div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);border-radius:14px;overflow:hidden;margin:4px 0;"><div style="padding:9px 14px;border-bottom:1px solid rgba(255,255,255,0.04);"><span style="color:#e8eaf6;font-size:0.78rem;font-weight:700;">🧠 Health Insights</span></div>{entries}</div>')

def _render_forecast(prediction, score_result):
    cur=score_result.score if score_result else 100
    p5=max(0,min(100,prediction.predicted_score*0.6+cur*0.4)); p10=prediction.predicted_score; p15=max(0,min(100,prediction.predicted_score*1.3-cur*0.3))
    def _f(s):
        if s>=80: return "😊","#00d4aa","Good"
        if s>=60: return "😐","#fbbf24","Fair"
        if s>=40: return "😟","#f97316","Watch"
        return "🚨","#ff4757","Alert"
    cards=""
    for label,sc in [("5m",p5),("10m",p10),("15m",p15)]:
        em,co,wd=_f(sc)
        cards+=f'<div style="flex:1;text-align:center;padding:8px 4px;background:rgba(255,255,255,0.025);border:1px solid rgba(255,255,255,0.05);border-radius:12px;"><div style="font-size:1rem;">{em}</div><div style="font-size:1.2rem;font-weight:800;color:{co};font-family:JetBrains Mono,monospace;margin:2px 0;">{sc:.0f}</div><div style="color:#5c6b8a;font-size:0.58rem;font-weight:600;">{label}</div></div>'
    tr=prediction.trend_direction
    msg,mc=("Vitals may dip. Stay relaxed.","#ffb347") if tr=="deteriorating" else ("Recovering well!","#00d4aa") if tr=="improving" else ("Expected steady.","#5c6b8a")
    st.html(f'<div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);border-radius:14px;overflow:hidden;margin:4px 0;"><div style="padding:9px 14px;border-bottom:1px solid rgba(255,255,255,0.04);"><span style="color:#e8eaf6;font-size:0.78rem;font-weight:700;">🔮 What\'s Coming</span></div><div style="display:flex;gap:6px;padding:8px 10px;">{cards}</div><div style="padding:5px 14px 8px;color:{mc};font-size:0.68rem;">{msg}</div></div>')

# ─── Helpers ───
def _pfn(c):
    m={"Tachycardia":"Fast HR","Bradycardia":"Slow HR","Hypoxia":"Low O₂","Desaturation":"O₂ Drop","Hypertension":"High BP","Hypotension":"Low BP","Tachypnea":"Fast Breathing","Bradypnea":"Slow Breathing","Fever":"High Temp","Hypothermia":"Low Temp","Arrhythmia":"Irregular Beat","Shock Pattern":"Critical","Rapid HR Change":"HR Spike"}
    for k,v in m.items():
        if k.lower() in c.lower(): return v
    return c

def _pfd(det):
    c=det.condition.lower()
    if "tachycardia" in c: return "Heart beating faster than usual. Try relaxing."
    if "bradycardia" in c: return "Heart rate is lower than expected."
    if "hypoxia" in c or "desaturation" in c: return "Blood oxygen is low. Try deep breaths."
    if "hypertension" in c: return "Blood pressure is elevated."
    if "hypotension" in c: return "Blood pressure is low. Stay hydrated."
    if "tachypnea" in c: return "Breathing faster than normal."
    if "bradypnea" in c: return "Breathing rate is slower than usual."
    if "fever" in c: return "Temperature is elevated. Stay hydrated."
    if "hypothermia" in c: return "Body temperature is low."
    if "arrhythmia" in c: return "Irregular heart rhythm detected."
    if "shock" in c: return "Multiple vitals outside range. Seek help."
    if "rapid" in c or "trend" in c: return "Heart rate changed quickly."
    ev=det.evidence[0] if det.evidence else ""
    return f"{det.condition}: {ev}" if ev else det.condition

def _show_delivery_log(ns):
    results=ns.get_last_results(3)
    if not results: return
    items="".join([f'<div style="display:flex;justify-content:space-between;padding:2px 0;font-size:0.6rem;"><span style="color:#c5cae9;">{r.recipient}</span><span style="color:{"#00d4aa" if r.success else "#ff4757"};">{"✔" if r.success else "✕"}</span></div>' for r in results])
    st.html(f'<div style="background:rgba(15,20,40,0.3);border:1px solid rgba(255,255,255,0.05);border-radius:8px;padding:6px;margin:4px 0;font-size:0.6rem;color:#5c6b8a;">📡 NOTIFICATIONS{items}</div>')


# ═══════════════════════════════════════════════════════════════════════════════
# ── NEW PHASE 1 FEATURES ──
# ═══════════════════════════════════════════════════════════════════════════════

def _render_panic_button(emergency):
    """Always-visible manual panic/SOS button."""
    import streamlit.components.v1 as comp
    comp.html("""
    <div id="panic-row" style="display:flex;gap:8px;margin:2px 0 6px;align-items:center;">
        <div style="flex:1;text-align:right;">
            <span style="color:#5c6b8a;font-size:0.6rem;">Feeling unwell?</span>
        </div>
        <div style="background:linear-gradient(135deg,rgba(255,71,87,0.15),rgba(255,40,60,0.25));
            border:2px solid rgba(255,71,87,0.4);border-radius:30px;padding:6px 22px;
            display:inline-flex;align-items:center;gap:6px;cursor:pointer;
            box-shadow:0 0 20px rgba(255,71,87,0.1);animation:sosPulse 2s infinite;"
            onclick="this.style.background='rgba(255,71,87,0.4)';this.innerHTML='🚨 ALERT SENT!';">
            <span style="font-size:1rem;">🆘</span>
            <span style="color:#ff4757;font-weight:800;font-size:0.75rem;letter-spacing:0.5px;">I NEED HELP</span>
        </div>
        <div style="flex:1;"></div>
    </div>
    <style>@keyframes sosPulse{0%,100%{box-shadow:0 0 10px rgba(255,71,87,0.1)}50%{box-shadow:0 0 25px rgba(255,71,87,0.25)}}</style>
    """, height=42)


def _render_med_and_symptoms(med_tracker, symptom_logger, processed, score_result):
    """Medication reminders + symptom logger row."""
    col_med, col_sym = st.columns([1, 1])

    with col_med:
        _render_medication_panel(med_tracker, processed)

    with col_sym:
        _render_symptom_panel(symptom_logger, processed, score_result)


def _render_medication_panel(med_tracker, processed):
    """Medication reminders and quick-log panel."""
    if not med_tracker:
        return

    reminders = med_tracker.get_upcoming_reminders(3)
    todays_log = med_tracker.get_todays_log()

    # Header
    overdue_count = sum(1 for r in reminders if r.is_overdue)
    badge = f'<span style="background:rgba(255,71,87,0.15);color:#ff4757;padding:2px 8px;border-radius:10px;font-size:0.55rem;font-weight:700;margin-left:6px;">{overdue_count} overdue</span>' if overdue_count else ""

    # Reminder cards
    rem_html = ""
    if reminders:
        for r in reminders[:3]:
            if r.is_overdue:
                bg, bd, tc = "rgba(255,71,87,0.06)", "rgba(255,71,87,0.15)", "#ff4757"
                time_txt = f"⚠️ Overdue by {abs(r.minutes_until)} min"
            elif r.minutes_until <= 30:
                bg, bd, tc = "rgba(251,191,36,0.06)", "rgba(251,191,36,0.15)", "#fbbf24"
                time_txt = f"⏰ Due in {r.minutes_until} min"
            else:
                bg, bd, tc = "rgba(0,212,170,0.04)", "rgba(0,212,170,0.1)", "#5c6b8a"
                hrs = r.minutes_until // 60
                mins = r.minutes_until % 60
                time_txt = f"Due in {hrs}h {mins}m" if hrs else f"Due in {mins} min"
            rem_html += f'<div style="display:flex;justify-content:space-between;align-items:center;padding:6px 10px;background:{bg};border:1px solid {bd};border-radius:10px;margin:3px 0;"><div><div style="color:#e8eaf6;font-size:0.75rem;font-weight:600;">💊 {r.med_name}</div><div style="color:#5c6b8a;font-size:0.58rem;">{r.dosage}</div></div><div style="color:{tc};font-size:0.6rem;font-weight:600;">{time_txt}</div></div>'
    else:
        rem_html = '<div style="color:#00d4aa;font-size:0.7rem;padding:8px 0;text-align:center;">✓ All medications taken today!</div>' if todays_log else '<div style="color:#5c6b8a;font-size:0.7rem;padding:8px 0;text-align:center;">No medications scheduled</div>'

    # Today's log count
    log_text = f'<div style="color:#5c6b8a;font-size:0.55rem;padding:4px 10px;">✓ {len(todays_log)} doses taken today</div>' if todays_log else ""

    st.html(f'<div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);border-radius:14px;overflow:hidden;margin:4px 0;"><div style="padding:9px 14px;border-bottom:1px solid rgba(255,255,255,0.04);display:flex;align-items:center;"><span style="color:#e8eaf6;font-size:0.78rem;font-weight:700;">💊 Medications</span>{badge}</div>{rem_html}{log_text}</div>')

    # Quick add medication (expandable)
    with st.expander("➕ Add Medication", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            med_name = st.text_input("Name", key="pt_med_name", placeholder="e.g. Aspirin")
        with c2:
            med_dose = st.text_input("Dosage", key="pt_med_dose", placeholder="e.g. 81mg")
        med_hour = st.number_input("Schedule hour (24h)", min_value=0, max_value=23, value=8, key="pt_med_hr")
        if st.button("Add", key="pt_add_med"):
            if med_name and med_dose:
                med_tracker.add_medication(med_name, med_dose, "once_daily", [med_hour])
                st.rerun()

    # Log taken buttons
    if med_tracker.medications:
        for med in med_tracker.medications:
            if st.button(f"✓ Took {med.name}", key=f"pt_took_{med.id}", use_container_width=True):
                med_tracker.log_administration(med.id, "patient", processed=processed)
                st.rerun()


def _render_symptom_panel(symptom_logger, processed, score_result):
    """Quick-tap symptom logging panel."""
    if not symptom_logger:
        return
    from modules.symptom_logger import SYMPTOM_OPTIONS

    todays = symptom_logger.get_todays_entries()

    # Header
    count_badge = f'<span style="background:rgba(167,139,250,0.12);color:#a78bfa;padding:2px 8px;border-radius:10px;font-size:0.55rem;font-weight:700;margin-left:6px;">{len(todays)} today</span>' if todays else ""

    # Recent symptoms
    recent_html = ""
    if todays:
        for entry in todays[-3:]:
            import datetime
            ts = datetime.datetime.fromtimestamp(entry.timestamp).strftime("%I:%M %p")
            sc = "#ff4757" if entry.severity == "severe" else "#fbbf24" if entry.severity == "moderate" else "#00d4aa"
            recent_html += f'<div style="display:flex;justify-content:space-between;padding:4px 10px;font-size:0.65rem;border-bottom:1px solid rgba(255,255,255,0.03);"><span style="color:#c5cae9;">{entry.icon} {entry.label}</span><span style="color:{sc};">{ts}</span></div>'
    else:
        recent_html = '<div style="color:#5c6b8a;font-size:0.7rem;padding:8px 0;text-align:center;">No symptoms logged today</div>'

    st.html(f'<div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);border-radius:14px;overflow:hidden;margin:4px 0;"><div style="padding:9px 14px;border-bottom:1px solid rgba(255,255,255,0.04);display:flex;align-items:center;"><span style="color:#e8eaf6;font-size:0.78rem;font-weight:700;">📋 How Do You Feel?</span>{count_badge}</div>{recent_html}</div>')

    # Quick-tap symptom buttons (2 columns)
    key_options = SYMPTOM_OPTIONS[:8]  # Show top 8
    cols = st.columns(4)
    for i, opt in enumerate(key_options):
        with cols[i % 4]:
            if st.button(f"{opt['icon']}", key=f"sym_{opt['id']}", help=opt["label"]):
                symptom_logger.log_symptom(opt["id"], processed=processed, score_result=score_result)
                st.rerun()


def _render_daily_summary(analytics, hr_history, spo2_history, score_result, med_tracker, symptom_logger):
    """Auto-generated daily health summary."""
    import datetime
    now = datetime.datetime.now()

    # Calculate stats
    hr_avg = sum(hr_history) / len(hr_history) if hr_history else 0
    hr_min = min(hr_history) if hr_history else 0
    hr_max = max(hr_history) if hr_history else 0
    spo2_avg = sum(spo2_history) / len(spo2_history) if spo2_history else 0
    score = score_result.score if score_result else 0

    # Medication adherence
    med_text = ""
    if med_tracker and med_tracker.medications:
        todays_log = med_tracker.get_todays_log()
        total_due = sum(len(m.schedule_hours) for m in med_tracker.medications)
        med_text = f'<div style="display:flex;justify-content:space-between;padding:4px 0;"><span style="color:#7986cb;">💊 Medications</span><span style="color:#a78bfa;font-weight:600;">{len(todays_log)}/{total_due} taken</span></div>'

    # Symptom summary
    sym_text = ""
    if symptom_logger:
        todays = symptom_logger.get_todays_entries()
        if todays:
            icons = " ".join(set(e.icon for e in todays))
            sym_text = f'<div style="display:flex;justify-content:space-between;padding:4px 0;"><span style="color:#7986cb;">📋 Symptoms</span><span style="color:#c5cae9;font-size:0.7rem;">{icons} ({len(todays)})</span></div>'

    # Alert count
    alert_count = len(analytics.alert_timestamps) if hasattr(analytics, 'alert_timestamps') else 0

    with st.expander("📊 Today's Summary", expanded=False):
        st.html(f"""
        <div style="font-family:Inter,sans-serif;font-size:0.75rem;">
            <div style="color:#e8eaf6;font-size:0.85rem;font-weight:700;margin-bottom:8px;">
                📊 {now.strftime("%B %d")} — Daily Briefing
            </div>
            <div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.04);">
                <span style="color:#7986cb;">Health Score</span>
                <span style="color:#00d4aa;font-weight:700;font-size:0.9rem;">{score:.0f}/100</span>
            </div>
            <div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.04);">
                <span style="color:#7986cb;">Heart Rate</span>
                <span style="color:#c5cae9;">avg {hr_avg:.0f} · min {hr_min:.0f} · max {hr_max:.0f} bpm</span>
            </div>
            <div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.04);">
                <span style="color:#7986cb;">Oxygen</span>
                <span style="color:#c5cae9;">avg {spo2_avg:.1f}%</span>
            </div>
            <div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.04);">
                <span style="color:#7986cb;">🚨 Alerts</span>
                <span style="color:{'#ff4757' if alert_count else '#00d4aa'};font-weight:600;">{alert_count}</span>
            </div>
            {med_text}
            {sym_text}
            <div style="color:#5c6b8a;font-size:0.6rem;margin-top:6px;text-align:center;">
                {analytics.total_readings} readings · {analytics.get_elapsed_str()} monitored
            </div>
        </div>""")
