# ============================================================
# 🚀 AI-ASSISTED CODE NOTICE
# This file was developed with assistance from OpenAI's ChatGPT (GPT-5)
# as part of the NASA Space Apps 2025 project:
# “TerraWatt — Will It Rain on My Parade?”
# ============================================================

import geopandas as gpd
import folium
import json

import folium

def add_country_boundaries(m, geojson_path, name="🌍 Country Boundaries"):
    """
    Add clean country borders (no filled geometry) to the map.
    """
    gdf = gpd.read_file(geojson_path)

    folium.GeoJson(
        gdf.to_json(),
        name=name,
        style_function=lambda x: {
            "fill": False,
            "color": "#999999",
            "weight": 1,
            "opacity": 0.7,
        },
        highlight_function=lambda x: {
            "color": "#FFD700",
            "weight": 2,
        },
        tooltip=folium.GeoJsonTooltip(fields=["ADMIN"], aliases=["Country:"]),
    ).add_to(m)

    return m

def highlight_country_on_map(m, gdf, iso_code, label=None):
    """
    Highlight a selected country by ISO code with a distinct fill.
    """
    if "ADM0_A3" in gdf.columns:
        match = gdf[gdf["ADM0_A3"] == iso_code]
    elif "ISO_A3" in gdf.columns:
        match = gdf[gdf["ISO_A3"] == iso_code]
    else:
        raise KeyError("No ISO code column found in the GeoDataFrame.")

    if not match.empty:
        geojson_data = json.loads(match.to_json())
        folium.GeoJson(
            geojson_data,
            name=label or f"Selected Country: {iso_code}",
            style_function=lambda x: {
                "fillColor": "#2a9df4",
                "color": "#004aad",
                "weight": 2.5,
                "fillOpacity": 0.5,
            },
            highlight_function=lambda x: {
                "fillColor": "#007bff",
                "color": "#0033cc",
                "weight": 3,
                "fillOpacity": 0.6,
            },
            tooltip=folium.GeoJsonTooltip(fields=["ADMIN"], aliases=["Country:"]),
        ).add_to(m)

    return m
