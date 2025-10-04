import os
import geopandas as gpd
import osmnx as ox
import folium
import requests
from io import StringIO

def extract_osm_ireland_110kv(out_dir="data/osm"):
    os.makedirs(out_dir, exist_ok=True)
    print("📡 Fetching OSM substations and 110 kV lines for Ireland...")

    # --- Get the boundary / polygon for Ireland ---
    ireland = ox.geocode_to_gdf("Ireland")
    # optionally buffer slightly if you want to include fringe lines crossing the boundary
    # ireland = ireland.to_crs(epsg=3857).buffer(5000).to_crs(epsg=4326)
    poly = ireland.geometry.unary_union

    # --- Substations (power=substation) within polygon ---
    tags_sub = {"power": "substation"}
    sub_gdf = ox.features_from_polygon(poly, tags=tags_sub)
    # Filter to those that have voltage including “110” (like “110000”, “110”, etc.)
    sub_gdf = sub_gdf[sub_gdf["voltage"].astype(str).str.contains("110", na=False)].copy()
    sub_gdf["voltage_kV"] = 110

    # --- Transmission lines (power=line) within polygon ---
    tags_line = {"power": "line"}
    line_gdf = ox.features_from_polygon(poly, tags=tags_line)
    line_gdf = line_gdf[line_gdf["voltage"].astype(str).str.contains("110", na=False)].copy()
    line_gdf["voltage_kV"] = 110

    # --- Save results ---
    subs_path = os.path.join(out_dir, "substations_110kV_clean.geojson")
    lines_path = os.path.join(out_dir, "lines_110kV_clean.geojson")
    sub_gdf.to_file(subs_path, driver="GeoJSON")
    line_gdf.to_file(lines_path, driver="GeoJSON")

    print(f"✅ Saved {len(sub_gdf)} substations and {len(line_gdf)} 110 kV lines")

    # --- Quick HTML preview ---
    m = folium.Map(location=[53.4, -8.0], zoom_start=7, tiles="cartodbpositron")

    folium.GeoJson(
        line_gdf.to_json(),
        name="110 kV Transmission Lines",
        style_function=lambda x: {"color": "#0033cc", "weight": 2},
    ).add_to(m)

    for _, row in sub_gdf.iterrows():
        geom = row.geometry
        if geom is None:
            continue
        if geom.geom_type == "Point":
            folium.CircleMarker(
                location=[geom.y, geom.x],
                radius=4,
                color="red",
                fill=True,
                fill_opacity=0.7,
                popup=row.get("name", "Unnamed 110 kV Substation"),
            ).add_to(m)
        else:
            # for non-point geometries (e.g. way center), you may use centroid
            centroid = geom.centroid
            folium.CircleMarker(
                location=[centroid.y, centroid.x],
                radius=4,
                color="red",
                fill=True,
                fill_opacity=0.7,
                popup=row.get("name", "Unnamed 110 kV Substation"),
            ).add_to(m)

    html_path = os.path.join(out_dir, "ireland_grid_preview.html")
    m.save(html_path)
    print(f"🌍 Preview saved → {html_path}")
    print(f"📂 Output → {out_dir}")

    return subs_path, lines_path


if __name__ == "__main__":
    extract_osm_ireland_110kv()





