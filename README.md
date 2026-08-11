# 🫀 Medisynth Live – AI-Powered Wearable Health Monitoring System

An intelligent wearable health monitoring system that continuously tracks vital parameters (heart rate, SpO₂, blood pressure, respiratory rate, temperature, and activity levels), uses hybrid AI algorithms (rule-based + ML) to detect anomalies, and provides real-time alerts for preventive healthcare.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

The dashboard opens at `http://localhost:8501`

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────┐
│              WEARABLE SENSORS                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │BLE Pulse │  │BLE Heart │  │ Phone Accel  │   │
│  │Oximeter  │  │Rate Mon  │  │ (DeviceMotion│   │
│  │(0x1822)  │  │(0x180D)  │  │  API)        │   │
│  └────┬─────┘  └────┬─────┘  └──────┬───────┘   │
│       │              │               │            │
│       └──────────────┴───────────────┘            │
│              Web Bluetooth API                    │
└──────────────────┬───────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────┐
│              PROCESSING PIPELINE                  │
│  ┌─────────────┐ ┌────────────┐ ┌────────────┐  │
│  │Preprocessing│ │ Baseline   │ │ Activity   │  │
│  │(Noise/EMA)  │ │ Engine     │ │ Classifier │  │
│  └─────┬───────┘ └─────┬──────┘ └─────┬──────┘  │
│        └───────────────┬───────────────┘          │
└────────────────────────┬─────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────┐
│              AI DETECTION LAYER                   │
│  ┌──────────────┐  ┌───────────────┐             │
│  │ Rule-Based   │  │ Isolation     │             │
│  │ 12-Step      │  │ Forest ML     │             │
│  │ Clinical     │  │ (scikit-learn)│             │
│  │ Reasoning    │  │ Anomaly Model │             │
│  └──────┬───────┘  └───────┬───────┘             │
│         └──────────────────┘                      │
│         Context-Aware Thresholds                  │
│         (Exercise/Sleep/Recovery)                  │
└────────────────────────┬─────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────┐
│              ALERT & RESPONSE                     │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐  │
│  │Browser │ │Push    │ │Hospital│ │Emergency │  │
│  │Alerts  │ │(ntfy)  │ │Finder  │ │Contacts  │  │
│  └────────┘ └────────┘ └────────┘ └──────────┘  │
└──────────────────────────────────────────────────┘
```

## 📊 Module Map

| Module | Purpose |
|--------|---------|
| `wearable_ble.py` | Web Bluetooth BLE connection (pulse oximeters, HR monitors) |
| `activity_detector.py` | Accelerometer-based activity classification (resting/walking/running) |
| `simulation_engine.py` | Real-time vital sign generation (HR, SpO₂, BP, RR, Temp) |
| `preprocessing.py` | Noise filtering, EMA smoothing, confidence scoring |
| `ai_detection.py` | 12-step explainable clinical reasoning engine |
| `ml_anomaly_model.py` | Isolation Forest unsupervised anomaly detection |
| `baseline_engine.py` | Personalized baseline capture & deviation tracking |
| `health_score.py` | Weighted health score computation (0-100) |
| `emergency_system.py` | 3-step emergency alert flow |
| `hospital_finder.py` | OpenStreetMap nearby hospital search |
| `notification_service.py` | Multi-channel alerts (ntfy, browser, WhatsApp) |
| `analytics_engine.py` | Session analytics & export |

## 🤖 AI Algorithms

### 1. Rule-Based Clinical Detection
- Tachycardia / Bradycardia (HR)
- Hypoxia / Desaturation (SpO₂)
- Hypertension / Hypotension (BP)
- Tachypnea / Bradypnea (RR)
- Fever / Hypothermia (Temp)
- Shock Pattern (multi-vital correlation)
- Arrhythmia (HRV coefficient of variation)
- Trend analysis (slope detection)
- **Context-aware thresholds** (exercise/sleep/recovery modes)

### 2. Machine Learning Anomaly Detection
- **Algorithm**: Isolation Forest (100 estimators)
- **Training**: Online learning from first 30 normal readings
- **Features**: 6-dimensional vital sign vector
- **Output**: Anomaly score (0-1), feature attribution
- **Retraining**: Automatic every 50 new samples

### 3. Predictive Health Intelligence
- 5/10/15 minute risk forecasting
- 5 specialized risk categories
- Confidence-weighted predictions

## 📡 Wearable Integration

### Web Bluetooth (BLE)
- **Heart Rate Service** (UUID: 0x180D)
- **Pulse Oximeter Service** (UUID: 0x1822)
- **Battery Service** (UUID: 0x180F)
- Compatible: BerryMed, Contec, Masimo, Nonin, Polar, Garmin

### Activity Detection (Accelerometer)
- **API**: DeviceMotion (browser accelerometer)
- **Classification**: Resting, Walking, Running
- **Method**: Variance analysis + zero-crossing frequency estimation
- **Auto-mode**: Switches monitoring thresholds based on detected activity

## 👥 Role-Based Views

- **Patient**: Health gauge, vital cards, AI insights, ML model status
- **Caregiver**: Alert feed, patient status, location sharing
- **Doctor**: Raw vs processed data, full AI analysis, export tools

## 🔧 Tech Stack

- **Python** + **Streamlit** (dashboard framework)
- **scikit-learn** (Isolation Forest ML model)
- **Plotly** (interactive charts)
- **NumPy** (signal processing)
- **Web Bluetooth API** (wearable sensor connection)
- **DeviceMotion API** (accelerometer activity detection)
