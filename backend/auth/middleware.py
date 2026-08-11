"""
Medisynth Live – Streamlit Auth Middleware
Manages auth state in st.session_state. Provides decorators and guards.
"""

import streamlit as st
from typing import Optional, Dict, List


def init_auth():
    """Initialize auth state keys. Call once at app startup."""
    defaults = {
        "auth_token": None,
        "auth_user": None,
        "auth_initialized": False,
        "selected_patient_id": None,
        "selected_patient_name": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def is_authenticated() -> bool:
    """Check if user is currently authenticated."""
    return st.session_state.get("auth_token") is not None and st.session_state.get("auth_user") is not None


def get_current_user() -> Optional[Dict]:
    """Get current authenticated user dict."""
    return st.session_state.get("auth_user")


def get_user_role() -> str:
    """Get current user's role. Returns 'guest' if not authenticated."""
    user = get_current_user()
    return user["role"] if user else "guest"


def login(email: str, password: str) -> tuple[bool, str]:
    """Attempt login. Returns (success, message)."""
    from backend.auth.jwt_auth import authenticate
    result = authenticate(email, password)
    if not result:
        return False, "Invalid email or password"

    st.session_state["auth_token"] = result["token"]
    st.session_state["auth_user"] = result["user"]

    # Auto-select patient for patient role
    if result["user"]["role"] == "patient":
        st.session_state["selected_patient_id"] = result["user"]["id"]
        st.session_state["selected_patient_name"] = result["user"]["full_name"]

    return True, f"Welcome, {result['user']['full_name']}!"


def register(email: str, password: str, full_name: str, role: str,
             phone: str = "", speciality: str = "") -> tuple[bool, str]:
    """Register a new user. Returns (success, message)."""
    from backend.auth.jwt_auth import register_user

    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    if not email or "@" not in email:
        return False, "Invalid email address"
    if not full_name.strip():
        return False, "Full name is required"

    result = register_user(email, password, full_name, role, phone, speciality)
    if not result:
        return False, "Email already registered"

    st.session_state["auth_token"] = result["token"]
    st.session_state["auth_user"] = result["user"]

    if role == "patient":
        st.session_state["selected_patient_id"] = result["user"]["id"]
        st.session_state["selected_patient_name"] = result["user"]["full_name"]

    return True, f"Account created! Welcome, {result['user']['full_name']}"


def logout():
    """Clear auth state."""
    from backend.models.database import log_audit
    user = get_current_user()
    if user:
        log_audit(user["id"], "logout")
    st.session_state["auth_token"] = None
    st.session_state["auth_user"] = None
    st.session_state["selected_patient_id"] = None
    st.session_state["selected_patient_name"] = None


def get_accessible_patients() -> List[Dict]:
    """Get list of patients the current user can access."""
    user = get_current_user()
    if not user:
        return []

    from backend.models.database import get_patients_for_doctor, get_patients_for_caregiver

    if user["role"] == "patient":
        return [{"id": user["id"], "full_name": user["full_name"]}]
    elif user["role"] == "doctor":
        return get_patients_for_doctor(user["id"])
    elif user["role"] == "caregiver":
        return get_patients_for_caregiver(user["id"])
    return []


def require_auth():
    """Gate function — call at top of page to require authentication."""
    if not is_authenticated():
        from ui.auth_page import render_auth_page
        render_auth_page()
        st.stop()
