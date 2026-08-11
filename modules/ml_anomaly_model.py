"""
Medisynth Live – ML Anomaly Detection Model
Lightweight Isolation Forest + Online Learning for real-time anomaly scoring.
Runs alongside rule-based detection for hybrid AI.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Optional
from collections import deque

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


@dataclass
class MLAnomalyResult:
    """Result from the ML anomaly detection model."""
    anomaly_score: float          # 0.0 (normal) to 1.0 (highly anomalous)
    is_anomaly: bool              # Binary decision
    model_confidence: float       # How confident the model is (0-100%)
    top_features: List[str]       # Which vitals contributed most to anomaly
    model_status: str             # "training", "ready", "prediction"
    samples_seen: int             # Total training samples
    training_progress: float      # 0.0 to 1.0


class MLAnomalyDetector:
    """
    Isolation Forest-based anomaly detector for vital signs.

    Training strategy:
    - Collects first N normal readings as training data
    - Fits Isolation Forest after MIN_TRAINING_SAMPLES
    - Continues to update model periodically with new normal data
    - Provides anomaly scores alongside rule-based detections
    """

    MIN_TRAINING_SAMPLES = 30     # Minimum readings before model is ready
    MAX_TRAINING_SAMPLES = 500    # Cap training buffer
    RETRAIN_INTERVAL = 50         # Retrain every N new normal samples
    CONTAMINATION = 0.05          # Expected anomaly ratio

    FEATURE_NAMES = ["heart_rate", "spo2", "bp_systolic", "bp_diastolic",
                     "resp_rate", "temperature"]

    def __init__(self):
        self._training_buffer: deque = deque(maxlen=self.MAX_TRAINING_SAMPLES)
        self._model: Optional[object] = None
        self._scaler: Optional[object] = None
        self._is_trained = False
        self._samples_seen = 0
        self._normal_since_last_train = 0
        self._feature_means: Optional[np.ndarray] = None
        self._feature_stds: Optional[np.ndarray] = None

    def _build_feature_vector(self, hr: float, spo2: float, bp_sys: float,
                               bp_dia: float, rr: float, temp: float) -> np.ndarray:
        """Build standardized feature vector from vitals."""
        return np.array([hr, spo2, bp_sys, bp_dia, rr, temp])

    def update_and_predict(self, hr: float, spo2: float,
                            bp_sys: float = 120, bp_dia: float = 80,
                            rr: float = 16, temp: float = 36.8,
                            is_normal_context: bool = True) -> MLAnomalyResult:
        """
        Feed a new vital reading. If model is trained, return anomaly prediction.
        If still training, collect data and return training status.

        Args:
            is_normal_context: True if rule-based system says this is normal
                              (used to decide whether to add to training set)
        """
        self._samples_seen += 1
        features = self._build_feature_vector(hr, spo2, bp_sys, bp_dia, rr, temp)

        if not SKLEARN_AVAILABLE:
            return MLAnomalyResult(
                anomaly_score=0.0, is_anomaly=False, model_confidence=0,
                top_features=[], model_status="unavailable (sklearn not installed)",
                samples_seen=self._samples_seen, training_progress=0.0,
            )

        # Phase 1: Collect training data from normal readings
        if is_normal_context:
            self._training_buffer.append(features)
            self._normal_since_last_train += 1

        # Phase 2: Train model when enough data
        training_progress = min(1.0, len(self._training_buffer) / self.MIN_TRAINING_SAMPLES)

        if not self._is_trained:
            if len(self._training_buffer) >= self.MIN_TRAINING_SAMPLES:
                try:
                    self._train_model()
                except Exception:
                    pass  # Model training failed, will retry next tick
            if not self._is_trained:
                return MLAnomalyResult(
                    anomaly_score=0.0, is_anomaly=False, model_confidence=0,
                    top_features=[], model_status="training",
                    samples_seen=self._samples_seen,
                    training_progress=training_progress,
                )

        # Phase 3: Periodic retraining with new normal data
        if (self._normal_since_last_train >= self.RETRAIN_INTERVAL
                and len(self._training_buffer) >= self.MIN_TRAINING_SAMPLES):
            try:
                self._train_model()
            except Exception:
                pass

        # Phase 4: Predict anomaly score
        return self._predict(features)

    def _train_model(self):
        """Train/retrain the Isolation Forest on collected normal data."""
        X = np.array(list(self._training_buffer))

        self._scaler = StandardScaler()
        X_scaled = self._scaler.fit_transform(X)

        self._model = IsolationForest(
            n_estimators=100,
            contamination=self.CONTAMINATION,
            random_state=42,
            max_samples=min(256, len(X)),
        )
        self._model.fit(X_scaled)

        self._feature_means = X.mean(axis=0)
        self._feature_stds = X.std(axis=0) + 1e-8  # Avoid div by zero

        self._is_trained = True
        self._normal_since_last_train = 0

    def _predict(self, features: np.ndarray) -> MLAnomalyResult:
        """Run anomaly prediction on a single feature vector."""
        X = features.reshape(1, -1)
        X_scaled = self._scaler.transform(X)

        # Isolation Forest: decision_function returns negative for anomalies
        raw_score = self._model.decision_function(X_scaled)[0]
        prediction = self._model.predict(X_scaled)[0]  # 1 = normal, -1 = anomaly

        # Convert to 0-1 anomaly score (higher = more anomalous)
        # decision_function typically ranges from -0.5 to 0.5
        anomaly_score = max(0.0, min(1.0, 0.5 - raw_score))

        is_anomaly = prediction == -1

        # Feature importance: which vitals deviate most from learned normal
        deviations = np.abs(features - self._feature_means) / self._feature_stds
        top_indices = np.argsort(deviations)[::-1][:3]
        top_features = []
        for idx in top_indices:
            if deviations[idx] > 1.5:  # Only report if >1.5 std dev
                direction = "↑" if features[idx] > self._feature_means[idx] else "↓"
                top_features.append(
                    f"{self.FEATURE_NAMES[idx]} {direction} ({deviations[idx]:.1f}σ)"
                )

        # Confidence based on training set size
        confidence = min(95, 40 + len(self._training_buffer) * 0.12)

        return MLAnomalyResult(
            anomaly_score=round(anomaly_score, 3),
            is_anomaly=is_anomaly,
            model_confidence=round(confidence, 1),
            top_features=top_features,
            model_status="prediction",
            samples_seen=self._samples_seen,
            training_progress=1.0,
        )

    def get_model_info(self) -> dict:
        """Return model metadata for UI display."""
        return {
            "algorithm": "Isolation Forest",
            "n_estimators": 100,
            "training_samples": len(self._training_buffer),
            "total_seen": self._samples_seen,
            "is_trained": self._is_trained,
            "contamination": self.CONTAMINATION,
            "features": self.FEATURE_NAMES,
            "sklearn_available": SKLEARN_AVAILABLE,
        }

    def reset(self):
        """Reset model state."""
        self._training_buffer.clear()
        self._model = None
        self._scaler = None
        self._is_trained = False
        self._samples_seen = 0
        self._normal_since_last_train = 0
