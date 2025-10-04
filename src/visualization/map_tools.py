import folium
from folium.plugins import Draw
import math


def add_draw_tools(m):
    """Add rectangle drawing tool to a Folium map."""
    draw = Draw(
        draw_options={
            "rectangle": True,
            "polyline": False,
            "polygon": False,
            "circle": False,
            "circlemarker": False,
            "marker": False,
        },
        edit_options={"edit": False},
    )
    draw.add_to(m)
    return m


def get_bbox_from_stdata(st_data):
    """
    Extract bounding box (lat_min, lat_max, lon_min, lon_max)
    from streamlit_folium draw data.
    Returns None if no rectangle was drawn.
    """
    if not st_data:
        return None

    drawings = st_data.get("all_drawings", [])
    if not drawings:
        return None

    geom = drawings[-1]
    if not geom or "geometry" not in geom or geom["geometry"]["type"] != "Polygon":
        return None

    coords = geom["geometry"]["coordinates"][0]
    lats = [float(c[1]) for c in coords]
    lons = [float(c[0]) for c in coords]
    lat_min, lat_max = min(lats), max(lats)
    lon_min, lon_max = min(lons), max(lons)
    return lat_min, lat_max, lon_min, lon_max


def is_bbox_too_small(lat_min, lat_max, lon_min, lon_max, min_km=28.0):
    """
    Check if the bounding box is smaller than the minimum resolution.
    Returns True if too small.
    """
    km_per_deg_lat = 111.32
    km_per_deg_lon = 111.32 * math.cos(math.radians((lat_min + lat_max) / 2))

    lat_km = abs(lat_max - lat_min) * km_per_deg_lat
    lon_km = abs(lon_max - lon_min) * km_per_deg_lon

    return lat_km < min_km or lon_km < min_km


def is_valid_bbox(lat_min, lat_max, lon_min, lon_max, max_span=5.0):
    """
    Validate that bounding box is not too large.
    Default max_span = 5 degrees (~500 km).
    Returns True if the box size is acceptable.
    """
    return abs(lat_max - lat_min) <= max_span and abs(lon_max - lon_min) <= max_span

def draw_bbox_on_map(m, lat_min, lat_max, lon_min, lon_max, color="blue", visible=True):
    """Draw the bounding box rectangle on the map (only for ERA5 mode)."""
    if not visible:
        return m  # skip drawing if not explicitly requested

    try:
        bounds = [
            [lat_min, lon_min],
            [lat_min, lon_max],
            [lat_max, lon_max],
            [lat_max, lon_min],
            [lat_min, lon_min],
        ]
        folium.PolyLine(bounds, color=color, weight=3, opacity=0.8).add_to(m)
    except Exception as e:
        print(f"⚠️ Could not draw rectangle: {e}")
    return m
