"""
Medisynth Live – Real-Time Vital Data Simulation Engine
Generates realistic time-series vital sign data (HR, SpO₂, BP, RR, Temp) across
Normal, Stress, Critical, Sleep, Exercise, and Recovery modes.
"""

import time
import math
import random
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


@dataclass
class VitalReading:
    """Single vital sign reading at a point in time."""
    timestamp: float
    heart_rate: float
    spo2: float
    bp_systolic: float = 120.0
    bp_diastolic: float = 80.0
    respiratory_rate: float = 16.0
    temperature: float = 36.8
    mode: str = "normal"
    is_synthetic: bool = False


class SimulationEngine:
    """
    Generates realistic vital sign data with natural physiological variation.
    Supports Normal, Stress, Critical, Sleep, Exercise, and Recovery modes.
    """

    def __init__(self):
        self.mode: str = "normal"
        self.mode_start_time: float = time.time()
        self.tick: int = 0
        self._phase_hr: float = random.uniform(0, 2 * math.pi)
        self._phase_spo2: float = random.uniform(0, 2 * math.pi)
        self._phase_bp: float = random.uniform(0, 2 * math.pi)
        self._phase_rr: float = random.uniform(0, 2 * math.pi)
        self._prev_hr: float = config.NORMAL_HR_BASE
        self._prev_spo2: float = config.NORMAL_SPO2_BASE
        self._prev_bp_sys: float = config.NORMAL_BP_SYS_BASE
        self._prev_bp_dia: float = config.NORMAL_BP_DIA_BASE
        self._prev_rr: float = config.NORMAL_RR_BASE
        self._prev_temp: float = config.NORMAL_TEMP_BASE

    def set_mode(self, mode: str) -> None:
        """Switch simulation mode with timestamp reset."""
        if mode in config.SIMULATION_MODES:
            # For recovery mode, capture current HR as start point
            if mode == "recovery":
                self._recovery_start_hr = self._prev_hr
                self._recovery_start_bp = self._prev_bp_sys
            self.mode = mode
            self.mode_start_time = time.time()

    def generate_reading(self) -> VitalReading:
        """Generate the next vital sign reading based on current mode."""
        self.tick += 1
        now = time.time()
        elapsed = now - self.mode_start_time

        generators = {
            "normal": self._generate_normal,
            "stress": self._generate_stress,
            "critical": self._generate_critical,
            "sleep": self._generate_sleep,
            "exercise": self._generate_exercise,
            "recovery": self._generate_recovery,
        }
        gen = generators.get(self.mode, self._generate_normal)
        hr, spo2, bp_sys, bp_dia, rr, temp = gen(elapsed)

        # Apply momentum smoothing — low alpha = gradual, visible transitions
        hr = self._smooth(self._prev_hr, hr, alpha=0.12)
        spo2 = self._smooth(self._prev_spo2, spo2, alpha=0.10)
        bp_sys = self._smooth(self._prev_bp_sys, bp_sys, alpha=0.10)
        bp_dia = self._smooth(self._prev_bp_dia, bp_dia, alpha=0.10)
        rr = self._smooth(self._prev_rr, rr, alpha=0.10)
        temp = self._smooth(self._prev_temp, temp, alpha=0.06)

        # Clamp to physiological limits
        hr = max(30, min(220, hr))
        spo2 = max(70, min(100, spo2))
        bp_sys = max(60, min(240, bp_sys))
        bp_dia = max(30, min(150, bp_dia))
        bp_dia = min(bp_dia, bp_sys - 15)  # Diastolic always less than systolic
        rr = max(4, min(45, rr))
        temp = max(34.0, min(42.0, temp))

        self._prev_hr = hr
        self._prev_spo2 = spo2
        self._prev_bp_sys = bp_sys
        self._prev_bp_dia = bp_dia
        self._prev_rr = rr
        self._prev_temp = temp

        return VitalReading(
            timestamp=now,
            heart_rate=round(hr, 1),
            spo2=round(spo2, 1),
            bp_systolic=round(bp_sys, 0),
            bp_diastolic=round(bp_dia, 0),
            respiratory_rate=round(rr, 1),
            temperature=round(temp, 1),
            mode=self.mode,
        )

    def _generate_normal(self, elapsed: float) -> tuple:
        """Normal mode: stable vitals with natural physiological variation."""
        rsa = 3.0 * math.sin(2 * math.pi * elapsed / 4.0 + self._phase_hr)
        drift = 2.0 * math.sin(2 * math.pi * elapsed / 60.0)
        hr = config.NORMAL_HR_BASE + rsa + drift + np.random.normal(0, 0.8)

        spo2_var = 0.3 * math.sin(2 * math.pi * elapsed / 8.0 + self._phase_spo2)
        spo2 = config.NORMAL_SPO2_BASE + spo2_var + np.random.normal(0, 0.15)

        bp_var = 3.0 * math.sin(2 * math.pi * elapsed / 12.0 + self._phase_bp)
        bp_sys = config.NORMAL_BP_SYS_BASE + bp_var + np.random.normal(0, 1.5)
        bp_dia = config.NORMAL_BP_DIA_BASE + bp_var * 0.5 + np.random.normal(0, 1.0)

        rr_var = 1.0 * math.sin(2 * math.pi * elapsed / 10.0 + self._phase_rr)
        rr = config.NORMAL_RR_BASE + rr_var + np.random.normal(0, 0.5)

        temp_var = 0.1 * math.sin(2 * math.pi * elapsed / 120.0)
        temp = config.NORMAL_TEMP_BASE + temp_var + np.random.normal(0, 0.05)

        return hr, spo2, bp_sys, bp_dia, rr, temp

    def _generate_stress(self, elapsed: float) -> tuple:
        """Stress mode: slow gradual HR increase, BP rise, slight SpO₂ dip.
        Uses a gentle linear ramp so each tick shows a visible small change."""
        # Linear ramp over ramp duration — NOT sigmoid, so early seconds show movement
        ramp = min(1.0, elapsed / config.STRESS_RAMP_DURATION_S)
        # Apply mild sigmoid only for final shaping
        ramp = ramp ** 0.7  # concave curve — faster start, slower finish

        target_hr = config.NORMAL_HR_BASE + (config.STRESS_HR_TARGET - config.NORMAL_HR_BASE) * ramp
        hr = target_hr + np.random.normal(0, 1.5) + 2.0 * math.sin(2 * math.pi * elapsed / 4.0)

        spo2 = config.NORMAL_SPO2_BASE - 2.0 * ramp + np.random.normal(0, 0.2)

        bp_sys = config.NORMAL_BP_SYS_BASE + (config.STRESS_BP_SYS_TARGET - config.NORMAL_BP_SYS_BASE) * ramp + np.random.normal(0, 1.5)
        bp_dia = config.NORMAL_BP_DIA_BASE + (config.STRESS_BP_DIA_TARGET - config.NORMAL_BP_DIA_BASE) * ramp + np.random.normal(0, 1.0)

        rr = config.NORMAL_RR_BASE + (config.STRESS_RR_TARGET - config.NORMAL_RR_BASE) * ramp + np.random.normal(0, 0.5)

        temp = config.NORMAL_TEMP_BASE + (config.STRESS_TEMP_TARGET - config.NORMAL_TEMP_BASE) * ramp + np.random.normal(0, 0.03)

        return hr, spo2, bp_sys, bp_dia, rr, temp

    def _generate_critical(self, elapsed: float) -> tuple:
        """Critical mode: gradual escalation over ~30s to full crisis.
        First 10s: mild increase visible. 10-20s: accelerating. 20-30s: full crisis."""
        # Slow linear ramp over 30 seconds so user sees gradual escalation
        ramp = min(1.0, elapsed / 30.0)
        # Power curve — starts slow, accelerates toward end (like real deterioration)
        ramp = ramp ** 1.5

        base_hr = config.NORMAL_HR_BASE + (config.CRITICAL_HR_MAX - config.NORMAL_HR_BASE) * ramp
        # Erratic oscillation grows with ramp
        erratic = config.CRITICAL_HR_ERRATIC_AMPLITUDE * ramp * math.sin(2 * math.pi * elapsed / 2.0)
        hr = base_hr + erratic + np.random.normal(0, 2.0 + 3.0 * ramp)

        spo2_target = config.CRITICAL_SPO2_MIN + random.uniform(0, 3)
        spo2 = config.NORMAL_SPO2_BASE - (config.NORMAL_SPO2_BASE - spo2_target) * ramp + np.random.normal(0, 0.3 + 0.5 * ramp)

        bp_sys = config.NORMAL_BP_SYS_BASE + (config.CRITICAL_BP_SYS_TARGET - config.NORMAL_BP_SYS_BASE) * ramp + np.random.normal(0, 2 + 2 * ramp)
        bp_dia = config.NORMAL_BP_DIA_BASE + (config.CRITICAL_BP_DIA_TARGET - config.NORMAL_BP_DIA_BASE) * ramp + np.random.normal(0, 1.5 + 1.5 * ramp)

        rr = config.NORMAL_RR_BASE + (config.CRITICAL_RR_TARGET - config.NORMAL_RR_BASE) * ramp + np.random.normal(0, 0.8)
        rr += 2.0 * math.sin(elapsed * 1.5) * ramp  # Irregular breathing grows

        temp = config.NORMAL_TEMP_BASE + (config.CRITICAL_TEMP_TARGET - config.NORMAL_TEMP_BASE) * ramp + np.random.normal(0, 0.05)

        return hr, spo2, bp_sys, bp_dia, rr, temp

    def _generate_sleep(self, elapsed: float) -> tuple:
        """Sleep mode: low HR, stable SpO₂, slow breathing, lower BP, slight temp drop."""
        ramp = min(1.0, 1 / (1 + math.exp(-6 * (elapsed / 20.0 - 0.5))))

        # Deep sleep oscillation (sleep cycles ~90min, simplified)
        sleep_cycle = 0.5 + 0.5 * math.sin(2 * math.pi * elapsed / 180.0)

        hr = config.SLEEP_HR_BASE - 3 * sleep_cycle + np.random.normal(0, 0.5)
        hr = config.NORMAL_HR_BASE + (hr - config.NORMAL_HR_BASE) * ramp

        spo2 = config.SLEEP_SPO2_BASE + np.random.normal(0, 0.1)
        spo2 = config.NORMAL_SPO2_BASE + (spo2 - config.NORMAL_SPO2_BASE) * ramp

        bp_sys = config.SLEEP_BP_SYS_BASE + np.random.normal(0, 1)
        bp_sys = config.NORMAL_BP_SYS_BASE + (bp_sys - config.NORMAL_BP_SYS_BASE) * ramp
        bp_dia = config.SLEEP_BP_DIA_BASE + np.random.normal(0, 0.8)
        bp_dia = config.NORMAL_BP_DIA_BASE + (bp_dia - config.NORMAL_BP_DIA_BASE) * ramp

        rr = config.SLEEP_RR_BASE + 1.0 * math.sin(2 * math.pi * elapsed / 6.0) + np.random.normal(0, 0.3)
        rr = config.NORMAL_RR_BASE + (rr - config.NORMAL_RR_BASE) * ramp

        temp = config.SLEEP_TEMP_BASE + np.random.normal(0, 0.03)
        temp = config.NORMAL_TEMP_BASE + (temp - config.NORMAL_TEMP_BASE) * ramp

        return hr, spo2, bp_sys, bp_dia, rr, temp

    def _generate_exercise(self, elapsed: float) -> tuple:
        """Exercise mode: high HR, elevated BP, rapid breathing, temperature rise."""
        ramp = min(1.0, 1 / (1 + math.exp(-8 * (elapsed / config.EXERCISE_RAMP_DURATION_S - 0.5))))

        hr = config.NORMAL_HR_BASE + (config.EXERCISE_HR_TARGET - config.NORMAL_HR_BASE) * ramp
        hr += 5 * math.sin(2 * math.pi * elapsed / 2.0)  # Rhythmic exertion
        hr += np.random.normal(0, 3)

        spo2 = config.EXERCISE_SPO2_BASE + np.random.normal(0, 0.3)

        bp_sys = config.NORMAL_BP_SYS_BASE + (config.EXERCISE_BP_SYS_TARGET - config.NORMAL_BP_SYS_BASE) * ramp + np.random.normal(0, 3)
        bp_dia = config.NORMAL_BP_DIA_BASE + (config.EXERCISE_BP_DIA_TARGET - config.NORMAL_BP_DIA_BASE) * ramp * 0.3 + np.random.normal(0, 1)

        rr = config.NORMAL_RR_BASE + (config.EXERCISE_RR_TARGET - config.NORMAL_RR_BASE) * ramp + np.random.normal(0, 1)

        temp = config.NORMAL_TEMP_BASE + (config.EXERCISE_TEMP_TARGET - config.NORMAL_TEMP_BASE) * ramp * 0.7 + np.random.normal(0, 0.05)

        return hr, spo2, bp_sys, bp_dia, rr, temp

    def _generate_recovery(self, elapsed: float) -> tuple:
        """Recovery mode: HR decays exponentially back to normal."""
        start_hr = getattr(self, '_recovery_start_hr', config.RECOVERY_HR_START)
        start_bp = getattr(self, '_recovery_start_bp', config.NORMAL_BP_SYS_BASE + 30)

        decay = math.exp(-0.693 * elapsed / config.RECOVERY_DECAY_HALF_LIFE_S)
        hr = config.NORMAL_HR_BASE + (start_hr - config.NORMAL_HR_BASE) * decay + np.random.normal(0, 1)

        spo2 = config.NORMAL_SPO2_BASE + 0.5 * (1 - decay) + np.random.normal(0, 0.15)

        bp_sys = config.NORMAL_BP_SYS_BASE + (start_bp - config.NORMAL_BP_SYS_BASE) * decay + np.random.normal(0, 1.5)
        bp_dia = config.NORMAL_BP_DIA_BASE + 5 * decay + np.random.normal(0, 1)

        rr = config.NORMAL_RR_BASE + 6 * decay + np.random.normal(0, 0.5)

        temp = config.NORMAL_TEMP_BASE + 0.8 * decay + np.random.normal(0, 0.03)

        return hr, spo2, bp_sys, bp_dia, rr, temp

    @staticmethod
    def _smooth(prev: float, current: float, alpha: float = 0.3) -> float:
        """Exponential moving average for smooth transitions."""
        return prev * (1 - alpha) + current * alpha
