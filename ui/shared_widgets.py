"""
Medisynth Live – Shared Clinical Widgets
Realistic ECG Monitor, Prediction Trend Chart, AI Health Chatbot.
Reused across Patient, Caregiver, and Doctor views.
"""

import streamlit as st
import streamlit.components.v1 as components
import math


def render_ecg_monitor(hr_history, processed, height=200, show_stats=False):
    """Realistic ECG monitor with clean PQRST waveform — mimics a bedside monitor.
    Shows 5-6 beats across the display with proper morphology and spacing."""
    hr = processed.clean_hr if processed else 72
    spo2 = processed.clean_spo2 if processed else 97.5

    w, h = 700, 160
    baseline_y = h * 0.55

    # ── Determine how many beats to show (based on HR and a ~3 second window) ──
    # At 70 bpm → ~3.5 beats in 3 sec.  At 140 bpm → ~7 beats.
    display_seconds = 3.5
    num_beats = max(3, min(8, int(hr / 60.0 * display_seconds + 0.5)))

    # Amplitude: higher HR → slightly taller R waves (sympathetic response)
    base_amp = 1.0
    if hr > 100:
        base_amp = 1.0 + (hr - 100) / 150.0
    elif hr < 60:
        base_amp = 0.85

    # ── Build PQRST complexes ──
    # Each complex occupies (w / num_beats) pixels.
    # PQRST is ~40% of the cycle, remaining 60% is isoelectric (flat baseline).
    ecg_points = []
    beat_width = w / num_beats

    # Add slight variation across beats from recent HR values
    recent_hrs = hr_history[-num_beats:] if len(hr_history) >= num_beats else [hr] * num_beats

    for beat_idx in range(num_beats):
        beat_hr = recent_hrs[beat_idx] if beat_idx < len(recent_hrs) else hr
        amp = base_amp * (1.0 + (beat_hr - 72) / 250.0)
        amp = max(0.5, min(1.6, amp))

        bx = beat_idx * beat_width  # Beat start x

        # PQRST template — 24 sub-points for smooth curves
        # Fractions are within the beat_width. Complex takes ~45% of beat cycle.
        template = [
            # Pre-P isoelectric
            (0.00, 0),
            (0.05, 0),
            # P wave (small rounded bump)
            (0.10, -3 * amp),
            (0.14, -7 * amp),
            (0.18, -8 * amp),     # P peak
            (0.22, -5 * amp),
            (0.26, -1 * amp),
            # PR segment (flat)
            (0.30, 0),
            (0.33, 0),
            # QRS complex (sharp, narrow)
            (0.35, 2 * amp),      # Q dip
            (0.37, -4 * amp),     # Q-R upstroke
            (0.39, -45 * amp),    # R peak (tall sharp spike)
            (0.41, -10 * amp),    # R-S downstroke
            (0.43, 16 * amp),     # S trough
            (0.45, 4 * amp),      # S recovery
            (0.47, 0),            # J point
            # ST segment (flat)
            (0.50, 0),
            (0.53, -1 * amp),
            # T wave (broad rounded bump)
            (0.57, -5 * amp),
            (0.62, -12 * amp),
            (0.67, -14 * amp),    # T peak
            (0.72, -10 * amp),
            (0.77, -4 * amp),
            (0.82, 0),
            # Post-T isoelectric
            (0.88, 0),
            (0.94, 0),
            (1.00, 0),
        ]

        for frac, y_offset in template:
            px = bx + frac * beat_width
            py = baseline_y + y_offset
            py = max(6, min(h - 6, py))
            ecg_points.append(f"{px:.1f},{py:.1f}")

    polyline = " ".join(ecg_points)

    # ── Grid lines (medical standard) ──
    grid = ""
    for gy in range(0, h + 1, 10):
        op = "0.14" if gy % 50 == 0 else "0.04"
        sw = "0.8" if gy % 50 == 0 else "0.4"
        grid += f'<line x1="0" y1="{gy}" x2="{w}" y2="{gy}" stroke="rgba(0,230,118,{op})" stroke-width="{sw}"/>'
    for gx in range(0, w + 1, 10):
        op = "0.14" if gx % 50 == 0 else "0.04"
        sw = "0.8" if gx % 50 == 0 else "0.4"
        grid += f'<line x1="{gx}" y1="0" x2="{gx}" y2="{h}" stroke="rgba(0,230,118,{op})" stroke-width="{sw}"/>'

    hr_color = "#00e676" if 60 <= hr <= 100 else "#ff1744" if hr > 120 or hr < 50 else "#ffab00"
    bpm_txt = f"{hr:.0f}" if processed else "--"

    # Pulsing dot at end of trace
    last_pt = ecg_points[-1] if ecg_points else f"{w},{baseline_y}"
    lx, ly = last_pt.split(",")

    # Stats bar
    stats_html = ""
    if show_stats and processed:
        stats_html = f"""
        <div style="display:flex;gap:16px;margin-top:5px;padding:4px 0;border-top:1px solid rgba(0,230,118,0.08);font-size:0.55rem;">
            <div><span style="color:#4a6a5a;">SpO₂</span> <span style="color:#a78bfa;font-weight:700;">{spo2:.1f}%</span></div>
            <div><span style="color:#4a6a5a;">RR</span> <span style="color:#38bdf8;font-weight:700;">{processed.clean_rr:.0f}</span></div>
            <div><span style="color:#4a6a5a;">BP</span> <span style="color:#f472b6;font-weight:700;">{processed.clean_bp_sys:.0f}/{processed.clean_bp_dia:.0f}</span></div>
            <div><span style="color:#4a6a5a;">Temp</span> <span style="color:#fbbf24;font-weight:700;">{processed.clean_temp:.1f}°</span></div>
        </div>"""

    components.html(f"""
    <div style="background:rgba(0,6,2,0.92);border:1px solid rgba(0,230,118,0.12);border-radius:12px;
        padding:10px 12px;font-family:'JetBrains Mono','Fira Code',monospace;position:relative;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
            <div style="display:flex;align-items:center;gap:5px;">
                <div style="width:6px;height:6px;border-radius:50%;background:#00e676;animation:ecgDot 1s infinite;"></div>
                <span style="color:#00e676;font-size:0.55rem;font-weight:600;letter-spacing:1.5px;">ECG II</span>
            </div>
            <div style="display:flex;align-items:center;gap:6px;">
                <span style="color:{hr_color};font-size:1.6rem;font-weight:900;line-height:1;">{bpm_txt}</span>
                <span style="color:#4a6a5a;font-size:0.5rem;line-height:1;">BPM</span>
            </div>
        </div>
        <svg width="100%" height="{h}" viewBox="0 0 {w} {h}" preserveAspectRatio="none" style="display:block;">
            {grid}
            <polyline points="{polyline}" fill="none" stroke="#00e676" stroke-width="2.2"
                stroke-linejoin="round" stroke-linecap="round" style="filter:drop-shadow(0 0 4px rgba(0,230,118,0.4));"/>
            <circle cx="{lx}" cy="{ly}" r="3.5" fill="#00e676" opacity="0.9">
                <animate attributeName="r" values="3;5;3" dur="0.8s" repeatCount="indefinite"/>
            </circle>
        </svg>
        <div style="display:flex;justify-content:space-between;font-size:0.45rem;color:#2d5a3d;margin-top:2px;">
            <span>Lead II</span><span>25mm/s</span><span>10mm/mV</span><span>Filter: 0.05-150Hz</span>
        </div>
        {stats_html}
    </div>
    <style>@keyframes ecgDot{{0%,100%{{opacity:1}}50%{{opacity:0.3}}}}</style>
    """, height=height)



def render_prediction_trend(hr_history, spo2_history, ai_result=None, key_suffix=""):
    """Prediction trend analysis chart with actual data + forecast + confidence bands."""
    import plotly.graph_objects as go
    import numpy as np

    if len(hr_history) < 8:
        st.html('<div style="color:#5c6b8a;font-size:0.75rem;text-align:center;padding:16px;">Need more data for prediction trend...</div>')
        return

    fig = go.Figure()
    n = len(hr_history)
    x_actual = list(range(n))

    # Actual HR
    fig.add_trace(go.Scatter(x=x_actual, y=hr_history[-80:], mode='lines', name='HR',
        line=dict(color='#00e676', width=2.5, shape='spline', smoothing=1.2),
        fill='tozeroy', fillcolor='rgba(0,230,118,0.03)',
        hovertemplate='HR: %{y:.0f} bpm<extra></extra>'))

    # Actual SpO2
    fig.add_trace(go.Scatter(x=x_actual, y=spo2_history[-80:], mode='lines', name='SpO₂',
        line=dict(color='#a78bfa', width=2, shape='spline', smoothing=1.2),
        yaxis='y2', hovertemplate='SpO₂: %{y:.1f}%<extra></extra>'))

    # Prediction forecast
    recent_hr = np.array(hr_history[-20:]) if n >= 20 else np.array(hr_history)
    recent_spo2 = np.array(spo2_history[-20:]) if n >= 20 else np.array(spo2_history)
    x_fit = np.arange(len(recent_hr))

    if len(recent_hr) >= 5:
        hr_c = np.polyfit(x_fit, recent_hr, 1)
        spo2_c = np.polyfit(x_fit, recent_spo2, 1)
        hr_res = recent_hr - np.polyval(hr_c, x_fit)
        hr_std = max(np.std(hr_res), 1)

        pred_n = 25
        x_pred = np.arange(n, n + pred_n)
        x_pf = np.arange(len(recent_hr), len(recent_hr) + pred_n)
        hr_pred = np.clip(hr_c[0] * x_pf + hr_c[1], 30, 200)
        spo2_pred = np.clip(spo2_c[0] * x_pf + spo2_c[1], 70, 100)

        conf_m = np.linspace(1, 2.5, pred_n)
        hr_up = hr_pred + 2 * hr_std * conf_m
        hr_lo = hr_pred - 2 * hr_std * conf_m

        fig.add_trace(go.Scatter(x=x_pred.tolist(), y=hr_pred.tolist(), mode='lines', name='HR Forecast',
            line=dict(color='#00e676', width=2, dash='dash'), hovertemplate='Pred HR: %{y:.0f}<extra></extra>'))
        fig.add_trace(go.Scatter(
            x=x_pred.tolist() + x_pred.tolist()[::-1],
            y=hr_up.tolist() + hr_lo.tolist()[::-1],
            fill='toself', fillcolor='rgba(0,230,118,0.06)',
            line=dict(color='rgba(0,0,0,0)'), name='95% CI', showlegend=True, hoverinfo='skip'))
        fig.add_trace(go.Scatter(x=x_pred.tolist(), y=spo2_pred.tolist(), mode='lines', name='SpO₂ Forecast',
            line=dict(color='#a78bfa', width=2, dash='dash'), yaxis='y2',
            hovertemplate='Pred SpO₂: %{y:.1f}%<extra></extra>'))

        slope = hr_c[0]
        txt = "RISING" if slope > 0.3 else "FALLING" if slope < -0.3 else "STABLE"
        tc = "#ff1744" if slope > 0.3 else "#ffab00" if slope < -0.3 else "#00e676"
        fig.add_annotation(x=n + pred_n // 2, y=hr_pred[pred_n // 2], text=txt, showarrow=False,
            font=dict(color=tc, size=9, family='JetBrains Mono'), bgcolor='rgba(10,14,26,0.85)',
            bordercolor=tc, borderwidth=1, borderpad=3)

    fig.add_vline(x=n - 1, line=dict(color='rgba(255,255,255,0.12)', width=1, dash='dot'))
    fig.add_annotation(x=n - 1, y=1.03, yref='paper', text='NOW', showarrow=False,
        font=dict(color='#5c6b8a', size=8), bgcolor='rgba(10,14,26,0.8)')

    fig.update_layout(
        template='plotly_dark', paper_bgcolor='rgba(10,14,26,0)', plot_bgcolor='rgba(15,20,40,0.5)',
        font=dict(family='Inter,sans-serif', color='#5c6b8a', size=10),
        height=260, margin=dict(l=45, r=45, t=25, b=20),
        legend=dict(orientation='h', y=1.12, x=0.5, xanchor='center', bgcolor='rgba(10,14,26,0.8)', font=dict(size=8)),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(title=dict(text='HR (bpm)', font=dict(color='#00e676', size=9)),
            showgrid=True, gridcolor='rgba(255,255,255,0.02)', zeroline=False, tickfont=dict(color='#00e676', size=9)),
        yaxis2=dict(title=dict(text='SpO₂ (%)', font=dict(color='#a78bfa', size=9)),
            overlaying='y', side='right', showgrid=False, zeroline=False,
            tickfont=dict(color='#a78bfa', size=9), range=[80, 102]),
        hovermode='x unified', transition=dict(duration=0))

    from ui.components import PLOTLY_CONFIG
    st.plotly_chart(fig, use_container_width=True, key=f"pred_trend_{key_suffix}", config=PLOTLY_CONFIG)


def render_ai_chatbot():
    """AI Health Chatbot — premium frosted-glass card with gradient accent."""
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "Hello! 👋 I'm your health assistant. Ask me anything about your vitals, health tips, or what your readings mean."}
        ]

    # ── Header bar ──
    st.html("""
    <div style="background:linear-gradient(135deg,rgba(0,212,170,0.12),rgba(124,58,237,0.12));
        border:1px solid rgba(124,58,237,0.2);border-bottom:none;
        border-radius:16px 16px 0 0;padding:14px 18px;
        backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);">
        <div style="display:flex;align-items:center;justify-content:space-between;">
            <div style="display:flex;align-items:center;gap:10px;">
                <div style="width:36px;height:36px;border-radius:12px;
                    background:linear-gradient(135deg,#00d4aa,#7c3aed);
                    display:flex;align-items:center;justify-content:center;
                    font-size:1.1rem;box-shadow:0 4px 14px rgba(124,58,237,0.3);">🤖</div>
                <div>
                    <div style="color:#f0f0ff;font-size:0.9rem;font-weight:800;letter-spacing:0.3px;">Health Assistant</div>
                    <div style="display:flex;align-items:center;gap:4px;">
                        <div style="width:6px;height:6px;border-radius:50%;background:#00e676;
                            box-shadow:0 0 6px #00e676;animation:onlinePulse 2s infinite;"></div>
                        <span style="color:#00e676;font-size:0.6rem;font-weight:600;">Online · AI Powered</span>
                    </div>
                </div>
            </div>
            <div style="background:rgba(124,58,237,0.15);border:1px solid rgba(124,58,237,0.25);
                border-radius:8px;padding:4px 10px;">
                <span style="color:#a78bfa;font-size:0.55rem;font-weight:700;letter-spacing:1px;">BETA</span>
            </div>
        </div>
    </div>
    <style>@keyframes onlinePulse{0%,100%{opacity:1}50%{opacity:0.4}}</style>
    """)

    # ── Chat area with visible border + background ──
    # Quick suggestion chips (only show when no user messages yet)
    has_user_msg = any(m["role"] == "user" for m in st.session_state.chat_messages)

    chat_container = st.container(height=300)
    with chat_container:
        # Apply custom styling to the container
        st.html("""<style>
            [data-testid="stVerticalBlockBorderWrapper"] > div {
                background: rgba(10, 14, 30, 0.6) !important;
            }
        </style>""")

        for msg in st.session_state.chat_messages:
            if msg["role"] == "assistant":
                st.html(f"""
                <div style="display:flex;gap:10px;margin:10px 4px;align-items:flex-start;">
                    <div style="width:26px;height:26px;border-radius:9px;
                        background:linear-gradient(135deg,#00d4aa,#7c3aed);
                        display:flex;align-items:center;justify-content:center;
                        font-size:0.75rem;flex-shrink:0;box-shadow:0 2px 8px rgba(0,212,170,0.2);">🤖</div>
                    <div style="background:rgba(0,212,170,0.08);border:1px solid rgba(0,212,170,0.15);
                        border-radius:4px 16px 16px 16px;padding:12px 16px;max-width:88%;
                        color:#d4d8f0;font-size:0.82rem;line-height:1.6;
                        box-shadow:0 2px 12px rgba(0,212,170,0.06);">{msg["content"]}</div>
                </div>""")
            else:
                st.html(f"""
                <div style="display:flex;gap:8px;margin:10px 4px;justify-content:flex-end;">
                    <div style="background:linear-gradient(135deg,rgba(124,58,237,0.18),rgba(124,58,237,0.1));
                        border:1px solid rgba(124,58,237,0.22);
                        border-radius:16px 4px 16px 16px;padding:12px 16px;max-width:88%;
                        color:#ede9fe;font-size:0.82rem;line-height:1.6;
                        box-shadow:0 2px 12px rgba(124,58,237,0.08);">{msg["content"]}</div>
                </div>""")

        # Quick chips when no conversation yet
        if not has_user_msg:
            st.html("""
            <div style="display:flex;flex-wrap:wrap;gap:6px;margin:12px 4px 4px;justify-content:center;">
                <div style="background:rgba(0,212,170,0.08);border:1px solid rgba(0,212,170,0.15);
                    border-radius:20px;padding:6px 14px;color:#00d4aa;font-size:0.7rem;font-weight:600;
                    cursor:default;">💓 Heart Rate</div>
                <div style="background:rgba(167,139,250,0.08);border:1px solid rgba(167,139,250,0.15);
                    border-radius:20px;padding:6px 14px;color:#a78bfa;font-size:0.7rem;font-weight:600;
                    cursor:default;">🫁 Oxygen</div>
                <div style="background:rgba(251,191,36,0.08);border:1px solid rgba(251,191,36,0.15);
                    border-radius:20px;padding:6px 14px;color:#fbbf24;font-size:0.7rem;font-weight:600;
                    cursor:default;">🧘 Stress Tips</div>
                <div style="background:rgba(56,189,248,0.08);border:1px solid rgba(56,189,248,0.15);
                    border-radius:20px;padding:6px 14px;color:#38bdf8;font-size:0.7rem;font-weight:600;
                    cursor:default;">📊 My Score</div>
            </div>""")

    # ── Bottom bar with gradient border ──
    st.html("""
    <div style="background:linear-gradient(135deg,rgba(0,212,170,0.06),rgba(124,58,237,0.06));
        border:1px solid rgba(124,58,237,0.15);border-top:none;
        border-radius:0 0 16px 16px;padding:6px 16px 10px;
        backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);">
        <div style="display:flex;justify-content:center;gap:12px;font-size:0.55rem;color:#5c6b8a;">
            <span>🔒 Private</span>
            <span>·</span>
            <span>💡 Ask about vitals, exercise, diet, sleep</span>
        </div>
    </div>
    """)

    # Input
    user_input = st.chat_input("Ask about your health...", key="health_chat_input")
    if user_input:
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        response = _generate_health_response(user_input)
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
        st.rerun()


def _generate_health_response(question: str) -> str:
    """Rule-based health assistant with comprehensive medical knowledge base."""
    q = question.lower().strip()

    # Get current vitals context
    processed = st.session_state.get("processed")
    score_result = st.session_state.get("score_result")
    ai_result = st.session_state.get("ai_result")
    med_tracker = st.session_state.get("med_tracker")
    symptom_logger = st.session_state.get("symptom_logger")

    vitals_ctx = ""
    if processed:
        vitals_ctx = (f"Your current vitals — HR: {processed.clean_hr:.0f} bpm, "
                      f"SpO₂: {processed.clean_spo2:.1f}%, BP: {processed.clean_bp_sys:.0f}/{processed.clean_bp_dia:.0f}, "
                      f"Temp: {processed.clean_temp:.1f}°C, RR: {processed.clean_rr:.0f}/min.")

    # Medication queries
    if any(w in q for w in ["medication", "medicine", "drug", "pill", "prescription", "med"]):
        if med_tracker and med_tracker.medications:
            ctx = med_tracker.get_medication_context_for_chatbot()
            reminders = med_tracker.get_upcoming_reminders(3)
            next_txt = ""
            if reminders:
                r = reminders[0]
                if r.is_overdue:
                    next_txt = f"\n\n⚠️ **{r.med_name}** is overdue! Please take it now."
                else:
                    next_txt = f"\n\n⏰ Next up: **{r.med_name}** in {r.minutes_until} minutes."
            return f"**Your Medications:**\n{ctx}{next_txt}"
        return "No medications are currently being tracked. You can add medications in the 💊 Medications panel above."

    # Symptom queries
    if any(w in q for w in ["symptom", "feel", "feeling", "how do i feel", "logged"]):
        if symptom_logger:
            summary = symptom_logger.get_correlation_summary()
            return f"**Symptom Log:**\n{summary}\n\n{vitals_ctx}"
        return "No symptoms logged yet. Use the 📋 How Do You Feel? panel to log symptoms."


    # Knowledge base
    if any(w in q for w in ["heart rate", "hr", "pulse", "heartbeat", "bpm"]):
        base = "**Heart Rate** is how many times your heart beats per minute. Normal resting range is 60–100 bpm. "
        if processed:
            hr = processed.clean_hr
            if hr > 100:
                return base + f"Your HR is {hr:.0f} bpm — slightly elevated. This can happen with stress, caffeine, or activity. Try deep breathing. If it persists above 120, consult your doctor."
            elif hr < 60:
                return base + f"Your HR is {hr:.0f} bpm — lower than average. This is common in athletes or during deep rest. If you feel dizzy, seek medical advice."
            else:
                return base + f"Your HR is {hr:.0f} bpm — perfectly normal! 💚"
        return base + "Stay active and manage stress to keep it healthy."

    if any(w in q for w in ["oxygen", "spo2", "o2", "saturation"]):
        base = "**Blood Oxygen (SpO₂)** measures how well oxygen is carried in your blood. Normal is 95–100%. "
        if processed:
            s = processed.clean_spo2
            if s < 92:
                return base + f"Your SpO₂ is {s:.1f}% — this is low. Try deep breathing. If it stays below 92%, seek immediate medical attention."
            elif s < 95:
                return base + f"Your SpO₂ is {s:.1f}% — slightly below optimal. Practice deep breathing exercises and ensure good ventilation."
            else:
                return base + f"Your SpO₂ is {s:.1f}% — excellent! Your oxygen levels are healthy. 💚"
        return base + "Deep breathing and regular exercise help maintain good levels."

    if any(w in q for w in ["blood pressure", "bp", "systolic", "diastolic", "hypertension"]):
        base = "**Blood Pressure** measures the force of blood against artery walls. Normal is around 120/80 mmHg. "
        if processed:
            s, d = processed.clean_bp_sys, processed.clean_bp_dia
            if s > 140 or d > 90:
                return base + f"Your BP is {s:.0f}/{d:.0f} — elevated. Reduce salt, manage stress, exercise regularly. If consistently high, see your doctor."
            elif s < 90:
                return base + f"Your BP is {s:.0f}/{d:.0f} — on the low side. Stay hydrated, avoid standing up too quickly."
            else:
                return base + f"Your BP is {s:.0f}/{d:.0f} — within healthy range! 💚"
        return base + "Maintain a low-sodium diet and regular exercise."

    if any(w in q for w in ["temperature", "temp", "fever", "cold"]):
        base = "**Body Temperature** — normal is 36.1–37.2°C (97–99°F). "
        if processed:
            t = processed.clean_temp
            if t > 38:
                return base + f"Your temperature is {t:.1f}°C — you may have a fever. Stay hydrated, rest, and consider taking acetaminophen. Seek care if above 39.5°C."
            elif t < 35.5:
                return base + f"Your temperature is {t:.1f}°C — lower than normal. Stay warm and monitor closely."
            else:
                return base + f"Your temperature is {t:.1f}°C — perfectly normal. 💚"
        return base + "Stay hydrated and dress appropriately for weather conditions."

    if any(w in q for w in ["breathing", "respiratory", "breath", "rr"]):
        base = "**Respiratory Rate** — normal resting rate is 12–20 breaths/min. "
        if processed:
            rr = processed.clean_rr
            if rr > 24:
                return base + f"Your RR is {rr:.0f}/min — elevated. Try to relax and breathe slowly. Anxiety and exertion can raise it."
            elif rr < 10:
                return base + f"Your RR is {rr:.0f}/min — quite low. If you feel lightheaded, seek medical attention."
            else:
                return base + f"Your RR is {rr:.0f}/min — normal and healthy. 💚"
        return base + "Practice mindful breathing — 4 seconds in, 7 seconds hold, 8 seconds out."

    if any(w in q for w in ["score", "health score", "how am i", "status", "overall"]):
        if score_result:
            s = score_result.score
            if s >= 90: return f"Your health score is **{s:.0f}/100** — Excellent! 💚 All your vitals are in great shape. {vitals_ctx}"
            elif s >= 75: return f"Your health score is **{s:.0f}/100** — Good! 💙 Minor fluctuations but nothing concerning. {vitals_ctx}"
            elif s >= 60: return f"Your health score is **{s:.0f}/100** — Fair. 💛 Some vitals need attention. Stay relaxed and hydrated. {vitals_ctx}"
            else: return f"Your health score is **{s:.0f}/100** — Needs attention. ⚠️ Some readings are outside normal range. {vitals_ctx}"
        return "I don't have enough data yet to calculate your health score. Give me a moment to gather readings."

    if any(w in q for w in ["what's wrong", "problem", "issue", "alert", "warning", "detection"]):
        if ai_result and ai_result.detections:
            issues = []
            for d in ai_result.detections[:3]:
                issues.append(f"• **{d.condition}** ({d.severity}) — {d.recommendation or 'Monitor closely'}")
            return "Here's what I'm seeing:\n\n" + "\n".join(issues) + f"\n\n{vitals_ctx}"
        return "✅ No issues detected right now! All your vitals look healthy. " + vitals_ctx

    if any(w in q for w in ["sleep", "rest", "tired", "fatigue"]):
        return ("**Sleep & Rest Tips:**\n• Aim for 7–9 hours of sleep\n• Keep a consistent sleep schedule\n"
                "• Avoid screens 1 hour before bed\n• Keep your room cool (18–20°C)\n• Limit caffeine after 2 PM\n\n"
                "Good sleep is crucial for heart health and immune function! 😴")

    if any(w in q for w in ["exercise", "workout", "fitness", "activity"]):
        return ("**Exercise Guidelines:**\n• 150 min moderate activity per week (brisk walking)\n"
                "• OR 75 min vigorous activity (running, swimming)\n• Include strength training 2x/week\n"
                "• Start slow if you're new — 10 min walks are great!\n\n"
                "Regular exercise lowers resting HR and blood pressure. 🏃‍♂️")

    if any(w in q for w in ["stress", "anxiety", "worried", "panic", "calm"]):
        return ("**Stress Management:**\n• Try the 4-7-8 breathing technique\n• Practice progressive muscle relaxation\n"
                "• Take a 10-minute walk outside\n• Limit news/social media intake\n• Talk to someone you trust\n\n"
                "Chronic stress raises blood pressure and heart rate. Your mental health matters! 🧘")

    if any(w in q for w in ["water", "hydration", "drink", "dehydrated"]):
        return ("**Hydration Tips:**\n• Aim for 8 glasses (2L) of water daily\n• Drink more during exercise or hot weather\n"
                "• Watch for signs: dark urine, dry mouth, headaches\n• Herbal tea and fruits count too!\n\n"
                "Dehydration can cause elevated heart rate and low blood pressure. 💧")

    if any(w in q for w in ["diet", "food", "eat", "nutrition"]):
        return ("**Heart-Healthy Diet:**\n• Eat plenty of fruits, vegetables, whole grains\n"
                "• Choose lean proteins (fish, chicken, beans)\n• Limit sodium to <2300mg/day\n"
                "• Reduce processed foods and added sugars\n• Include omega-3 rich foods (salmon, walnuts)\n\n"
                "A good diet is the foundation of cardiovascular health! 🥗")

    if any(w in q for w in ["emergency", "help", "call", "ambulance", "sos"]):
        return ("🚨 **If you're having a medical emergency, call 911/112 immediately!**\n\n"
                "Emergency signs:\n• Chest pain or pressure\n• Difficulty breathing\n• Sudden weakness/numbness\n"
                "• Severe headache\n• Loss of consciousness\n\n"
                "This app can alert your emergency contacts — check the sidebar to set them up.")

    if any(w in q for w in ["ecg", "ekg", "electrocardiogram", "monitor"]):
        return ("**About the ECG Monitor:**\n\nThe green waveform shows your heart's electrical activity. "
                "Each spike (QRS complex) represents one heartbeat.\n\n"
                "• **P wave**: Atrial contraction\n• **QRS complex**: Ventricular contraction (the tall spike)\n"
                "• **T wave**: Heart resetting for next beat\n\nRegular, evenly-spaced complexes = healthy rhythm! 💚")

    if any(w in q for w in ["hi", "hello", "hey", "good"]):
        return f"Hello! 😊 I'm here to help you understand your health. {vitals_ctx}\n\nAsk me about your heart rate, oxygen levels, blood pressure, or general health tips!"

    if any(w in q for w in ["thank", "thanks", "bye", "goodbye"]):
        return "You're welcome! 😊 Stay healthy and don't hesitate to ask if you have more questions. Take care! 💚"

    # Default: provide vitals summary + suggestion
    return (f"I'm not sure about that specific question, but here's what I can help with:\n\n"
            f"• Ask about any vital sign (heart rate, oxygen, BP, temperature, breathing)\n"
            f"• Ask 'How am I doing?' for your health score\n"
            f"• Ask about exercise, sleep, diet, stress, or hydration tips\n"
            f"• Ask 'What's wrong?' if you see any alerts\n\n"
            f"{vitals_ctx}")


def render_historical_data_entry(key_suffix=""):
    """Form to enter past health records to train the AI model."""
    import datetime
    from backend.models.database import insert_past_vitals

    st.html(f"""
    <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);border-radius:14px;overflow:hidden;margin:12px 0 4px;">
        <div style="padding:9px 14px;border-bottom:1px solid rgba(255,255,255,0.04);">
            <span style="color:#e8eaf6;font-size:0.8rem;font-weight:700;">📚 Add Historical Health Record</span>
        </div>
    </div>""")

    with st.expander("Enter Past Vitals Data (Trains AI)"):
        st.write("Past data helps the AI understand baseline trends for future risk prediction.")
        col1, col2, col3 = st.columns(3)
        with col1:
            hr = st.number_input("Heart Rate (bpm)", min_value=30, max_value=200, value=72, key=f"hist_hr_{key_suffix}")
            sys = st.number_input("Systolic BP", min_value=60, max_value=250, value=120, key=f"hist_sys_{key_suffix}")
        with col2:
            spo2 = st.number_input("SpO₂ (%)", min_value=50, max_value=100, value=98, key=f"hist_spo2_{key_suffix}")
            dia = st.number_input("Diastolic BP", min_value=30, max_value=150, value=80, key=f"hist_dia_{key_suffix}")
        with col3:
            rr = st.number_input("Resp Rate (/min)", min_value=8, max_value=40, value=16, key=f"hist_rr_{key_suffix}")
            temp = st.number_input("Temp (°C)", min_value=30.0, max_value=42.0, value=37.0, step=0.1, key=f"hist_temp_{key_suffix}")

        rec_date = st.date_input("Date of Record", value=datetime.date.today(), key=f"hist_date_{key_suffix}")
        rec_time = st.time_input("Time of Record", value=datetime.datetime.now().time(), key=f"hist_time_{key_suffix}")

        if st.button("Save Record & Retrain AI", key=f"hist_btn_{key_suffix}", use_container_width=True, type="primary"):
            patient_id = st.session_state.get("selected_patient_id")
            if not patient_id:
                st.error("No active patient selected.")
            else:
                dt = datetime.datetime.combine(rec_date, rec_time)
                timestamp = dt.timestamp()
                # Estimate a rough health score based on these vitals
                score = 100.0
                if hr > 100 or hr < 60: score -= 10
                if spo2 < 95: score -= 15
                if sys > 140 or sys < 90: score -= 10

                insert_past_vitals(patient_id, timestamp, float(hr), float(spo2), float(sys), float(dia), float(rr), float(temp), score)
                st.success("Record saved!")

                # Trigger background AI training
                import subprocess
                try:
                    subprocess.Popen(["python", "-m", "ai_engine.train_model", "--samples", "500"])
                    st.toast("🚀 AI Model Retraining initiated in background with new data.")
                except Exception as e:
                    st.error(f"Failed to start AI training: {e}")
