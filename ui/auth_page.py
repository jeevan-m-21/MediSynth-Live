"""
Medisynth Live – Authentication Page
Premium glassmorphic login/register UI with role-based access.
"""

import streamlit as st
import streamlit.components.v1 as components


def render_auth_page():
    """Render the full-page authentication screen."""

    # Inject auth-specific CSS
    st.html("""
    <style>
    /* Hide Streamlit chrome during auth */
    header[data-testid="stHeader"] { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    .stApp > header { display: none !important; }
    div[data-testid="stSidebarCollapsedControl"] { display: none !important; }

    /* Auth container */
    .auth-wrapper {
        min-height: 100vh;
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 20px;
    }
    </style>
    """)

    # ── Animated background ──
    components.html("""
    <div id="auth-bg" style="position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:-1;
        background:linear-gradient(135deg,#030712 0%,#0a1628 30%,#0f1d35 60%,#0a0e1a 100%);overflow:hidden;">
        <svg width="100%" height="100%" style="position:absolute;top:0;left:0;">
            <defs>
                <radialGradient id="g1" cx="20%" cy="30%">
                    <stop offset="0%" stop-color="rgba(0,212,170,0.06)"/>
                    <stop offset="100%" stop-color="rgba(0,212,170,0)"/>
                </radialGradient>
                <radialGradient id="g2" cx="80%" cy="70%">
                    <stop offset="0%" stop-color="rgba(124,58,237,0.05)"/>
                    <stop offset="100%" stop-color="rgba(124,58,237,0)"/>
                </radialGradient>
            </defs>
            <circle cx="20%" cy="30%" r="300" fill="url(#g1)">
                <animate attributeName="r" values="250;350;250" dur="8s" repeatCount="indefinite"/>
            </circle>
            <circle cx="80%" cy="70%" r="250" fill="url(#g2)">
                <animate attributeName="r" values="200;300;200" dur="10s" repeatCount="indefinite"/>
            </circle>
        </svg>
        <!-- ECG line across screen -->
        <svg width="100%" height="80" style="position:absolute;bottom:20%;left:0;opacity:0.06;">
            <polyline points="0,40 60,40 80,40 90,10 100,70 110,35 120,40 200,40 280,40 300,40 310,10 320,70 330,35 340,40 420,40 500,40 520,40 530,10 540,70 550,35 560,40 640,40 720,40 740,40 750,10 760,70 770,35 780,40 860,40 940,40 960,40 970,10 980,70 990,35 1000,40 1080,40 1160,40 1180,40 1190,10 1200,70 1210,35 1220,40 1300,40 1400,40"
                fill="none" stroke="#00d4aa" stroke-width="2">
                <animate attributeName="stroke-dashoffset" from="0" to="-200" dur="3s" repeatCount="indefinite"/>
            </polyline>
        </svg>
    </div>
    """, height=0)

    # ── Logo + Title ──
    st.html("""
    <div style="text-align:center;margin-bottom:8px;">
        <div style="display:inline-flex;align-items:center;gap:12px;margin-bottom:8px;">
            <div style="width:48px;height:48px;border-radius:14px;
                background:linear-gradient(135deg,#00d4aa 0%,#7c3aed 100%);
                display:flex;align-items:center;justify-content:center;font-size:1.5rem;
                box-shadow:0 8px 32px rgba(0,212,170,0.25);">🫀</div>
            <div>
                <div style="font-size:1.8rem;font-weight:900;
                    background:linear-gradient(135deg,#00d4aa,#7c3aed);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                    letter-spacing:-0.5px;line-height:1;">Medisynth Live</div>
                <div style="color:#5c6b8a;font-size:0.65rem;font-weight:500;letter-spacing:2px;
                    text-transform:uppercase;margin-top:2px;">AI-POWERED HEALTH MONITORING</div>
            </div>
        </div>
    </div>
    """)

    # ── Auth Tabs ──
    tab_login, tab_register = st.tabs(["🔐 Sign In", "📝 Create Account"])

    with tab_login:
        _render_login_form()

    with tab_register:
        _render_register_form()

    # ── Demo Credentials Footer ──
    st.html("""
    <div style="margin-top:20px;padding:14px 18px;
        background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);
        border-radius:14px;">
        <div style="color:#5c6b8a;font-size:0.6rem;font-weight:600;letter-spacing:1px;
            text-transform:uppercase;margin-bottom:8px;">🧪 Demo Credentials</div>
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;font-size:0.65rem;">
            <div style="padding:8px;background:rgba(0,212,170,0.04);border:1px solid rgba(0,212,170,0.1);border-radius:10px;">
                <div style="color:#00d4aa;font-weight:700;margin-bottom:3px;">👤 Patient</div>
                <div style="color:#7986cb;">patient@medisynth.live</div>
                <div style="color:#4a5568;">patient123</div>
            </div>
            <div style="padding:8px;background:rgba(124,58,237,0.04);border:1px solid rgba(124,58,237,0.1);border-radius:10px;">
                <div style="color:#a78bfa;font-weight:700;margin-bottom:3px;">🩺 Doctor</div>
                <div style="color:#7986cb;">doctor@medisynth.live</div>
                <div style="color:#4a5568;">doctor123</div>
            </div>
            <div style="padding:8px;background:rgba(56,189,248,0.04);border:1px solid rgba(56,189,248,0.1);border-radius:10px;">
                <div style="color:#38bdf8;font-weight:700;margin-bottom:3px;">🤝 Caregiver</div>
                <div style="color:#7986cb;">caregiver@medisynth.live</div>
                <div style="color:#4a5568;">caregiver123</div>
            </div>
            <div style="padding:8px;background:rgba(251,191,36,0.04);border:1px solid rgba(251,191,36,0.1);border-radius:10px;">
                <div style="color:#fbbf24;font-weight:700;margin-bottom:3px;">⚙️ Developer</div>
                <div style="color:#7986cb;">developer@medisynth.live</div>
                <div style="color:#4a5568;">developer123</div>
            </div>
        </div>
    </div>
    """)

    # ── Security badges ──
    st.html("""
    <div style="display:flex;justify-content:center;gap:20px;margin-top:16px;padding:10px 0;">
        <div style="display:flex;align-items:center;gap:4px;color:#3d4a66;font-size:0.55rem;">
            <span>🔒</span> <span>SHA-256 Encrypted</span>
        </div>
        <div style="display:flex;align-items:center;gap:4px;color:#3d4a66;font-size:0.55rem;">
            <span>🛡️</span> <span>JWT Authentication</span>
        </div>
        <div style="display:flex;align-items:center;gap:4px;color:#3d4a66;font-size:0.55rem;">
            <span>📋</span> <span>HIPAA Audit Trail</span>
        </div>
        <div style="display:flex;align-items:center;gap:4px;color:#3d4a66;font-size:0.55rem;">
            <span>🔑</span> <span>Role-Based Access</span>
        </div>
    </div>
    """)


def _render_login_form():
    """Login form with role icon feedback."""
    from backend.auth.middleware import login

    # Card wrapper
    st.html("""<div style="padding:4px 0;">
        <div style="color:#e8eaf6;font-size:1rem;font-weight:700;margin-bottom:4px;">Welcome Back</div>
        <div style="color:#5c6b8a;font-size:0.72rem;margin-bottom:12px;">
            Sign in to access your health dashboard</div>
    </div>""")

    email = st.text_input("Email", key="login_email", placeholder="you@medisynth.live")
    password = st.text_input("Password", type="password", key="login_password", placeholder="••••••••")

    col_btn, col_status = st.columns([1, 2])
    with col_btn:
        login_clicked = st.button("Sign In →", key="btn_login", use_container_width=True, type="primary")

    if login_clicked:
        if not email or not password:
            st.error("Please enter both email and password")
        else:
            success, msg = login(email, password)
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)


def _render_register_form():
    """Registration form with role selection."""
    from backend.auth.middleware import register

    st.html("""<div style="padding:4px 0;">
        <div style="color:#e8eaf6;font-size:1rem;font-weight:700;margin-bottom:4px;">Create Account</div>
        <div style="color:#5c6b8a;font-size:0.72rem;margin-bottom:12px;">
            Set up your clinical monitoring profile</div>
    </div>""")

    # Role selection — big cards
    st.html('<div style="color:#7986cb;font-size:0.7rem;font-weight:600;margin-bottom:4px;">I am a...</div>')
    role = st.radio("Role", ["patient", "doctor", "caregiver"],
                    format_func=lambda r: {"patient": "👤 Patient", "doctor": "🩺 Doctor",
                                           "caregiver": "🤝 Caregiver"}[r],
                    horizontal=True, key="reg_role", label_visibility="collapsed")

    col1, col2 = st.columns(2)
    with col1:
        full_name = st.text_input("Full Name", key="reg_name", placeholder="Dr. Ananya Rao")
    with col2:
        phone = st.text_input("Phone (optional)", key="reg_phone", placeholder="+91 98765 43210")

    email = st.text_input("Email", key="reg_email", placeholder="you@medisynth.live")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        password = st.text_input("Password", type="password", key="reg_password", placeholder="Min 6 characters")
    with col_p2:
        confirm = st.text_input("Confirm Password", type="password", key="reg_confirm", placeholder="Re-enter password")

    # Doctor-specific fields
    speciality = ""
    license_no = ""
    if role == "doctor":
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            speciality = st.text_input("Speciality", key="reg_spec", placeholder="e.g. Cardiology")
        with col_s2:
            license_no = st.text_input("License No.", key="reg_license", placeholder="e.g. MCI-2024-12345")

    reg_clicked = st.button("Create Account →", key="btn_register", use_container_width=True, type="primary")

    if reg_clicked:
        if not full_name or not email or not password:
            st.error("All fields are required")
        elif password != confirm:
            st.error("Passwords do not match")
        elif len(password) < 6:
            st.error("Password must be at least 6 characters")
        else:
            success, msg = register(email, password, full_name, role, phone, speciality)
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
