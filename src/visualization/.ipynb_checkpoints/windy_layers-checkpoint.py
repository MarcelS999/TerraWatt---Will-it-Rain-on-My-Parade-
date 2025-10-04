# ============================================================
# 🚀 AI-ASSISTED CODE NOTICE
# This file was developed with assistance from OpenAI's ChatGPT (GPT-5)
# as part of the NASA Space Apps 2025 project:
# “TerraWatt — Will It Rain on My Parade?”
# ============================================================

import requests
import pandas as pd
import folium
from folium.plugins import HeatMap

# --- NASA Grid Fetcher ---
def get_nasa_grid(lat_min, lat_max, lon_min, lon_max, params=["WS50M", "WS100M"]):
    """
    Fetch NASA POWER climatology data for a bounding box region.
    Returns a DataFrame with seasonal + annual values for each parameter.
    """
    url = (
        "https://power.larc.nasa.gov/api/temporal/climatology/region?"
        f"parameters={','.join(params)}"
        f"&community=RE&longitude-min={lon_min}&longitude-max={lon_max}"
        f"&latitude-min={lat_min}&latitude-max={lat_max}&format=JSON"
    )
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()

    df_list = []
    for p in data["properties"]["parameter"]:
        grid = data["properties"]["parameter"][p]
        for key, values in grid.items():
            lat, lon = map(float, key.split(","))
            df_list.append({
                "lat": lat,
                "lon": lon,
                "param": p,
                **values
            })

    df = pd.DataFrame(df_list)
    return df.pivot(index=["lat", "lon"], columns="param").reset_index()

# --- Add Overlay Layers ---
def add_wind_layers(m, df):
    """
    Add heatmap overlays to a Folium map:
    - Annual Wind Speed
    - Capacity Factor (proxy)
    - Seasonal Wind Speed
    """
    # Wind speed ANN
    wind_data = [[row.lat, row.lon, row["WS100M"]["ANN"]] for _, row in df.iterrows()]
    HeatMap(wind_data, name="🌬️ Wind Speed (100m)", radius=20).add_to(m)

    # Capacity factor proxy (WS^3 normalized)
    df["CF"] = (df["WS100M"]["ANN"]**3 / df["WS100M"]["ANN"].max()**3).clip(0, 1)
    cf_data = [[row.lat, row.lon, row.CF] for _, row in df.iterrows()]
    HeatMap(cf_data, name="⚡ Capacity Factor", radius=20).add_to(m)

    # Seasonal layers
    for season in ["DJF", "MAM", "JJA", "SON"]:
        season_data = [[row.lat, row.lon, row["WS100M"][season]] for _, row in df.iterrows()]
        HeatMap(season_data, name=f"📅 {season} Wind", radius=20).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    return m
