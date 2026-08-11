"""
Medisynth Live – Auto Activity Detection
Dual-mode: Hardware accelerometer (mobile) OR synced with simulation mode (desktop).
Auto-classifies: Resting · Walking · Running · Exercise · Sleep
"""


def get_activity_widget_html(current_mode: str = "normal") -> str:
    """Return combined HTML + JS for activity detection (single iframe).

    Args:
        current_mode: Current simulation mode from Streamlit (normal/exercise/sleep/etc.)
    """
    # Map simulation mode to activity display
    mode_map = {
        "normal": {"label": "Resting", "icon": "🧘", "color": "#00d4aa"},
        "exercise": {"label": "Exercise", "icon": "🏃", "color": "#ff4757"},
        "stress": {"label": "Elevated", "icon": "⚡", "color": "#ffb347"},
        "critical": {"label": "Critical", "icon": "🚨", "color": "#ff4757"},
        "sleep": {"label": "Sleeping", "icon": "🌙", "color": "#7c3aed"},
        "recovery": {"label": "Recovery", "icon": "🔄", "color": "#4fc3f7"},
    }
    info = mode_map.get(current_mode, mode_map["normal"])
    label = info["label"]
    icon = info["icon"]
    color = info["color"]

    return f"""
    <style>body {{ background: transparent !important; margin: 0; padding: 0; }}</style>
    <div style="margin:0; padding:12px; background:rgba(15,20,40,0.6);
        border:1px solid rgba(0,212,170,0.2); border-radius:12px;">

        <!-- Header -->
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:10px;">
            <div style="display:flex; align-items:center; gap:8px;">
                <div id="accel-dot" style="width:8px; height:8px; border-radius:50%;
                    background:{color}; box-shadow:0 0 6px {color}; transition:all 0.3s;"></div>
                <span style="color:#e8eaf6; font-size:0.7rem; font-weight:800;
                    letter-spacing:1.5px;">ACTIVITY DETECTION</span>
            </div>
            <span id="accel-status" style="font-size:0.55rem; color:{color};
                font-weight:600;" id="accel-source">Simulation</span>
        </div>

        <!-- Activity Display -->
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:10px;
            padding:8px; background:rgba(255,255,255,0.02); border-radius:8px;">
            <div id="accel-icon" style="font-size:1.8rem;">{icon}</div>
            <div style="flex:1;">
                <div id="accel-activity" style="color:{color}; font-size:1rem; font-weight:800;
                    font-family:'JetBrains Mono',monospace;">{label}</div>
                <div id="accel-source-label" style="color:#3d4a6b; font-size:0.5rem; letter-spacing:0.5px;">
                    CURRENT ACTIVITY MODE
                </div>
            </div>
            <div style="text-align:right;">
                <div id="accel-confidence" style="color:#7986cb; font-size:0.9rem; font-weight:700;
                    font-family:'JetBrains Mono',monospace;">SIM</div>
                <div style="color:#3d4a6b; font-size:0.5rem;">SOURCE</div>
            </div>
        </div>

        <!-- Toggle Button -->
        <button id="accel-toggle"
            style="width:100%; padding:7px; background:transparent;
            border:1px solid rgba(0,212,170,0.3); border-radius:8px; color:#00d4aa;
            font-size:0.6rem; font-weight:700; cursor:pointer; letter-spacing:1px;
            transition:all 0.2s;"
            onmouseover="this.style.background='rgba(0,212,170,0.1)'"
            onmouseout="this.style.background='transparent'">
            📱 Switch to Accelerometer
        </button>

        <!-- Feedback -->
        <div id="accel-feedback" style="display:none; font-size:0.55rem;
            margin-top:6px; padding:6px 10px; border-radius:6px; line-height:1.4;"></div>

        <!-- Sensor Info -->
        <div style="margin-top:8px; padding:5px 8px; background:rgba(255,255,255,0.02);
            border-radius:6px;">
            <div style="color:#3d4a6b; font-size:0.4rem; letter-spacing:0.5px;">
                SIM = Synced with Lifestyle Mode buttons · ACC = Phone accelerometer hardware
            </div>
        </div>
    </div>

    <script>
    (function() {{
        const WINDOW = 30;
        const buf = [];
        let useAccel = false;
        let currentAct = '{label.lower()}';
        let conf = 0;

        const dot = document.getElementById('accel-dot');
        const statusEl = document.getElementById('accel-status');
        const actEl = document.getElementById('accel-activity');
        const confEl = document.getElementById('accel-confidence');
        const iconEl = document.getElementById('accel-icon');
        const toggleBtn = document.getElementById('accel-toggle');
        const feedbackEl = document.getElementById('accel-feedback');
        const sourceLabel = document.getElementById('accel-source-label');

        function showFB(msg, type) {{
            if (!feedbackEl) return;
            const c = {{
                info: {{ bg: 'rgba(124,58,237,0.08)', bd: 'rgba(124,58,237,0.2)', t: '#a78bfa' }},
                success: {{ bg: 'rgba(0,212,170,0.08)', bd: 'rgba(0,212,170,0.2)', t: '#00d4aa' }},
                warning: {{ bg: 'rgba(255,179,71,0.08)', bd: 'rgba(255,179,71,0.2)', t: '#ffb347' }}
            }}[type] || {{ bg: 'rgba(124,58,237,0.08)', bd: 'rgba(124,58,237,0.2)', t: '#a78bfa' }};
            feedbackEl.style.display = 'block';
            feedbackEl.style.background = c.bg;
            feedbackEl.style.border = '1px solid ' + c.bd;
            feedbackEl.style.color = c.t;
            feedbackEl.textContent = msg;
        }}

        function classify(mags) {{
            if (mags.length < 10) return {{ a: 'resting', c: 50 }};
            const mean = mags.reduce((a,b) => a+b, 0) / mags.length;
            const variance = mags.reduce((a,b) => a + (b-mean)**2, 0) / mags.length;
            const std = Math.sqrt(variance);
            const centered = mags.map(m => m - mean);
            let zc = 0;
            for (let i = 1; i < centered.length; i++) {{
                if (centered[i] * centered[i-1] < 0) zc++;
            }}
            const freq = zc / (mags.length / 10);

            if (std < 0.5 && mean < 10.5) return {{ a: 'resting', c: Math.min(95, 60 + (0.5-std)*60) }};
            if (std < 2.0 && freq < 3) return {{ a: 'walking', c: Math.min(90, 50 + std*20) }};
            return {{ a: 'running', c: Math.min(95, 40 + std*15) }};
        }}

        function handleMotion(e) {{
            const acc = e.accelerationIncludingGravity;
            if (!acc || acc.x === null) return;
            const mag = Math.sqrt(acc.x**2 + acc.y**2 + acc.z**2);
            buf.push(mag);
            if (buf.length > WINDOW * 3) buf.splice(0, buf.length - WINDOW);

            if (buf.length >= 10) {{
                const r = classify(buf.slice(-WINDOW));
                currentAct = r.a;
                conf = r.c;
                updateAccelUI();
            }}
        }}

        function updateAccelUI() {{
            if (!dot) return;
            const icons = {{ resting: '🧘', walking: '🚶', running: '🏃' }};
            const colors = {{ resting: '#00d4aa', walking: '#ffb347', running: '#ff4757' }};
            const col = colors[currentAct] || '#00d4aa';

            dot.style.background = col;
            dot.style.boxShadow = '0 0 6px ' + col;
            statusEl.textContent = 'Accelerometer';
            statusEl.style.color = col;
            actEl.textContent = currentAct.charAt(0).toUpperCase() + currentAct.slice(1);
            actEl.style.color = col;
            confEl.textContent = conf.toFixed(0) + '%';
            iconEl.textContent = icons[currentAct] || '📱';
            sourceLabel.textContent = 'DETECTED BY ACCELEROMETER';
            toggleBtn.textContent = '⏹ Switch to Simulation';
        }}

        async function toggleSource() {{
            if (useAccel) {{
                // Switch back to simulation mode
                window.removeEventListener('devicemotion', handleMotion, true);
                useAccel = false;
                buf.length = 0;
                showFB('Switched to Simulation Mode. Activity follows Lifestyle Mode buttons.', 'info');
                // Reset to simulation display (will update on next Streamlit rerender)
                confEl.textContent = 'SIM';
                sourceLabel.textContent = 'CURRENT ACTIVITY MODE';
                toggleBtn.textContent = '📱 Switch to Accelerometer';
                return;
            }}

            // Try to activate accelerometer
            const isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);

            // iOS permission
            if (typeof DeviceMotionEvent !== 'undefined' &&
                typeof DeviceMotionEvent.requestPermission === 'function') {{
                try {{
                    const perm = await DeviceMotionEvent.requestPermission();
                    if (perm !== 'granted') {{
                        showFB('⚠ Motion permission denied.', 'warning');
                        return;
                    }}
                }} catch(e) {{
                    showFB('⚠ Permission error: ' + e.message, 'warning');
                    return;
                }}
            }}

            // Start accelerometer
            window.addEventListener('devicemotion', handleMotion, true);
            useAccel = true;
            showFB('✓ Accelerometer active. Move device to detect activity.', 'success');

            // Check if data arrives
            setTimeout(() => {{
                if (useAccel && buf.length === 0) {{
                    showFB(
                        '📱 No accelerometer data. This device may lack motion sensors. ' +
                        'Activity is synced with Lifestyle Mode buttons instead.',
                        'warning'
                    );
                    useAccel = false;
                    confEl.textContent = 'SIM';
                    sourceLabel.textContent = 'CURRENT ACTIVITY MODE';
                    toggleBtn.textContent = '📱 Switch to Accelerometer';
                }}
            }}, 3000);
        }}

        if (toggleBtn) {{
            toggleBtn.addEventListener('click', toggleSource);
        }}
    }})();
    </script>
    """
