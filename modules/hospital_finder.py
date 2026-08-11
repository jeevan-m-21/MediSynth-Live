"""
Medisynth Live – Nearby Hospital Finder
Uses OpenStreetMap Overpass API (free, no API key) to find hospitals
near the patient's live GPS coordinates.
"""

import urllib.request
import urllib.parse
import json
import time
import math
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class NearbyHospital:
    """A nearby hospital with location and contact info."""
    name: str
    lat: float
    lng: float
    distance_km: float
    address: str = ""
    phone: str = ""
    emergency: bool = False
    maps_url: str = ""
    directions_url: str = ""


# Cache to avoid repeated API calls
_cached_hospitals: List[NearbyHospital] = []
_cache_lat: float = 0
_cache_lng: float = 0
_cache_time: float = 0
_CACHE_TTL = 120  # 2 minutes


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in km using Haversine formula."""
    R = 6371  # Earth radius in km
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(d_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def find_nearby_hospitals(lat: float, lng: float, radius_km: float = 5,
                          max_results: int = 5) -> List[NearbyHospital]:
    """Find nearby hospitals using OpenStreetMap Overpass API.

    Args:
        lat: Patient latitude
        lng: Patient longitude
        radius_km: Search radius in km (default 5)
        max_results: Maximum hospitals to return

    Returns:
        List of NearbyHospital sorted by distance
    """
    global _cached_hospitals, _cache_lat, _cache_lng, _cache_time

    # Return cache if still fresh and location hasn't moved much
    if (_cached_hospitals and
        time.time() - _cache_time < _CACHE_TTL and
        _haversine(lat, lng, _cache_lat, _cache_lng) < 0.5):
        return _cached_hospitals

    hospitals = []

    try:
        hospitals = _query_overpass(lat, lng, radius_km)
    except Exception:
        pass

    if not hospitals:
        # Fallback: return Google Maps search link
        hospitals = _fallback_search(lat, lng)

    # Calculate distances and sort
    for h in hospitals:
        h.distance_km = round(_haversine(lat, lng, h.lat, h.lng), 2)
        h.maps_url = f"https://www.google.com/maps/search/?api=1&query={h.lat},{h.lng}"
        h.directions_url = (
            f"https://www.google.com/maps/dir/{lat},{lng}/{h.lat},{h.lng}"
        )

    hospitals.sort(key=lambda h: h.distance_km)
    hospitals = hospitals[:max_results]

    # Update cache
    _cached_hospitals = hospitals
    _cache_lat = lat
    _cache_lng = lng
    _cache_time = time.time()

    return hospitals


def _query_overpass(lat: float, lng: float, radius_km: float) -> List[NearbyHospital]:
    """Query OpenStreetMap Overpass API for hospitals."""
    radius_m = int(radius_km * 1000)

    # Overpass QL query: find hospitals and clinics near coordinates
    query = f"""
    [out:json][timeout:8];
    (
      node["amenity"="hospital"](around:{radius_m},{lat},{lng});
      way["amenity"="hospital"](around:{radius_m},{lat},{lng});
      node["amenity"="clinic"](around:{radius_m},{lat},{lng});
      node["healthcare"="hospital"](around:{radius_m},{lat},{lng});
    );
    out center body 10;
    """

    url = "https://overpass-api.de/api/interpreter"
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("User-Agent", "MedisynthLive/1.0")

    hospitals = []
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read().decode())

    seen_names = set()
    for element in result.get("elements", []):
        tags = element.get("tags", {})
        name = tags.get("name", "").strip()

        if not name or name.lower() in seen_names:
            continue
        seen_names.add(name.lower())

        # Get coordinates (nodes have direct lat/lon, ways have center)
        h_lat = element.get("lat") or element.get("center", {}).get("lat", 0)
        h_lng = element.get("lon") or element.get("center", {}).get("lon", 0)

        if not h_lat or not h_lng:
            continue

        # Extract useful tags
        address_parts = []
        for key in ["addr:full", "addr:street", "addr:city"]:
            val = tags.get(key, "")
            if val:
                address_parts.append(val)
        address = ", ".join(address_parts) if address_parts else ""

        phone = tags.get("phone", tags.get("contact:phone", ""))
        emergency = tags.get("emergency", "") == "yes"

        hospitals.append(NearbyHospital(
            name=name,
            lat=h_lat,
            lng=h_lng,
            distance_km=0,
            address=address,
            phone=phone,
            emergency=emergency,
        ))

    return hospitals


def _fallback_search(lat: float, lng: float) -> List[NearbyHospital]:
    """Fallback: return a Google Maps hospital search link as a single result."""
    return [NearbyHospital(
        name="Search Nearby Hospitals",
        lat=lat,
        lng=lng,
        distance_km=0,
        address="Open Google Maps to find hospitals near you",
        maps_url=f"https://www.google.com/maps/search/hospital/@{lat},{lng},14z",
        directions_url=f"https://www.google.com/maps/search/hospital/@{lat},{lng},14z",
    )]


def format_hospitals_for_message(hospitals: List[NearbyHospital], max_count: int = 3) -> str:
    """Format hospital list for inclusion in emergency notification text."""
    if not hospitals:
        return ""

    lines = ["--- NEARBY HOSPITALS ---"]
    for i, h in enumerate(hospitals[:max_count], 1):
        dist = f"{h.distance_km:.1f}km" if h.distance_km > 0 else ""
        lines.append(f"{i}. {h.name} ({dist})")
        if h.phone:
            lines.append(f"   Tel: {h.phone}")
        lines.append(f"   Directions: {h.directions_url}")

    return "\n".join(lines)
