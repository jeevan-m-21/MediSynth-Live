"""
Medisynth Live – Session Analytics Engine
Tracks session statistics, event timeline, score history,
and generates downloadable HTML health reports.
"""

import time
import datetime
from dataclasses import dataclass, field
from typing import List, Optional, Dict
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


@dataclass
class VitalStats:
    """Statistics for a single vital sign."""
    name: str
    unit: str
    min_val: float
    max_val: float
    mean_val: float
    std_val: float
    current: float
    samples: int


@dataclass
class TimelineEvent:
    """A single event on the monitoring timeline."""
    timestamp: float
    event_type: str  # detection, mode_change, alert, baseline
    severity: str
    title: str
    detail: str


@dataclass
class SessionSummary:
    """Complete session analytics summary."""
    session_id: str
    start_time: float
    duration_s: float
    total_readings: int
    vital_stats: List[VitalStats]
    timeline: List[TimelineEvent]
    score_history: List[float]
    score_min: float
    score_max: float
    score_mean: float
    detections_count: int
    critical_events: int
    mode_changes: int
    overall_assessment: str


class AnalyticsEngine:
    """Tracks and analyzes an entire monitoring session."""

    def __init__(self):
        self.session_id = f"MS-{int(time.time()) % 100000:05d}"
        self.start_time = time.time()
        self.total_readings = 0
        self.mode_changes = 0
        self.detections_count = 0
        self.critical_events = 0
        self.current_mode = "normal"

        # Vital histories
        self.hr_all: List[float] = []
        self.spo2_all: List[float] = []
        self.bp_sys_all: List[float] = []
        self.bp_dia_all: List[float] = []
        self.rr_all: List[float] = []
        self.temp_all: List[float] = []
        self.score_all: List[float] = []

        # Event timeline
        self.timeline: List[TimelineEvent] = []

    def record_reading(self, hr, spo2, bp_sys=120, bp_dia=80, rr=16, temp=36.8, score=100):
        self.total_readings += 1
        self.hr_all.append(hr)
        self.spo2_all.append(spo2)
        self.bp_sys_all.append(bp_sys)
        self.bp_dia_all.append(bp_dia)
        self.rr_all.append(rr)
        self.temp_all.append(temp)
        self.score_all.append(score)

    def record_detection(self, condition: str, severity: str, detail: str = ""):
        self.detections_count += 1
        if severity == "critical":
            self.critical_events += 1
        self.timeline.append(TimelineEvent(
            timestamp=time.time(), event_type="detection",
            severity=severity, title=condition, detail=detail,
        ))

    def record_mode_change(self, new_mode: str):
        if new_mode != self.current_mode:
            self.mode_changes += 1
            self.timeline.append(TimelineEvent(
                timestamp=time.time(), event_type="mode_change",
                severity="info", title=f"Mode → {new_mode.upper()}",
                detail=f"Switched from {self.current_mode} to {new_mode}",
            ))
            self.current_mode = new_mode

    def record_alert(self, score: float, detail: str = ""):
        self.timeline.append(TimelineEvent(
            timestamp=time.time(), event_type="alert",
            severity="critical", title=f"Emergency Alert (Score: {score:.0f})",
            detail=detail,
        ))

    def get_elapsed(self) -> float:
        return time.time() - self.start_time

    def get_elapsed_str(self) -> str:
        elapsed = self.get_elapsed()
        mins, secs = divmod(int(elapsed), 60)
        hrs, mins = divmod(mins, 60)
        if hrs > 0:
            return f"{hrs}h {mins}m {secs}s"
        return f"{mins}m {secs}s"

    def _compute_stats(self, data: List[float], name: str, unit: str) -> VitalStats:
        if not data:
            return VitalStats(name, unit, 0, 0, 0, 0, 0, 0)
        arr = np.array(data)
        return VitalStats(
            name=name, unit=unit,
            min_val=round(float(arr.min()), 1),
            max_val=round(float(arr.max()), 1),
            mean_val=round(float(arr.mean()), 1),
            std_val=round(float(arr.std()), 2),
            current=round(float(arr[-1]), 1),
            samples=len(data),
        )

    def get_summary(self) -> SessionSummary:
        scores = self.score_all or [100]
        return SessionSummary(
            session_id=self.session_id,
            start_time=self.start_time,
            duration_s=self.get_elapsed(),
            total_readings=self.total_readings,
            vital_stats=[
                self._compute_stats(self.hr_all, "Heart Rate", "bpm"),
                self._compute_stats(self.spo2_all, "SpO₂", "%"),
                self._compute_stats(self.bp_sys_all, "BP Systolic", "mmHg"),
                self._compute_stats(self.bp_dia_all, "BP Diastolic", "mmHg"),
                self._compute_stats(self.rr_all, "Respiratory Rate", "br/min"),
                self._compute_stats(self.temp_all, "Temperature", "°C"),
            ],
            timeline=list(self.timeline[-50:]),
            score_history=list(scores[-100:]),
            score_min=round(min(scores), 1),
            score_max=round(max(scores), 1),
            score_mean=round(float(np.mean(scores)), 1),
            detections_count=self.detections_count,
            critical_events=self.critical_events,
            mode_changes=self.mode_changes,
            overall_assessment=self._assess_session(scores),
        )

    def _assess_session(self, scores: List[float]) -> str:
        if not scores:
            return "No data available"
        avg = np.mean(scores)
        min_s = min(scores)
        if min_s < 20:
            return "Critical events detected during this session. Immediate clinical review recommended."
        if min_s < 40:
            return "High-risk events occurred. Follow-up assessment strongly recommended."
        if avg < 60:
            return "Elevated risk detected. Consider preventive measures."
        if avg < 75:
            return "Mostly stable with some deviations. Continue monitoring."
        if avg >= 90:
            return "Excellent health indicators throughout the session."
        return "Good overall health with minor fluctuations."

    def generate_csv(self) -> str:
        """Generate CSV data string for download."""
        lines = ["Timestamp,Heart Rate,SpO2,BP Systolic,BP Diastolic,Resp Rate,Temperature,Score"]
        n = min(len(self.hr_all), len(self.spo2_all), len(self.bp_sys_all),
                len(self.bp_dia_all), len(self.rr_all), len(self.temp_all), len(self.score_all))
        for i in range(n):
            ts = datetime.datetime.fromtimestamp(self.start_time + i * config.UPDATE_INTERVAL_S).isoformat()
            lines.append(f"{ts},{self.hr_all[i]},{self.spo2_all[i]},{self.bp_sys_all[i]},"
                         f"{self.bp_dia_all[i]},{self.rr_all[i]},{self.temp_all[i]},{self.score_all[i]:.1f}")
        return "\n".join(lines)

    def generate_html_report(self) -> str:
        """Generate a downloadable HTML health report."""
        summary = self.get_summary()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        duration = self.get_elapsed_str()

        stats_rows = ""
        for vs in summary.vital_stats:
            stats_rows += f"""
            <tr>
                <td>{vs.name}</td><td>{vs.current} {vs.unit}</td>
                <td>{vs.min_val}</td><td>{vs.max_val}</td>
                <td>{vs.mean_val}</td><td>{vs.std_val}</td>
            </tr>"""

        timeline_rows = ""
        for ev in reversed(summary.timeline[-20:]):
            ts = datetime.datetime.fromtimestamp(ev.timestamp).strftime("%H:%M:%S")
            sev_color = "#ff4757" if ev.severity == "critical" else "#ffb347" if ev.severity == "warning" else "#00d4aa"
            timeline_rows += f"""
            <tr>
                <td>{ts}</td>
                <td><span style="color:{sev_color}; font-weight:600;">●</span> {ev.severity.upper()}</td>
                <td>{ev.title}</td><td>{ev.detail}</td>
            </tr>"""

        score_color = "#00d4aa" if summary.score_mean >= 80 else "#ffb347" if summary.score_mean >= 50 else "#ff4757"

        return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<title>Medisynth Live Health Report – {summary.session_id}</title>
<style>
    body {{ font-family: 'Segoe UI', sans-serif; background: #0a0e1a; color: #e8eaf6; padding: 40px; }}
    .header {{ text-align: center; margin-bottom: 40px; }}
    .header h1 {{ color: #00d4aa; margin: 0; font-size: 2rem; }}
    .header p {{ color: #7986cb; }}
    .card {{ background: rgba(15,20,40,0.8); border: 1px solid rgba(255,255,255,0.08);
             border-radius: 16px; padding: 24px; margin-bottom: 24px; }}
    .card h2 {{ color: #a78bfa; font-size: 1.1rem; text-transform: uppercase; letter-spacing: 1.5px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.06); font-size: 0.9rem; }}
    th {{ color: #7986cb; font-weight: 600; }}
    .score-big {{ font-size: 4rem; font-weight: 900; color: {score_color}; text-align: center; }}
    .kpi-row {{ display: flex; gap: 16px; flex-wrap: wrap; }}
    .kpi {{ flex: 1; min-width: 140px; text-align: center; padding: 16px;
            background: rgba(255,255,255,0.03); border-radius: 12px; }}
    .kpi .num {{ font-size: 1.6rem; font-weight: 800; color: #e8eaf6; }}
    .kpi .label {{ font-size: 0.75rem; color: #7986cb; text-transform: uppercase; letter-spacing: 1px; }}
    .footer {{ text-align: center; color: #4a5568; font-size: 0.8rem; margin-top: 40px; }}
    @media print {{ body {{ background: white; color: #333; }} .card {{ border-color: #ddd; background: #f9f9f9; }} }}
</style></head><body>

<div class="header">
    <h1>🫀 Medisynth Live — Health Report</h1>
    <p>Session {summary.session_id} • Generated {now} • Duration: {duration}</p>
</div>

<div class="card">
    <h2>📊 Session Overview</h2>
    <div class="kpi-row">
        <div class="kpi"><div class="num">{summary.total_readings}</div><div class="label">Total Readings</div></div>
        <div class="kpi"><div class="num" style="color:{score_color};">{summary.score_mean:.0f}</div><div class="label">Avg Score</div></div>
        <div class="kpi"><div class="num">{summary.detections_count}</div><div class="label">Detections</div></div>
        <div class="kpi"><div class="num" style="color:#ff4757;">{summary.critical_events}</div><div class="label">Critical Events</div></div>
        <div class="kpi"><div class="num">{summary.mode_changes}</div><div class="label">Mode Changes</div></div>
    </div>
</div>

<div class="card">
    <h2>🩺 Overall Assessment</h2>
    <p style="font-size:1.1rem; line-height:1.6;">{summary.overall_assessment}</p>
    <p>Score Range: <strong>{summary.score_min:.0f}</strong> – <strong>{summary.score_max:.0f}</strong>
       (Mean: <strong>{summary.score_mean:.0f}</strong>)</p>
</div>

<div class="card">
    <h2>🏥 Vital Sign Statistics</h2>
    <table>
        <tr><th>Vital Sign</th><th>Current</th><th>Min</th><th>Max</th><th>Mean</th><th>Std Dev</th></tr>
        {stats_rows}
    </table>
</div>

<div class="card">
    <h2>📋 Event Timeline (Recent)</h2>
    <table>
        <tr><th>Time</th><th>Severity</th><th>Event</th><th>Detail</th></tr>
        {timeline_rows if timeline_rows else '<tr><td colspan="4" style="color:#7986cb;">No events recorded</td></tr>'}
    </table>
</div>

<div class="footer">
    <p>This report is auto-generated by Medisynth Live AI Health Monitoring System.<br>
    Not a substitute for professional medical advice. Consult your healthcare provider for clinical decisions.</p>
</div>

</body></html>"""

    def reset(self):
        self.__init__()
