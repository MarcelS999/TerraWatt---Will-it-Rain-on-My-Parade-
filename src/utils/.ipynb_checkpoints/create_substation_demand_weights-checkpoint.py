import geopandas as gpd
import pandas as pd
# ======================================================
# CONFIG
# ======================================================
import os

# Always resolve project root (2 levels up from utils/)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

SUBS_PATH = os.path.join(PROJECT_ROOT, "data", "osm", "substations_110kV_clean.geojson")
BUILTUP_PATH = os.path.join(PROJECT_ROOT, "data", "shape", "ne_10m_urban_areas.shp")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "substation_demand_weights.csv")

BUFFER_RADIUS_M = 15000  # ~15 km

# ======================================================
# LOAD DATA
# ======================================================
subs = gpd.read_file(SUBS_PATH)
builtup = gpd.read_file(BUILTUP_PATH)

# Ensure projected CRS for area-based calculations
subs = subs.to_crs("EPSG:3857")
builtup = builtup.to_crs("EPSG:3857")

# Clip built-up polygons roughly to substation region
builtup = builtup.clip(subs.unary_union.buffer(20000))

# ======================================================
# COMPUTE BUILT-UP AREA WEIGHT PER SUBSTATION
# ======================================================
print("🏙️ Computing built-up area coverage around substations...")

subs["builtup_area"] = 0.0
for i, sub in subs.iterrows():
    buf = sub.geometry.buffer(BUFFER_RADIUS_M)
    intersect = builtup.intersection(buf)
    total_area = intersect.area.sum()
    subs.at[i, "builtup_area"] = total_area

# Handle empty areas (rural substations)
subs["builtup_area"] = subs["builtup_area"].replace(0, subs["builtup_area"].mean() * 0.1)

# Normalize
subs["demand_weight"] = subs["builtup_area"] / subs["builtup_area"].sum()

# ======================================================
# SAVE RESULTS
# ======================================================
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

subs_out = subs[["name", "demand_weight"]].copy()
subs_out.to_csv(OUTPUT_PATH, index=False)

print(f"✅ Saved demand weights → {OUTPUT_PATH}")
print(subs_out.head())
print(f"Sum of weights: {subs_out['demand_weight'].sum():.4f} (should be 1.0000)")
