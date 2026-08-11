"""
Medisynth Live – Premium CSS Injection
Dark glassmorphism theme with Inter font, smooth animations, and status-responsive colors.
"""


def get_premium_css() -> str:
    return """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ── Global Reset ── */
    .stApp {
        background: linear-gradient(145deg, #0a0e1a 0%, #0f1428 40%, #131833 100%) !important;
        font-family: 'Inter', sans-serif !important;
        color: #e8eaf6 !important;
    }

    /* Hide Streamlit branding */
    #MainMenu, footer, header {visibility: hidden;}
    .stDeployButton {display: none;}

    /* ── Scrollbar ── */
    ::-webkit-scrollbar {width: 6px;}
    ::-webkit-scrollbar-track {background: #0a0e1a;}
    ::-webkit-scrollbar-thumb {background: rgba(124, 58, 237, 0.4); border-radius: 3px;}

    /* ── Glass Card ── */
    .glass-card {
        background: rgba(15, 20, 40, 0.65);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        margin-bottom: 16px;
    }
    .glass-card:hover {
        border-color: rgba(255, 255, 255, 0.12);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35);
        transform: translateY(-2px);
    }

    /* ── Vital Card ── */
    .vital-card {
        background: rgba(15, 20, 40, 0.65);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 20px 24px;
        text-align: center;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    .vital-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #00d4aa, #7c3aed);
        border-radius: 16px 16px 0 0;
    }
    .vital-label {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #7986cb;
        margin-bottom: 8px;
    }
    .vital-value {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #e8eaf6, #c5cae9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.1;
    }
    .vital-unit {
        font-size: 0.85rem;
        color: #7986cb;
        font-weight: 500;
    }

    /* ── Health Score ── */
    .score-container {
        text-align: center;
        padding: 32px 24px;
        background: rgba(15, 20, 40, 0.65);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 20px;
        position: relative;
        overflow: hidden;
    }
    .score-value {
        font-size: 5rem;
        font-weight: 900;
        line-height: 1;
        margin: 8px 0;
    }
    .score-label {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #7986cb;
    }
    .score-status {
        font-size: 1.1rem;
        font-weight: 600;
        margin-top: 8px;
        padding: 6px 16px;
        border-radius: 20px;
        display: inline-block;
    }

    /* ── Gradient Bar ── */
    .gradient-bar-container {
        width: 100%;
        height: 8px;
        background: rgba(255, 255, 255, 0.06);
        border-radius: 4px;
        margin: 16px 0;
        overflow: hidden;
    }
    .gradient-bar-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* ── Status Banner ── */
    .status-banner {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        padding: 12px 24px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.9rem;
        margin-bottom: 20px;
        letter-spacing: 0.5px;
        transition: all 0.5s ease;
    }
    .status-stable {
        background: rgba(0, 212, 170, 0.1);
        border: 1px solid rgba(0, 212, 170, 0.25);
        color: #00d4aa;
    }
    .status-monitoring {
        background: rgba(255, 179, 71, 0.1);
        border: 1px solid rgba(255, 179, 71, 0.25);
        color: #ffb347;
    }
    .status-critical {
        background: rgba(255, 71, 87, 0.12);
        border: 1px solid rgba(255, 71, 87, 0.3);
        color: #ff4757;
        animation: pulse-critical 2s infinite;
    }

    /* ── AI Reasoning Panel (Production) ── */
    .ai-reasoning-panel {
        background: rgba(10, 14, 30, 0.85);
        backdrop-filter: blur(24px);
        border: 1px solid rgba(124, 58, 237, 0.25);
        border-radius: 16px;
        padding: 0;
        position: relative;
        overflow: hidden;
    }
    .ai-reasoning-panel::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #7c3aed, #a855f7, #c084fc);
        border-radius: 16px 16px 0 0;
        animation: shimmerBar 3s ease-in-out infinite;
    }
    @keyframes shimmerBar {
        0%, 100% { opacity: 0.7; }
        50% { opacity: 1; }
    }
    .ai-reasoning-header {
        padding: 14px 18px 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid rgba(124, 58, 237, 0.12);
    }
    .ai-reasoning-title {
        color: #c084fc;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    .ai-reasoning-status {
        font-size: 0.6rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 12px;
        animation: statusPulse 2s ease-in-out infinite;
    }
    @keyframes statusPulse {
        0%, 100% { opacity: 0.8; }
        50% { opacity: 1; }
    }
    .ai-reasoning-body {
        padding: 6px 14px 14px;
        max-height: 420px;
        overflow-y: auto;
        scroll-behavior: smooth;
    }
    .ai-reasoning-body::-webkit-scrollbar { width: 4px; }
    .ai-reasoning-body::-webkit-scrollbar-thumb {
        background: rgba(124, 58, 237, 0.3);
        border-radius: 2px;
    }

    /* Pipeline step */
    .ai-step {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        padding: 7px 4px;
        font-size: 0.8rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.03);
        position: relative;
        animation: stepReveal 0.5s ease-out forwards;
        opacity: 0;
        transform: translateX(-8px);
    }
    @keyframes stepReveal {
        to { opacity: 1; transform: translateX(0); }
    }
    .ai-step:nth-child(1) { animation-delay: 0s; }
    .ai-step:nth-child(2) { animation-delay: 0.06s; }
    .ai-step:nth-child(3) { animation-delay: 0.12s; }
    .ai-step:nth-child(4) { animation-delay: 0.18s; }
    .ai-step:nth-child(5) { animation-delay: 0.24s; }
    .ai-step:nth-child(6) { animation-delay: 0.30s; }
    .ai-step:nth-child(7) { animation-delay: 0.36s; }
    .ai-step:nth-child(8) { animation-delay: 0.42s; }
    .ai-step:nth-child(9) { animation-delay: 0.48s; }
    .ai-step:nth-child(10) { animation-delay: 0.54s; }
    .ai-step:nth-child(11) { animation-delay: 0.60s; }
    .ai-step:nth-child(12) { animation-delay: 0.66s; }
    .ai-step:nth-child(13) { animation-delay: 0.72s; }
    .ai-step:nth-child(14) { animation-delay: 0.78s; }
    .ai-step:nth-child(15) { animation-delay: 0.84s; }
    .ai-step:last-child { border-bottom: none; }

    .ai-step-icon {
        font-size: 0.9rem;
        flex-shrink: 0;
        width: 22px;
        text-align: center;
    }
    .ai-step-content {
        flex: 1;
        min-width: 0;
    }
    .ai-step-label {
        font-weight: 500;
        line-height: 1.3;
    }
    .ai-step-detail {
        font-size: 0.65rem;
        color: #5c6b8a;
        margin-top: 1px;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Severity glow */
    .ai-step-critical {
        background: rgba(255, 71, 87, 0.06);
        border-left: 2px solid #ff4757;
        padding-left: 8px;
        margin-left: -4px;
    }
    .ai-step-warning {
        background: rgba(255, 179, 71, 0.04);
        border-left: 2px solid #ffb347;
        padding-left: 8px;
        margin-left: -4px;
    }
    .ai-step-active {
        background: rgba(0, 212, 170, 0.04);
        border-left: 2px solid #00d4aa;
        padding-left: 8px;
        margin-left: -4px;
    }

    /* Pipeline progress */
    .ai-pipeline-bar {
        display: flex;
        gap: 2px;
        padding: 6px 14px;
        background: rgba(0,0,0,0.2);
    }
    .ai-pipeline-dot {
        flex: 1;
        height: 3px;
        border-radius: 2px;
        transition: background 0.4s ease;
    }

    /* Verdict card */
    .ai-verdict {
        margin: 8px 14px 14px;
        padding: 12px 14px;
        border-radius: 10px;
        font-size: 0.78rem;
        font-weight: 600;
        line-height: 1.4;
    }
    .ai-verdict-normal {
        background: rgba(0, 212, 170, 0.08);
        border: 1px solid rgba(0, 212, 170, 0.2);
        color: #00d4aa;
    }
    .ai-verdict-warning {
        background: rgba(255, 179, 71, 0.08);
        border: 1px solid rgba(255, 179, 71, 0.2);
        color: #ffb347;
    }
    .ai-verdict-critical {
        background: rgba(255, 71, 87, 0.08);
        border: 1px solid rgba(255, 71, 87, 0.25);
        color: #ff4757;
        animation: pulse-critical 2s infinite;
    }

    /* Explainability section */
    .ai-explain {
        margin: 0 14px 12px;
        padding: 10px;
        background: rgba(124, 58, 237, 0.05);
        border: 1px solid rgba(124, 58, 237, 0.12);
        border-radius: 8px;
    }
    .ai-explain-title {
        color: #a78bfa;
        font-size: 0.6rem;
        font-weight: 700;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .ai-explain-row {
        display: flex;
        justify-content: space-between;
        padding: 2px 0;
        font-size: 0.7rem;
    }
    .ai-explain-label { color: #7986cb; }
    .ai-explain-value { font-weight: 600; font-family: 'JetBrains Mono', monospace; }

    /* ── Alert Card ── */
    .alert-card {
        background: rgba(255, 71, 87, 0.08);
        border: 1px solid rgba(255, 71, 87, 0.25);
        border-radius: 16px;
        padding: 24px;
        animation: pulse-critical 2s infinite;
    }
    .alert-title {
        color: #ff4757;
        font-size: 1.1rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 12px;
    }

    /* ── Breakdown Item ── */
    .breakdown-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        font-size: 0.85rem;
    }
    .breakdown-item:last-child {border-bottom: none;}
    .breakdown-label {color: #c5cae9;}
    .breakdown-deduction {
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
    }
    .deduction-negative {color: #ff4757;}
    .deduction-zero {color: #00d4aa;}

    /* ── Section Headers ── */
    .section-header {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #7986cb;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: rgba(10, 14, 26, 0.95) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
    }
    section[data-testid="stSidebar"] .stRadio label {
        color: #c5cae9 !important;
        font-weight: 500 !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, rgba(0, 212, 170, 0.15), rgba(124, 58, 237, 0.15)) !important;
        border: 1px solid rgba(0, 212, 170, 0.3) !important;
        color: #e8eaf6 !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        padding: 8px 20px !important;
        transition: all 0.3s ease !important;
        letter-spacing: 0.3px !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, rgba(0, 212, 170, 0.25), rgba(124, 58, 237, 0.25)) !important;
        border-color: rgba(0, 212, 170, 0.5) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 20px rgba(0, 212, 170, 0.15) !important;
    }

    /* ── Mode Buttons ── */
    .mode-btn-normal .stButton > button {
        background: rgba(0, 212, 170, 0.12) !important;
        border-color: rgba(0, 212, 170, 0.35) !important;
    }
    .mode-btn-stress .stButton > button {
        background: rgba(255, 179, 71, 0.12) !important;
        border-color: rgba(255, 179, 71, 0.35) !important;
    }
    .mode-btn-critical .stButton > button {
        background: rgba(255, 71, 87, 0.12) !important;
        border-color: rgba(255, 71, 87, 0.35) !important;
    }

    /* ── Metrics override ── */
    [data-testid="stMetric"] {
        background: rgba(15, 20, 40, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 16px;
    }
    [data-testid="stMetricValue"] {
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
    }

    /* ── Plotly chart container ── */
    .stPlotlyChart {
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.04);
    }

    /* ── Animations ── */
    @keyframes pulse-critical {
        0%, 100% { box-shadow: 0 0 0 0 rgba(255, 71, 87, 0.15); }
        50% { box-shadow: 0 0 20px 4px rgba(255, 71, 87, 0.1); }
    }
    @keyframes fadeSlideIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes pulseGlow {
        0%, 100% { opacity: 0.7; }
        50% { opacity: 1; }
    }

    /* ── Contact cards ── */
    .contact-card {
        background: rgba(15, 20, 40, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 12px 16px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: rgba(15, 20, 40, 0.5);
        border-radius: 12px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #7986cb;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(0, 212, 170, 0.12) !important;
        color: #00d4aa !important;
    }

    /* ── Expanders ── */
    .streamlit-expanderHeader {
        background: rgba(15, 20, 40, 0.4) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        color: #c5cae9 !important;
        font-weight: 600 !important;
    }

    /* ── Input fields ── */
    .stTextInput input, .stNumberInput input {
        background: rgba(15, 20, 40, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
        color: #e8eaf6 !important;
        font-family: 'Inter', sans-serif !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: rgba(0, 212, 170, 0.4) !important;
        box-shadow: 0 0 0 2px rgba(0, 212, 170, 0.1) !important;
    }

    /* ── Select box ── */
    .stSelectbox > div > div {
        background: rgba(15, 20, 40, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
    }

    /* ── Toggle ── */
    .stCheckbox label span {
        color: #c5cae9 !important;
    }

    /* ── Plotly Fullscreen Fix ── */
    .js-plotly-plot .plotly .modebar {
        background: rgba(10, 14, 26, 0.8) !important;
    }
    .js-plotly-plot .plotly .modebar-btn path {
        fill: #7986cb !important;
    }
    .js-plotly-plot .plotly .modebar-btn:hover path {
        fill: #00d4aa !important;
    }
    /* Force dark background in fullscreen */
    .plotly-notifier {
        background: #0a0e1a !important;
    }

    /* ── Loading Overlay ── */
    .loading-overlay {
        background: rgba(10, 14, 26, 0.85);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(124, 58, 237, 0.2);
        border-radius: 16px;
        padding: 32px;
        text-align: center;
        margin: 12px 0;
        animation: loadingPulse 1.5s infinite ease-in-out;
    }
    .loading-spinner {
        width: 48px; height: 48px;
        border: 3px solid rgba(255,255,255,0.06);
        border-top: 3px solid #00d4aa;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
        margin: 0 auto 16px;
    }
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    @keyframes loadingPulse {
        0%, 100% { border-color: rgba(124, 58, 237, 0.2); }
        50% { border-color: rgba(0, 212, 170, 0.3); }
    }

    /* ── Notification Status ── */
    .notif-badge-success {
        background: rgba(0, 212, 170, 0.1);
        border: 1px solid rgba(0, 212, 170, 0.2);
        color: #00d4aa;
        font-size: 0.7rem;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
    }
    .notif-badge-fail {
        background: rgba(255, 71, 87, 0.1);
        border: 1px solid rgba(255, 71, 87, 0.2);
        color: #ff4757;
        font-size: 0.7rem;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
    }
    .notif-badge-pending {
        background: rgba(255, 179, 71, 0.1);
        border: 1px solid rgba(255, 179, 71, 0.2);
        color: #ffb347;
        font-size: 0.7rem;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        animation: loadingPulse 1s infinite;
    }

    /* ── Emergency Pulse Animation ── */
    @keyframes pulse-critical {
        0%, 100% { border-color: rgba(255, 71, 87, 0.2); }
        50% { border-color: rgba(255, 71, 87, 0.6); box-shadow: 0 0 20px rgba(255, 71, 87, 0.15); }
    }

    /* ── Toggle Switch Styling ── */
    .stToggle > label {
        color: #c5cae9 !important;
    }
    .stToggle > div > div {
        background-color: rgba(255,255,255,0.1) !important;
    }

    /* ── Sidebar Button Improvements ── */
    section[data-testid="stSidebar"] .stButton > button {
        font-size: 0.78rem !important;
        padding: 8px 12px !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        background: rgba(15,20,40,0.6) !important;
        color: #c5cae9 !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        border-color: rgba(0, 212, 170, 0.4) !important;
        background: rgba(0, 212, 170, 0.08) !important;
        color: #00d4aa !important;
        transform: translateY(-1px) !important;
    }
    section[data-testid="stSidebar"] .stButton > button:active {
        transform: translateY(0) !important;
    }

    /* ── Expander Styling ── */
    section[data-testid="stSidebar"] .streamlit-expanderHeader {
        font-size: 0.8rem !important;
        color: #7986cb !important;
    }
</style>
"""


def inject_css():
    """Inject premium CSS into the Streamlit app."""
    import streamlit as st
    st.html(get_premium_css())
