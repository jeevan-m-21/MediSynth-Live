"""
Medisynth Live – Data Service Layer
Abstracts SQLite database calls into application-level models and standard functions.
"""

from backend.models.database import (
    get_user_by_id,
    get_user_by_email,
    get_patients_for_doctor,
    get_patients_for_caregiver,
    can_access_patient,
    get_emergency_contacts
)

def get_user(user_id: str):
    """Retrieve a user by their ID."""
    return get_user_by_id(user_id)

def get_patients_by_doctor(doctor_id: str):
    """Retrieve all patients assigned to a specific doctor."""
    return get_patients_for_doctor(doctor_id)

def get_patients_by_caregiver(caregiver_id: str):
    """Retrieve all patients assigned to a specific caregiver."""
    return get_patients_for_caregiver(caregiver_id)

def get_patient_by_user(user_id: str):
    """For a patient user, retrieve their patient profile. Currently identical to get_user."""
    user = get_user_by_id(user_id)
    if user and user.get("role") == "patient":
        return user
    return None

def check_access(provider_id: str, provider_role: str, patient_id: str) -> bool:
    """Verify if a provider is authorized to view a patient's data."""
    return can_access_patient(provider_id, provider_role, patient_id)
