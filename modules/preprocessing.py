"""
Medisynth Live – Data Preprocessing & Reliability Layer
Noise filtering, Z-score outlier rejection, weighted moving average smoothing,
and data confidence scoring for all 5 vital signs.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Tuple
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


@dataclass
class ProcessedData:
    clean_hr: float
    clean_spo2: float
    clean_bp_sys: float
    clean_bp_dia: float
    clean_rr: float
    clean_temp: float
    raw_hr: float
    raw_spo2: float
    raw_bp_sys: float
    raw_bp_dia: float
    raw_rr: float
    raw_temp: float
    confidence: float
    hr_smoothed_history: List[float]
    spo2_smoothed_history: List[float]
    outlier_detected: bool
    noise_level: float


class PreprocessingPipeline:
    def __init__(self, window_size: int = config.SMOOTHING_WINDOW):
        self.window_size = window_size
        self.hr_buffer: List[float] = []
        self.spo2_buffer: List[float] = []
        self.bp_sys_buffer: List[float] = []
        self.bp_dia_buffer: List[float] = []
        self.rr_buffer: List[float] = []
        self.temp_buffer: List[float] = []
        self.hr_smoothed: List[float] = []
        self.spo2_smoothed: List[float] = []
        self.outlier_count: int = 0
        self.total_count: int = 0

    def process(self, raw_hr: float, raw_spo2: float,
                raw_bp_sys: float = 120, raw_bp_dia: float = 80,
                raw_rr: float = 16, raw_temp: float = 36.8) -> ProcessedData:
        self.total_count += 1

        # Outlier rejection
        hr_clean, hr_out = self._reject_outlier(raw_hr, self.hr_buffer)
        spo2_clean, spo2_out = self._reject_outlier(raw_spo2, self.spo2_buffer)
        bp_sys_clean, bp_sys_out = self._reject_outlier(raw_bp_sys, self.bp_sys_buffer)
        bp_dia_clean, bp_dia_out = self._reject_outlier(raw_bp_dia, self.bp_dia_buffer)
        rr_clean, rr_out = self._reject_outlier(raw_rr, self.rr_buffer)
        temp_clean, temp_out = self._reject_outlier(raw_temp, self.temp_buffer, z_thresh=2.5)

        is_outlier = hr_out or spo2_out or bp_sys_out
        if is_outlier:
            self.outlier_count += 1

        # Buffer management
        max_pts = config.HISTORY_MAX_POINTS
        for buf, val in [(self.hr_buffer, hr_clean), (self.spo2_buffer, spo2_clean),
                         (self.bp_sys_buffer, bp_sys_clean), (self.bp_dia_buffer, bp_dia_clean),
                         (self.rr_buffer, rr_clean), (self.temp_buffer, temp_clean)]:
            buf.append(val)
            if len(buf) > max_pts:
                del buf[:-max_pts]

        # Smoothing
        hr_smooth = self._moving_average(self.hr_buffer)
        spo2_smooth = self._moving_average(self.spo2_buffer)
        bp_sys_smooth = self._moving_average(self.bp_sys_buffer)
        bp_dia_smooth = self._moving_average(self.bp_dia_buffer)
        rr_smooth = self._moving_average(self.rr_buffer)
        temp_smooth = self._moving_average(self.temp_buffer)

        self.hr_smoothed.append(hr_smooth)
        self.spo2_smoothed.append(spo2_smooth)
        if len(self.hr_smoothed) > max_pts:
            self.hr_smoothed = self.hr_smoothed[-max_pts:]
            self.spo2_smoothed = self.spo2_smoothed[-max_pts:]

        noise_level = self._estimate_noise()
        confidence = self._compute_confidence(noise_level, is_outlier)

        return ProcessedData(
            clean_hr=round(hr_smooth, 1), clean_spo2=round(spo2_smooth, 1),
            clean_bp_sys=round(bp_sys_smooth, 0), clean_bp_dia=round(bp_dia_smooth, 0),
            clean_rr=round(rr_smooth, 1), clean_temp=round(temp_smooth, 1),
            raw_hr=round(raw_hr, 1), raw_spo2=round(raw_spo2, 1),
            raw_bp_sys=round(raw_bp_sys, 0), raw_bp_dia=round(raw_bp_dia, 0),
            raw_rr=round(raw_rr, 1), raw_temp=round(raw_temp, 1),
            confidence=round(confidence, 1),
            hr_smoothed_history=list(self.hr_smoothed),
            spo2_smoothed_history=list(self.spo2_smoothed),
            outlier_detected=is_outlier, noise_level=round(noise_level, 3),
        )

    def _reject_outlier(self, value: float, buffer: List[float], z_thresh: float = None) -> Tuple[float, bool]:
        z_thresh = z_thresh or config.OUTLIER_Z_THRESHOLD
        if len(buffer) < 3:
            return value, False
        recent = buffer[-min(20, len(buffer)):]
        mean, std = np.mean(recent), np.std(recent)
        if std < 0.01:
            return value, False
        if abs((value - mean) / std) > z_thresh:
            return buffer[-1], True
        return value, False

    def _moving_average(self, buffer: List[float]) -> float:
        if not buffer:
            return 0.0
        window = buffer[-self.window_size:]
        weights = np.linspace(0.5, 1.0, len(window))
        return float(np.average(window, weights=weights))

    def _estimate_noise(self) -> float:
        if len(self.hr_buffer) < 5:
            return 0.0
        return min(1.0, np.var(self.hr_buffer[-10:]) / 100.0)

    def _compute_confidence(self, noise_level: float, outlier_detected: bool) -> float:
        confidence = 100.0
        confidence -= noise_level * 30
        if self.total_count > 0:
            confidence -= (self.outlier_count / self.total_count) * 20
        if outlier_detected:
            confidence -= 10
        if len(self.hr_buffer) < 10:
            confidence -= (10 - len(self.hr_buffer)) * 2
        return max(config.MIN_CONFIDENCE, min(100, confidence))

    def reset(self):
        for buf in [self.hr_buffer, self.spo2_buffer, self.bp_sys_buffer,
                    self.bp_dia_buffer, self.rr_buffer, self.temp_buffer,
                    self.hr_smoothed, self.spo2_smoothed]:
            buf.clear()
        self.outlier_count = 0
        self.total_count = 0
