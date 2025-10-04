# ============================================================
# 🚀 AI-ASSISTED CODE NOTICE
# This file was developed with assistance from OpenAI's ChatGPT (GPT-5)
# as part of the NASA Space Apps 2025 project:
# “TerraWatt — Will It Rain on My Parade?”
# ============================================================

import geopandas as gpd
import pandas as pd

def load_wind_farms(shp_path="data/generators/Wind Farms June 2022_ESPG3857.shp"):
    """
    Load and clean the SEAI/Wind Energy Ireland shapefile of wind farms in Ireland.

    Parameters
    ----------
    shp_path : str
        Path to the shapefile (.shp)
    Returns
    -------
    gdf : GeoDataFrame
        Cleaned GeoDataFrame with name, capacity, and lat/lon
    """
    gdf = gpd.read_file(shp_path)
    gdf = gdf.to_crs("EPSG:4326")  # convert to lat/lon

    # Normalize column names
    gdf.columns = gdf.columns.str.lower()

    # Attempt to find key fields
    name_col = next((c for c in gdf.columns if "name" in c.lower()), None)
    cap_col = next((c for c in gdf.columns if "cap" in c.lower()), None)

    # Extract lat/lon
    gdf["lat"] = gdf.geometry.y
    gdf["lon"] = gdf.geometry.x

    # Simplify final structure
    gdf_clean = gdf[[name_col, "lat", "lon", cap_col]].rename(
        columns={name_col: "name", cap_col: "capacity_mw"}
    )

    gdf_clean = gdf_clean.dropna(subset=["lat", "lon", "capacity_mw"])

    print(f"✅ Loaded {len(gdf_clean)} Irish wind farms from shapefile")
    return gdf_clean
