"""
Medisynth Live – Audio Alert System
Browser-based sound alerts using HTML5 Audio API with Web Audio synthesized tones.
"""

import streamlit as st


def get_alert_audio_js(severity: str = "critical") -> str:
    """Generate JavaScript for browser audio alert using Web Audio API synthesis."""
    if severity == "critical":
        # Urgent alarm: two-tone alternating siren
        return """
        <script>
        (function() {
            if (window._medisynth_audio_muted) return;
            try {
                const ctx = new (window.AudioContext || window.webkitAudioContext)();
                function playTone(freq, start, dur) {
                    const osc = ctx.createOscillator();
                    const gain = ctx.createGain();
                    osc.type = 'square';
                    osc.frequency.value = freq;
                    gain.gain.setValueAtTime(0.08, ctx.currentTime + start);
                    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + start + dur);
                    osc.connect(gain);
                    gain.connect(ctx.destination);
                    osc.start(ctx.currentTime + start);
                    osc.stop(ctx.currentTime + start + dur);
                }
                playTone(880, 0, 0.15);
                playTone(660, 0.18, 0.15);
                playTone(880, 0.36, 0.15);
                playTone(660, 0.54, 0.15);
            } catch(e) {}
        })();
        </script>
        """
    elif severity == "warning":
        # Warning chime: gentle two-note
        return """
        <script>
        (function() {
            if (window._medisynth_audio_muted) return;
            try {
                const ctx = new (window.AudioContext || window.webkitAudioContext)();
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = 'sine';
                osc.frequency.value = 523;
                gain.gain.setValueAtTime(0.06, ctx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.4);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start();
                osc.stop(ctx.currentTime + 0.4);
            } catch(e) {}
        })();
        </script>
        """
    else:
        # Info beep: soft single tone
        return """
        <script>
        (function() {
            if (window._medisynth_audio_muted) return;
            try {
                const ctx = new (window.AudioContext || window.webkitAudioContext)();
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = 'sine';
                osc.frequency.value = 440;
                gain.gain.setValueAtTime(0.03, ctx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.2);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start();
                osc.stop(ctx.currentTime + 0.2);
            } catch(e) {}
        })();
        </script>
        """


def get_mute_toggle_js(muted: bool) -> str:
    """JavaScript to set the global mute flag."""
    return f"""
    <script>
        window._medisynth_audio_muted = {'true' if muted else 'false'};
    </script>
    """


def play_alert(severity: str = "critical"):
    """Inject audio alert into the page."""
    import streamlit.components.v1 as components
    components.html(get_alert_audio_js(severity), height=0)


def inject_mute_state(muted: bool):
    """Inject mute state JavaScript."""
    import streamlit.components.v1 as components
    components.html(get_mute_toggle_js(muted), height=0)
