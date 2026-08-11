"""
Medisynth Live – Patient Selector Widget
Dropdown for doctor/caregiver to switch between assigned patients.
Injected into the sidebar without breaking existing simulation panel.
"""

import streamlit as st


def render_patient_selector():
    """Render patient selector in sidebar for doctor/caregiver roles.
    Returns True if a patient is selected, False otherwise."""
    from backend.auth.middleware import get_current_user, get_accessible_patients

    user = get_current_user()
    if not user or user["role"] == "patient":
        return True  # Patients always see their own data

    patients = get_accessible_patients()
    if not patients:
        st.warning("No patients assigned to you yet.")
        return False

    # Build selector
    role_label = "🩺 Doctor" if user["role"] == "doctor" else "🤝 Caregiver"
    st.html(f"""
    <div style="padding:8px 12px;background:linear-gradient(135deg,rgba(124,58,237,0.06),rgba(0,212,170,0.04));
        border:1px solid rgba(124,58,237,0.12);border-radius:12px;margin-bottom:8px;">
        <div style="color:#a78bfa;font-size:0.6rem;font-weight:600;letter-spacing:1px;
            text-transform:uppercase;margin-bottom:4px;">{role_label} VIEW</div>
        <div style="color:#e8eaf6;font-size:0.85rem;font-weight:700;">{user['full_name']}</div>
        <div style="color:#5c6b8a;font-size:0.6rem;">{user.get('speciality', '')}</div>
    </div>""")

    st.html('<div style="color:#7986cb;font-size:0.6rem;font-weight:600;letter-spacing:0.5px;margin:4px 0;">👥 SELECT PATIENT</div>')

    # Format patient options
    patient_names = [p["full_name"] for p in patients]
    patient_ids = [p["id"] for p in patients]

    # Find current selection index
    current_id = st.session_state.get("selected_patient_id")
    default_idx = 0
    if current_id in patient_ids:
        default_idx = patient_ids.index(current_id)

    selected = st.selectbox(
        "Patient",
        range(len(patients)),
        format_func=lambda i: f"👤 {patient_names[i]}",
        index=default_idx,
        key="patient_selector",
        label_visibility="collapsed"
    )

    # Update selection using the context swapper from app
    if selected != default_idx:
        from app import switch_patient_context
        switch_patient_context(patient_ids[selected], patient_names[selected])
        st.rerun()
    elif not current_id:
        # Initial load fallback
        from app import switch_patient_context
        switch_patient_context(patient_ids[selected], patient_names[selected])

    # Patient status badge
    st.html(f"""
    <div style="padding:6px 10px;background:rgba(0,212,170,0.05);border:1px solid rgba(0,212,170,0.1);
        border-radius:10px;margin:4px 0;display:flex;align-items:center;gap:6px;">
        <div style="width:8px;height:8px;border-radius:50%;background:#00d4aa;animation:patPulse 2s infinite;"></div>
        <div>
            <div style="color:#e8eaf6;font-size:0.72rem;font-weight:600;">{patient_names[selected]}</div>
            <div style="color:#5c6b8a;font-size:0.55rem;">ID: {patient_ids[selected]} · Live</div>
        </div>
    </div>
    <style>@keyframes patPulse{{0%,100%{{opacity:1}}50%{{opacity:0.4}}}}</style>
    """)

    st.divider()
    return True


def render_user_badge():
    """Small user badge in sidebar showing current user and logout button."""
    from backend.auth.middleware import get_current_user, logout

    user = get_current_user()
    if not user:
        return

    role_colors = {"patient": "#00d4aa", "doctor": "#a78bfa", "caregiver": "#38bdf8"}
    role_icons = {"patient": "👤", "doctor": "🩺", "caregiver": "🤝"}
    color = role_colors.get(user["role"], "#7986cb")
    icon = role_icons.get(user["role"], "👤")

    st.html(f"""
    <div style="padding:8px 12px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);
        border-radius:12px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;">
        <div style="display:flex;align-items:center;gap:8px;">
            <div style="width:32px;height:32px;border-radius:10px;background:rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.12);
                display:flex;align-items:center;justify-content:center;font-size:1rem;">{icon}</div>
            <div>
                <div style="color:#e8eaf6;font-size:0.72rem;font-weight:600;">{user['full_name']}</div>
                <div style="color:{color};font-size:0.55rem;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">{user['role']}</div>
            </div>
        </div>
    </div>""")

    if st.button("🚪 Sign Out", key="btn_logout", use_container_width=True):
        logout()
        st.rerun()
