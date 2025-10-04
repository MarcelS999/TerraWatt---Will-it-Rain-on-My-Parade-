# ============================================================
# 🚀 AI-ASSISTED CODE NOTICE
# This file was developed with assistance from OpenAI's ChatGPT (GPT-5)
# as part of the NASA Space Apps 2025 project:
# “TerraWatt — Will It Rain on My Parade?”
# ============================================================

import streamlit as st
import geopandas as gpd
import os
import folium
import numpy as np
import json
import rasterio
from shapely.geometry import Point
from matplotlib import cm as mpl_cm
from matplotlib.colors import Normalize
from streamlit_folium import st_folium
import branca.colormap as cm
from rasterio.enums import Resampling

# ======================================================
# 🌍 STREAMLIT CONFIG
# ======================================================
st.set_page_config(page_title="Irish Wind & Grid Map", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 0rem; padding-bottom: 0rem;}
    header, footer {visibility: hidden;}
    .full-map {height: calc(100vh - 3rem);}
    </style>
""", unsafe_allow_html=True)

st.title("🇮🇪 Irish Transmission Grid & Wind Farm Map")

# ======================================================
# 📂 PATHS
# ======================================================
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
LINES_PATH = os.path.join(PROJECT_ROOT, "data", "osm", "lines_110kV_clean.geojson")
SUBS_PATH  = os.path.join(PROJECT_ROOT, "data", "osm", "substations_110kV_clean.geojson")
WIND_PATH  = os.path.join(PROJECT_ROOT, "data", "wind_farms", "Wind Farms June 2022_ESPG3857.shp")
ERA5_STD   = os.path.join(PROJECT_ROOT, "data", "era5", "era5_ireland_std_1994_2024.tif")

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

def add_raster_layer(m, tif_path, name="Wind Variability", cmap="plasma", opacity=0.75):
    """Add a high-quality interpolated raster overlay to Folium."""
    with rasterio.open(tif_path) as src:
        upscale_factor = 4
        data = src.read(
            out_shape=(
                src.count,
                int(src.height * upscale_factor),
                int(src.width * upscale_factor)
            ),
            resampling=Resampling.bilinear
        )[0]

        vmin, vmax = np.nanmin(data), np.nanmax(data)
        bounds = src.bounds
        norm = Normalize(vmin=vmin, vmax=vmax)
        cmap_obj = mpl_cm.get_cmap(cmap)
        rgba = (cmap_obj(norm(data)) * 255).astype(np.uint8)

        folium.raster_layers.ImageOverlay(
            image=rgba,
            bounds=[[bounds.bottom, bounds.left], [bounds.top, bounds.right]],
            opacity=opacity,
            name=name,
        ).add_to(m)

        legend = cm.LinearColormap(
            [mpl_cm.get_cmap(cmap)(x) for x in np.linspace(0, 1, 6)],
            vmin=vmin, vmax=vmax, caption=name,
        )
        legend.add_to(m)

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

# Add Std Dev raster layer only
add_raster_layer(m, ERA5_STD, "📉 30-Year Std Dev (Wind Variability)")

# Add substations (red)
for _, row in subs.iterrows():
    if row["coords"]:
        folium.CircleMarker(location=row["coords"], radius=3, color="red", fill=True).add_to(m)

# Add wind farms (green)
for _, row in wind.iterrows():
    if row["coords"]:
        folium.CircleMarker(location=row["coords"], radius=4, color="green", fill=True).add_to(m)

# Convert lines safely to GeoJSON
for col in lines.select_dtypes(include=["datetime64[ns]"]).columns:
    lines[col] = lines[col].astype(str)
lines_geojson = json.loads(lines[["geometry"]].to_json())

folium.GeoJson(
    lines_geojson,
    name="Transmission Lines",
    style_function=lambda x: {"color": "#0060FF", "weight": 2, "opacity": 0.7},
).add_to(m)

folium.LayerControl().add_to(m)

# ======================================================
# 🗺️ STREAMLIT MAP + CLICK HANDLER
# ======================================================
from src.analysis.site_summary import summarize_site

st.sidebar.header("📍 Site Summary")

map_data = st_folium(m, height=700, width="100%", returned_objects=["last_clicked"])
if map_data and map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    st.sidebar.info(f"🗺️ Selected point: ({lat:.3f}, {lon:.3f})")

    summary = summarize_site("User-selected site", lat=lat, lon=lon)
    st.markdown(summary.get("summary_text", "⚠️ No summary text generated."))
else:
    st.sidebar.write("👆 Click anywhere on the map to generate a site summary.")
# ======================================================
# 🎨 LEGEND (Custom HTML Overlay)
# ======================================================
legend_html = """
<div style="
    position: fixed; 
    bottom: 25px; left: 25px; 
    z-index: 9999; 
    background-color: rgba(255, 255, 255, 0.85); 
    padding: 10px 15px; 
    border-radius: 8px;
    box-shadow: 0px 2px 8px rgba(0,0,0,0.2);
    font-size: 13px;
    line-height: 1.5;
">
<b>Legend</b><br>
<svg width="16" height="16"><circle cx="8" cy="8" r="5" fill="green" /></svg> Wind Farm<br>
<svg width="16" height="16"><circle cx="8" cy="8" r="5" fill="red" /></svg> Substation<br>
<svg width="16" height="8"><line x1="0" y1="4" x2="16" y2="4" stroke="#0060FF" stroke-width="2" /></svg> Transmission Line<br>
🟣 ERA5 Std Dev (Wind Variability)
</div>
"""
st.markdown(legend_html, unsafe_allow_html=True)
