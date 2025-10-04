# ============================================================
# 🚀 AI-ASSISTED CODE NOTICE
# This file was developed with assistance from OpenAI's ChatGPT (GPT-5)
# as part of the NASA Space Apps 2025 project:
# “TerraWatt — Will It Rain on My Parade?”
# ============================================================

import geopandas as gpd
import folium
import pandas as pd
import numpy as np

def add_transmission_layer(m, lines_path, subs_path=None, label="⚡ 110 kV Transmission Grid"):
    """
    Add Irish transmission grid (lines + optional substations) to a Folium map.
    Automatically cleans any non-serializable attributes (timestamps, lists, dicts).
    """

    def _sanitize_gdf(gdf):
        if gdf is None or gdf.empty:
            return gdf

        for col in gdf.columns:
            # Convert datetime / Timestamp columns → string
            if pd.api.types.is_datetime64_any_dtype(gdf[col]) or (
                len(gdf[col]) > 0 and isinstance(gdf[col].iloc[0], pd.Timestamp)
            ):
                gdf[col] = gdf[col].astype(str)
            # Convert unsupported objects (lists, dicts, numpy types)
            gdf[col] = gdf[col].apply(
                lambda x: str(x) if isinstance(x, (dict, list, np.generic)) else x
            )
        return gdf

    try:
        # --- Load GeoJSONs ---
        lines = gpd.read_file(lines_path)
        if lines.crs is not None and lines.crs.to_string() != "EPSG:4326":
            lines = lines.to_crs(4326)
        lines = _sanitize_gdf(lines)
    except Exception as e:
        print(f"⚠️ Could not load lines GeoJSON: {e}")
        lines = gpd.GeoDataFrame()  # fallback empty

    try:
        subs = gpd.read_file(subs_path) if subs_path else gpd.GeoDataFrame()
        if not subs.empty and subs.crs is not None and subs.crs.to_string() != "EPSG:4326":
            subs = subs.to_crs(4326)
        subs = _sanitize_gdf(subs)
    except Exception as e:
        print(f"⚠️ Could not load substations GeoJSON: {e}")
        subs = gpd.GeoDataFrame()  # fallback empty

    # --- If both are empty, abort gracefully ---
    if lines.empty and subs.empty:
        raise ValueError("❌ No transmission features found in GeoJSONs.")

    # --- Add transmission lines ---
    if not lines.empty:
        folium.GeoJson(
            data=lines.to_json(),
            name=label,
            style_function=lambda x: {"color": "#0044cc", "weight": 2, "opacity": 0.7},
            tooltip=folium.GeoJsonTooltip(
                fields=[f for f in ["name", "voltage_kV"] if f in lines.columns],
                aliases=["Line name", "Voltage [kV]"],
                localize=True,
            ),
        ).add_to(m)

    # --- Add substations ---
    if not subs.empty:
        for _, row in subs.iterrows():
            geom = row.geometry.centroid if row.geometry.geom_type != "Point" else row.geometry
            folium.CircleMarker(
                location=[geom.y, geom.x],
                radius=4,
                color="red",
                fill=True,
                fill_opacity=0.8,
                popup=row.get("name", "Unnamed substation"),
            ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    print(f"✅ Added {len(lines)} lines and {len(subs)} substations to the map.")
    return m
