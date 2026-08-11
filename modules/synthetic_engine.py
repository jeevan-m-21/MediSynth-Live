"""
Medisynth Live – Synthetic Rare-Scenario Engine
Generates specialized rare medical scenarios for training and demonstration.
Now includes Sepsis and Panic Attack scenarios.
"""

import time
import math
import random
import numpy as np
from dataclasses import dataclass
from typing import Optional

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.simulation_engine import VitalReading


@dataclass
class SyntheticScenario:
    """Definition of a synthetic rare scenario."""
    name: str
    description: str
    duration_s: float
    severity: str  # "moderate", "severe", "critical"
    icon: str = "⚡"


# Pre-defined rare scenarios
SCENARIOS = {
    "cardiac_stress": SyntheticScenario(
        name="Cardiac Stress Event",
        description="Progressive cardiac stress with HR escalation and irregular rhythm",
        duration_s=30, severity="severe", icon="💔",
    ),
    "hypoxia": SyntheticScenario(
        name="Hypoxia Episode",
        description="Sudden oxygen desaturation simulating respiratory compromise",
        duration_s=25, severity="critical", icon="🫁",
    ),
    "sudden_anomaly": SyntheticScenario(
        name="Sudden Anomaly",
        description="Unexpected vital sign deviation — mixed pattern anomaly",
        duration_s=20, severity="moderate", icon="⚡",
    ),
    "bradycardia_event": SyntheticScenario(
        name="Bradycardia Event",
        description="Heart rate drops significantly below normal range",
        duration_s=25, severity="severe", icon="🐢",
    ),
    "sepsis": SyntheticScenario(
        name="Sepsis Progression",
        description="Fever + tachycardia + hypotension + tachypnea cascade",
        duration_s=40, severity="critical", icon="🦠",
    ),
    "panic_attack": SyntheticScenario(
        name="Panic Attack",
        description="Rapid HR spike + hyperventilation with normal SpO₂",
        duration_s=20, severity="moderate", icon="😰",
    ),
}


class SyntheticEngine:
    """Generates rare medical scenarios with realistic vital sign patterns."""

    def __init__(self):
        self.active_scenario: Optional[str] = None
        self.scenario_start: float = 0
        self.is_training_mode: bool = False

    def start_scenario(self, scenario_key: str) -> Optional[SyntheticScenario]:
        if scenario_key in SCENARIOS:
            self.active_scenario = scenario_key
            self.scenario_start = time.time()
            return SCENARIOS[scenario_key]
        return None

    def stop_scenario(self) -> None:
        self.active_scenario = None

    def is_active(self) -> bool:
        if self.active_scenario is None:
            return False
        elapsed = time.time() - self.scenario_start
        scenario = SCENARIOS.get(self.active_scenario)
        if scenario and elapsed > scenario.duration_s:
            self.active_scenario = None
            return False
        return True

    def get_active_scenario_info(self) -> Optional[SyntheticScenario]:
        if self.is_active() and self.active_scenario:
            return SCENARIOS.get(self.active_scenario)
        return None

    def generate_reading(self, base_hr: float = 70, base_spo2: float = 97.5,
                         base_bp_sys: float = 120, base_bp_dia: float = 80,
                         base_rr: float = 16, base_temp: float = 36.8) -> Optional[VitalReading]:
        if not self.is_active() or not self.active_scenario:
            return None

        elapsed = time.time() - self.scenario_start
        scenario = SCENARIOS[self.active_scenario]
        progress = min(1.0, elapsed / scenario.duration_s)

        generators = {
            "cardiac_stress": self._cardiac_stress,
            "hypoxia": self._hypoxia,
            "sudden_anomaly": self._sudden_anomaly,
            "bradycardia_event": self._bradycardia,
            "sepsis": self._sepsis,
            "panic_attack": self._panic_attack,
        }
        gen = generators.get(self.active_scenario)
        if not gen:
            return None

        hr, spo2, bp_sys, bp_dia, rr, temp = gen(elapsed, progress, base_hr, base_spo2,
                                                   base_bp_sys, base_bp_dia, base_rr, base_temp)

        # Clamp
        hr = max(30, min(200, hr))
        spo2 = max(70, min(100, spo2))
        bp_sys = max(60, min(240, bp_sys))
        bp_dia = max(30, min(150, bp_dia))
        bp_dia = min(bp_dia, bp_sys - 15)
        rr = max(4, min(45, rr))
        temp = max(34, min(42, temp))

        return VitalReading(
            timestamp=time.time(),
            heart_rate=round(hr, 1), spo2=round(spo2, 1),
            bp_systolic=round(bp_sys, 0), bp_diastolic=round(bp_dia, 0),
            respiratory_rate=round(rr, 1), temperature=round(temp, 1),
            mode=f"synthetic_{self.active_scenario}",
            is_synthetic=True,
        )

    def _cardiac_stress(self, elapsed, progress, bhr, bspo2, bbps, bbpd, brr, btemp):
        stress_curve = math.sin(math.pi * progress)
        hr = bhr + 60 * stress_curve + np.random.normal(0, 3)
        if progress > 0.4:
            hr += 10 * math.sin(elapsed * 5) * (progress - 0.4)
        spo2 = bspo2 - 4 * stress_curve + np.random.normal(0, 0.4)
        bp_sys = bbps + 30 * stress_curve + np.random.normal(0, 2)
        bp_dia = bbpd + 15 * stress_curve + np.random.normal(0, 1.5)
        rr = brr + 8 * stress_curve + np.random.normal(0, 0.5)
        temp = btemp + 0.3 * stress_curve + np.random.normal(0, 0.05)
        return hr, spo2, bp_sys, bp_dia, rr, temp

    def _hypoxia(self, elapsed, progress, bhr, bspo2, bbps, bbpd, brr, btemp):
        drop = 1 / (1 + math.exp(-12 * (progress - 0.3)))
        spo2 = bspo2 - 14 * drop + np.random.normal(0, 0.6)
        hr = bhr + 30 * drop + np.random.normal(0, 2)
        bp_sys = bbps + 10 * drop + np.random.normal(0, 2)
        bp_dia = bbpd + 5 * drop + np.random.normal(0, 1)
        rr = brr + 10 * drop + np.random.normal(0, 0.8)
        temp = btemp + np.random.normal(0, 0.05)
        return hr, spo2, bp_sys, bp_dia, rr, temp

    def _sudden_anomaly(self, elapsed, progress, bhr, bspo2, bbps, bbpd, brr, btemp):
        spike = 25 * math.sin(elapsed * 3) * progress
        noise = np.random.normal(0, 8 * progress)
        hr = bhr + spike + noise
        spo2 = bspo2 - 6 * progress * abs(math.sin(elapsed * 2)) + np.random.normal(0, 1)
        bp_sys = bbps + 15 * math.sin(elapsed * 2.5) * progress + np.random.normal(0, 3)
        bp_dia = bbpd + 8 * math.sin(elapsed * 2.5) * progress + np.random.normal(0, 2)
        rr = brr + 4 * progress * math.sin(elapsed * 1.5) + np.random.normal(0, 0.5)
        temp = btemp + np.random.normal(0, 0.1)
        return hr, spo2, bp_sys, bp_dia, rr, temp

    def _bradycardia(self, elapsed, progress, bhr, bspo2, bbps, bbpd, brr, btemp):
        drop = 1 / (1 + math.exp(-10 * (progress - 0.3)))
        hr = bhr - 30 * drop + np.random.normal(0, 2)
        spo2 = bspo2 - 2 * drop + np.random.normal(0, 0.3)
        bp_sys = bbps - 15 * drop + np.random.normal(0, 2)
        bp_dia = bbpd - 8 * drop + np.random.normal(0, 1)
        rr = brr - 3 * drop + np.random.normal(0, 0.3)
        temp = btemp - 0.2 * drop + np.random.normal(0, 0.03)
        return hr, spo2, bp_sys, bp_dia, rr, temp

    def _sepsis(self, elapsed, progress, bhr, bspo2, bbps, bbpd, brr, btemp):
        """Sepsis: fever + tachycardia + hypotension + tachypnea cascade."""
        ramp = 1 / (1 + math.exp(-6 * (progress - 0.3)))

        # Fever onset (rising temp)
        temp = btemp + 2.5 * ramp + np.random.normal(0, 0.1)

        # Compensatory tachycardia
        hr = bhr + 45 * ramp + np.random.normal(0, 3)
        hr += 5 * math.sin(elapsed * 1.5) * ramp  # Irregular

        # Hypotension (vasodilation)
        bp_sys = bbps - 35 * ramp + np.random.normal(0, 3)
        bp_dia = bbpd - 20 * ramp + np.random.normal(0, 2)

        # Tachypnea
        rr = brr + 12 * ramp + np.random.normal(0, 1)

        # SpO₂ drops late
        late_ramp = max(0, ramp - 0.4) / 0.6
        spo2 = bspo2 - 6 * late_ramp + np.random.normal(0, 0.5)

        return hr, spo2, bp_sys, bp_dia, rr, temp

    def _panic_attack(self, elapsed, progress, bhr, bspo2, bbps, bbpd, brr, btemp):
        """Panic attack: rapid HR + hyperventilation but normal SpO₂."""
        # Rapid onset, quick peak, then gradual resolution
        if progress < 0.4:
            intensity = progress / 0.4
        elif progress < 0.7:
            intensity = 1.0
        else:
            intensity = (1.0 - progress) / 0.3

        hr = bhr + 55 * intensity + np.random.normal(0, 4)
        spo2 = bspo2 + 0.5 * intensity + np.random.normal(0, 0.2)  # Actually slightly UP
        bp_sys = bbps + 25 * intensity + np.random.normal(0, 3)
        bp_dia = bbpd + 12 * intensity + np.random.normal(0, 2)
        rr = brr + 14 * intensity + np.random.normal(0, 1.5)  # Hyperventilation
        temp = btemp + 0.2 * intensity + np.random.normal(0, 0.05)

        return hr, spo2, bp_sys, bp_dia, rr, temp
