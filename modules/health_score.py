"""
Medisynth Live – AI Health Score Engine
Computes real-time health score (0-100) with itemized breakdown across 8 categories,
including trend penalty and stability bonus.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


@dataclass
class ScoreBreakdownItem:
    category: str
    weight: float
    deduction: float
    reason: str
    icon: str


@dataclass
class HealthScoreResult:
    score: float
    status: str  # excellent, good, mild_risk, moderate_risk, critical
    status_label: str
    status_color: str
    status_emoji: str
    breakdown: List[ScoreBreakdownItem]
    trend_direction: str = "stable"  # improving, stable, worsening


class HealthScoreEngine:
    def __init__(self):
        self.score_history: List[float] = []

    def compute(self, hr: float, spo2: float,
                bp_sys: float = 120, bp_dia: float = 80,
                rr: float = 16, temp: float = 36.8,
                baseline_hr: Optional[float] = None,
                baseline_spo2: Optional[float] = None,
                confidence: float = 100.0,
                mode: str = "normal") -> HealthScoreResult:
        breakdown: List[ScoreBreakdownItem] = []
        total_deduction = 0.0

        # 1. Heart Rate (25%)
        hr_ded = self._hr_deduction(hr, mode)
        total_deduction += hr_ded
        reason = "Normal range" if hr_ded == 0 else self._hr_reason(hr, mode)
        breakdown.append(ScoreBreakdownItem("Heart Rate", config.SCORE_WEIGHT_HR, round(hr_ded, 1), reason, "💓"))

        # 2. SpO₂ (20%)
        spo2_ded = self._spo2_deduction(spo2)
        total_deduction += spo2_ded
        reason = "Normal range" if spo2_ded == 0 else self._spo2_reason(spo2)
        breakdown.append(ScoreBreakdownItem("Oxygen Saturation", config.SCORE_WEIGHT_SPO2, round(spo2_ded, 1), reason, "🫁"))

        # 3. Blood Pressure (15%)
        bp_ded = self._bp_deduction(bp_sys, bp_dia, mode)
        total_deduction += bp_ded
        reason = "Normal range" if bp_ded == 0 else self._bp_reason(bp_sys, bp_dia)
        breakdown.append(ScoreBreakdownItem("Blood Pressure", config.SCORE_WEIGHT_BP, round(bp_ded, 1), reason, "🩸"))

        # 4. Respiratory Rate (10%)
        rr_ded = self._rr_deduction(rr, mode)
        total_deduction += rr_ded
        reason = "Normal range" if rr_ded == 0 else f"RR {rr:.0f} breaths/min"
        breakdown.append(ScoreBreakdownItem("Respiratory Rate", config.SCORE_WEIGHT_RR, round(rr_ded, 1), reason, "🌬️"))

        # 5. Temperature (5%)
        temp_ded = self._temp_deduction(temp, mode)
        total_deduction += temp_ded
        reason = "Normal range" if temp_ded == 0 else f"Temp {temp:.1f}°C"
        breakdown.append(ScoreBreakdownItem("Body Temperature", config.SCORE_WEIGHT_TEMP, round(temp_ded, 1), reason, "🌡️"))

        # 6. Baseline Deviation (15%)
        dev_ded = 0.0
        if baseline_hr is not None and mode not in ("exercise", "recovery"):
            dev_ded = self._deviation_deduction(hr, spo2, baseline_hr, baseline_spo2 or 97.5)
        total_deduction += dev_ded
        reason = "Within baseline" if dev_ded == 0 else ("Expected for activity" if mode in ("exercise", "recovery") else "Deviation from baseline")
        breakdown.append(ScoreBreakdownItem("Baseline Deviation", config.SCORE_WEIGHT_DEVIATION, round(dev_ded, 1), reason, "📊"))

        # 7. Data Confidence (5%)
        conf_ded = self._confidence_deduction(confidence)
        total_deduction += conf_ded
        reason = "High confidence" if conf_ded == 0 else f"Confidence: {confidence:.0f}%"
        breakdown.append(ScoreBreakdownItem("Data Quality", config.SCORE_WEIGHT_CONFIDENCE, round(conf_ded, 1), reason, "📡"))

        # 8. Trend Penalty (5%)
        trend_ded = self._trend_penalty()
        total_deduction += trend_ded
        trend_dir = self._get_trend_direction()
        reason = "Stable" if trend_ded == 0 else f"Score {trend_dir}"
        breakdown.append(ScoreBreakdownItem("Trend Stability", config.SCORE_WEIGHT_TREND, round(trend_ded, 1), reason, "📈"))

        # Stability bonus: if ALL vitals normal, small bonus
        all_normal = (hr_ded == 0 and spo2_ded == 0 and bp_ded == 0 and rr_ded == 0 and temp_ded == 0)
        if all_normal and dev_ded == 0:
            total_deduction = max(0, total_deduction - 3)  # Small bonus

        score = max(0, min(100, 100 - total_deduction))

        # Track history
        self.score_history.append(score)
        if len(self.score_history) > config.HISTORY_MAX_POINTS:
            self.score_history = self.score_history[-config.HISTORY_MAX_POINTS:]

        status = self._get_status(score)
        status_info = config.SCORE_STATUS_MAP[status]

        return HealthScoreResult(
            score=round(score, 1), status=status,
            status_label=status_info["label"], status_color=status_info["color"],
            status_emoji=status_info["emoji"], breakdown=breakdown,
            trend_direction=trend_dir,
        )

    # ── Deduction Calculators ──

    def _hr_deduction(self, hr: float, mode: str = "normal") -> float:
        if mode == "exercise":
            if 50 <= hr <= 170: return 0
            if hr > 190 or hr < 40: return config.SCORE_HR_MAX_DEDUCTION
            if hr > 180: return 15
            if hr > 170: return 5
            return 3
        if mode == "recovery":
            if 50 <= hr <= 140: return 0
            if hr > 160: return 15
            if hr > 140: return 5
            return 3
        if mode == "sleep":
            if 40 <= hr <= 85: return 0
            if hr > 100: return 10
            if hr < 38: return 15
            return 3
        # Default resting thresholds
        if 55 <= hr <= 95:
            return 0
        if hr > 150 or hr < 40:
            return config.SCORE_HR_MAX_DEDUCTION
        if hr > 130:
            return 20
        if hr > 110:
            return 14
        if hr > 95:
            return 8
        if hr < 50:
            return 12
        return 4

    def _hr_reason(self, hr, mode="normal"):
        if mode in ("exercise", "recovery"):
            if hr > 170: return f"HR elevated even for {mode} at {hr:.0f} bpm"
            return f"HR {hr:.0f} bpm (expected during {mode})"
        if hr > 130: return f"HR critically elevated at {hr:.0f} bpm"
        if hr > 110: return f"HR significantly elevated at {hr:.0f} bpm"
        if hr > 95: return f"HR mildly elevated at {hr:.0f} bpm"
        if hr < 50: return f"HR below normal at {hr:.0f} bpm"
        return f"HR at {hr:.0f} bpm"

    def _spo2_deduction(self, spo2: float) -> float:
        if spo2 >= 95: return 0
        if spo2 < 85: return config.SCORE_SPO2_MAX_DEDUCTION
        if spo2 < 88: return 25
        if spo2 < 92: return 18
        return 8

    def _spo2_reason(self, spo2):
        if spo2 < 88: return f"SpO₂ critically low at {spo2:.1f}%"
        if spo2 < 92: return f"SpO₂ dangerously low at {spo2:.1f}%"
        return f"SpO₂ slightly below optimal at {spo2:.1f}%"

    def _bp_deduction(self, sys: float, dia: float, mode: str = "normal") -> float:
        if mode == "exercise":
            if sys <= 180 and dia <= 100: return 0
            if sys > 200: return config.SCORE_BP_MAX_DEDUCTION
            if sys > 180: return 8
            return 3
        if mode == "recovery":
            if sys <= 160 and dia <= 95: return 0
            if sys > 180: return 12
            return 5
        # Default resting
        if 90 <= sys <= 135 and 60 <= dia <= 85:
            return 0
        ded = 0
        if sys > 180 or dia > 120:
            ded = config.SCORE_BP_MAX_DEDUCTION
        elif sys > 160 or dia > 100:
            ded = 15
        elif sys > 140 or dia > 90:
            ded = 8
        elif sys < 85:
            ded = 15
        elif sys < 90:
            ded = 8
        return ded

    def _bp_reason(self, sys, dia):
        if sys > 160: return f"BP severely elevated {sys:.0f}/{dia:.0f}"
        if sys > 140: return f"BP elevated {sys:.0f}/{dia:.0f}"
        if sys < 90: return f"BP low {sys:.0f}/{dia:.0f}"
        return f"BP {sys:.0f}/{dia:.0f} mmHg"

    def _rr_deduction(self, rr: float, mode: str = "normal") -> float:
        if mode == "exercise":
            if 10 <= rr <= 35: return 0
            if rr > 40: return config.SCORE_RR_MAX_DEDUCTION
            return 3
        if mode == "recovery":
            if 10 <= rr <= 28: return 0
            return 3
        if 10 <= rr <= 22: return 0
        if rr > 30 or rr < 8: return config.SCORE_RR_MAX_DEDUCTION
        if rr > 24: return 8
        return 5

    def _temp_deduction(self, temp: float, mode: str = "normal") -> float:
        if mode == "exercise":
            if 36.0 <= temp <= 39.0: return 0
            if temp > 40.0: return config.SCORE_TEMP_MAX_DEDUCTION
            return 3
        if mode == "recovery":
            if 36.0 <= temp <= 38.5: return 0
            return 3
        if 36.0 <= temp <= 37.5: return 0
        if temp > 39.5 or temp < 35.0: return config.SCORE_TEMP_MAX_DEDUCTION
        if temp > 38.5: return 10
        if temp > 38.0: return 5
        if temp < 35.5: return 10
        return 3

    def _deviation_deduction(self, hr, spo2, bl_hr, bl_spo2) -> float:
        hr_dev = abs(hr - bl_hr) / max(bl_hr, 1) * 100
        spo2_dev = abs(spo2 - bl_spo2) / max(bl_spo2, 1) * 100
        max_dev = max(hr_dev, spo2_dev)
        if max_dev > config.DEVIATION_CRITICAL_PCT:
            return config.SCORE_DEVIATION_MAX_DEDUCTION
        if max_dev > config.DEVIATION_WARNING_PCT:
            return 12
        if max_dev > 8:
            return 5
        return 0

    def _confidence_deduction(self, confidence: float) -> float:
        if confidence >= 85: return 0
        if confidence < 50: return config.SCORE_CONFIDENCE_MAX_DEDUCTION
        if confidence < 70: return 7
        return 3

    def _trend_penalty(self) -> float:
        """Penalize rapidly worsening scores."""
        if len(self.score_history) < 5:
            return 0
        recent = self.score_history[-10:]
        if len(recent) < 3:
            return 0
        import numpy as np
        slope = np.polyfit(range(len(recent)), recent, 1)[0]
        if slope < -2:  # Rapidly deteriorating
            return min(config.SCORE_TREND_MAX_DEDUCTION, abs(slope) * 1.5)
        return 0

    def _get_trend_direction(self) -> str:
        if len(self.score_history) < 5:
            return "stable"
        recent = self.score_history[-8:]
        import numpy as np
        slope = np.polyfit(range(len(recent)), recent, 1)[0]
        if slope > 1:
            return "improving"
        if slope < -1:
            return "worsening"
        return "stable"

    @staticmethod
    def _get_status(score: float) -> str:
        if score >= config.SCORE_EXCELLENT_MIN:
            return "excellent"
        if score >= config.SCORE_GOOD_MIN:
            return "good"
        if score >= config.SCORE_MILD_RISK_MIN:
            return "mild_risk"
        if score >= config.SCORE_MODERATE_RISK_MIN:
            return "moderate_risk"
        return "critical"

    def reset(self):
        self.score_history.clear()
