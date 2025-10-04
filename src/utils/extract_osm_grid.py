import os
import geopandas as gpd
import osmnx as ox
import folium


def extract_osm_ireland_110kv(out_dir="data/osm"):
    os.makedirs(out_dir, exist_ok=True)

    print("📡 Fetching OSM substations and 110 kV lines for Ireland...")

    # --- Define Ireland bounding box ---
    ireland = ox.geocode_to_gdf("Ireland")
    bounds = ireland.total_bounds  # [minx, miny, maxx, maxy]

    # --- Fetch substations ---
    substations = ox.geometries_from_bbox(
        north=bounds[3], south=bounds[1],
        east=bounds[2], west=bounds[0],
        tags={"power": "substation"},
    )

    substations = substations[
        substations["voltage"].astype(str).str.contains("110", na=False)
    ].copy()
    substations["voltage_kV"] = 110
    substations["name"] = substations.get("name", "Unnamed Substation")

    subs_path = os.path.join(out_dir, "substations_110kV_clean.geojson")
    substations.to_file(subs_path, driver="GeoJSON")

    # --- Fetch transmission lines ---
    lines = ox.geometries_from_bbox(
        north=bounds[3], south=bounds[1],
        east=bounds[2], west=bounds[0],
        tags={"power": "line"},
    )
    lines = lines[
        lines["voltage"].astype(str).str.contains("110", na=False)
    ].copy()
    lines["voltage_kV"] = 110

    lines_path = os.path.join(out_dir, "lines_110kV_clean.geojson")
    lines.to_file(lines_path, driver="GeoJSON")

    print(f"✅ Saved {len(substations)} substations and {len(lines)} 110 kV lines")
    print(f"📂 Output → {out_dir}")

    # --- Generate Folium Preview ---
    if not substations.empty or not lines.empty:
        # Center map roughly on Ireland
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2
        m = folium.Map(location=[center_lat, center_lon], zoom_start=7, tiles="cartodbpositron")

        # Add transmission lines
        if not lines.empty:
            folium.GeoJson(
                lines.to_json(),
                name="110 kV Transmission Lines",
                style_function=lambda x: {"color": "#0033cc", "weight": 2},
            ).add_to(m)

        # Add substations
        for _, row in substations.iterrows():
            if row.geometry.geom_type == "Point":
                folium.CircleMarker(
                    location=[row.geometry.y, row.geometry.x],
                    radius=4,
                    color="red",
                    fill=True,
                    fill_opacity=0.7,
                    popup=row.get("name", "Unnamed 110 kV Substation"),
                ).add_to(m)

        folium.LayerControl(collapsed=False).add_to(m)

        # Save HTML preview
        html_path = os.path.join(out_dir, "ireland_grid_preview.html")
        m.save(html_path)
        print(f"🌍 Preview saved → {html_path}")
    else:
        print("⚠️ No 110 kV assets found to preview.")

    return subs_path, lines_path


if __name__ == "__main__":
    extract_osm_ireland_110kv()


