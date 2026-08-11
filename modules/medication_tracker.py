"""
Medisynth Live – Medication Tracker Module
Tracks medication schedules, reminders, administration logging, and drug-vital correlation.
"""

import time
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Medication:
    """A prescribed medication."""
    id: str
    name: str
    dosage: str
    frequency: str          # "once_daily", "twice_daily", "three_daily", "as_needed"
    schedule_hours: List[int]   # e.g., [8, 20] for twice daily at 8AM and 8PM
    notes: str = ""
    category: str = "general"  # "cardiac", "bp", "diabetes", "pain", "general"
    added_ts: float = field(default_factory=time.time)


@dataclass
class MedicationLog:
    """A single medication administration event."""
    med_id: str
    med_name: str
    dosage: str
    taken_ts: float
    taken_by: str = "patient"   # "patient", "caretaker", "self"
    notes: str = ""
    # Vitals at time of administration (for drug-vital correlation)
    hr_at_time: Optional[float] = None
    spo2_at_time: Optional[float] = None
    bp_sys_at_time: Optional[float] = None
    bp_dia_at_time: Optional[float] = None


@dataclass
class MedicationReminder:
    """An upcoming medication reminder."""
    med_id: str
    med_name: str
    dosage: str
    due_hour: int
    is_overdue: bool = False
    minutes_until: int = 0


class MedicationTracker:
    """Manages medication schedules, reminders, and administration logging."""

    def __init__(self):
        self.medications: List[Medication] = []
        self.logs: List[MedicationLog] = []
        self._next_id = 1

    def add_medication(self, name: str, dosage: str, frequency: str,
                       schedule_hours: List[int], notes: str = "",
                       category: str = "general") -> Medication:
        """Add a new medication to the schedule."""
        med = Medication(
            id=f"med_{self._next_id}",
            name=name,
            dosage=dosage,
            frequency=frequency,
            schedule_hours=sorted(schedule_hours),
            notes=notes,
            category=category,
        )
        self._next_id += 1
        self.medications.append(med)
        return med

    def remove_medication(self, med_id: str):
        """Remove a medication from the schedule."""
        self.medications = [m for m in self.medications if m.id != med_id]

    def log_administration(self, med_id: str, taken_by: str = "patient",
                           notes: str = "", processed=None) -> MedicationLog:
        """Log that a medication was taken/administered."""
        med = self._find_med(med_id)
        if not med:
            return None
        log = MedicationLog(
            med_id=med_id,
            med_name=med.name,
            dosage=med.dosage,
            taken_ts=time.time(),
            taken_by=taken_by,
            notes=notes,
            hr_at_time=processed.clean_hr if processed else None,
            spo2_at_time=processed.clean_spo2 if processed else None,
            bp_sys_at_time=processed.clean_bp_sys if processed else None,
            bp_dia_at_time=processed.clean_bp_dia if processed else None,
        )
        self.logs.append(log)
        return log

    def get_upcoming_reminders(self, count: int = 5) -> List[MedicationReminder]:
        """Get upcoming medication reminders sorted by urgency."""
        import datetime
        now = datetime.datetime.now()
        current_hour = now.hour
        current_min = now.minute
        reminders = []

        for med in self.medications:
            for hour in med.schedule_hours:
                # Check if already taken today at this hour
                already_taken = self._taken_today(med.id, hour)
                if already_taken:
                    continue

                # Calculate minutes until due
                due_min = (hour - current_hour) * 60 - current_min
                is_overdue = due_min < 0

                reminders.append(MedicationReminder(
                    med_id=med.id,
                    med_name=med.name,
                    dosage=med.dosage,
                    due_hour=hour,
                    is_overdue=is_overdue,
                    minutes_until=due_min,
                ))

        # Sort: overdue first, then by minutes until due
        reminders.sort(key=lambda r: (not r.is_overdue, r.minutes_until))
        return reminders[:count]

    def get_todays_log(self) -> List[MedicationLog]:
        """Get all medication logs from today."""
        import datetime
        today_start = datetime.datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        ).timestamp()
        return [log for log in self.logs if log.taken_ts >= today_start]

    def get_adherence_rate(self, days: int = 7) -> float:
        """Calculate medication adherence rate over N days (0-100%)."""
        if not self.medications:
            return 100.0
        total_expected = sum(len(m.schedule_hours) for m in self.medications) * days
        if total_expected == 0:
            return 100.0
        actual = len(self.logs)
        return min(100.0, (actual / total_expected) * 100)

    def get_recent_logs(self, count: int = 10) -> List[MedicationLog]:
        """Get most recent medication logs."""
        return sorted(self.logs, key=lambda l: l.taken_ts, reverse=True)[:count]

    def get_drug_vital_data(self, med_id: str) -> List[dict]:
        """Get vitals recorded at time of medication administration for correlation."""
        return [
            {
                "timestamp": log.taken_ts,
                "hr": log.hr_at_time,
                "spo2": log.spo2_at_time,
                "bp_sys": log.bp_sys_at_time,
                "bp_dia": log.bp_dia_at_time,
            }
            for log in self.logs
            if log.med_id == med_id and log.hr_at_time is not None
        ]

    def get_medication_context_for_chatbot(self) -> str:
        """Generate medication context string for the AI chatbot."""
        if not self.medications:
            return "No medications currently tracked."
        lines = []
        for med in self.medications:
            times = ", ".join([f"{h}:00" for h in med.schedule_hours])
            lines.append(f"• {med.name} {med.dosage} — {med.frequency} at {times}")
        reminders = self.get_upcoming_reminders(3)
        if reminders:
            overdue = [r for r in reminders if r.is_overdue]
            if overdue:
                lines.append(f"\n⚠️ OVERDUE: {overdue[0].med_name} was due at {overdue[0].due_hour}:00")
        return "\n".join(lines)

    def _find_med(self, med_id: str) -> Optional[Medication]:
        for m in self.medications:
            if m.id == med_id:
                return m
        return None

    def _taken_today(self, med_id: str, target_hour: int) -> bool:
        """Check if a specific dose was already taken today."""
        import datetime
        today_start = datetime.datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        ).timestamp()
        for log in self.logs:
            if log.med_id == med_id and log.taken_ts >= today_start:
                log_hour = datetime.datetime.fromtimestamp(log.taken_ts).hour
                if abs(log_hour - target_hour) <= 1:  # within 1 hour tolerance
                    return True
        return False


# ── Category icons ──
CATEGORY_ICONS = {
    "cardiac": "❤️",
    "bp": "🩸",
    "diabetes": "💉",
    "pain": "💊",
    "general": "💊",
    "respiratory": "🫁",
    "neurological": "🧠",
    "antibiotic": "🦠",
}

FREQUENCY_LABELS = {
    "once_daily": "Once daily",
    "twice_daily": "Twice daily",
    "three_daily": "Three times daily",
    "four_daily": "Four times daily",
    "as_needed": "As needed",
}
