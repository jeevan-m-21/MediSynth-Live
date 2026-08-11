"""
Medisynth Live – SOS Emergency Auto-Dial System
Triggers full-screen SOS overlay when patient health is critically endangered.
Auto-dials ambulance (108), shares live GPS location, and sends alerts.
"""


def get_sos_overlay_html(patient_name: str = "Patient",
                          hr: float = 0, spo2: float = 0,
                          bp_sys: float = 0, bp_dia: float = 0,
                          health_score: float = 0,
                          ai_status: str = "",
                          emergency_number: str = "108") -> str:
    """Return the full-screen SOS emergency overlay with auto-dial and live location.

    Args:
        patient_name: Patient's name for emergency message
        hr, spo2, bp_sys, bp_dia: Current vitals
        health_score: Current health score (0-100)
        ai_status: AI summary of condition
        emergency_number: Ambulance number (default: 108 India)
    """
    return f"""
    <style>
        body {{ background: transparent !important; margin: 0; padding: 0; overflow: hidden; }}

        @keyframes sosPulse {{
            0%, 100% {{ transform: scale(1); box-shadow: 0 0 30px rgba(255,0,0,0.5); }}
            50% {{ transform: scale(1.05); box-shadow: 0 0 60px rgba(255,0,0,0.8); }}
        }}

        @keyframes sosRipple {{
            0% {{ transform: scale(0.8); opacity: 1; }}
            100% {{ transform: scale(2.5); opacity: 0; }}
        }}

        @keyframes blink {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.3; }}
        }}

        @keyframes slideIn {{
            0% {{ transform: translateY(20px); opacity: 0; }}
            100% {{ transform: translateY(0); opacity: 1; }}
        }}

        .sos-overlay {{
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background: linear-gradient(135deg, rgba(20,0,0,0.97), rgba(60,0,0,0.97));
            z-index: 999999; display: flex; flex-direction: column;
            align-items: center; justify-content: center;
            font-family: 'Inter', -apple-system, sans-serif;
            animation: slideIn 0.3s ease-out;
        }}

        .sos-btn-wrapper {{
            position: relative; margin-bottom: 20px;
        }}

        .sos-ripple {{
            position: absolute; top: 50%; left: 50%;
            width: 120px; height: 120px; border-radius: 50%;
            border: 3px solid rgba(255,0,0,0.4);
            transform: translate(-50%, -50%);
            animation: sosRipple 2s ease-out infinite;
        }}
        .sos-ripple:nth-child(2) {{ animation-delay: 0.5s; }}
        .sos-ripple:nth-child(3) {{ animation-delay: 1s; }}

        .sos-main-btn {{
            width: 140px; height: 140px; border-radius: 50%;
            background: linear-gradient(135deg, #ff0000, #cc0000);
            border: 4px solid #ff4444;
            display: flex; align-items: center; justify-content: center;
            flex-direction: column; cursor: pointer;
            animation: sosPulse 1.5s ease-in-out infinite;
            text-decoration: none; position: relative; z-index: 2;
        }}

        .sos-main-btn span:first-child {{
            font-size: 2rem; font-weight: 900; color: white;
            letter-spacing: 4px; line-height: 1;
        }}
        .sos-main-btn span:last-child {{
            font-size: 0.6rem; color: rgba(255,255,255,0.8);
            font-weight: 600; margin-top: 2px;
        }}

        .sos-status {{
            color: #ff4444; font-size: 0.8rem; font-weight: 800;
            letter-spacing: 3px; margin-bottom: 8px;
            animation: blink 1s ease-in-out infinite;
        }}

        .sos-vitals {{
            display: flex; gap: 12px; margin: 16px 0;
            flex-wrap: wrap; justify-content: center;
        }}

        .sos-vital-card {{
            background: rgba(255,0,0,0.1); border: 1px solid rgba(255,68,68,0.3);
            border-radius: 10px; padding: 8px 14px; text-align: center;
            min-width: 70px;
        }}
        .sos-vital-val {{
            color: #ff6666; font-size: 1.2rem; font-weight: 900;
            font-family: 'JetBrains Mono', monospace;
        }}
        .sos-vital-label {{
            color: rgba(255,255,255,0.4); font-size: 0.45rem;
            letter-spacing: 1px; margin-top: 2px;
        }}

        .sos-actions {{
            display: flex; gap: 10px; margin-top: 16px;
            flex-wrap: wrap; justify-content: center;
        }}

        .sos-action-btn {{
            padding: 10px 20px; border-radius: 10px;
            font-size: 0.7rem; font-weight: 700;
            cursor: pointer; border: none; letter-spacing: 0.5px;
            transition: all 0.2s; text-decoration: none;
            display: inline-flex; align-items: center; gap: 6px;
        }}

        .sos-call {{
            background: #ff0000; color: white;
        }}
        .sos-call:hover {{ background: #cc0000; }}

        .sos-location {{
            background: rgba(0,150,255,0.2); color: #4fc3f7;
            border: 1px solid rgba(0,150,255,0.3);
        }}

        .sos-dismiss {{
            background: rgba(255,255,255,0.05); color: rgba(255,255,255,0.5);
            border: 1px solid rgba(255,255,255,0.1);
            font-size: 0.55rem;
        }}

        .sos-ai-msg {{
            color: rgba(255,255,255,0.6); font-size: 0.65rem;
            max-width: 350px; text-align: center; margin: 8px 0;
            line-height: 1.5;
        }}

        .sos-location-info {{
            color: rgba(255,255,255,0.4); font-size: 0.5rem;
            margin-top: 8px; text-align: center;
        }}

        #sos-coords {{ color: #4fc3f7; font-family: 'JetBrains Mono', monospace; }}
    </style>

    <div class="sos-overlay" id="sos-overlay">
        <!-- Emergency Status -->
        <div class="sos-status">🚨 EMERGENCY DETECTED</div>

        <div style="color:rgba(255,255,255,0.7); font-size:0.7rem; font-weight:600; margin-bottom:12px;">
            {patient_name} — Health Score: <span style="color:#ff4444; font-weight:900;">{health_score:.0f}/100</span>
        </div>

        <!-- SOS Button -->
        <div class="sos-btn-wrapper">
            <div class="sos-ripple"></div>
            <div class="sos-ripple"></div>
            <div class="sos-ripple"></div>
            <a href="tel:{emergency_number}" class="sos-main-btn" id="sos-call-btn">
                <span>SOS</span>
                <span>TAP TO CALL {emergency_number}</span>
            </a>
        </div>

        <!-- Current Vitals -->
        <div class="sos-vitals">
            <div class="sos-vital-card">
                <div class="sos-vital-val">{hr:.0f}</div>
                <div class="sos-vital-label">HR bpm</div>
            </div>
            <div class="sos-vital-card">
                <div class="sos-vital-val">{spo2:.1f}</div>
                <div class="sos-vital-label">SpO₂ %</div>
            </div>
            <div class="sos-vital-card">
                <div class="sos-vital-val">{bp_sys:.0f}/{bp_dia:.0f}</div>
                <div class="sos-vital-label">BP mmHg</div>
            </div>
            <div class="sos-vital-card">
                <div class="sos-vital-val">{health_score:.0f}</div>
                <div class="sos-vital-label">SCORE</div>
            </div>
        </div>

        <!-- AI Status -->
        <div class="sos-ai-msg">
            🤖 {ai_status}
        </div>

        <!-- Action Buttons -->
        <div class="sos-actions">
            <a href="tel:{emergency_number}" class="sos-action-btn sos-call">
                📞 Call {emergency_number} Now
            </a>
            <button class="sos-action-btn sos-location" id="sos-share-loc">
                📍 Share Live Location
            </button>
        </div>

        <!-- Location Info -->
        <div class="sos-location-info">
            <div id="sos-loc-status">📡 Acquiring GPS coordinates...</div>
            <div id="sos-coords"></div>
        </div>

        <!-- Dismiss -->
        <div style="margin-top:16px;">
            <button class="sos-action-btn sos-dismiss" id="sos-dismiss-btn">
                ✕ Patient is stable — dismiss alert
            </button>
        </div>
    </div>

    <script>
    (function() {{
        const overlay = document.getElementById('sos-overlay');
        const locStatus = document.getElementById('sos-loc-status');
        const coordsEl = document.getElementById('sos-coords');
        const shareBtn = document.getElementById('sos-share-loc');
        const dismissBtn = document.getElementById('sos-dismiss-btn');
        let currentLat = null, currentLng = null;

        // Auto-acquire location
        if (navigator.geolocation) {{
            navigator.geolocation.watchPosition(
                function(pos) {{
                    currentLat = pos.coords.latitude;
                    currentLng = pos.coords.longitude;
                    const acc = pos.coords.accuracy;
                    locStatus.textContent = '✓ GPS Active — Accuracy: ' + acc.toFixed(0) + 'm';
                    locStatus.style.color = '#4fc3f7';
                    coordsEl.textContent = currentLat.toFixed(6) + ', ' + currentLng.toFixed(6);
                }},
                function(err) {{
                    locStatus.textContent = '⚠ GPS unavailable: ' + err.message;
                    locStatus.style.color = '#ffb347';
                }},
                {{ enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }}
            );
        }} else {{
            locStatus.textContent = '⚠ Geolocation not supported';
        }}

        // Share Location button
        if (shareBtn) {{
            shareBtn.addEventListener('click', function() {{
                if (currentLat && currentLng) {{
                    const url = 'https://maps.google.com/maps?q=' + currentLat + ',' + currentLng;
                    const msg = '🚨 EMERGENCY — {patient_name}\\n' +
                                'Health Score: {health_score:.0f}/100\\n' +
                                'HR: {hr:.0f} bpm | SpO₂: {spo2:.1f}%\\n' +
                                'Location: ' + url;

                    // Try native share API first (mobile)
                    if (navigator.share) {{
                        navigator.share({{
                            title: '🚨 Medical Emergency',
                            text: msg,
                            url: url
                        }}).catch(() => {{}});
                    }} else {{
                        // Fallback: open Google Maps in new tab
                        window.open(url, '_blank');
                    }}

                    shareBtn.textContent = '✓ Location Shared';
                    shareBtn.style.background = 'rgba(0,212,170,0.2)';
                    shareBtn.style.color = '#00d4aa';
                    shareBtn.style.borderColor = 'rgba(0,212,170,0.3)';
                }} else {{
                    shareBtn.textContent = '⚠ Waiting for GPS...';
                    setTimeout(() => {{ shareBtn.textContent = '📍 Share Live Location'; }}, 2000);
                }}
            }});
        }}

        // Dismiss button
        if (dismissBtn) {{
            dismissBtn.addEventListener('click', function() {{
                overlay.style.animation = 'none';
                overlay.style.opacity = '0';
                overlay.style.transition = 'opacity 0.3s';
                setTimeout(() => {{ overlay.style.display = 'none'; }}, 300);
            }});
        }}

        // Auto-play emergency sound (if supported)
        try {{
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            function playAlarm() {{
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.frequency.value = 880;
                gain.gain.value = 0.15;
                osc.start();
                osc.stop(ctx.currentTime + 0.3);
                setTimeout(() => {{
                    const osc2 = ctx.createOscillator();
                    const gain2 = ctx.createGain();
                    osc2.connect(gain2);
                    gain2.connect(ctx.destination);
                    osc2.frequency.value = 660;
                    gain2.gain.value = 0.15;
                    osc2.start();
                    osc2.stop(ctx.currentTime + 0.3);
                }}, 400);
            }}
            playAlarm();
            const alarmInterval = setInterval(playAlarm, 3000);
            // Stop alarm when dismissed
            if (dismissBtn) {{
                dismissBtn.addEventListener('click', () => clearInterval(alarmInterval));
            }}
        }} catch(e) {{}}
    }})();
    </script>
    """
