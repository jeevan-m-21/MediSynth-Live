"""
Medisynth Live – Location Service
Gets REAL device location via IP geolocation (no browser permission needed).
"""

import urllib.request
import json
import time
import streamlit as st

# Cached location to avoid repeated API calls
_cached_location = None
_cache_time = 0
_CACHE_TTL = 300  # 5 minutes


def get_real_location() -> dict:
    """Get real location via IP-based geolocation. Returns dict with lat, lng, city, region."""
    global _cached_location, _cache_time

    if _cached_location and (time.time() - _cache_time < _CACHE_TTL):
        return _cached_location

    try:
        req = urllib.request.Request(
            "http://ip-api.com/json/?fields=status,lat,lon,city,regionName,country",
            headers={"User-Agent": "MedisynthLive/1.0"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            if data.get("status") == "success":
                _cached_location = {
                    "lat": data["lat"],
                    "lng": data["lon"],
                    "city": data.get("city", ""),
                    "region": data.get("regionName", ""),
                    "country": data.get("country", ""),
                }
                _cache_time = time.time()
                return _cached_location
    except Exception:
        pass

    # Fallback — still try to return something
    return {"lat": 0, "lng": 0, "city": "Unknown", "region": "", "country": ""}


def build_maps_link(lat: float, lng: float) -> str:
    """Build a Google Maps link from coordinates."""
    return f"https://www.google.com/maps?q={lat},{lng}"


def format_location(lat: float, lng: float) -> str:
    """Format coordinates for display."""
    lat_dir = "N" if lat >= 0 else "S"
    lng_dir = "E" if lng >= 0 else "W"
    return f"{abs(lat):.4f}°{lat_dir}, {abs(lng):.4f}°{lng_dir}"


def request_location():
    """Get and store location in session state."""
    loc = get_real_location()
    if loc and loc.get("lat"):
        st.session_state["location"] = loc
