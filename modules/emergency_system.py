"""
Medisynth Live – Emergency Alert & Notification System
Manages emergency contacts, alert triggers, and notification flow.
"""

import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


@dataclass
class EmergencyContact:
    name: str
    phone: str
    relationship: str
    id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"contact_{int(time.time() * 1000)}"


@dataclass
class AlertRecord:
    timestamp: float
    alert_type: str  # user_alert, contact_notify, confirmation
    health_score: float
    heart_rate: float
    spo2: float
    risk_level: str
    location: Optional[Dict[str, float]] = None
    contacts_notified: List[str] = field(default_factory=list)
    message: str = ""
    google_maps_link: str = ""
    step: int = 1  # 1=alert user, 2=notify contacts, 3=confirmed

class EmergencySystem:
    def __init__(self):
        self.alert_history: List[AlertRecord] = []
        self.last_alert_time: float = 0
        self.active_alert: Optional[AlertRecord] = None
        self.alert_step: int = 0  # 0=none, 1=user alerted, 2=contacts notified, 3=confirmed
        self.dismissed_until: float = 0  # Suppress re-trigger after dismiss

    @property
    def contacts(self) -> List[EmergencyContact]:
        import streamlit as st
        from backend.models.database import get_emergency_contacts
        patient_id = st.session_state.get("selected_patient_id")
        if not patient_id:
            return []
        db_contacts = get_emergency_contacts(patient_id)
        return [EmergencyContact(id=c["id"], name=c["name"], phone=c["phone"], relationship=c["relationship"]) for c in db_contacts]

    def add_contact(self, name: str, phone: str, relationship: str) -> Optional[EmergencyContact]:
        import streamlit as st
        from backend.models.database import add_emergency_contact
        patient_id = st.session_state.get("selected_patient_id")
        if not patient_id:
            return None
        contact_id = add_emergency_contact(patient_id, name, phone, relationship)
        return EmergencyContact(id=contact_id, name=name, phone=phone, relationship=relationship)

    def remove_contact(self, contact_id: str):
        import streamlit as st
        from backend.models.database import remove_emergency_contact
        patient_id = st.session_state.get("selected_patient_id")
        if not patient_id:
            return
        remove_emergency_contact(contact_id, patient_id)

    def should_trigger_alert(self, health_score: float, ai_status: str) -> bool:
        now = time.time()
        # Respect dismiss cooldown (user clicked Dismiss)
        if now < self.dismissed_until:
            return False
        if now - self.last_alert_time < config.ALERT_COOLDOWN_S:
            return False
        return health_score < config.EMERGENCY_SCORE_THRESHOLD or ai_status == "critical"

    def trigger_alert(self, health_score: float, hr: float, spo2: float,
                      risk_level: str, location: Optional[Dict[str, float]] = None) -> AlertRecord:
        maps_link = ""
        if location and "lat" in location and "lng" in location:
            maps_link = f"https://www.google.com/maps?q={location['lat']},{location['lng']}"

        risk_emoji = "🔴" if risk_level == "critical" else "🟡"
        message = (
            f"{risk_emoji} MEDISYNTH LIVE EMERGENCY ALERT\n\n"
            f"Patient requires immediate attention.\n\n"
            f"Health Score: {health_score:.0f}/100\n"
            f"Heart Rate: {hr:.0f} bpm\n"
            f"SpO₂: {spo2:.1f}%\n"
            f"Risk Level: {risk_level.upper()}\n"
        )
        if maps_link:
            message += f"\n📍 Location: {maps_link}"

        alert = AlertRecord(
            timestamp=time.time(), alert_type="user_alert",
            health_score=health_score, heart_rate=hr, spo2=spo2,
            risk_level=risk_level, location=location,
            contacts_notified=[], message=message,
            google_maps_link=maps_link, step=1,
        )
        self.active_alert = alert
        self.alert_step = 1
        self.last_alert_time = time.time()
        self.alert_history.append(alert)
        return alert

    def notify_contacts(self) -> List[str]:
        """Step 2: Notify emergency contacts. Returns list of notified names."""
        if not self.active_alert:
            return []
        notified = [c.name for c in self.contacts]
        self.active_alert.contacts_notified = notified
        self.active_alert.step = 2
        self.alert_step = 2
        return notified

    def confirm_alert(self) -> bool:
        """Step 3: Mark alert as confirmed/sent."""
        if not self.active_alert:
            return False
        self.active_alert.step = 3
        self.alert_step = 3
        return True

    def dismiss_alert(self):
        self.active_alert = None
        self.alert_step = 0
        # Suppress re-triggering for 120 seconds after manual dismiss
        self.dismissed_until = time.time() + 120

    def get_alert_history(self) -> List[AlertRecord]:
        return list(self.alert_history)

    def reset(self):
        self.alert_history.clear()
        self.last_alert_time = 0
        self.active_alert = None
        self.alert_step = 0
        self.dismissed_until = 0
