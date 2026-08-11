"""
Medisynth Live – Care Log & Shift Notes Module
For caretakers: log activities, tasks, and shift handoffs.
"""
import time
from dataclasses import dataclass, field
from typing import List, Optional

CARE_ACTIVITIES = [
    {"id": "medication", "label": "Gave Medication", "icon": "💊", "category": "medical"},
    {"id": "vitals_check", "label": "Vitals Check", "icon": "🩺", "category": "medical"},
    {"id": "fed", "label": "Fed / Meal", "icon": "🍽️", "category": "daily"},
    {"id": "water", "label": "Hydration", "icon": "💧", "category": "daily"},
    {"id": "bathroom", "label": "Bathroom", "icon": "🚻", "category": "daily"},
    {"id": "turned", "label": "Repositioned", "icon": "🔄", "category": "care"},
    {"id": "bandage", "label": "Wound Care", "icon": "🩹", "category": "medical"},
    {"id": "exercise", "label": "Light Exercise", "icon": "🚶", "category": "activity"},
    {"id": "sleep", "label": "Sleeping", "icon": "😴", "category": "rest"},
    {"id": "awake", "label": "Woke Up", "icon": "☀️", "category": "rest"},
    {"id": "visitor", "label": "Visitor", "icon": "👥", "category": "social"},
    {"id": "observation", "label": "Observation", "icon": "📝", "category": "medical"},
]

@dataclass
class CareEntry:
    activity_id: str
    label: str
    icon: str
    category: str
    timestamp: float = field(default_factory=time.time)
    notes: str = ""
    logged_by: str = "caretaker"
    hr: Optional[float] = None
    spo2: Optional[float] = None
    bp_sys: Optional[float] = None
    bp_dia: Optional[float] = None
    health_score: Optional[float] = None

@dataclass
class TaskItem:
    id: str
    title: str
    due_hour: int
    is_done: bool = False
    done_ts: Optional[float] = None
    notes: str = ""
    assigned_by: str = "doctor"
    created_ts: float = field(default_factory=time.time)

class CareLog:
    def __init__(self):
        self.entries: List[CareEntry] = []
        self.tasks: List[TaskItem] = []
        self._task_id = 1

    def log_activity(self, activity_id: str, notes: str = "",
                     logged_by: str = "caretaker",
                     processed=None, score_result=None) -> Optional[CareEntry]:
        opt = next((a for a in CARE_ACTIVITIES if a["id"] == activity_id), None)
        if not opt:
            return None
        entry = CareEntry(
            activity_id=activity_id, label=opt["label"], icon=opt["icon"],
            category=opt["category"], notes=notes, logged_by=logged_by,
            hr=processed.clean_hr if processed else None,
            spo2=processed.clean_spo2 if processed else None,
            bp_sys=processed.clean_bp_sys if processed else None,
            bp_dia=processed.clean_bp_dia if processed else None,
            health_score=score_result.score if score_result else None,
        )
        self.entries.append(entry)
        return entry

    def add_task(self, title: str, due_hour: int, assigned_by: str = "doctor") -> TaskItem:
        task = TaskItem(id=f"task_{self._task_id}", title=title, due_hour=due_hour, assigned_by=assigned_by)
        self._task_id += 1
        self.tasks.append(task)
        return task

    def complete_task(self, task_id: str, notes: str = ""):
        for t in self.tasks:
            if t.id == task_id:
                t.is_done = True
                t.done_ts = time.time()
                t.notes = notes
                return True
        return False

    def get_pending_tasks(self) -> List[TaskItem]:
        return sorted([t for t in self.tasks if not t.is_done], key=lambda t: t.due_hour)

    def get_todays_entries(self) -> List[CareEntry]:
        import datetime
        start = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        return [e for e in self.entries if e.timestamp >= start]

    def get_recent_entries(self, count: int = 10) -> List[CareEntry]:
        return sorted(self.entries, key=lambda e: e.timestamp, reverse=True)[:count]

    def generate_shift_report(self) -> str:
        import datetime
        todays = self.get_todays_entries()
        lines = ["MEDISYNTH LIVE – SHIFT REPORT", datetime.datetime.now().strftime("%B %d, %Y — %I:%M %p"), ""]
        lines.append(f"ACTIVITIES ({len(todays)} entries)")
        for e in todays:
            ts = datetime.datetime.fromtimestamp(e.timestamp).strftime("%H:%M")
            n = f" — {e.notes}" if e.notes else ""
            lines.append(f"  {ts}  {e.icon} {e.label}{n}")
        pending = self.get_pending_tasks()
        done = [t for t in self.tasks if t.is_done]
        lines.append(f"\nTASKS ({len(done)} done, {len(pending)} pending)")
        for t in done:
            ts = datetime.datetime.fromtimestamp(t.done_ts).strftime("%H:%M") if t.done_ts else ""
            lines.append(f"  ✔ {t.title} (done {ts})")
        for t in pending:
            lines.append(f"  ○ {t.title} (due {t.due_hour}:00)")
        return "\n".join(lines)
