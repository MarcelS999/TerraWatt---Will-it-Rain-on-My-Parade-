# ============================================================
# AI USE DECLARATION
# ============================================================
# This file was developed with significant assistance from AI tools:
# 
# 1. Cursor AI (https://cursor.sh/)
#    - Primary development environment with AI-powered code completion
#    - Real-time code suggestions and refactoring assistance
#    - Integrated debugging and error resolution
#
# 2. ChatGPT (OpenAI - https://openai.com/chatgpt)
#    - Conversational AI assistance for complex coding tasks
#    - Strategic planning and architectural guidance
#    - Code generation and debugging support
#
# Project: TerraWatt — Will It Rain on My Parade?
# Challenge: NASA Space Apps 2025
# 
# All AI-generated code has been reviewed, tested, and validated
# by the human development team. AI tools served as collaborative
# partners in the development process.
# ============================================================

import planetary_computer as pc
import pystac_client
import xarray as xr
import pandas as pd
import folium
import numpy as np


def get_era5_wind_grid(lat_min, lat_max, lon_min, lon_max, start, end, out_prefix="era5_wind", interval="hourly" , debug=False ):

    """
    Fetch ERA5 10m wind data, clip to bounding box, resample to uniform grid (e.g., 0.1°),
    and return as a clean DataFrame ready for Folium heatmap overlay.
    """

    # --- Connect to Planetary Computer STAC ---
    catalog = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1/")

    search = catalog.search(
        collections=["era5-pds"],
        datetime=f"{start}/{end}",
        query={"era5:kind": {"eq": "an"}},
    )

    items = list(search.get_items())
    if not items:
        raise ValueError(f"No ERA5 dataset items found for {start} to {end}")

    signed_item = pc.sign(items[0])

    # --- Load eastward/northward wind components ---
    u10_asset = signed_item.assets["eastward_wind_at_10_metres"]
    v10_asset = signed_item.assets["northward_wind_at_10_metres"]

    ds_u10 = xr.open_dataset(u10_asset.href, **u10_asset.extra_fields["xarray:open_kwargs"])
    ds_v10 = xr.open_dataset(v10_asset.href, **v10_asset.extra_fields["xarray:open_kwargs"])
    ds = xr.merge([ds_u10, ds_v10])

    if debug:
        print("ERA5 dataset dims:", ds.dims)
        print("ERA5 lat range:", float(ds.lat.max()), "→", float(ds.lat.min()))
        print("ERA5 lon range:", float(ds.lon.min()), "→", float(ds.lon.max()))
        print("Requested bbox:", lat_min, lat_max, lon_min, lon_max)

    # Convert bbox longitudes to 0–360 for ERA5
    if lon_min < 0:
        lon_min = 360 + lon_min
    if lon_max < 0:
        lon_max = 360 + lon_max

    # --- Clip dataset ---
    lat_slice = slice(float(lat_max), float(lat_min))  # descending
    lon_slice = slice(float(lon_min), float(lon_max))  # ascending
    ds_clip = ds.sel(lat=lat_slice, lon=lon_slice, time=slice(start, end))

    if ds_clip.dims.get("lat", 0) == 0 or ds_clip.dims.get("lon", 0) == 0:
        raise ValueError("❌ Empty selection: Check if bbox intersects ERA5 grid.")

    # --- Compute wind speed magnitude ---
    ds_clip["wind_speed"] = np.sqrt(
        ds_clip["eastward_wind_at_10_metres"] ** 2 + ds_clip["northward_wind_at_10_metres"] ** 2
    )

    # --- Resample to finer, uniform grid ---
    lat_vals = np.arange(float(ds_clip.lat.min()), float(ds_clip.lat.max()) + res, res)
    lon_vals = np.arange(float(ds_clip.lon.min()), float(ds_clip.lon.max()) + res, res)

    new_lat = xr.DataArray(lat_vals, dims="lat")
    new_lon = xr.DataArray(lon_vals, dims="lon")

    ds_resampled = ds_clip.interp(lat=new_lat, lon=new_lon, method="linear")

    if debug:
        print(f"📐 Resampled grid → {len(lat_vals)}×{len(lon_vals)} points ({res}° resolution)")

    # --- Convert to DataFrame ---
    df = ds_resampled["wind_speed"].to_dataframe().reset_index()

    # Convert longitudes from [0,360] → [-180,180]
    if "lon" in df.columns:
        df["lon"] = df["lon"].apply(lambda x: x - 360 if x > 180 else x)
    elif "longitude" in df.columns:
        df["longitude"] = df["longitude"].apply(lambda x: x - 360 if x > 180 else x)

    # Drop NaNs, enforce float
    df = df.dropna(subset=["wind_speed"])
    df["lat"] = df["lat"].astype(float)
    df["lon"] = df["lon"].astype(float)
    df["wind_speed"] = df["wind_speed"].astype(float)

    if debug:
        print(f"📊 Final DataFrame: {df.shape}")
        print(df.head())

    # --- Save outputs ---
    csv_path = f"{out_prefix}.csv"
    readme_path = f"{out_prefix}_README.txt"

    citation = (
        "# Data source: ERA5 hourly data on single levels from 1979 to present\n"
        "# Provided by the Copernicus Climate Change Service (C3S)\n"
        "# Citation: Hersbach, H., Bell, B., Berrisford, P., et al. (2020): "
        "The ERA5 global reanalysis. Quarterly Journal of the Royal Meteorological Society, "
        "146(730), 1999–2049. https://doi.org/10.1002/qj.3803\n"
        "# License: Contains modified Copernicus Climate Change Service information [Year]\n"
    )

    df.to_csv(csv_path, index=False)
    with open(readme_path, "w") as f:
        f.write(citation)

    print(f"💾 Saved {csv_path} and {readme_path}")

    return df, csv_path, readme_path


def _export_with_citation(df, out_prefix, start, end):
    """Helper to always write CSV + README.txt and return paths."""
    csv_path = f"{out_prefix}_{start}_{end}.csv"
    readme_path = f"{out_prefix}_README.txt"

    df.to_csv(csv_path, index=False)
    citation = (
        "Data source: ERA5 hourly data on single levels from 1979 to present\n"
        "Provided by the Copernicus Climate Change Service (C3S)\n"
        "Citation: Hersbach, H., Bell, B., Berrisford, P., et al. (2020): "
        "The ERA5 global reanalysis. Quarterly Journal of the Royal Meteorological Society, "
        "146(730), 1999–2049. https://doi.org/10.1002/qj.3803\n"
        "License: Contains modified Copernicus Climate Change Service information [Year]\n"
    )
    with open(readme_path, "w") as f:
        f.write(citation)
    return df, csv_path, readme_path


def add_era5_layer(m, df, label="🌬 ERA5 Wind 10m"):
    """Add ERA5 gridded data as a heatmap overlay on a Folium map."""
    from folium.plugins import HeatMap

    if df.empty:
        print("⚠️ No data for overlay.")
        return m

    # Identify lat/lon columns
    if "lat" in df.columns and "lon" in df.columns:
        lat_col, lon_col = "lat", "lon"
    elif "latitude" in df.columns and "longitude" in df.columns:
        lat_col, lon_col = "latitude", "longitude"
    else:
        raise ValueError("❌ Could not find lat/lon columns in DataFrame.")

    df = df.dropna(subset=["wind_speed", lat_col, lon_col])
    df = df[(df[lat_col].between(-90, 90)) & (df[lon_col].between(-180, 180))]

    if df.empty:
        print("⚠️ Filtered DataFrame empty after cleaning.")
        return m

    # Normalize intensity (avoid division by zero)
    ws = df["wind_speed"].values
    ws_min, ws_max = np.nanmin(ws), np.nanmax(ws)
    if ws_max - ws_min < 1e-6:
        ws_norm = np.ones_like(ws) * 0.5
    else:
        ws_norm = (ws - ws_min) / (ws_max - ws_min)

    heat_data = [[row[lat_col], row[lon_col], val] for (_, row), val in zip(df.iterrows(), ws_norm)]

    HeatMap(
        heat_data,
        name=label,
        radius=14,
        blur=22,
        max_zoom=5,
        min_opacity=0.4,
        max_opacity=0.9,
        gradient={
            0.0: "blue",
            0.25: "lime",
            0.5: "yellow",
            0.75: "orange",
            1.0: "red",
        },
        show=True,
    ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    print(f"✅ Added ERA5 HeatMap with {len(heat_data)} points.")
    return m
