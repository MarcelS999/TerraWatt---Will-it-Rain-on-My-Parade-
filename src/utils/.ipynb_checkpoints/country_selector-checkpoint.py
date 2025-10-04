import geopandas as gpd
from shapely.geometry import Point
import json
import folium

_countries_gdf = None


def load_country_shapes(geojson_path: str):
    """Load countries GeoJSON into a cached GeoDataFrame."""
    global _countries_gdf
    if _countries_gdf is None:
        _countries_gdf = gpd.read_file(geojson_path)
        _countries_gdf = _countries_gdf.to_crs("EPSG:4326")
    return _countries_gdf


def get_country_from_point(lat: float, lon: float):
    """
    Given lat/lon, return the country containing that point.
    Works with GeoJSON polygons or multipolygons.
    """
    gdf = _countries_gdf
    if gdf is None:
        raise RuntimeError("Country shapes not loaded. Call load_country_shapes() first.")
    point = Point(lon, lat)
    match = gdf[gdf.geometry.contains(point)]
    if not match.empty:
        row = match.iloc[0]
        return {
            "iso_a3": row.get("ADM0_A3") or row.get("ISO_A3"),
            "country_name": row.get("ADMIN") or row.get("NAME"),
        }
    return None


def highlight_country_on_map(m, countries_gdf, iso_a3, label=None):
    """Highlight a single country polygon on the Folium map."""
    country_shape = countries_gdf[
        (countries_gdf["ADM0_A3"] == iso_a3) | (countries_gdf["ISO_A3"] == iso_a3)
    ]
    if country_shape.empty:
        return m

    shape_geojson = json.loads(country_shape.to_json())
    folium.GeoJson(
        shape_geojson,
        name=label or f"Selected Country: {iso_a3}",
        style_function=lambda x: {
            "fillColor": "#3388ff",
            "color": "blue",
            "weight": 3,
            "fillOpacity": 0.25,
        },
        highlight_function=lambda x: {"weight": 4, "color": "#0033cc"},
    ).add_to(m)
    return m

