"""
Medisynth Live – Real Notification Service

Provider priority (auto-tries all until one succeeds):
1. Twilio SMS         — if TWILIO_ACCOUNT_SID set
2. Fast2SMS           — if FAST2SMS_API_KEY set (FREE India)
3. CallMeBot WhatsApp — if CALLMEBOT_API_KEY set (FREE)
4. Email SMTP         — if SMTP_EMAIL set
5. Desktop Notify     — ALWAYS works (Windows toast + browser popup)
6. WhatsApp Compose   — Opens WhatsApp with pre-filled message
"""

import os
import time
import json
import threading
import urllib.request
import urllib.parse
from dataclasses import dataclass, field
from typing import Optional, List, Dict


@dataclass
class NotificationResult:
    success: bool
    provider: str
    recipient: str
    message_preview: str
    error: str = ""
    timestamp: float = 0.0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()


class NotificationService:
    """Multi-provider notification service with desktop fallback."""

    def __init__(self):
        self.sent_log: List[NotificationResult] = []
        self.last_send_time: float = 0
        self.cooldown_seconds: float = 30
        self._sending: bool = False
        self._pending_browser_alerts: List[dict] = []
        self._pending_whatsapp_links: List[str] = []

        # ── Provider credentials from env ──
        self.twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
        self.twilio_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
        self.twilio_from = os.environ.get("TWILIO_PHONE_NUMBER", "")
        self.fast2sms_key = os.environ.get("FAST2SMS_API_KEY", "")
        self.callmebot_key = os.environ.get("CALLMEBOT_API_KEY", "")
        self.smtp_email = os.environ.get("SMTP_EMAIL", "")
        self.smtp_password = os.environ.get("SMTP_PASSWORD", "")
        self.smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.environ.get("SMTP_PORT", "587"))

        # ntfy.sh — FREE push notifications, zero config
        self.ntfy_topic = os.environ.get("NTFY_TOPIC", "medisynth-jvovi4b4")
        self.ntfy_enabled = True  # Always enabled

    def _clean_phone(self, phone: str) -> str:
        clean = phone.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if clean.startswith("+91"):
            return clean
        if clean.startswith("91") and len(clean) >= 12:
            return "+" + clean
        if clean.startswith("+"):
            return clean
        if clean.startswith("0"):
            clean = clean[1:]
        return "+91" + clean

    def _get_indian_number(self, phone: str) -> str:
        clean = self._clean_phone(phone)
        if clean.startswith("+91"):
            return clean[3:]
        return clean.lstrip("+")

    def get_available_provider(self) -> str:
        if self.twilio_sid and self.twilio_token and self.twilio_from:
            return "twilio"
        if self.fast2sms_key:
            return "fast2sms"
        if self.callmebot_key:
            return "callmebot"
        if self.smtp_email and self.smtp_password:
            return "email"
        return "desktop"

    def send_emergency_alert(self, phone: str, contact_name: str, message: str,
                              maps_link: str = "",
                              patient_name: str = "Patient") -> NotificationResult:
        """Send alert — tries external providers first, always falls back to desktop."""
        # Cooldown
        recent = [r for r in self.sent_log
                  if r.recipient == phone and time.time() - r.timestamp < self.cooldown_seconds]
        if recent:
            return NotificationResult(
                success=False, provider="cooldown", recipient=phone,
                message_preview="Cooldown active",
                error=f"Wait {int(self.cooldown_seconds - (time.time() - recent[-1].timestamp))}s"
            )

        # Don't duplicate location if message already has it
        full_msg = message
        if maps_link and maps_link not in message:
            full_msg += f"\nLocation: {maps_link}"

        # Try external providers first
        providers_to_try = []
        if self.twilio_sid and self.twilio_token:
            providers_to_try.append("twilio")
        if self.fast2sms_key:
            providers_to_try.append("fast2sms")
        if self.callmebot_key:
            providers_to_try.append("callmebot")
        if self.smtp_email and self.smtp_password:
            providers_to_try.append("email")

        for provider in providers_to_try:
            try:
                if provider == "twilio":
                    result = self._send_twilio(phone, full_msg)
                elif provider == "fast2sms":
                    result = self._send_fast2sms(phone, full_msg)
                elif provider == "callmebot":
                    result = self._send_callmebot(phone, full_msg)
                elif provider == "email":
                    result = self._send_email(phone, name, full_msg)
                else:
                    continue
                if result.success:
                    self.sent_log.append(result)
                    self.last_send_time = time.time()
                    return result
            except Exception:
                continue

        # ALL external providers failed (or none configured)
        # -> Try ntfy.sh (real phone push) + Desktop fallback
        ntfy_result = self._send_ntfy(phone, patient_name, full_msg, maps_link)
        if ntfy_result.success:
            self.sent_log.append(ntfy_result)
            self.last_send_time = time.time()
            # Also fire desktop + WhatsApp compose
            self._send_desktop(phone, contact_name, full_msg, maps_link)
            return ntfy_result

        # Final fallback: desktop only
        result = self._send_desktop(phone, contact_name, full_msg, maps_link)
        self.sent_log.append(result)
        self.last_send_time = time.time()
        return result

    def send_to_all_contacts(self, contacts: list, message: str,
                              maps_link: str = "",
                              patient_name: str = "Patient") -> List[NotificationResult]:
        results = []
        for contact in contacts:
            result = self.send_emergency_alert(
                contact.phone, contact.name, message, maps_link,
                patient_name=patient_name,
            )
            results.append(result)
        return results

    def send_to_all_contacts_async(self, contacts: list, message: str,
                                     maps_link: str = ""):
        if self._sending:
            return
        self._sending = True

        def _run():
            try:
                self.send_to_all_contacts(contacts, message, maps_link)
            finally:
                self._sending = False

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

    # ═══════════════════════════════════════════
    #  NTFY.SH — FREE PHONE PUSH (ZERO CONFIG)
    # ═══════════════════════════════════════════

    def _send_ntfy(self, phone: str, patient_name: str, message: str,
                    maps_link: str = "") -> NotificationResult:
        """Send push notification via ntfy.sh — FREE, no signup, no API key."""
        if not self.ntfy_enabled or not self.ntfy_topic:
            return NotificationResult(
                success=False, provider="ntfy", recipient=phone,
                message_preview="", error="ntfy disabled"
            )
        try:
            url = f"https://ntfy.sh/{self.ntfy_topic}"
            # Message already contains full vitals + location, send as-is
            body = message[:1000]

            data = body.encode("utf-8")
            req = urllib.request.Request(url, data=data, method="POST")
            req.add_header("Title", f"MEDISYNTH EMERGENCY - {patient_name}")
            req.add_header("Priority", "urgent")
            req.add_header("Tags", "rotating_light,heart,warning")
            if maps_link:
                req.add_header("Click", maps_link)

            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    result_data = json.loads(resp.read().decode())
                    return NotificationResult(
                        success=True, provider="ntfy.sh",
                        recipient=phone,
                        message_preview=f"Push sent (topic: {self.ntfy_topic})"
                    )
                return NotificationResult(
                    success=False, provider="ntfy", recipient=phone,
                    message_preview="", error=f"HTTP {resp.status}"
                )
        except Exception as e:
            return NotificationResult(
                success=False, provider="ntfy", recipient=phone,
                message_preview="", error=str(e)[:80]
            )

    def get_ntfy_subscribe_url(self) -> str:
        """Get the URL for the user to subscribe on their phone."""
        return f"https://ntfy.sh/{self.ntfy_topic}"

    # ═══════════════════════════════════════════
    #  DESKTOP + BROWSER (ALWAYS WORKS)
    # ═══════════════════════════════════════════

    def _send_desktop(self, phone: str, name: str, message: str,
                       maps_link: str = "") -> NotificationResult:
        """Send Windows desktop toast + queue browser notification + WhatsApp link."""
        success = False
        preview_parts = []

        # 1. Windows Toast Notification
        try:
            from plyer import notification as plyer_notify
            plyer_notify.notify(
                title="🚨 MEDISYNTH EMERGENCY",
                message=f"{name} ({phone})\nHealth Score Critical!\n{message[:100]}",
                app_name="Medisynth Live",
                timeout=30,
            )
            success = True
            preview_parts.append("Desktop ✔")
        except Exception as e:
            preview_parts.append(f"Desktop: {str(e)[:30]}")

        # 2. Queue browser JS notification (rendered on next tick)
        short_msg = message.replace("\n", " ")[:120]
        self._pending_browser_alerts.append({
            "title": f"🚨 EMERGENCY — {name}",
            "body": short_msg,
            "phone": phone,
        })
        preview_parts.append("Browser ✔")
        success = True

        # 3. Build WhatsApp compose link (user clicks to send)
        clean = self._clean_phone(phone).lstrip("+")
        wa_msg = urllib.parse.quote(message[:500])
        wa_link = f"https://wa.me/{clean}?text={wa_msg}"
        self._pending_whatsapp_links.append(wa_link)
        preview_parts.append("WhatsApp link ✔")

        return NotificationResult(
            success=success,
            provider="desktop+browser",
            recipient=phone,
            message_preview=" | ".join(preview_parts),
        )

    def get_pending_browser_alerts(self) -> List[dict]:
        """Get and clear pending browser notifications."""
        alerts = list(self._pending_browser_alerts)
        self._pending_browser_alerts.clear()
        return alerts

    def get_pending_whatsapp_links(self) -> List[str]:
        """Get and clear pending WhatsApp compose links."""
        links = list(self._pending_whatsapp_links)
        self._pending_whatsapp_links.clear()
        return links

    # ═══════════════════════════════════════════
    #  EXTERNAL PROVIDERS
    # ═══════════════════════════════════════════

    def _send_twilio(self, phone: str, message: str) -> NotificationResult:
        try:
            import base64
            clean = self._clean_phone(phone)
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_sid}/Messages.json"
            data = urllib.parse.urlencode({
                "To": clean, "From": self.twilio_from, "Body": message[:1600],
            }).encode()
            auth = base64.b64encode(f"{self.twilio_sid}:{self.twilio_token}".encode()).decode()
            req = urllib.request.Request(url, data=data, method="POST")
            req.add_header("Authorization", f"Basic {auth}")
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode())
                return NotificationResult(
                    success=True, provider="twilio", recipient=clean,
                    message_preview=f"SID: {result.get('sid', 'OK')}"
                )
        except Exception as e:
            return NotificationResult(
                success=False, provider="twilio", recipient=phone,
                message_preview="", error=str(e)[:80]
            )

    def _send_fast2sms(self, phone: str, message: str) -> NotificationResult:
        try:
            num = self._get_indian_number(phone)
            if len(num) != 10:
                return NotificationResult(
                    success=False, provider="fast2sms", recipient=phone,
                    message_preview="", error=f"Need 10-digit number, got: {num}"
                )
            url = "https://www.fast2sms.com/dev/bulkV2"
            data = urllib.parse.urlencode({
                "route": "q", "message": message[:160],
                "language": "english", "flash": "0", "numbers": num,
            }).encode()
            req = urllib.request.Request(url, data=data, method="POST")
            req.add_header("authorization", self.fast2sms_key)
            req.add_header("Content-Type", "application/x-www-form-urlencoded")
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode())
                if result.get("return"):
                    return NotificationResult(
                        success=True, provider="fast2sms", recipient=f"+91{num}",
                        message_preview="SMS sent via Fast2SMS"
                    )
                err = result.get("message", "Failed")
                if isinstance(err, list):
                    err = err[0]
                return NotificationResult(
                    success=False, provider="fast2sms", recipient=phone,
                    message_preview="", error=str(err)[:80]
                )
        except Exception as e:
            return NotificationResult(
                success=False, provider="fast2sms", recipient=phone,
                message_preview="", error=str(e)[:80]
            )

    def _send_callmebot(self, phone: str, message: str) -> NotificationResult:
        try:
            num = self._clean_phone(phone).lstrip("+")
            encoded_msg = urllib.parse.quote(message[:1000])
            url = f"https://api.callmebot.com/whatsapp.php?phone={num}&text={encoded_msg}&apikey={self.callmebot_key}"
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "MedisynthLive/1.0")
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = resp.read().decode()
                if resp.status == 200 and "sent" in body.lower():
                    return NotificationResult(
                        success=True, provider="callmebot", recipient=self._clean_phone(phone),
                        message_preview="WhatsApp sent via CallMeBot"
                    )
                return NotificationResult(
                    success=False, provider="callmebot", recipient=phone,
                    message_preview="", error=body[:80]
                )
        except Exception as e:
            return NotificationResult(
                success=False, provider="callmebot", recipient=phone,
                message_preview="", error=str(e)[:80]
            )

    def _send_email(self, phone: str, name: str, message: str) -> NotificationResult:
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart()
            msg['From'] = self.smtp_email
            msg['To'] = self.smtp_email
            msg['Subject'] = f"🚨 MEDISYNTH EMERGENCY - {name} ({phone})"
            html = f"""<html><body style="font-family:sans-serif;background:#0a0e1a;color:#e8eaf6;padding:20px;">
            <h2 style="color:#ff4757;">🚨 Emergency Alert</h2>
            <p><b>{name}</b> ({phone})</p>
            <pre style="background:#1a1e30;padding:16px;border-radius:8px;color:#e8eaf6;white-space:pre-wrap;">{message}</pre>
            </body></html>"""
            msg.attach(MIMEText(html, 'html'))
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_email, self.smtp_password)
                server.send_message(msg)
            return NotificationResult(
                success=True, provider="email", recipient=phone,
                message_preview=f"Email → {self.smtp_email}"
            )
        except Exception as e:
            return NotificationResult(
                success=False, provider="email", recipient=phone,
                message_preview="", error=str(e)[:80]
            )

    # ═══════════════════════════════════════════
    #  STATUS
    # ═══════════════════════════════════════════

    def get_provider_status(self) -> Dict[str, str]:
        active = self.get_available_provider()
        # If no external provider, show ntfy as active since it actually sends to phone
        if active == "desktop" and self.ntfy_enabled:
            active_label = "📲 ntfy.sh Push (Free)"
        else:
            labels = {
                "twilio": "📱 Twilio SMS",
                "fast2sms": "🇮🇳 Fast2SMS",
                "callmebot": "💬 WhatsApp",
                "email": "📧 Email",
                "desktop": "🖥️ Desktop Only",
            }
            active_label = labels.get(active, active)
        return {
            "active": active,
            "active_label": active_label,
            "twilio": "✅" if self.twilio_sid else "—",
            "fast2sms": "✅" if self.fast2sms_key else "—",
            "callmebot": "✅" if self.callmebot_key else "—",
            "email": "✅" if self.smtp_email else "—",
            "ntfy": "✅ Free" if self.ntfy_enabled else "—",
            "desktop": "✅",
        }

    def get_sent_count(self) -> int:
        return len(self.sent_log)

    def get_success_count(self) -> int:
        return sum(1 for r in self.sent_log if r.success)

    def get_last_results(self, n: int = 5) -> List[NotificationResult]:
        return self.sent_log[-n:]
