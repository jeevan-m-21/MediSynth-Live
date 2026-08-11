"""
Medisynth Live – JWT Authentication Module
HMAC-SHA256 token generation, password hashing (SHA-256 + salt), session management.
Zero external dependencies — uses Python stdlib only.
"""

import hashlib
import hmac
import json
import time
import os
import base64
import secrets
from typing import Optional, Dict

# ── Secret key for JWT signing (auto-generated per deployment) ──
_SECRET_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), ".jwt_secret")

def _get_secret() -> str:
    if os.path.exists(_SECRET_FILE):
        with open(_SECRET_FILE, "r") as f:
            return f.read().strip()
    secret = secrets.token_hex(32)
    with open(_SECRET_FILE, "w") as f:
        f.write(secret)
    return secret

JWT_SECRET = _get_secret()
JWT_EXPIRY_HOURS = 24
SALT = "medisynth_v2_"


# ═══════════════════════════════════════════════════════════════════════════════
# ── Password Hashing (SHA-256 + salt — no external deps) ──
# ═══════════════════════════════════════════════════════════════════════════════

def hash_password(password: str) -> str:
    """Hash a password with salt using SHA-256."""
    salted = f"{SALT}{password}"
    return hashlib.sha256(salted.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return hash_password(password) == hashed


# ═══════════════════════════════════════════════════════════════════════════════
# ── JWT Token (HMAC-SHA256 — no pyjwt dependency) ──
# ═══════════════════════════════════════════════════════════════════════════════

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def _b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def create_token(user_id: str, role: str, email: str, name: str) -> str:
    """Create a JWT token with user claims."""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "role": role,
        "email": email,
        "name": name,
        "iat": int(time.time()),
        "exp": int(time.time() + JWT_EXPIRY_HOURS * 3600),
    }
    h = _b64url_encode(json.dumps(header).encode())
    p = _b64url_encode(json.dumps(payload).encode())
    signature = hmac.new(JWT_SECRET.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
    s = _b64url_encode(signature)
    return f"{h}.{p}.{s}"


def decode_token(token: str) -> Optional[Dict]:
    """Decode and verify a JWT token. Returns payload or None if invalid/expired."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        h, p, s = parts
        # Verify signature
        expected_sig = hmac.new(JWT_SECRET.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
        actual_sig = _b64url_decode(s)
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        # Decode payload
        payload = json.loads(_b64url_decode(p))
        # Check expiry
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# ── Authentication Service ──
# ═══════════════════════════════════════════════════════════════════════════════

def authenticate(email: str, password: str) -> Optional[Dict]:
    """Authenticate a user. Returns {token, user} or None."""
    from backend.models.database import get_user_by_email, update_last_login, log_audit

    user = get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user["password"]):
        log_audit("unknown", "login_failed", details=f"email={email}")
        return None

    token = create_token(user["id"], user["role"], user["email"], user["full_name"])
    update_last_login(user["id"])
    log_audit(user["id"], "login_success")

    return {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "phone": user["phone"],
            "speciality": user.get("speciality", ""),
            "license_no": user.get("license_no", ""),
        }
    }


def get_current_user(token: str) -> Optional[Dict]:
    """Get current user from token. Returns user dict or None."""
    payload = decode_token(token)
    if not payload:
        return None
    from backend.models.database import get_user_by_id
    user = get_user_by_id(payload["sub"])
    if not user:
        return None
    return {
        "id": user["id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "role": user["role"],
        "phone": user["phone"],
        "speciality": user.get("speciality", ""),
    }


def register_user(email: str, password: str, full_name: str, role: str,
                   phone: str = "", speciality: str = "") -> Optional[Dict]:
    """Register a new user. Returns auth result or None if email exists."""
    from backend.models.database import get_db, log_audit
    import uuid

    conn = get_db()
    # Check if email exists
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return None

    user_id = f"{role[:3]}_{uuid.uuid4().hex[:6]}"
    hashed = hash_password(password)

    conn.execute(
        "INSERT INTO users (id, email, password, full_name, role, phone, speciality) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, email, hashed, full_name, role, phone, speciality)
    )
    conn.commit()
    conn.close()

    log_audit(user_id, "register", details=f"role={role}")
    return authenticate(email, password)
