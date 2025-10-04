# ============================================================
# 🚀 AI-ASSISTED CODE NOTICE
# This file was developed with assistance from OpenAI's ChatGPT (GPT-5)
# as part of the NASA Space Apps 2025 project:
# “TerraWatt — Will It Rain on My Parade?”
# ============================================================

import geopandas as gpd
import os

def simplify_geojson(input_path, output_path, tolerance=0.001):
    gdf = gpd.read_file(input_path)
    gdf = gdf.to_crs(4326)
    
    # keep only useful columns
    keep = ["name", "voltage", "voltage_kV", "power", "geometry"]
    gdf = gdf[[c for c in keep if c in gdf.columns]]
    
    # simplify geometry
    gdf["geometry"] = gdf["geometry"].simplify(tolerance, preserve_topology=True)
    gdf = gdf[gdf.geometry.notnull()]
    
    gdf.to_file(output_path, driver="GeoJSON")
    print(f"✅ Saved simplified → {output_path} ({len(gdf)} features)")

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(PROJECT_ROOT, "data", "osm")

simplify_geojson(
    os.path.join(data_dir, "lines_110kV_clean.geojson"),
    os.path.join(data_dir, "lines_110kV_light.geojson")
)
simplify_geojson(
    os.path.join(data_dir, "substations_110kV_clean.geojson"),
    os.path.join(data_dir, "substations_110kV_light.geojson")
)
