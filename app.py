import streamlit as st
import geopandas as gpd
import os
import folium
import numpy as np
import json
from shapely.geometry import Point
from streamlit_folium import st_folium
from src.analysis.site_summary import summarize_site

# ======================================================
# 🌍 STREAMLIT CONFIG
# ======================================================
st.set_page_config(page_title="TerraWatt | Irish Wind Atlas", layout="wide", page_icon="🌬️")

st.markdown("""
    <style>
    .block-container {
        padding-top: 0rem;
        padding-bottom: 0rem;
        max-width: 95%;
    }
    header, footer {visibility: hidden;}
    iframe {
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    h1 {
        text-align: center;
        font-family: 'Segoe UI', sans-serif;
        color: #0A3D62;
        font-size: 2.2rem;
        border-bottom: 2px solid #0A3D62;
        padding-bottom: 0.4rem;
        margin-bottom: 1rem;
    }
    [data-testid="stSidebar"] {
        background-color: #F8FAFC;
        border-right: 1px solid #E3E6E8;
    }
    .summary-card {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 1rem 1.5rem;
        margin-top: 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        font-size: 0.95rem;
        line-height: 1.5;
        color: #222;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🇮🇪 Irish Transmission Grid & Wind Resource Map")

# ======================================================
# 📂 PATHS
# ======================================================
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
LINES_PATH = os.path.join(PROJECT_ROOT, "data", "osm", "lines_110kV_clean.geojson")
SUBS_PATH  = os.path.join(PROJECT_ROOT, "data", "osm", "substations_110kV_clean.geojson")
WIND_PATH  = os.path.join(PROJECT_ROOT, "data", "wind_farms", "Wind Farms June 2022_ESPG3857.shp")

# ======================================================
# 📘 HELPERS
# ======================================================
def load_layer(path):
    if not os.path.exists(path):
        st.warning(f"⚠️ Missing file: {path}")
        return gpd.GeoDataFrame()
    gdf = gpd.read_file(path)
    if gdf.crs and gdf.crs.to_string() != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")
    return gdf[gdf.geometry.notnull()].copy()

def safe_point_coords(g):
    if g is None or g.is_empty:
        return None
    if g.geom_type == "Point":
        return [g.y, g.x]
    return [g.centroid.y, g.centroid.x]

# ======================================================
# 🧭 LOAD DATA
# ======================================================
lines = load_layer(LINES_PATH)
subs  = load_layer(SUBS_PATH)
wind  = load_layer(WIND_PATH)

subs["coords"] = subs.geometry.apply(safe_point_coords)
wind["coords"] = wind.geometry.apply(safe_point_coords)

# ======================================================
# 🗺️ BUILD FOLIUM MAP
# ======================================================
m = folium.Map(location=[53.5, -8], zoom_start=7, tiles="CartoDB positron")

# Transmission lines
for col in lines.select_dtypes(include=["datetime64[ns]"]).columns:
    lines[col] = lines[col].astype(str)
lines_geojson = json.loads(lines[["geometry"]].to_json())
folium.GeoJson(
    lines_geojson,
    name="Transmission Lines",
    style_function=lambda x: {"color": "#007BFF", "weight": 2, "opacity": 0.7},
).add_to(m)

# Substations (red)
for _, row in subs.iterrows():
    if row["coords"]:
        folium.CircleMarker(location=row["coords"], radius=3, color="#D7263D", fill=True).add_to(m)

# Wind farms (green)
for _, row in wind.iterrows():
    if row["coords"]:
        folium.CircleMarker(location=row["coords"], radius=4, color="#009E73", fill=True).add_to(m)

# ======================================================
# 🌈 ADD MAP LEGEND (now inside the map)
# ======================================================
legend_html = """
<div style="
    position: fixed;
    bottom: 35px; right: 20px;
    z-index:9999;
    background-color: rgba(255, 255, 255, 0.92);
    border-radius: 10px;
    padding: 10px 15px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    font-size: 13px;
    color: #222;
    line-height: 1.5;
">
<b>🗺️ Map Legend</b><br>
<svg width="10" height="10"><circle cx="5" cy="5" r="4" fill="#007BFF" /></svg> Transmission Lines<br>
<svg width="10" height="10"><circle cx="5" cy="5" r="4" fill="#D7263D" /></svg> Substations<br>
<svg width="10" height="10"><circle cx="5" cy="5" r="4" fill="#009E73" /></svg> Wind Farms
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

# Layer control
folium.LayerControl().add_to(m)

# ======================================================
# 🗺️ STREAMLIT MAP + CLICK HANDLER
# ======================================================
st.sidebar.header("📍 Site Summary")

map_data = st_folium(m, height=700, width="100%", returned_objects=["last_clicked"])

if map_data and map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    st.sidebar.info(f"🗺️ Selected point: ({lat:.3f}, {lon:.3f})")

    summary = summarize_site("User-selected site", lat=lat, lon=lon)
    st.markdown(f"<div class='summary-card'>{summary.get('summary_text', '⚠️ No summary text generated.')}</div>", unsafe_allow_html=True)
else:
    st.sidebar.markdown("### 👈 Click anywhere on the map to generate a site summary.")
