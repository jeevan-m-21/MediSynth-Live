"""
Medisynth Live – Personalized Baseline Engine
Captures and manages personalized vital sign baselines for deviation tracking.
"""

import time
from dataclasses import dataclass
from typing import List, Optional
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


@dataclass
class BaselineProfile:
    hr_mean: float
    hr_std: float
    spo2_mean: float
    spo2_std: float
    samples_count: int
    capture_duration_s: float
    captured_at: float


@dataclass
class DeviationReport:
    hr_deviation_pct: float
    spo2_deviation_pct: float
    hr_deviation_abs: float
    spo2_deviation_abs: float
    hr_status: str  # normal, elevated, high, critical
    spo2_status: str
    overall_status: str


class BaselineEngine:
    def __init__(self, capture_duration: float = config.BASELINE_CAPTURE_DURATION_S):
        self.capture_duration = capture_duration
        self.hr_samples: List[float] = []
        self.spo2_samples: List[float] = []
        self.capture_start: Optional[float] = None
        self.baseline: Optional[BaselineProfile] = None
        self.is_capturing: bool = False

    def start_capture(self):
        self.hr_samples.clear()
        self.spo2_samples.clear()
        self.capture_start = time.time()
        self.is_capturing = True
        self.baseline = None

    def add_sample(self, hr: float, spo2: float) -> bool:
        """Add a sample during baseline capture. Returns True when capture is complete."""
        if not self.is_capturing:
            return False
        self.hr_samples.append(hr)
        self.spo2_samples.append(spo2)

        elapsed = time.time() - (self.capture_start or time.time())
        if elapsed >= self.capture_duration and len(self.hr_samples) >= 5:
            self._finalize_baseline()
            return True
        return False

    def _finalize_baseline(self):
        self.baseline = BaselineProfile(
            hr_mean=round(float(np.mean(self.hr_samples)), 1),
            hr_std=round(float(np.std(self.hr_samples)), 2),
            spo2_mean=round(float(np.mean(self.spo2_samples)), 1),
            spo2_std=round(float(np.std(self.spo2_samples)), 2),
            samples_count=len(self.hr_samples),
            capture_duration_s=time.time() - (self.capture_start or time.time()),
            captured_at=time.time(),
        )
        self.is_capturing = False

    def get_capture_progress(self) -> float:
        if not self.is_capturing or not self.capture_start:
            return 1.0 if self.baseline else 0.0
        elapsed = time.time() - self.capture_start
        return min(1.0, elapsed / self.capture_duration)

    def compute_deviation(self, current_hr: float, current_spo2: float) -> Optional[DeviationReport]:
        if not self.baseline:
            return None
        bl = self.baseline
        hr_dev_abs = current_hr - bl.hr_mean
        spo2_dev_abs = current_spo2 - bl.spo2_mean
        hr_dev_pct = (hr_dev_abs / max(bl.hr_mean, 1)) * 100
        spo2_dev_pct = (spo2_dev_abs / max(bl.spo2_mean, 1)) * 100

        hr_status = self._classify_hr_deviation(abs(hr_dev_pct))
        spo2_status = self._classify_spo2_deviation(abs(spo2_dev_pct))

        overall = "normal"
        if hr_status in ("high", "critical") or spo2_status in ("high", "critical"):
            overall = "critical"
        elif hr_status == "elevated" or spo2_status == "elevated":
            overall = "elevated"

        return DeviationReport(
            hr_deviation_pct=round(hr_dev_pct, 1),
            spo2_deviation_pct=round(spo2_dev_pct, 1),
            hr_deviation_abs=round(hr_dev_abs, 1),
            spo2_deviation_abs=round(spo2_dev_abs, 1),
            hr_status=hr_status, spo2_status=spo2_status,
            overall_status=overall,
        )

    @staticmethod
    def _classify_hr_deviation(pct: float) -> str:
        if pct > config.DEVIATION_CRITICAL_PCT:
            return "critical"
        if pct > config.DEVIATION_WARNING_PCT:
            return "high"
        if pct > 8:
            return "elevated"
        return "normal"

    @staticmethod
    def _classify_spo2_deviation(pct: float) -> str:
        if pct > 5:
            return "critical"
        if pct > 3:
            return "high"
        if pct > 1.5:
            return "elevated"
        return "normal"

    def has_baseline(self) -> bool:
        return self.baseline is not None

    def reset(self):
        self.hr_samples.clear()
        self.spo2_samples.clear()
        self.capture_start = None
        self.baseline = None
        self.is_capturing = False
