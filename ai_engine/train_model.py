"""
Medisynth Live – AI Model Training Pipeline
Offline training script for the anomaly detection and risk prediction models.
Reads historical vitals data and trains/exports models for predict.py to consume.

Usage:
    python -m ai_engine.train_model [--data-path vitals.csv] [--output-dir ./models]
"""

import os
import sys
import json
import time
import numpy as np
from typing import List, Dict, Optional

# Add parent to path for config access
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class VitalsDataset:
    """Manages vitals data for training. Can load from CSV, DB, or generate synthetic."""

    def __init__(self):
        self.records: List[Dict] = []

    def load_from_db(self, patient_id: Optional[str] = None):
        """Load vitals from SQLite database."""
        try:
            from backend.models.database import get_db
            conn = get_db()
            query = "SELECT * FROM vitals_log"
            params = ()
            if patient_id:
                query += " WHERE patient_id = ?"
                params = (patient_id,)
            query += " ORDER BY timestamp"
            rows = conn.execute(query, params).fetchall()
            conn.close()
            self.records = [dict(r) for r in rows]
            print(f"[TRAIN] Loaded {len(self.records)} records from database")
        except Exception as e:
            print(f"[TRAIN] DB load failed: {e}, generating synthetic data")
            self.generate_synthetic()

    def load_from_csv(self, filepath: str):
        """Load vitals from CSV file."""
        import csv
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            self.records = []
            for row in reader:
                self.records.append({
                    "heart_rate": float(row.get("heart_rate", 72)),
                    "spo2": float(row.get("spo2", 97.5)),
                    "bp_systolic": float(row.get("bp_systolic", 120)),
                    "bp_diastolic": float(row.get("bp_diastolic", 80)),
                    "resp_rate": float(row.get("resp_rate", 16)),
                    "temperature": float(row.get("temperature", 36.8)),
                    "health_score": float(row.get("health_score", 85)),
                    "mode": row.get("mode", "normal"),
                })
        print(f"[TRAIN] Loaded {len(self.records)} records from {filepath}")

    def generate_synthetic(self, n_samples: int = 5000):
        """Generate synthetic training data across all modes."""
        import config
        from modules.simulation_engine import SimulationEngine

        print(f"[TRAIN] Generating {n_samples} synthetic samples...")
        modes = ["normal", "stress", "critical", "sleep", "exercise", "recovery"]
        samples_per_mode = n_samples // len(modes)

        sim = SimulationEngine()
        for mode in modes:
            sim.set_mode(mode)
            for i in range(samples_per_mode):
                elapsed = i * 2.0  # 2 second intervals
                reading = sim.generate_reading()
                self.records.append({
                    "heart_rate": reading.heart_rate,
                    "spo2": reading.spo2,
                    "bp_systolic": reading.bp_systolic,
                    "bp_diastolic": reading.bp_diastolic,
                    "resp_rate": reading.respiratory_rate,
                    "temperature": reading.temperature,
                    "mode": mode,
                    "is_anomaly": mode == "critical",
                })
            sim = SimulationEngine()  # Reset for next mode

        np.random.shuffle(self.records)
        print(f"[TRAIN] Generated {len(self.records)} synthetic records")

    def to_feature_matrix(self) -> np.ndarray:
        """Convert records to numpy feature matrix."""
        features = []
        for r in self.records:
            features.append([
                r.get("heart_rate", 72),
                r.get("spo2", 97.5),
                r.get("bp_systolic", 120),
                r.get("bp_diastolic", 80),
                r.get("resp_rate", 16),
                r.get("temperature", 36.8),
            ])
        return np.array(features)

    def get_labels(self) -> np.ndarray:
        """Get anomaly labels (1 = anomaly, 0 = normal)."""
        return np.array([1 if r.get("is_anomaly") or r.get("mode") == "critical" else 0
                         for r in self.records])


class ModelTrainer:
    """Trains anomaly detection models using scikit-learn."""

    def __init__(self, output_dir: str = "./ai_engine/models"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.metrics = {}

    def train_isolation_forest(self, X: np.ndarray, labels: np.ndarray):
        """Train Isolation Forest for unsupervised anomaly detection."""
        from sklearn.ensemble import IsolationForest
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics import classification_report, f1_score

        print("\n[TRAIN] ── Isolation Forest ──")
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Train on normal data only
        normal_mask = labels == 0
        X_normal = X_scaled[normal_mask]

        model = IsolationForest(
            n_estimators=200,
            contamination=0.05,
            max_samples='auto',
            random_state=42,
        )
        model.fit(X_normal)

        # Evaluate on full dataset
        preds = model.predict(X_scaled)
        # IF returns -1 for anomaly, 1 for normal
        pred_labels = (preds == -1).astype(int)

        f1 = f1_score(labels, pred_labels, zero_division=0)
        print(f"  F1 Score: {f1:.3f}")
        print(classification_report(labels, pred_labels, target_names=["Normal", "Anomaly"], zero_division=0))

        self.metrics["isolation_forest"] = {
            "f1_score": round(f1, 4),
            "n_train_normal": int(normal_mask.sum()),
            "n_total": len(X),
        }

        # Save model
        import pickle
        model_path = os.path.join(self.output_dir, "isolation_forest.pkl")
        scaler_path = os.path.join(self.output_dir, "scaler.pkl")
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        with open(scaler_path, 'wb') as f:
            pickle.dump(scaler, f)
        print(f"  Saved: {model_path}")

    def train_risk_thresholds(self, X: np.ndarray, labels: np.ndarray):
        """Compute statistical thresholds for risk scoring from training data."""
        print("\n[TRAIN] ── Risk Thresholds ──")

        feature_names = ["heart_rate", "spo2", "bp_systolic", "bp_diastolic", "resp_rate", "temperature"]
        thresholds = {}

        normal_mask = labels == 0
        X_normal = X[normal_mask]

        for i, name in enumerate(feature_names):
            values = X_normal[:, i]
            thresholds[name] = {
                "mean": round(float(np.mean(values)), 2),
                "std": round(float(np.std(values)), 2),
                "p5": round(float(np.percentile(values, 5)), 2),
                "p95": round(float(np.percentile(values, 95)), 2),
                "min": round(float(np.min(values)), 2),
                "max": round(float(np.max(values)), 2),
            }
            print(f"  {name}: μ={thresholds[name]['mean']}, σ={thresholds[name]['std']}, "
                  f"range=[{thresholds[name]['p5']}, {thresholds[name]['p95']}]")

        # Save thresholds
        threshold_path = os.path.join(self.output_dir, "thresholds.json")
        with open(threshold_path, 'w') as f:
            json.dump(thresholds, f, indent=2)
        print(f"  Saved: {threshold_path}")

        self.metrics["thresholds"] = thresholds

    def save_training_report(self):
        """Save training metrics report."""
        report = {
            "trained_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "model_version": "v1.0",
            "metrics": self.metrics,
        }
        report_path = os.path.join(self.output_dir, "training_report.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n[TRAIN] Report saved: {report_path}")


def main():
    """Run the full training pipeline."""
    import argparse
    parser = argparse.ArgumentParser(description="Medisynth AI Model Training")
    parser.add_argument("--data-path", type=str, help="Path to CSV vitals data")
    parser.add_argument("--output-dir", type=str, default="./ai_engine/models")
    parser.add_argument("--samples", type=int, default=5000, help="Synthetic samples to generate")
    args = parser.parse_args()

    print("=" * 60)
    print("  MEDISYNTH LIVE - AI MODEL TRAINING PIPELINE")
    print("=" * 60)

    # Load data
    dataset = VitalsDataset()
    if args.data_path:
        dataset.load_from_csv(args.data_path)
    else:
        dataset.load_from_db()
        if not dataset.records:
            dataset.generate_synthetic(n_samples=args.samples)

    # Build feature matrix
    X = dataset.to_feature_matrix()
    labels = dataset.get_labels()
    print(f"\n[TRAIN] Dataset: {len(X)} samples, {labels.sum()} anomalies, "
          f"{len(X) - labels.sum()} normal")

    # Train models
    trainer = ModelTrainer(output_dir=args.output_dir)
    trainer.train_isolation_forest(X, labels)
    trainer.train_risk_thresholds(X, labels)
    trainer.save_training_report()

    print("\n" + "═" * 60)
    print("  TRAINING COMPLETE ✓")
    print("=" * 60)


if __name__ == "__main__":
    main()
