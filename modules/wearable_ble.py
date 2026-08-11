"""
Medisynth Live – Web Bluetooth Wearable Service
Connects to real BLE pulse oximeters and heart rate monitors.
Supports standard BLE Health profiles (Heart Rate 0x180D, Pulse Oximeter 0x1822).
"""


def get_ble_widget_html() -> str:
    """Return combined HTML + JS for BLE wearable connection (single iframe)."""
    return """
    <style>body { background: transparent !important; margin: 0; padding: 0; }</style>
    <div style="margin:0; padding:12px; background:rgba(15,20,40,0.6);
        border:1px solid rgba(124,58,237,0.25); border-radius:12px;">

        <!-- Header -->
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:10px;">
            <div style="display:flex; align-items:center; gap:8px;">
                <div id="ble-dot" style="width:8px; height:8px; border-radius:50%;
                    background:#5c6b8a; transition:all 0.3s;"></div>
                <span style="color:#e8eaf6; font-size:0.7rem; font-weight:800;
                    letter-spacing:1.5px;">WEARABLE SENSOR</span>
            </div>
            <span id="ble-status" style="font-size:0.55rem; color:#5c6b8a;
                font-weight:600;">Disconnected</span>
        </div>

        <!-- Device Info (hidden when disconnected) -->
        <div id="ble-device-info" style="display:none; font-size:0.6rem; margin-bottom:8px;
            padding:6px 10px; background:rgba(0,212,170,0.06); border-radius:8px;"></div>

        <!-- Connect Button -->
        <button id="ble-connect-btn"
            style="width:100%; padding:8px; background:transparent;
            border:1px solid #7c3aed; border-radius:8px; color:#a78bfa;
            font-size:0.65rem; font-weight:700; cursor:pointer; letter-spacing:1px;
            transition:all 0.2s; margin-bottom:8px;"
            onmouseover="this.style.background='rgba(124,58,237,0.15)'"
            onmouseout="this.style.background='transparent'">
            🔗 Pair Wearable
        </button>

        <!-- Live Data (hidden when disconnected) -->
        <div id="ble-live-data" style="display:none; gap:8px; margin-top:4px;">
            <div style="flex:1; text-align:center; padding:6px; background:rgba(255,71,87,0.06);
                border-radius:8px; border:1px solid rgba(255,71,87,0.1);">
                <div id="ble-hr-val" style="color:#ff4757; font-size:1.1rem; font-weight:900;
                    font-family:'JetBrains Mono',monospace;">--</div>
                <div style="color:#5c6b8a; font-size:0.4rem; letter-spacing:1px;">HR bpm</div>
            </div>
            <div style="flex:1; text-align:center; padding:6px; background:rgba(0,212,170,0.06);
                border-radius:8px; border:1px solid rgba(0,212,170,0.1);">
                <div id="ble-spo2-val" style="color:#00d4aa; font-size:1.1rem; font-weight:900;
                    font-family:'JetBrains Mono',monospace;">--</div>
                <div style="color:#5c6b8a; font-size:0.4rem; letter-spacing:1px;">SpO2 %</div>
            </div>
            <div style="flex:1; text-align:center; padding:6px; background:rgba(124,58,237,0.06);
                border-radius:8px; border:1px solid rgba(124,58,237,0.1);">
                <div id="ble-readings-val" style="color:#a78bfa; font-size:1.1rem; font-weight:900;
                    font-family:'JetBrains Mono',monospace;">0</div>
                <div style="color:#5c6b8a; font-size:0.4rem; letter-spacing:1px;">READINGS</div>
            </div>
        </div>

        <!-- Feedback message -->
        <div id="ble-feedback" style="display:none; font-size:0.55rem;
            margin-top:6px; padding:6px 10px; border-radius:6px;
            line-height:1.4;"></div>

        <!-- Supported protocols -->
        <div style="margin-top:8px; padding:6px 8px; background:rgba(255,255,255,0.02);
            border-radius:6px;">
            <div style="color:#5c6b8a; font-size:0.45rem; letter-spacing:0.5px; margin-bottom:4px;">
                SUPPORTED PROTOCOLS
            </div>
            <div style="display:flex; flex-wrap:wrap; gap:3px;">
                <span style="background:rgba(124,58,237,0.1); color:#a78bfa; padding:1px 6px;
                    border-radius:6px; font-size:0.45rem;">BLE Heart Rate (0x180D)</span>
                <span style="background:rgba(124,58,237,0.1); color:#a78bfa; padding:1px 6px;
                    border-radius:6px; font-size:0.45rem;">Pulse Oximeter (0x1822)</span>
                <span style="background:rgba(124,58,237,0.1); color:#a78bfa; padding:1px 6px;
                    border-radius:6px; font-size:0.45rem;">Battery (0x180F)</span>
            </div>
            <div style="color:#3d4a6b; font-size:0.4rem; margin-top:4px;">
                Compatible: BerryMed · Contec · Masimo · Nonin · Polar · Garmin
            </div>
        </div>
    </div>

    <script>
    (function() {
        const state = {
            connected: false, device: null, server: null,
            deviceName: '', batteryLevel: -1,
            lastHR: 0, lastSpO2: 0, readings: 0
        };

        const feedbackEl = document.getElementById('ble-feedback');
        const dotEl = document.getElementById('ble-dot');
        const statusEl = document.getElementById('ble-status');
        const btn = document.getElementById('ble-connect-btn');
        const deviceInfo = document.getElementById('ble-device-info');
        const liveData = document.getElementById('ble-live-data');

        function showFeedback(msg, type) {
            if (!feedbackEl) return;
            const colors = {
                info: { bg: 'rgba(124,58,237,0.08)', border: 'rgba(124,58,237,0.2)', text: '#a78bfa' },
                success: { bg: 'rgba(0,212,170,0.08)', border: 'rgba(0,212,170,0.2)', text: '#00d4aa' },
                error: { bg: 'rgba(255,71,87,0.08)', border: 'rgba(255,71,87,0.2)', text: '#ff4757' },
                warning: { bg: 'rgba(255,179,71,0.08)', border: 'rgba(255,179,71,0.2)', text: '#ffb347' }
            };
            const c = colors[type] || colors.info;
            feedbackEl.style.display = 'block';
            feedbackEl.style.background = c.bg;
            feedbackEl.style.border = '1px solid ' + c.border;
            feedbackEl.style.color = c.text;
            feedbackEl.textContent = msg;
        }

        function parseHeartRate(value) {
            const flags = value.getUint8(0);
            return (flags & 0x01) ? value.getUint16(1, true) : value.getUint8(1);
        }

        function updateLiveUI() {
            if (!dotEl) return;
            if (state.connected) {
                dotEl.style.background = '#00d4aa';
                dotEl.style.boxShadow = '0 0 8px #00d4aa';
                statusEl.textContent = 'Connected';
                statusEl.style.color = '#00d4aa';
                btn.textContent = '⏹ Disconnect';
                btn.style.borderColor = '#ff4757';
                btn.style.color = '#ff4757';
                deviceInfo.innerHTML = '<span style="color:#a78bfa;">📱 ' + state.deviceName + '</span>' +
                    (state.batteryLevel >= 0 ? ' <span style="color:#00d4aa;">🔋 ' + state.batteryLevel + '%</span>' : '');
                deviceInfo.style.display = 'block';
                liveData.style.display = 'flex';
                document.getElementById('ble-hr-val').textContent = state.lastHR || '--';
                document.getElementById('ble-spo2-val').textContent = state.lastSpO2 ? state.lastSpO2.toFixed(1) : '--';
                document.getElementById('ble-readings-val').textContent = state.readings;
            } else {
                dotEl.style.background = '#5c6b8a';
                dotEl.style.boxShadow = 'none';
                statusEl.textContent = 'Disconnected';
                statusEl.style.color = '#5c6b8a';
                btn.textContent = '🔗 Pair Wearable';
                btn.style.borderColor = '#7c3aed';
                btn.style.color = '#a78bfa';
                deviceInfo.style.display = 'none';
                liveData.style.display = 'none';
            }
        }

        function onDisconnect() {
            state.connected = false;
            state.device = null;
            state.server = null;
            showFeedback('Device disconnected. Click Pair to reconnect.', 'warning');
            updateLiveUI();
        }

        async function connectBLE() {
            // If already connected, disconnect
            if (state.connected && state.device) {
                try { state.device.gatt.disconnect(); } catch(e) {}
                onDisconnect();
                return;
            }

            // Check Web Bluetooth support
            if (!navigator.bluetooth) {
                showFeedback(
                    '⚠ Web Bluetooth requires Chrome/Edge on HTTPS. ' +
                    'On desktop: enable chrome://flags/#enable-web-bluetooth-new-permissions-backend. ' +
                    'On mobile: use Chrome and pair a BLE pulse oximeter.',
                    'warning'
                );
                // Animate the button to show it responded
                btn.style.background = 'rgba(255,179,71,0.15)';
                setTimeout(() => { btn.style.background = 'transparent'; }, 1000);
                return;
            }

            try {
                showFeedback('Opening Bluetooth scanner... Select your device.', 'info');
                btn.textContent = '⏳ Scanning...';
                btn.style.borderColor = '#a78bfa';

                const device = await navigator.bluetooth.requestDevice({
                    filters: [
                        { services: ['heart_rate'] },
                        { services: [0x1822] },
                        { namePrefix: 'BerryMed' },
                        { namePrefix: 'Pulse' },
                        { namePrefix: 'Contec' },
                    ],
                    optionalServices: ['heart_rate', 0x1822, 'battery_service'],
                    acceptAllDevices: false
                });

                state.device = device;
                state.deviceName = device.name || 'BLE Sensor';
                device.addEventListener('gattserverdisconnected', onDisconnect);

                showFeedback('Connecting to ' + state.deviceName + '...', 'info');

                const server = await device.gatt.connect();
                state.server = server;
                state.connected = true;

                // Subscribe to Heart Rate
                try {
                    const hrService = await server.getPrimaryService('heart_rate');
                    const hrChar = await hrService.getCharacteristic('heart_rate_measurement');
                    await hrChar.startNotifications();
                    hrChar.addEventListener('characteristicvaluechanged', (e) => {
                        state.lastHR = parseHeartRate(e.target.value);
                        state.readings++;
                        updateLiveUI();
                    });
                } catch(e) {}

                // Subscribe to Pulse Oximeter
                try {
                    const plxService = await server.getPrimaryService(0x1822);
                    const plxChar = await plxService.getCharacteristic(0x2A5F);
                    await plxChar.startNotifications();
                    plxChar.addEventListener('characteristicvaluechanged', (e) => {
                        state.lastSpO2 = e.target.value.getUint16(0, true) / 10.0;
                        state.readings++;
                        updateLiveUI();
                    });
                } catch(e) {}

                // Read Battery
                try {
                    const batService = await server.getPrimaryService('battery_service');
                    const batChar = await batService.getCharacteristic('battery_level');
                    const bv = await batChar.readValue();
                    state.batteryLevel = bv.getUint8(0);
                } catch(e) {}

                showFeedback('✓ Connected to ' + state.deviceName + '! Receiving live data.', 'success');
                updateLiveUI();

            } catch (err) {
                if (err.name === 'NotFoundError') {
                    showFeedback('No device selected. Click Pair to try again.', 'info');
                } else if (err.name === 'SecurityError') {
                    showFeedback(
                        '⚠ Bluetooth blocked by browser security. Requires HTTPS or localhost with Chrome/Edge.',
                        'error'
                    );
                } else {
                    showFeedback('Connection failed: ' + (err.message || err), 'error');
                }
                state.connected = false;
                updateLiveUI();
            }
        }

        // Attach click handler directly
        if (btn) {
            btn.addEventListener('click', connectBLE);
        }
    })();
    </script>
    """
