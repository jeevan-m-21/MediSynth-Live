"""
Medisynth Live – Database Layer
SQLite-based user store, role relationships, and vitals history.
Zero external dependencies — uses Python's built-in sqlite3.
"""

import sqlite3
import os
import time
from typing import Optional, List, Dict

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "medisynth.db")


def get_db() -> sqlite3.Connection:
    """Get a database connection with row_factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize all tables. Safe to call multiple times (IF NOT EXISTS)."""
    conn = get_db()
    conn.executescript("""
    -- Users table with role-based access
    CREATE TABLE IF NOT EXISTS users (
        id          TEXT PRIMARY KEY,
        email       TEXT UNIQUE NOT NULL,
        password    TEXT NOT NULL,
        full_name   TEXT NOT NULL,
        role        TEXT NOT NULL CHECK(role IN ('patient','doctor','caregiver')),
        phone       TEXT DEFAULT '',
        speciality  TEXT DEFAULT '',
        license_no  TEXT DEFAULT '',
        avatar_url  TEXT DEFAULT '',
        is_active   INTEGER DEFAULT 1,
        created_at  REAL DEFAULT (strftime('%s','now')),
        last_login  REAL DEFAULT 0
    );

    -- Doctor ↔ Patient mapping
    CREATE TABLE IF NOT EXISTS doctor_patient_map (
        doctor_id   TEXT NOT NULL REFERENCES users(id),
        patient_id  TEXT NOT NULL REFERENCES users(id),
        assigned_at REAL DEFAULT (strftime('%s','now')),
        is_active   INTEGER DEFAULT 1,
        PRIMARY KEY (doctor_id, patient_id)
    );

    -- Caregiver ↔ Patient mapping
    CREATE TABLE IF NOT EXISTS caregiver_patient_map (
        caregiver_id TEXT NOT NULL REFERENCES users(id),
        patient_id   TEXT NOT NULL REFERENCES users(id),
        assigned_at  REAL DEFAULT (strftime('%s','now')),
        is_active    INTEGER DEFAULT 1,
        PRIMARY KEY (caregiver_id, patient_id)
    );

    -- Vitals history (for persistent storage across sessions)
    CREATE TABLE IF NOT EXISTS vitals_log (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id  TEXT NOT NULL REFERENCES users(id),
        timestamp   REAL NOT NULL,
        heart_rate  REAL,
        spo2        REAL,
        bp_systolic REAL,
        bp_diastolic REAL,
        resp_rate   REAL,
        temperature REAL,
        health_score REAL,
        mode        TEXT DEFAULT 'normal'
    );

    -- AI predictions log
    CREATE TABLE IF NOT EXISTS predictions_log (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id  TEXT NOT NULL REFERENCES users(id),
        timestamp   REAL NOT NULL,
        risk_score  REAL,
        anomaly_flag INTEGER DEFAULT 0,
        model_version TEXT DEFAULT 'v1',
        details     TEXT DEFAULT '{}'
    );

    -- Session audit trail (HIPAA-style)
    CREATE TABLE IF NOT EXISTS audit_log (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     TEXT NOT NULL,
        action      TEXT NOT NULL,
        target_id   TEXT DEFAULT '',
        ip_address  TEXT DEFAULT '',
        timestamp   REAL DEFAULT (strftime('%s','now')),
        details     TEXT DEFAULT ''
    );

    -- Emergency Contacts
    CREATE TABLE IF NOT EXISTS emergency_contacts (
        id           TEXT PRIMARY KEY,
        user_id      TEXT NOT NULL REFERENCES users(id),
        name         TEXT NOT NULL,
        phone        TEXT NOT NULL,
        relationship TEXT NOT NULL,
        created_at   REAL DEFAULT (strftime('%s','now'))
    );

    -- Index for fast lookups
    CREATE INDEX IF NOT EXISTS idx_vitals_patient ON vitals_log(patient_id, timestamp);
    CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id, timestamp);
    CREATE INDEX IF NOT EXISTS idx_dpm_doctor ON doctor_patient_map(doctor_id);
    CREATE INDEX IF NOT EXISTS idx_cpm_caregiver ON caregiver_patient_map(caregiver_id);
    CREATE INDEX IF NOT EXISTS idx_contacts_user ON emergency_contacts(user_id);
    """)
    conn.commit()
    conn.close()


def seed_demo_users():
    """Create demo users for testing. Skips if already exist."""
    from backend.auth.jwt_auth import hash_password
    import uuid

    conn = get_db()
    demo_users = [
        {"id": "pat_001", "email": "patient@medisynth.live", "password": hash_password("patient123"),
         "full_name": "Arjun Mehta", "role": "patient", "phone": "+91 98765 43210"},
        {"id": "pat_002", "email": "patient2@medisynth.live", "password": hash_password("patient123"),
         "full_name": "Priya Sharma", "role": "patient", "phone": "+91 98765 43211"},
        {"id": "doc_001", "email": "doctor@medisynth.live", "password": hash_password("doctor123"),
         "full_name": "Dr. Ananya Rao", "role": "doctor", "speciality": "Cardiology",
         "license_no": "MCI-2019-45678"},
        {"id": "doc_002", "email": "dr.kumar@medisynth.live", "password": hash_password("doctor123"),
         "full_name": "Dr. Vikram Kumar", "role": "doctor", "speciality": "Internal Medicine",
         "license_no": "MCI-2020-12345"},
        {"id": "cg_001", "email": "caregiver@medisynth.live", "password": hash_password("caregiver123"),
         "full_name": "Meera Nair", "role": "caregiver", "phone": "+91 98765 43212"},
    ]

    for user in demo_users:
        try:
            conn.execute(
                "INSERT OR IGNORE INTO users (id, email, password, full_name, role, phone, speciality, license_no) "
                "VALUES (:id, :email, :password, :full_name, :role, :phone, :speciality, :license_no)",
                {**{"phone": "", "speciality": "", "license_no": ""}, **user}
            )
        except sqlite3.IntegrityError:
            pass

    # Assign relationships
    relationships = [
        ("doctor_patient_map", "doc_001", "pat_001"),
        ("doctor_patient_map", "doc_001", "pat_002"),
        ("doctor_patient_map", "doc_002", "pat_001"),
        ("caregiver_patient_map", "cg_001", "pat_001"),
        ("caregiver_patient_map", "cg_001", "pat_002"),
    ]
    for table, provider_id, patient_id in relationships:
        col = "doctor_id" if "doctor" in table else "caregiver_id"
        try:
            conn.execute(
                f"INSERT OR IGNORE INTO {table} ({col}, patient_id) VALUES (?, ?)",
                (provider_id, patient_id)
            )
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    conn.close()


# ── Query helpers ──

def get_user_by_email(email: str) -> Optional[Dict]:
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE email = ? AND is_active = 1", (email,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: str) -> Optional[Dict]:
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id = ? AND is_active = 1", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_patients_for_doctor(doctor_id: str) -> List[Dict]:
    conn = get_db()
    rows = conn.execute("""
        SELECT u.* FROM users u
        JOIN doctor_patient_map dpm ON u.id = dpm.patient_id
        WHERE dpm.doctor_id = ? AND dpm.is_active = 1 AND u.is_active = 1
    """, (doctor_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_patients_for_caregiver(caregiver_id: str) -> List[Dict]:
    conn = get_db()
    rows = conn.execute("""
        SELECT u.* FROM users u
        JOIN caregiver_patient_map cpm ON u.id = cpm.patient_id
        WHERE cpm.caregiver_id = ? AND cpm.is_active = 1 AND u.is_active = 1
    """, (caregiver_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def can_access_patient(user_id: str, user_role: str, patient_id: str) -> bool:
    """RBAC check: can this user access this patient's data?"""
    if user_role == "patient":
        return user_id == patient_id
    if user_role == "doctor":
        conn = get_db()
        row = conn.execute(
            "SELECT 1 FROM doctor_patient_map WHERE doctor_id=? AND patient_id=? AND is_active=1",
            (user_id, patient_id)
        ).fetchone()
        conn.close()
        return row is not None
    if user_role == "caregiver":
        conn = get_db()
        row = conn.execute(
            "SELECT 1 FROM caregiver_patient_map WHERE caregiver_id=? AND patient_id=? AND is_active=1",
            (user_id, patient_id)
        ).fetchone()
        conn.close()
        return row is not None
    return False


def log_audit(user_id: str, action: str, target_id: str = "", details: str = ""):
    conn = get_db()
    conn.execute(
        "INSERT INTO audit_log (user_id, action, target_id, details) VALUES (?, ?, ?, ?)",
        (user_id, action, target_id, details)
    )
    conn.commit()
    conn.close()


def update_last_login(user_id: str):
    conn = get_db()
    conn.execute("UPDATE users SET last_login = ? WHERE id = ?", (time.time(), user_id))
    conn.commit()
    conn.close()


def get_emergency_contacts(user_id: str) -> List[Dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT id, name, phone, relationship FROM emergency_contacts WHERE user_id = ? ORDER BY created_at ASC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_emergency_contact(user_id: str, name: str, phone: str, relationship: str) -> str:
    import uuid
    contact_id = f"cnt_{uuid.uuid4().hex[:8]}"
    conn = get_db()
    conn.execute(
        "INSERT INTO emergency_contacts (id, user_id, name, phone, relationship) VALUES (?, ?, ?, ?, ?)",
        (contact_id, user_id, name, phone, relationship)
    )
    conn.commit()
    conn.close()
    return contact_id


def remove_emergency_contact(contact_id: str, user_id: str):
    conn = get_db()
    conn.execute("DELETE FROM emergency_contacts WHERE id = ? AND user_id = ?", (contact_id, user_id))
    conn.commit()
    conn.close()


def insert_past_vitals(patient_id: str, timestamp: float, hr: float, spo2: float, bp_sys: float, bp_dia: float, rr: float, temp: float, health_score: float = 85.0):
    conn = get_db()
    conn.execute("""
        INSERT INTO vitals_log (patient_id, timestamp, heart_rate, spo2, bp_systolic, bp_diastolic, resp_rate, temperature, health_score, mode)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'historical')
    """, (patient_id, timestamp, hr, spo2, bp_sys, bp_dia, rr, temp, health_score))
    conn.commit()
    conn.close()
