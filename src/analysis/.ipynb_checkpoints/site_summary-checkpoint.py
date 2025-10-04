"""
site_summary.py
----------------
Generates a smart, human-readable site summary for a given location.
If ERA5 2019 NetCDF exists, computes the *true* capacity factor (CF)
from hourly wind data. Otherwise, falls back to climatology-based CF.

Also returns a structured JSON-friendly dict for Streamlit sidebar display.
"""

import os
import geopandas as gpd
import rasterio
import numpy as np
import xarray as xr
from shapely.geometry import Point
from src.analysis.compute_cf_2019 import compute_cf_2019  # ✅ your CF function

# ============================================================
# CONFIG
# ============================================================
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
ERA5_DIR = os.path.join(PROJECT_ROOT, "data", "era5")
GRID_DIR = os.path.join(PROJECT_ROOT, "data", "osm")

MEAN_TIF = os.path.join(ERA5_DIR, "era5_ireland_mean_1994_2024.tif")
STD_TIF  = os.path.join(ERA5_DIR, "era5_ireland_std_1994_2024.tif")
SUBS_PATH = os.path.join(GRID_DIR, "substations_110kV_clean.geojson")

# ============================================================
# DATA HELPERS
# ============================================================
def extract_raster_value(tif_path, lon, lat):
    """Sample raster value at a given coordinate (correct lon/lat order)."""
    with rasterio.open(tif_path) as src:
        if src.bounds.left > 0 and lon < 0:
            lon = lon % 360
        lat = np.clip(lat, src.bounds.bottom, src.bounds.top)
        lon = np.clip(lon, src.bounds.left, src.bounds.right)
        val = list(src.sample([(lon, lat)]))[0][0]
        if np.isnan(val) or np.isinf(val):
            return np.nan
        return float(val)

def find_nearest_substation(lon, lat, subs_path):
    """Find the closest substation and its distance (km)."""
    subs = gpd.read_file(subs_path)
    if subs.crs.to_string() != "EPSG:4326":
        subs = subs.to_crs("EPSG:4326")
    pt = Point(lon, lat)
    subs["distance_km"] = subs.geometry.distance(pt) * 111  # deg→km
    nearest = subs.sort_values("distance_km").iloc[0]
    possible_name_cols = ["NAME", "Name", "name", "Sub_Name", "Station", "Substation"]
    name_col = next((c for c in possible_name_cols if c in subs.columns), None)
    sub_name = str(nearest[name_col]) if name_col else "Unknown Substation"
    return sub_name, float(nearest["distance_km"])

def estimate_grid_cost(distance_km):
    """Estimate cost (€) of connecting to nearest 110 kV substation."""
    base_cost = 250_000
    per_km_cost = 25_000
    return base_cost + per_km_cost * distance_km

# ============================================================
# NARRATIVE (suitability removed)
# ============================================================
def generate_narrative(name, mean_ws, std_ws, cf, sub_name, dist_km, grid_cost):
    """Generate clean, human-readable summary (no suitability)."""
    if np.isnan(mean_ws) or mean_ws <= 1.0:
        return (
            f"📍 **Site Summary: {name}**\n\n"
            f"Insufficient wind data available for this location. "
            f"The nearest substation is **{sub_name}**, about **{dist_km:.1f} km** away. "
            f"Estimated grid connection cost: **€{grid_cost/1e3:.0f} k**."
        )

    wind_desc = (
        "exceptional" if mean_ws > 9.5 else
        "strong" if mean_ws > 8.0 else
        "moderate" if mean_ws > 6.5 else
        "weak"
    )

    if cf < 0.15:
        cf_phrase = "poor generation potential"
    elif cf < 0.30:
        cf_phrase = "modest generation potential"
    elif cf < 0.45:
        cf_phrase = "solid energy potential"
    else:
        cf_phrase = "excellent energy potential"

    return (
        f"📍 **Site Summary: {name}**\n\n"
        f"This location experiences **{wind_desc}** average winds of about "
        f"{mean_ws:.1f} m/s, with a standard deviation of **{std_ws:.2f} m/s**. "
        f"The computed 2019 capacity factor of **{cf*100:.1f}%** suggests **{cf_phrase}**. "
        f"The nearest 110 kV substation is **{sub_name}**, approximately "
        f"**{dist_km:.1f} km** away, with an estimated grid connection cost of "
        f"roughly **€{grid_cost/1e3:.0f} k**."
    )

# ============================================================
# MAIN SUMMARY
# ============================================================
def summarize_site(name: str, lat: float, lon: float):
    """Generate full site summary and return as dict."""
    from src.processing.wind_extrapolation import extrapolate_wind_expected

    try:
        # --- 1️⃣ Extract mean (10m) & std dev ---
        mean_ws_10m = extract_raster_value(MEAN_TIF, lon, lat)
        std_ws = extract_raster_value(STD_TIF, lon, lat)

        # --- 2️⃣ Extrapolate to 100m hub height ---
        mean_ws = extrapolate_wind_expected(mean_ws_10m, ref_height=10, hub_height=100, z0=0.03)

        # --- 3️⃣ Find nearest substation ---
        sub_name, dist_km = find_nearest_substation(lon, lat, SUBS_PATH)
        grid_cost = estimate_grid_cost(dist_km)

        # --- 4️⃣ Compute capacity factor ---
        try:
            cf = compute_cf_2019(lat, lon)
            cf_source = "ERA5 2019 (3 MW turbine model)"
        except Exception as e:
            print(f"⚠️ CF computation failed: {e}")
            cf = 0.005 * (mean_ws ** 2.5)
            cf_source = "Climatology fallback"

        cf = np.clip(cf, 0, 0.55)

        # --- 5️⃣ Generate human summary ---
        summary_text = generate_narrative(name, mean_ws, std_ws, cf, sub_name, dist_km, grid_cost)

        # --- 6️⃣ Package output ---
        summary = {
            "site_name": name,
            "latitude": lat,
            "longitude": lon,
            "mean_wind_speed": round(mean_ws, 2),
            "std_wind_speed": round(std_ws, 2),
            "capacity_factor": round(cf, 3),
            "capacity_factor_source": cf_source,
            "nearest_substation": sub_name,
            "distance_km": round(dist_km, 2),
            "grid_cost_eur": int(grid_cost),
            "summary_text": summary_text,
        }

        print(f"📊 {name} ({lat:.2f}, {lon:.2f}) → CF {cf*100:.1f}% | Sub {sub_name} ({dist_km:.1f} km)")
        return summary

    except Exception as e:
        print(f"❌ summarize_site() failed: {e}")
        return {
            "site_name": name,
            "latitude": lat,
            "longitude": lon,
            "summary_text": f"⚠️ Unable to compute summary: {e}"
        }

# ============================================================
# DEMO
# ============================================================
if __name__ == "__main__":
    s = summarize_site("Co. Mayo", 53.9, -9.3)
    print("\n" + s["summary_text"])
