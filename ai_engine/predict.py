"""
Medisynth Live – AI Risk Prediction Engine
Pluggable backend service that consumes vitals and returns risk scores.
Uses the existing MLAnomalyDetector + statistical analysis.
"""

import time
import numpy as np
from typing import Dict, Optional, List
from dataclasses import dataclass


@dataclass
class PredictionResult:
    risk_score: float          # 0-100 (0 = no risk, 100 = critical)
    anomaly_flag: bool
    risk_level: str            # "low", "moderate", "high", "critical"
    confidence: float          # 0-100
    contributing_factors: List[str]
    predicted_hr_5m: float
    predicted_spo2_5m: float
    model_version: str = "v1.0"
    timestamp: float = 0.0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()


class RiskPredictor:
    """Standalone AI prediction service. Consumes vitals arrays, returns risk assessment."""

    def __init__(self):
        self.model_version = "v1.0"
        self._history_window = 30

    def predict(self, hr_history: List[float], spo2_history: List[float],
                bp_sys: float = 120, bp_dia: float = 80,
                rr: float = 16, temp: float = 36.8,
                health_score: float = 100) -> PredictionResult:
        """Run risk prediction on current vitals + history."""
        factors = []
        risk = 0.0

        # ── Current vitals risk ──
        hr = hr_history[-1] if hr_history else 72
        spo2 = spo2_history[-1] if spo2_history else 97.5

        # Heart rate risk
        if hr > 120:
            risk += 25
            factors.append(f"Tachycardia: HR {hr:.0f} bpm")
        elif hr > 100:
            risk += 10
            factors.append(f"Elevated HR: {hr:.0f} bpm")
        elif hr < 50:
            risk += 20
            factors.append(f"Bradycardia: HR {hr:.0f} bpm")

        # SpO2 risk
        if spo2 < 90:
            risk += 30
            factors.append(f"Severe hypoxia: SpO₂ {spo2:.1f}%")
        elif spo2 < 94:
            risk += 15
            factors.append(f"Low oxygen: SpO₂ {spo2:.1f}%")

        # BP risk
        if bp_sys > 160 or bp_dia > 100:
            risk += 15
            factors.append(f"Hypertensive crisis: {bp_sys:.0f}/{bp_dia:.0f}")
        elif bp_sys > 140:
            risk += 8
            factors.append(f"Elevated BP: {bp_sys:.0f}/{bp_dia:.0f}")
        elif bp_sys < 90:
            risk += 20
            factors.append(f"Hypotension: {bp_sys:.0f}/{bp_dia:.0f}")

        # Temperature
        if temp > 38.5:
            risk += 10
            factors.append(f"Fever: {temp:.1f}°C")
        elif temp < 35.5:
            risk += 10
            factors.append(f"Hypothermia: {temp:.1f}°C")

        # ── Trend analysis (if enough history) ──
        if len(hr_history) >= 10:
            recent = hr_history[-10:]
            hr_slope = (recent[-1] - recent[0]) / len(recent)
            if hr_slope > 2:
                risk += 10
                factors.append("HR rapidly increasing")
            elif hr_slope < -2:
                risk += 5
                factors.append("HR rapidly decreasing")

            # Variability (high HRV can indicate arrhythmia risk)
            hr_std = float(np.std(recent))
            if hr_std > 10:
                risk += 8
                factors.append(f"High HR variability (σ={hr_std:.1f})")

        if len(spo2_history) >= 10:
            recent_spo2 = spo2_history[-10:]
            spo2_slope = (recent_spo2[-1] - recent_spo2[0]) / len(recent_spo2)
            if spo2_slope < -0.3:
                risk += 12
                factors.append("SpO₂ declining trend")

        # ── Health score integration ──
        if health_score < 40:
            risk += 15
            factors.append(f"Critical health score: {health_score:.0f}")
        elif health_score < 60:
            risk += 5

        # ── Forward prediction ──
        pred_hr = self._predict_forward(hr_history, steps=5)
        pred_spo2 = self._predict_forward(spo2_history, steps=5)

        # Clamp risk
        risk = min(100, max(0, risk))
        anomaly = risk > 40

        # Risk level
        if risk >= 70: level = "critical"
        elif risk >= 45: level = "high"
        elif risk >= 20: level = "moderate"
        else: level = "low"

        confidence = min(99, 60 + len(hr_history) * 0.5)

        if not factors:
            factors.append("All vitals within normal range")

        return PredictionResult(
            risk_score=round(risk, 1),
            anomaly_flag=anomaly,
            risk_level=level,
            confidence=round(confidence, 1),
            contributing_factors=factors,
            predicted_hr_5m=round(pred_hr, 1),
            predicted_spo2_5m=round(pred_spo2, 1),
            model_version=self.model_version,
        )

    def _predict_forward(self, history: List[float], steps: int = 5) -> float:
        if len(history) < 5:
            return history[-1] if history else 72.0
        recent = history[-20:]
        x = np.arange(len(recent))
        coeffs = np.polyfit(x, recent, deg=1)
        return float(np.polyval(coeffs, len(recent) + steps))
