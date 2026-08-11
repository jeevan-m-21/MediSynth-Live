"""
Medisynth Live – Sidebar Controls
Clean buttons, aligned layout, loading states, notification status.
"""

import streamlit as st
import time
from modules.sound_alerts import inject_mute_state
from modules.wearable_ble import get_ble_widget_html
from modules.activity_detector import get_activity_widget_html


def render_simulation_panel(sim_engine, synthetic_engine, emergency_system, notification_service=None):
    """Render sidebar simulation controls."""
    import config

    # ── Branding ──
    st.html("""
    <div style="text-align:center; padding:12px 0 6px;">
        <div style="font-size:2rem;">🫀</div>
        <div style="font-size:1rem; font-weight:800; color:#00d4aa;
            background:linear-gradient(135deg, #00d4aa, #7c3aed);
            -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
            Medisynth Live
        </div>
        <div style="font-size:0.55rem; font-weight:600; color:#7986cb;
            letter-spacing:2px; text-transform:uppercase;">
            AI-POWERED HEALTH MONITORING
        </div>
    </div>
    """)

    # ── Wearable Sensor Connection ──
    st.html('<div class="section-header">📡 WEARABLE SENSOR</div>')
    import streamlit.components.v1 as components
    components.html(get_ble_widget_html(), height=280, scrolling=False)

    # ── Auto Activity Detection ──
    st.html('<div class="section-header">🏃 ACTIVITY DETECTION</div>')
    components.html(get_activity_widget_html(current_mode=sim_engine.mode), height=260, scrolling=False)

    # ── Dashboard View (determined by auth role) ──
    current_role = st.session_state.get("role", "Patient")
    role_colors = {"Patient": "#00d4aa", "Doctor": "#a78bfa", "Caregiver": "#38bdf8"}
    role_icons = {"Patient": "👤", "Doctor": "🩺", "Caregiver": "🤝"}
    rc = role_colors.get(current_role, "#7986cb")
    ri = role_icons.get(current_role, "👤")
    st.html(f"""
    <div style="padding:8px 12px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.04);
        border-radius:10px;margin:4px 0;display:flex;align-items:center;gap:8px;">
        <span style="font-size:1rem;">{ri}</span>
        <div>
            <div style="color:{rc};font-size:0.65rem;font-weight:700;letter-spacing:0.5px;text-transform:uppercase;">{current_role} Dashboard</div>
        </div>
    </div>""")

    # Patient name is now handled via auth/patient_selector

    # ── Mode Display ──
    st.html('<div class="section-header">🎮 SIMULATION CONTROLS</div>')
    mode = sim_engine.mode
    mode_info = config.SIMULATION_MODES.get(mode, {})
    st.html(f"""
    <div style="background:rgba(15,20,40,0.5); border:1px solid rgba(255,255,255,0.08);
        border-radius:10px; padding:10px; margin-bottom:10px; text-align:center;">
        <span style="font-size:1rem;">{mode_info.get('icon','💚')}</span>
        <strong style="color:#00d4aa; margin-left:4px;">{mode_info.get('label', mode)}</strong>
        <div style="color:#7986cb; font-size:0.65rem;">{mode_info.get('description','')}</div>
    </div>
    """)

    # ── Mode Buttons (full width, stacked for clarity) ──
    if st.button("💚 Normal — Stable Vitals", key="m_normal", use_container_width=True):
        sim_engine.set_mode("normal")
        st.rerun()
    if st.button("💛 Stress — Cardiac Stress", key="m_stress", use_container_width=True):
        sim_engine.set_mode("stress")
        st.rerun()
    if st.button("🔴 Critical — Emergency", key="m_critical", use_container_width=True):
        sim_engine.set_mode("critical")
        st.rerun()

    with st.expander("🌙 Lifestyle Modes"):
        if st.button("🌙 Sleep Mode", key="m_sleep", use_container_width=True):
            sim_engine.set_mode("sleep")
            st.rerun()
        if st.button("🏃 Exercise Mode", key="m_exercise", use_container_width=True):
            sim_engine.set_mode("exercise")
            st.rerun()
        if st.button("🔄 Recovery Mode", key="m_recovery", use_container_width=True):
            sim_engine.set_mode("recovery")
            st.rerun()

    # ── Sound ──
    sound_muted = st.toggle("🔇 Mute Alerts", value=st.session_state.get("sound_muted", False), key="sound_toggle")
    st.session_state.sound_muted = sound_muted
    inject_mute_state(sound_muted)

    # ── Synthetic Scenarios (Developer Only) ──
    if st.session_state.get("auth_user", {}).get("role") == "developer":
        st.html('<div class="section-header" style="margin-top:12px;">🧬 SYNTHETIC SCENARIOS</div>')

        training = st.toggle("🎓 Training Mode", value=synthetic_engine.is_training_mode, key="training_toggle")
        synthetic_engine.is_training_mode = training

        from modules.synthetic_engine import SCENARIOS

        active = synthetic_engine.get_active_scenario_info()
        if active:
            elapsed = time.time() - synthetic_engine.scenario_start
            progress = min(1.0, elapsed / active.duration_s)
            st.html(f"""
            <div style="background:rgba(124,58,237,0.12); border:1px solid rgba(124,58,237,0.3);
                border-radius:8px; padding:8px; margin:6px 0; font-size:0.75rem;">
                <div style="color:#a78bfa; font-weight:600;">{active.icon} {active.name}</div>
                <div style="color:#7986cb; font-size:0.65rem;">{active.description}</div>
                <div style="margin-top:4px; width:100%; height:3px; background:rgba(255,255,255,0.06); border-radius:2px;">
                    <div style="width:{progress*100:.0f}%; height:100%; background:#a78bfa; border-radius:2px;"></div>
                </div>
            </div>
            """)

        # Scenario buttons — full width for readability
        for key, scenario in SCENARIOS.items():
            if st.button(f"{scenario.icon} {scenario.name}", key=f"synth_{key}", use_container_width=True):
                synthetic_engine.start_scenario(key)
                st.rerun()

    # ── Notification Provider ──
    if notification_service:
        st.html('<div class="section-header" style="margin-top:12px;">📡 NOTIFICATIONS</div>')
        status = notification_service.get_provider_status()
        active_label = status.get("active_label", "None")
        sent = notification_service.get_sent_count()
        success = notification_service.get_success_count()
        last_results = notification_service.get_last_results(3)

        # Status card
        has_india = status.get("fast2sms") == "✅" or status.get("twilio") == "✅" or status.get("callmebot") == "✅"
        border_color = "rgba(0,212,170,0.2)" if has_india else "rgba(255,179,71,0.3)"
        st.html(f"""
        <div style="background:rgba(15,20,40,0.4); border:1px solid {border_color};
            border-radius:8px; padding:8px; font-size:0.7rem;">
            <div style="color:#00d4aa; font-weight:600;">Active: {active_label}</div>
            <div style="color:#7986cb;">Sent: {success}/{sent} successful</div>
        </div>
        """)

        # Provider checklist
        prov_items = ""
        for key, icon, label in [
            ("fast2sms", "🇮🇳", "Fast2SMS"),
            ("callmebot", "💬", "WhatsApp"),
            ("twilio", "📱", "Twilio"),
            ("email", "📧", "Email"),
        ]:
            val = status.get(key, "—")
            color = "#00d4aa" if val == "✅" else "#4a5568"
            prov_items += f'<span style="color:{color}; margin-right:8px;">{icon}{val}</span>'
        st.html(f'<div style="font-size:0.6rem; padding:4px 0;">{prov_items}</div>')

        # Show recent results
        if last_results:
            for r in last_results:
                color = "#00d4aa" if r.success else "#ff4757"
                txt = f"✔ {r.provider}" if r.success else f"✕ {r.error[:40]}"
                st.html(f'<div style="font-size:0.6rem; padding:2px 0; color:{color};">{r.recipient} → {txt}</div>')

        # ntfy.sh subscribe link (ALWAYS shown)
        ntfy_url = notification_service.get_ntfy_subscribe_url()
        st.html(f"""
        <div style="background:rgba(0,212,170,0.06); border:1px solid rgba(0,212,170,0.3);
            border-radius:10px; padding:10px; margin:6px 0;">
            <div style="color:#00d4aa; font-weight:700; font-size:0.8rem; margin-bottom:4px;">
                📲 Get alerts on your phone:
            </div>
            <div style="font-size:0.7rem; color:#c5cae9; margin-bottom:6px;">
                Open this link on your phone ↓
            </div>
            <a href="{ntfy_url}" target="_blank" style="display:block; background:rgba(0,212,170,0.15);
                border:1px solid rgba(0,212,170,0.3); border-radius:8px; padding:8px;
                color:#00d4aa; text-decoration:none; font-family:'JetBrains Mono',monospace;
                font-size:0.7rem; text-align:center; font-weight:600; word-break:break-all;">
                {ntfy_url}
            </a>
            <div style="color:#7986cb; font-size:0.6rem; margin-top:4px;">
                Click "Subscribe" on the page → get instant push alerts!
            </div>
        </div>
        """)

    # ── Emergency Contacts ──
    st.html('<div class="section-header" style="margin-top:12px;">🚨 EMERGENCY CONTACTS</div>')

    for contact in emergency_system.contacts:
        st.html(f"""
        <div style="background:rgba(15,20,40,0.4); border:1px solid rgba(255,255,255,0.06);
            border-radius:8px; padding:8px; margin:4px 0; font-size:0.8rem;">
            <div style="color:#e8eaf6; font-weight:600;">{contact.name}</div>
            <div style="color:#7986cb; font-size:0.65rem;">{contact.phone} • {contact.relationship}</div>
        </div>
        """)
        if st.button("Remove", key=f"del_{contact.id}"):
            emergency_system.remove_contact(contact.id)
            st.rerun()

    with st.expander("➕ Add Contact"):
        name = st.text_input("Name", key="new_name")
        phone = st.text_input("Phone (+91...)", key="new_phone", placeholder="+91XXXXXXXXXX")
        rel = st.selectbox("Relationship", ["Family", "Friend", "Doctor", "Nurse"], key="new_rel")
        if st.button("Add Contact", key="add_btn"):
            if name and phone:
                emergency_system.add_contact(name, phone, rel)
                st.rerun()

    # ── Reset ──
    st.html("<div style='height:12px;'></div>")
    if st.button("🔄 Reset System", key="reset_btn", use_container_width=True):
        for key in list(st.session_state.keys()):
            if key not in ("role", "sound_muted"):
                del st.session_state[key]
        st.rerun()
