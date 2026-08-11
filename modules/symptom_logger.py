"""
Medisynth Live – Symptom Logger Module
Allows patients to log symptoms and correlates them with real-time vitals.
"""

import time
from dataclasses import dataclass, field
from typing import List, Optional


# ── Quick-tap symptom options ──
SYMPTOM_OPTIONS = [
    {"id": "dizzy", "label": "Dizzy", "icon": "🌀", "severity": "moderate"},
    {"id": "chest_pain", "label": "Chest Pain", "icon": "💔", "severity": "severe"},
    {"id": "shortness", "label": "Short of Breath", "icon": "😮‍💨", "severity": "severe"},
    {"id": "nausea", "label": "Nauseous", "icon": "🤢", "severity": "moderate"},
    {"id": "headache", "label": "Headache", "icon": "🤕", "severity": "mild"},
    {"id": "fatigue", "label": "Fatigue", "icon": "😴", "severity": "mild"},
    {"id": "palpitations", "label": "Palpitations", "icon": "💓", "severity": "moderate"},
    {"id": "anxiety", "label": "Anxious", "icon": "😰", "severity": "moderate"},
    {"id": "sweating", "label": "Sweating", "icon": "💦", "severity": "mild"},
    {"id": "pain", "label": "Body Pain", "icon": "🤒", "severity": "moderate"},
    {"id": "weakness", "label": "Weakness", "icon": "😵", "severity": "moderate"},
    {"id": "fine", "label": "Feeling Good", "icon": "😊", "severity": "none"},
]


@dataclass
class SymptomEntry:
    """A logged symptom event."""
    symptom_id: str
    label: str
    icon: str
    severity: str       # "none", "mild", "moderate", "severe"
    timestamp: float = field(default_factory=time.time)
    notes: str = ""
    # Vitals at time of symptom
    hr: Optional[float] = None
    spo2: Optional[float] = None
    bp_sys: Optional[float] = None
    bp_dia: Optional[float] = None
    rr: Optional[float] = None
    temp: Optional[float] = None
    health_score: Optional[float] = None


class SymptomLogger:
    """Manages patient symptom logging with vital correlation."""

    def __init__(self):
        self.entries: List[SymptomEntry] = []

    def log_symptom(self, symptom_id: str, notes: str = "",
                    processed=None, score_result=None) -> SymptomEntry:
        """Log a symptom with current vitals context."""
        opt = self._find_option(symptom_id)
        if not opt:
            return None

        entry = SymptomEntry(
            symptom_id=symptom_id,
            label=opt["label"],
            icon=opt["icon"],
            severity=opt["severity"],
            notes=notes,
            hr=processed.clean_hr if processed else None,
            spo2=processed.clean_spo2 if processed else None,
            bp_sys=processed.clean_bp_sys if processed else None,
            bp_dia=processed.clean_bp_dia if processed else None,
            rr=processed.clean_rr if processed else None,
            temp=processed.clean_temp if processed else None,
            health_score=score_result.score if score_result else None,
        )
        self.entries.append(entry)
        return entry

    def get_recent(self, count: int = 10) -> List[SymptomEntry]:
        """Get most recent symptom entries."""
        return sorted(self.entries, key=lambda e: e.timestamp, reverse=True)[:count]

    def get_todays_entries(self) -> List[SymptomEntry]:
        """Get all symptoms logged today."""
        import datetime
        today_start = datetime.datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        ).timestamp()
        return [e for e in self.entries if e.timestamp >= today_start]

    def get_correlation_summary(self) -> str:
        """Generate a plain-English correlation summary for the chatbot."""
        if not self.entries:
            return "No symptoms logged yet."

        recent = self.get_todays_entries()
        if not recent:
            return "No symptoms logged today."

        lines = []
        for entry in recent[-3:]:
            import datetime
            ts = datetime.datetime.fromtimestamp(entry.timestamp).strftime("%I:%M %p")
            vital_note = ""
            if entry.hr and entry.bp_sys:
                vital_note = f" (HR: {entry.hr:.0f}, BP: {entry.bp_sys:.0f}/{entry.bp_dia:.0f})"
            lines.append(f"• {entry.icon} {entry.label} at {ts}{vital_note}")

        return "Today's symptoms:\n" + "\n".join(lines)

    def get_severity_summary(self) -> dict:
        """Count symptoms by severity for today."""
        today = self.get_todays_entries()
        counts = {"severe": 0, "moderate": 0, "mild": 0, "none": 0}
        for e in today:
            counts[e.severity] = counts.get(e.severity, 0) + 1
        return counts

    def _find_option(self, symptom_id: str) -> Optional[dict]:
        for opt in SYMPTOM_OPTIONS:
            if opt["id"] == symptom_id:
                return opt
        return None
