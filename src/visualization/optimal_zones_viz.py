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

"""
optimal_zones_viz.py
--------------------
Pydeck visualization for optimal wind farm zones.
Creates interactive 3D maps showing optimal development areas
with wind resources, grid connectivity, and economic factors.
"""

import pandas as pd
import numpy as np
import streamlit as st
import folium
from streamlit_folium import st_folium
from src.analysis.optimal_zones import generate_optimal_zones

# Try to import pydeck, fallback to folium if not available
try:
    import pydeck as pdk
    PYDECK_AVAILABLE = True
except ImportError:
    PYDECK_AVAILABLE = False

# ============================================================
# COLOR SCHEMES
# ============================================================
ZONE_COLORS = {
    "Excellent": [0, 255, 0, 180],      # Green
    "Good": [0, 200, 100, 160],         # Light green
    "Moderate": [255, 255, 0, 140],     # Yellow
    "Marginal": [255, 165, 0, 120]      # Orange
}

WIND_COLORS = [
    [255, 0, 0, 200],      # Red (low wind)
    [255, 165, 0, 200],    # Orange
    [255, 255, 0, 200],    # Yellow
    [0, 255, 0, 200],      # Green (high wind)
    [0, 0, 255, 200]       # Blue (very high wind)
]

# ============================================================
# LAYER CREATION
# ============================================================
def create_optimal_zones_layer(zones_gdf):
    """Create Pydeck layer for optimal zones."""
    
    # Prepare data for Pydeck
    zones_data = []
    for _, row in zones_gdf.iterrows():
        zones_data.append({
            'lat': row['latitude'],
            'lon': row['longitude'],
            'wind_score': row['wind_score'],
            'grid_score': row['grid_score'],
            'composite_score': row['composite_score'],
            'wind_speed': row['wind_speed_mps'],
            'grid_distance': row['grid_distance_km'],
            'grid_cost': row['grid_cost_eur'],
            'zone_category': row['zone_category'],
            'color': ZONE_COLORS.get(row['zone_category'], [128, 128, 128, 150])
        })
    
    return pdk.Layer(
        'ScatterplotLayer',
        data=zones_data,
        get_position='[lon, lat]',
        get_fill_color='color',
        get_radius=2000,  # 2km radius
        pickable=True,
        auto_highlight=True,
        opacity=0.8
    )

def create_wind_heatmap_layer(zones_gdf):
    """Create wind speed heatmap layer."""
    
    # Prepare wind data
    wind_data = []
    for _, row in zones_gdf.iterrows():
        # Color based on wind speed
        wind_speed = row['wind_speed_mps']
        if wind_speed < 6:
            color = WIND_COLORS[0]  # Red
        elif wind_speed < 7:
            color = WIND_COLORS[1]  # Orange
        elif wind_speed < 8:
            color = WIND_COLORS[2]  # Yellow
        elif wind_speed < 9:
            color = WIND_COLORS[3]  # Green
        else:
            color = WIND_COLORS[4]  # Blue
        
        wind_data.append({
            'lat': row['latitude'],
            'lon': row['longitude'],
            'wind_speed': wind_speed,
            'color': color
        })
    
    return pdk.Layer(
        'ScatterplotLayer',
        data=wind_data,
        get_position='[lon, lat]',
        get_fill_color='color',
        get_radius=1500,  # 1.5km radius
        pickable=True,
        auto_highlight=True,
        opacity=0.6
    )

def create_grid_connectivity_layer(zones_gdf):
    """Create grid connectivity visualization layer."""
    
    grid_data = []
    for _, row in zones_gdf.iterrows():
        # Color based on grid distance (closer = better)
        grid_dist = row['grid_distance_km']
        if grid_dist <= 10:
            color = [0, 255, 0, 180]      # Green (close)
        elif grid_dist <= 20:
            color = [255, 255, 0, 160]    # Yellow
        elif grid_dist <= 30:
            color = [255, 165, 0, 140]    # Orange
        else:
            color = [255, 0, 0, 120]      # Red (far)
        
        grid_data.append({
            'lat': row['latitude'],
            'lon': row['longitude'],
            'grid_distance': grid_dist,
            'grid_cost': row['grid_cost_eur'],
            'color': color
        })
    
    return pdk.Layer(
        'ScatterplotLayer',
        data=grid_data,
        get_position='[lon, lat]',
        get_fill_color='color',
        get_radius=1000,  # 1km radius
        pickable=True,
        auto_highlight=True,
        opacity=0.7
    )

def create_cluster_centers_layer(cluster_stats):
    """Create layer showing cluster centers."""
    
    cluster_data = []
    for cluster in cluster_stats:
        cluster_data.append({
            'lat': cluster['centroid_lat'],
            'lon': cluster['centroid_lon'],
            'cluster_id': cluster['cluster_id'],
            'count': cluster['count'],
            'avg_score': cluster['avg_score'],
            'avg_wind_speed': cluster['avg_wind_speed']
        })
    
    return pdk.Layer(
        'ScatterplotLayer',
        data=cluster_data,
        get_position='[lon, lat]',
        get_fill_color='[255, 0, 255, 200]',  # Magenta
        get_radius=5000,  # 5km radius
        pickable=True,
        auto_highlight=True,
        opacity=0.9
    )

# ============================================================
# TOOLTIP TEMPLATES
# ============================================================
def get_zone_tooltip():
    """Get tooltip template for optimal zones."""
    return {
        'html': '''
        <div style="background-color: white; padding: 10px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h3 style="margin: 0 0 5px 0; color: #333;">Optimal Wind Zone</h3>
            <p style="margin: 2px 0;"><b>Category:</b> {zone_category}</p>
            <p style="margin: 2px 0;"><b>Wind Speed:</b> {wind_speed:.1f} m/s</p>
            <p style="margin: 2px 0;"><b>Grid Distance:</b> {grid_distance:.1f} km</p>
            <p style="margin: 2px 0;"><b>Grid Cost:</b> €{grid_cost:,.0f}</p>
            <p style="margin: 2px 0;"><b>Composite Score:</b> {composite_score:.2f}</p>
        </div>
        ''',
        'style': {
            'backgroundColor': 'white',
            'color': 'black'
        }
    }

def get_cluster_tooltip():
    """Get tooltip template for cluster centers."""
    return {
        'html': '''
        <div style="background-color: white; padding: 10px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h3 style="margin: 0 0 5px 0; color: #333;">Development Cluster {cluster_id}</h3>
            <p style="margin: 2px 0;"><b>Zone Count:</b> {count}</p>
            <p style="margin: 2px 0;"><b>Avg Wind Speed:</b> {avg_wind_speed:.1f} m/s</p>
            <p style="margin: 2px 0;"><b>Avg Score:</b> {avg_score:.2f}</p>
        </div>
        ''',
        'style': {
            'backgroundColor': 'white',
            'color': 'black'
        }
    }

# ============================================================
# MAIN VISUALIZATION
# ============================================================
def create_optimal_zones_map(zones_gdf=None, cluster_stats=None, show_layers=None):
    """
    Create Pydeck map for optimal zones visualization.
    
    Parameters:
    -----------
    zones_gdf : GeoDataFrame
        Optimal zones data
    cluster_stats : list
        Cluster statistics
    show_layers : dict
        Dictionary controlling which layers to show
    
    Returns:
    --------
    pdk.Deck
        Pydeck map object
    """
    
    if zones_gdf is None:
        # Generate optimal zones if not provided
        zones_gdf, cluster_stats = generate_optimal_zones()
    
    if show_layers is None:
        show_layers = {
            'optimal_zones': True,
            'wind_heatmap': True,
            'grid_connectivity': False,
            'cluster_centers': True
        }
    
    # Create layers
    layers = []
    
    if show_layers.get('optimal_zones', True):
        zones_layer = create_optimal_zones_layer(zones_gdf)
        zones_layer.tooltip = get_zone_tooltip()
        layers.append(zones_layer)
    
    if show_layers.get('wind_heatmap', True):
        wind_layer = create_wind_heatmap_layer(zones_gdf)
        wind_layer.tooltip = {
            'html': '''
            <div style="background-color: white; padding: 10px; border-radius: 5px;">
                <h3 style="margin: 0 0 5px 0; color: #333;">Wind Resource</h3>
                <p style="margin: 2px 0;"><b>Wind Speed:</b> {wind_speed:.1f} m/s</p>
            </div>
            ''',
            'style': {'backgroundColor': 'white', 'color': 'black'}
        }
        layers.append(wind_layer)
    
    if show_layers.get('grid_connectivity', False):
        grid_layer = create_grid_connectivity_layer(zones_gdf)
        grid_layer.tooltip = {
            'html': '''
            <div style="background-color: white; padding: 10px; border-radius: 5px;">
                <h3 style="margin: 0 0 5px 0; color: #333;">Grid Connectivity</h3>
                <p style="margin: 2px 0;"><b>Distance:</b> {grid_distance:.1f} km</p>
                <p style="margin: 2px 0;"><b>Cost:</b> €{grid_cost:,.0f}</p>
            </div>
            ''',
            'style': {'backgroundColor': 'white', 'color': 'black'}
        }
        layers.append(grid_layer)
    
    if show_layers.get('cluster_centers', True) and cluster_stats:
        cluster_layer = create_cluster_centers_layer(cluster_stats)
        cluster_layer.tooltip = get_cluster_tooltip()
        layers.append(cluster_layer)
    
    # Create the map
    deck = pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v10',
        initial_view_state=pdk.ViewState(
            latitude=53.5,
            longitude=-8.0,
            zoom=7,
            pitch=45,
            bearing=0
        ),
        layers=layers,
        tooltip=True
    )
    
    return deck

# ============================================================
# FOLIUM FALLBACK VISUALIZATION
# ============================================================
def create_folium_optimal_zones_map(zones_gdf, cluster_stats=None, show_layers=None):
    """Create folium map for optimal zones (same format as first page)."""
    
    # Create base map (same as first page)
    m = folium.Map(location=[53.5, -8], zoom_start=7, tiles="CartoDB positron")
    
    # Default layer visibility
    if show_layers is None:
        show_layers = {
            'optimal_zones': True,
            'wind_heatmap': True,
            'grid_connectivity': False,
            'cluster_centers': True,
            'mean_wind_speed': False,
            'wind_standard_deviation': False
        }
    
    # Add wind data layers first (so they appear behind other elements)
    if show_layers.get('mean_wind_speed', False) or show_layers.get('wind_standard_deviation', False):
        # Get styling parameters from session state or use defaults
        wind_opacity = st.session_state.get('wind_opacity', 0.6)
        wind_radius = st.session_state.get('wind_radius', 25)
        wind_blur = st.session_state.get('wind_blur', 15)
        add_wind_data_layers(m, show_layers, wind_opacity, wind_radius, wind_blur)
    
    # Add optimal zones
    if show_layers.get('optimal_zones', True):
        for _, row in zones_gdf.iterrows():
            # Different colors for offshore vs onshore
            if hasattr(row, 'wind_farm_type') and row.get('wind_farm_type') == 'Offshore':
                color = {
                    'Excellent': 'blue',
                    'Good': 'lightblue', 
                    'Moderate': 'cyan',
                    'Marginal': 'lightcyan'
                }.get(row['zone_category'], 'gray')
            else:  # Onshore
                color = {
                    'Excellent': 'green',
                    'Good': 'lightgreen', 
                    'Moderate': 'yellow',
                    'Marginal': 'orange'
                }.get(row['zone_category'], 'gray')
            
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=8,
                color=color,
                fill=True,
                fillOpacity=0.7,
                popup=folium.Popup(
                    f"""
                    <b>Optimal Wind Zone</b><br>
                    Category: {row['zone_category']}<br>
                    Wind Speed: {row['wind_speed_mps']:.1f} m/s<br>
                    Grid Distance: {row['grid_distance_km']:.1f} km<br>
                    Grid Cost: €{row['grid_cost_eur']:,.0f}<br>
                    Score: {row['composite_score']:.2f}
                    """,
                    max_width=200
                )
            ).add_to(m)
    
    # Add cluster centers
    if cluster_stats:
        for cluster in cluster_stats:
            folium.Marker(
                location=[cluster['centroid_lat'], cluster['centroid_lon']],
                icon=folium.Icon(color='red', icon='star'),
                popup=folium.Popup(
                    f"""
                    <b>Development Cluster {cluster['cluster_id']}</b><br>
                    Zones: {cluster['count']}<br>
                    Avg Wind: {cluster['avg_wind_speed']:.1f} m/s<br>
                    Avg Score: {cluster['avg_score']:.2f}
                    """,
                    max_width=200
                )
            ).add_to(m)
    
    # Add legend (same style as first page)
    legend_html = """
    <div style="position: fixed; bottom: 35px; right: 20px; z-index:9999;
                background-color: rgba(255, 255, 255, 0.92);
                border-radius: 10px;
                padding: 10px 15px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.15);
                font-size: 13px;
                color: #222;
                line-height: 1.5;
    ">
    <b>🗺️ Map Legend</b><br>
    <b>Onshore Zones:</b><br>
    <svg width="10" height="10"><circle cx="5" cy="5" r="4" fill="green" /></svg> Excellent<br>
    <svg width="10" height="10"><circle cx="5" cy="5" r="4" fill="lightgreen" /></svg> Good<br>
    <svg width="10" height="10"><circle cx="5" cy="5" r="4" fill="yellow" /></svg> Moderate<br>
    <svg width="10" height="10"><circle cx="5" cy="5" r="4" fill="orange" /></svg> Marginal<br>
    <b>Offshore Zones:</b><br>
    <svg width="10" height="10"><circle cx="5" cy="5" r="4" fill="blue" /></svg> Excellent<br>
    <svg width="10" height="10"><circle cx="5" cy="5" r="4" fill="lightblue" /></svg> Good<br>
    <svg width="10" height="10"><circle cx="5" cy="5" r="4" fill="cyan" /></svg> Moderate<br>
    <svg width="10" height="10"><circle cx="5" cy="5" r="4" fill="lightcyan" /></svg> Marginal<br>
    <b>Infrastructure:</b><br>
    <svg width="10" height="10"><circle cx="5" cy="5" r="4" fill="#009E73" /></svg> Existing Wind Farms<br>
    <svg width="10" height="10"><circle cx="5" cy="5" r="4" fill="#D7263D" /></svg> Substations<br>
    <svg width="10" height="10"><circle cx="5" cy="5" r="4" fill="red" /></svg> Cluster Centers<br>
    <b>Wind Data Layers:</b><br>
    <svg width="10" height="10"><circle cx="5" cy="5" r="4" fill="blue" /></svg> Mean Wind Speed<br>
    <svg width="10" height="10"><circle cx="5" cy="5" r="4" fill="green" /></svg> Wind Variability
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

def extract_wind_farm_name(row):
    """Extract wind farm name from data row."""
    # Try different possible name fields (case insensitive)
    name_fields = [
        'Name', 'NAME', 'name', 'Site_Name', 'SITE_NAME', 'Wind_Farm', 'WIND_FARM',
        'SiteName', 'SITENAME', 'site_name', 'wind_farm_name', 'WIND_FARM_NAME',
        'Project', 'PROJECT', 'project_name', 'PROJECT_NAME', 'Title', 'TITLE'
    ]
    
    for field in name_fields:
        if field in row and pd.notna(row[field]) and str(row[field]).strip():
            name = str(row[field]).strip()
            # Clean up the name
            if name.lower() not in ['unknown', 'null', 'none', '']:
                return name
    
    # Try to find any field that might contain a name (looks like text)
    for col in row.index:
        if col != 'geometry' and pd.notna(row[col]):
            value = str(row[col]).strip()
            # If it looks like a name (contains letters and is reasonable length)
            if (len(value) > 3 and len(value) < 100 and 
                any(c.isalpha() for c in value) and 
                value.lower() not in ['unknown', 'null', 'none', '']):
                return value
    
    # If no name found, create a generic one
    return f"Wind Farm {row.name if hasattr(row, 'name') else 'Unknown'}"

def extract_wind_farm_capacity(row):
    """Extract wind farm capacity from data row."""
    # Try different possible capacity fields
    capacity_fields = [
        'Capacity', 'CAPACITY', 'capacity', 'MW', 'mw', 'Power', 'POWER', 'Size', 'SIZE',
        'Installed_Capacity', 'INSTALLED_CAPACITY', 'installed_capacity',
        'Total_Capacity', 'TOTAL_CAPACITY', 'total_capacity',
        'Rated_Power', 'RATED_POWER', 'rated_power', 'Capacity_MW', 'CAPACITY_MW'
    ]
    
    for field in capacity_fields:
        if field in row and pd.notna(row[field]):
            try:
                value = str(row[field]).strip()
                # Remove common units and extract number
                value = value.replace('MW', '').replace('mw', '').replace('MWh', '').strip()
                capacity = float(value)
                if capacity > 0 and capacity < 10000:  # Reasonable capacity range
                    return capacity
            except (ValueError, TypeError):
                continue
    
    # Try to find any numeric field that might be capacity
    for col in row.index:
        if col != 'geometry' and pd.notna(row[col]):
            try:
                value = str(row[col]).strip()
                # Look for numeric values that could be capacity
                if any(keyword in col.lower() for keyword in ['capacity', 'power', 'mw', 'size', 'rated']):
                    capacity = float(value)
                    if 0 < capacity < 10000:  # Reasonable capacity range
                        return capacity
            except (ValueError, TypeError):
                continue
    
    # If no capacity found, return None
    return None

def create_wind_farm_popup(name, capacity, row):
    """Create HTML popup for wind farm marker."""
    # Start building the popup HTML
    popup_html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 280px;">
        <h3 style="margin: 0 0 10px 0; color: #2E8B57; font-size: 16px;">Wind Farm: {name}</h3>
    """
    
    # Add capacity if available
    if capacity is not None:
        popup_html += f"""
        <p style="margin: 5px 0; font-size: 14px;"><b>Capacity:</b> {capacity:.1f} MW</p>
        """
    else:
        popup_html += f"""
        <p style="margin: 5px 0; font-size: 14px; color: #666;"><b>Capacity:</b> Not available</p>
        """
    
    # Add coordinates
    if 'coords' in row and row['coords']:
        lat, lon = row['coords']
        popup_html += f"""
        <p style="margin: 5px 0; font-size: 12px; color: #666;"><b>Location:</b> {lat:.4f}, {lon:.4f}</p>
        """
    
    # Add any additional information from the data
    additional_info = []
    for col in row.index:
        if col not in ['geometry', 'coords'] and pd.notna(row[col]) and str(row[col]).strip():
            value = str(row[col]).strip()
            # Skip very long text fields and empty values
            if 0 < len(value) < 100 and value.lower() not in ['unknown', 'null', 'none', '']:
                # Format the field name nicely
                field_name = col.replace('_', ' ').title()
                additional_info.append(f"<b>{field_name}:</b> {value}")
    
    if additional_info:
        popup_html += f"""
        <div style="margin-top: 10px; font-size: 12px; border-top: 1px solid #ddd; padding-top: 8px;">
            <b>Additional Information:</b><br>
            {''.join([f'<div style="margin: 2px 0;">{info}</div>' for info in additional_info[:5]])}
        </div>
        """
    
    popup_html += """
    </div>
    """
    
    return popup_html

def determine_onshore_offshore_osm(lat, lon):
    """Determine if a location is onshore or offshore using OpenStreetMap data."""
    try:
        import requests
        import json
        
        # Use Overpass API to query OpenStreetMap for land/water information
        overpass_url = "http://overpass-api.de/api/interpreter"
        
        # Create a small bounding box around the point (±0.01 degrees ≈ 1km)
        bbox = f"{lat-0.01},{lon-0.01},{lat+0.01},{lon+0.01}"
        
        # Query for water bodies (oceans, seas, lakes, rivers)
        water_query = f"""
        [out:json][timeout:25];
        (
          way["natural"="water"]({bbox});
          way["waterway"]({bbox});
          relation["natural"="water"]({bbox});
          relation["waterway"]({bbox});
        );
        out geom;
        """
        
        # Query for land areas
        land_query = f"""
        [out:json][timeout:25];
        (
          way["natural"!="water"]["waterway"!="*"]({bbox});
          relation["natural"!="water"]["waterway"!="*"]({bbox});
        );
        out geom;
        """
        
        # Check for water bodies
        water_response = requests.get(overpass_url, params={'data': water_query}, timeout=10)
        if water_response.status_code == 200:
            water_data = water_response.json()
            if water_data.get('elements'):
                return 'Offshore'  # Found water bodies
        
        # Check for land areas
        land_response = requests.get(overpass_url, params={'data': land_query}, timeout=10)
        if land_response.status_code == 200:
            land_data = land_response.json()
            if land_data.get('elements'):
                return 'Onshore'  # Found land areas
        
        # If no clear data, fall back to simplified method
        return determine_onshore_offshore_simple(lat, lon)
        
    except Exception as e:
        # Fallback to simple method if OSM query fails
        return determine_onshore_offshore_simple(lat, lon)

def determine_onshore_offshore_simple(lat, lon):
    """Simple fallback method for onshore/offshore determination."""
    try:
        # Ireland's approximate boundaries (simplified)
        ireland_bounds = {
            'lat_min': 51.0,
            'lat_max': 55.5,
            'lon_min': -11.0,
            'lon_max': -5.0
        }
        
        # Check if coordinates are within Ireland bounds
        if not (ireland_bounds['lat_min'] <= lat <= ireland_bounds['lat_max'] and 
                ireland_bounds['lon_min'] <= lon <= ireland_bounds['lon_max']):
            return 'Offshore'  # Outside Ireland bounds
        
        # Simplified onshore/offshore determination based on distance from coast
        # Ireland's approximate coastline characteristics
        # West coast (more exposed to Atlantic)
        if lon < -8.5:
            # West of -8.5° longitude - more likely offshore
            if lat < 52.5 or lat > 54.5:
                return 'Offshore'
            else:
                return 'Onshore'
        
        # East coast (more sheltered)
        elif lon > -6.5:
            # East of -6.5° longitude - more likely onshore
            if lat < 51.5 or lat > 55.0:
                return 'Offshore'
            else:
                return 'Onshore'
        
        # Central areas - use latitude as proxy
        else:
            if lat < 52.0 or lat > 55.0:
                return 'Offshore'
            else:
                return 'Onshore'
                
    except Exception as e:
        # Final fallback: use simple distance from center
        center_lat, center_lon = 53.5, -8.0
        distance = ((lat - center_lat)**2 + (lon - center_lon)**2)**0.5
        
        if distance > 2.0:  # More than 2 degrees from center
            return 'Offshore'
        else:
            return 'Onshore'

def determine_onshore_offshore(lat, lon):
    """Determine if a location is onshore or offshore based on coordinates."""
    # Try OSM-based detection first, fall back to simple method
    return determine_onshore_offshore_osm(lat, lon)

def get_wind_speed_at_location_historical(lat, lon):
    """Get historical wind speed data for a specific location across all years."""
    try:
        import os
        import pandas as pd
        import numpy as np
        
        PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
        PROJECT_ROOT = os.path.join(PROJECT_ROOT, "..", "..")
        
        # Try to load individual year files for more detailed analysis
        wind_speeds = []
        years = list(range(1994, 2020))  # 1994-2019
        
        for year in years:
            year_file = os.path.join(PROJECT_ROOT, "data", "era5", f"era5_ireland_wind_{year}.nc")
            if os.path.exists(year_file):
                try:
                    # Load NetCDF file
                    import xarray as xr
                    ds = xr.open_dataset(year_file)
                    
                    # Find nearest grid point
                    lat_idx = np.argmin(np.abs(ds.latitude - lat))
                    lon_idx = np.argmin(np.abs(ds.longitude - lon))
                    
                    # Get wind speed data for this year
                    wind_speed = ds.u10.isel(latitude=lat_idx, longitude=lon_idx).values
                    if not np.isnan(wind_speed):
                        wind_speeds.append(float(wind_speed))
                    
                    ds.close()
                    
                except Exception as e:
                    continue
        
        # If no individual year data, fall back to mean data
        if not wind_speeds:
            wind_data_path = os.path.join(PROJECT_ROOT, "data", "era5", "era5_ireland_mean_wind_1994_2024.csv")
            
            if os.path.exists(wind_data_path):
                wind_data = pd.read_csv(wind_data_path)
                
                # Convert longitude from 0-360 to -180-180 if needed
                if 'longitude' in wind_data.columns:
                    wind_data['longitude'] = wind_data['longitude'].apply(lambda x: x - 360 if x > 180 else x)
                
                # Find nearest data point
                distances = np.sqrt((wind_data['latitude'] - lat)**2 + (wind_data['longitude'] - lon)**2)
                nearest_idx = distances.idxmin()
                
                # Get wind speed for this location
                wind_speed = wind_data.loc[nearest_idx, 'wind_speed_10m']
                wind_speeds = [wind_speed]
        
        return wind_speeds if wind_speeds else None
        
    except Exception as e:
        return None

def get_historical_wind_speeds_for_zones(zones_gdf):
    """Get historical wind speed data for all optimal zones."""
    try:
        all_wind_data = []
        
        for _, zone in zones_gdf.iterrows():
            lat, lon = zone['latitude'], zone['longitude']
            zone_wind_data = get_wind_speed_at_location_historical(lat, lon)
            if zone_wind_data is not None:
                all_wind_data.extend(zone_wind_data)
        
        return all_wind_data
        
    except Exception as e:
        return None

def add_wind_data_layers(m, show_layers, wind_opacity=0.6, wind_radius=25, wind_blur=15):
    """Add wind data layers (mean wind speed and standard deviation) to the map."""
    try:
        from folium import plugins
        import folium
        import pandas as pd
        import os
        import numpy as np
        
        # Load wind data
        PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
        PROJECT_ROOT = os.path.join(PROJECT_ROOT, "..", "..")
        
        # Mean wind speed data
        if show_layers.get('mean_wind_speed', False):
            mean_wind_path = os.path.join(PROJECT_ROOT, "data", "era5", "era5_ireland_mean_wind_1994_2024.csv")
            if os.path.exists(mean_wind_path):
                try:
                    df_mean = pd.read_csv(mean_wind_path)
                    
                    # Convert longitude from 0-360 to -180-180 if needed
                    if 'longitude' in df_mean.columns:
                        df_mean['longitude'] = df_mean['longitude'].apply(lambda x: x - 360 if x > 180 else x)
                    
                    # Filter data for Ireland bounds
                    df_mean = df_mean[
                        (df_mean['latitude'] >= 51.0) & (df_mean['latitude'] <= 55.5) &
                        (df_mean['longitude'] >= -11.0) & (df_mean['longitude'] <= -5.0)
                    ]
                    
                    # Create heatmap data with normalized values
                    wind_speeds = df_mean['wind_speed_10m'].dropna()
                    if len(wind_speeds) > 0:
                        min_wind = wind_speeds.min()
                        max_wind = wind_speeds.max()
                        
                        mean_wind_data = []
                        for _, row in df_mean.iterrows():
                            if not pd.isna(row['wind_speed_10m']):
                                # Normalize wind speed for better visualization
                                normalized_speed = (row['wind_speed_10m'] - min_wind) / (max_wind - min_wind) if max_wind > min_wind else 0.5
                                mean_wind_data.append([row['latitude'], row['longitude'], normalized_speed])
                        
                        # Add mean wind speed heatmap with improved styling for better resolution
                        # Use a more sophisticated approach with better rendering
                        wind_heatmap = plugins.HeatMap(
                            mean_wind_data,
                            name="Mean Wind Speed (m/s)",
                            radius=wind_radius,
                            gradient={
                                0.0: '#0000FF',    # Blue - Low wind speeds
                                0.2: '#0080FF',    # Light blue
                                0.4: '#00FFFF',    # Cyan
                                0.6: '#FFFF00',    # Yellow
                                0.8: '#FF8000',    # Orange
                                1.0: '#FF0000'     # Red - High wind speeds
                            },
                            min_opacity=wind_opacity,
                            max_zoom=20,  # Increased max zoom for better resolution
                            blur=wind_blur,
                            use_local_extrema=False,  # Better rendering
                            show=False  # Start hidden, user can toggle
                        )
                        wind_heatmap.add_to(m)
                        
                        # Add a more detailed wind speed layer using circles for better resolution
                        for i, (lat, lon, intensity) in enumerate(mean_wind_data[:100]):  # Limit to first 100 points for performance
                            # Convert normalized intensity back to wind speed for display
                            actual_wind_speed = min_wind + intensity * (max_wind - min_wind)
                            
                            # Color based on wind speed
                            if actual_wind_speed < 6:
                                color = '#0000FF'  # Blue
                            elif actual_wind_speed < 8:
                                color = '#0080FF'  # Light blue
                            elif actual_wind_speed < 10:
                                color = '#00FFFF'  # Cyan
                            elif actual_wind_speed < 12:
                                color = '#FFFF00'  # Yellow
                            else:
                                color = '#FF0000'  # Red
                            
                            # Add circle marker for better resolution
                            folium.CircleMarker(
                                location=[lat, lon],
                                radius=3,
                                color=color,
                                fill=True,
                                fillOpacity=0.6,
                                popup=f"Wind Speed: {actual_wind_speed:.1f} m/s"
                            ).add_to(m)
                        
                        st.success(f"✅ Mean wind speed layer loaded: {len(mean_wind_data)} data points")
                    else:
                        st.warning("No valid wind speed data found")
                        
                except Exception as e:
                    st.error(f"Error loading mean wind speed data: {e}")
            else:
                st.warning("Mean wind speed data file not found")
        
        # Wind standard deviation data
        if show_layers.get('wind_standard_deviation', False):
            std_wind_path = os.path.join(PROJECT_ROOT, "data", "era5", "era5_ireland_std_1994_2024.tif")
            if os.path.exists(std_wind_path):
                st.info("Wind standard deviation layer requires GeoTIFF processing - using simplified visualization")
                
                # Create a simplified variability indicator based on mean wind data
                mean_wind_path = os.path.join(PROJECT_ROOT, "data", "era5", "era5_ireland_mean_wind_1994_2024.csv")
                if os.path.exists(mean_wind_path):
                    try:
                        df_mean = pd.read_csv(mean_wind_path)
                        if 'longitude' in df_mean.columns:
                            df_mean['longitude'] = df_mean['longitude'].apply(lambda x: x - 360 if x > 180 else x)
                        
                        # Filter data for Ireland bounds
                        df_mean = df_mean[
                            (df_mean['latitude'] >= 51.0) & (df_mean['latitude'] <= 55.5) &
                            (df_mean['longitude'] >= -11.0) & (df_mean['longitude'] <= -5.0)
                        ]
                        
                        # Create variability data (simplified - in reality you'd use actual std dev)
                        # Use wind speed as a proxy for variability (higher wind = more variable)
                        wind_speeds = df_mean['wind_speed_10m'].dropna()
                        if len(wind_speeds) > 0:
                            min_wind = wind_speeds.min()
                            max_wind = wind_speeds.max()
                            
                            variability_data = []
                            for _, row in df_mean.iterrows():
                                if not pd.isna(row['wind_speed_10m']):
                                    # Create variability proxy (higher wind speed = more variable)
                                    variability_proxy = (row['wind_speed_10m'] - min_wind) / (max_wind - min_wind) if max_wind > min_wind else 0.5
                                    variability_data.append([row['latitude'], row['longitude'], variability_proxy])
                            
                            # Add wind variability heatmap with improved styling for better resolution
                            variability_heatmap = plugins.HeatMap(
                                variability_data,
                                name="Wind Variability (std dev)",
                                radius=wind_radius,
                                gradient={
                                    0.0: '#00FF00',    # Green - Low variability
                                    0.3: '#80FF00',    # Light green
                                    0.5: '#FFFF00',    # Yellow
                                    0.7: '#FF8000',    # Orange
                                    1.0: '#FF0000'     # Red - High variability
                                },
                                min_opacity=wind_opacity,
                                max_zoom=20,  # Increased max zoom for better resolution
                                blur=wind_blur,
                                use_local_extrema=False,  # Better rendering
                                show=False  # Start hidden, user can toggle
                            )
                            variability_heatmap.add_to(m)
                            
                            # Add detailed variability markers for better resolution
                            for i, (lat, lon, intensity) in enumerate(variability_data[:100]):  # Limit to first 100 points for performance
                                # Color based on variability
                                if intensity < 0.3:
                                    color = '#00FF00'  # Green - Low variability
                                elif intensity < 0.5:
                                    color = '#80FF00'  # Light green
                                elif intensity < 0.7:
                                    color = '#FFFF00'  # Yellow
                                elif intensity < 0.9:
                                    color = '#FF8000'  # Orange
                                else:
                                    color = '#FF0000'  # Red - High variability
                                
                                # Add circle marker for better resolution
                                folium.CircleMarker(
                                    location=[lat, lon],
                                    radius=3,
                                    color=color,
                                    fill=True,
                                    fillOpacity=0.6,
                                    popup=f"Variability: {intensity:.2f}"
                                ).add_to(m)
                            
                            st.success(f"✅ Wind variability layer loaded: {len(variability_data)} data points")
                        else:
                            st.warning("No valid wind data for variability calculation")
                            
                    except Exception as e:
                        st.error(f"Error loading wind variability data: {e}")
                else:
                    st.warning("Mean wind speed data file not found for variability calculation")
            else:
                st.warning("Wind standard deviation data file not found")
        
    except ImportError:
        st.warning("Folium plugins not available for wind data layers")
    except Exception as e:
        st.warning(f"Could not load wind data layers: {e}")

def add_infrastructure_to_map(m):
    """Add transmission infrastructure to the map (same as first page)."""
    import os
    import geopandas as gpd
    import json
    import pandas as pd
    
    # Load infrastructure data (same paths as first page)
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.join(PROJECT_ROOT, "..", "..")
    
    LINES_PATH = os.path.join(PROJECT_ROOT, "data", "osm", "lines_110kV_clean.geojson")
    SUBS_PATH = os.path.join(PROJECT_ROOT, "data", "osm", "substations_110kV_clean.geojson")
    WIND_PATH = os.path.join(PROJECT_ROOT, "data", "wind_farms", "Wind Farms June 2022_ESPG3857.shp")
    
    def load_layer(path):
        if not os.path.exists(path):
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
    
    # Load data
    lines = load_layer(LINES_PATH)
    subs = load_layer(SUBS_PATH)
    wind = load_layer(WIND_PATH)
    
    if not lines.empty:
        subs["coords"] = subs.geometry.apply(safe_point_coords)
        wind["coords"] = wind.geometry.apply(safe_point_coords)
        
        # Add transmission lines
        for col in lines.select_dtypes(include=["datetime64[ns]"]).columns:
            lines[col] = lines[col].astype(str)
        lines_geojson = json.loads(lines[["geometry"]].to_json())
        folium.GeoJson(
            lines_geojson,
            name="Transmission Lines",
            style_function=lambda x: {"color": "#007BFF", "weight": 2, "opacity": 0.7},
        ).add_to(m)
        
        # Add substations
        for _, row in subs.iterrows():
            if row["coords"]:
                folium.CircleMarker(location=row["coords"], radius=3, color="#D7263D", fill=True).add_to(m)
        
        # Add existing wind farms with enhanced tooltips (only if wind farms exist)
        if not wind.empty:
            for _, row in wind.iterrows():
                if row["coords"]:
                    # Extract wind farm information
                    wind_farm_name = extract_wind_farm_name(row)
                    wind_farm_capacity = extract_wind_farm_capacity(row)
                    
                    # Create enhanced popup
                    popup_html = create_wind_farm_popup(wind_farm_name, wind_farm_capacity, row)
                    
                    folium.CircleMarker(
                        location=row["coords"], 
                        radius=6, 
                        color="#009E73", 
                        fill=True,
                        fillOpacity=0.8,
                        popup=folium.Popup(popup_html, max_width=300)
                    ).add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    return m

# ============================================================
# STREAMLIT INTEGRATION
# ============================================================
def render_optimal_zones_map():
    """Render optimal zones map in Streamlit."""
    
    st.title("🎯 Optimal Wind Farm Zones")
    st.markdown("Interactive visualization of optimal wind farm development areas in Ireland.")
    
    # ======================================================
    # 🎛️ SELECTION CRITERIA CONTROLS
    # ======================================================
    st.sidebar.header("🎛️ Selection Criteria")
    
    # Wind farm type selection
    st.sidebar.subheader("🌊 Wind Farm Type")
    wind_farm_type = st.sidebar.radio(
        "Select Wind Farm Type:",
        ["Onshore", "Offshore", "Auto-Detect"],
        index=2,
        help="Choose between onshore, offshore, or auto-detect based on location"
    )
    
    # Wind resource criteria
    st.sidebar.subheader("🌬️ Wind Resource")
    
    # Adjust wind speed criteria based on type
    if wind_farm_type == "Offshore":
        min_wind_speed = st.sidebar.slider(
            "Minimum Wind Speed (m/s)", 
            min_value=6.0, 
            max_value=15.0, 
            value=8.0, 
            step=0.5,
            help="Offshore wind farms typically require higher wind speeds"
        )
    else:  # Onshore
        min_wind_speed = st.sidebar.slider(
            "Minimum Wind Speed (m/s)", 
            min_value=5.0, 
            max_value=12.0, 
            value=6.0, 
            step=0.5,
            help="Onshore wind farms can operate at lower wind speeds"
        )
    
    # Grid connectivity criteria
    st.sidebar.subheader("🏗️ Grid Connectivity")
    
    # Adjust grid distance criteria based on type
    if wind_farm_type == "Offshore":
        max_grid_distance = st.sidebar.slider(
            "Maximum Distance to Shore (km)", 
            min_value=5, 
            max_value=50, 
            value=25, 
            step=5,
            help="Offshore wind farms are typically closer to shore for grid connection"
        )
    else:  # Onshore
        max_grid_distance = st.sidebar.slider(
            "Maximum Grid Distance (km)", 
            min_value=10, 
            max_value=100, 
            value=50, 
            step=5,
            help="Onshore wind farms can be further from transmission infrastructure"
        )
    
    # Scoring weights (normalized to sum to 1)
    st.sidebar.subheader("⚖️ Scoring Weights")
    
    # Use number inputs with automatic normalization and session state
    wind_input = st.sidebar.number_input(
        "Wind Resource Weight", 
        min_value=0.0, 
        max_value=1.0, 
        value=st.session_state.get('wind_input', 0.5), 
        step=0.1,
        help="Importance of wind resource in scoring"
    )
    grid_input = st.sidebar.number_input(
        "Grid Connectivity Weight", 
        min_value=0.0, 
        max_value=1.0, 
        value=st.session_state.get('grid_input', 0.3), 
        step=0.1,
        help="Importance of grid connectivity in scoring"
    )
    env_input = st.sidebar.number_input(
        "Environmental Weight", 
        min_value=0.0, 
        max_value=1.0, 
        value=st.session_state.get('env_input', 0.2), 
        step=0.1,
        help="Importance of environmental factors in scoring"
    )
    
    # Store in session state
    st.session_state.wind_input = wind_input
    st.session_state.grid_input = grid_input
    st.session_state.env_input = env_input
    
    # Normalize weights to sum to 1
    total_weight = wind_input + grid_input + env_input
    if total_weight > 0:
        wind_weight = wind_input / total_weight
        grid_weight = grid_input / total_weight
        env_weight = env_input / total_weight
    else:
        wind_weight = 0.5
        grid_weight = 0.3
        env_weight = 0.2
    
    # Display normalized weights
    st.sidebar.markdown(f"**Normalized Weights:**")
    st.sidebar.markdown(f"Wind: {wind_weight:.1%}")
    st.sidebar.markdown(f"Grid: {grid_weight:.1%}")
    st.sidebar.markdown(f"Environmental: {env_weight:.1%}")
    
    # Analysis parameters
    st.sidebar.subheader("📊 Analysis Parameters")
    
    # Adjust grid resolution based on type
    if wind_farm_type == "Offshore":
        grid_resolution = st.sidebar.selectbox(
            "Grid Resolution", 
            options=[0.05, 0.1, 0.15, 0.2], 
            index=1,
            format_func=lambda x: f"{x}° ({x*111:.1f} km)",
            help="Offshore analysis can use finer resolution"
        )
    else:  # Onshore
        grid_resolution = st.sidebar.selectbox(
            "Grid Resolution", 
            options=[0.1, 0.15, 0.2, 0.25], 
            index=0,
            format_func=lambda x: f"{x}° ({x*111:.1f} km)",
            help="Resolution of analysis grid (lower = faster calculation)"
        )
    
    # Quick calculation option
    quick_calc = st.sidebar.checkbox(
        "⚡ Quick Calculation", 
        value=False,
        help="Use faster calculation with reduced grid resolution"
    )
    
    if quick_calc:
        grid_resolution = 0.2  # Use coarser grid for faster calculation
    
    # Zone filtering
    st.sidebar.subheader("🔍 Zone Filtering")
    show_excellent = st.sidebar.checkbox("Excellent Zones", value=True)
    show_good = st.sidebar.checkbox("Good Zones", value=True)
    show_moderate = st.sidebar.checkbox("Moderate Zones", value=True)
    show_marginal = st.sidebar.checkbox("Marginal Zones", value=False)
    
    # Map display controls
    st.sidebar.subheader("🗺️ Map Display")
    show_optimal = st.sidebar.checkbox("Show Optimal Zones", value=True)
    show_wind = st.sidebar.checkbox("Show Wind Heatmap", value=True)
    show_grid = st.sidebar.checkbox("Show Grid Connectivity", value=False)
    show_clusters = st.sidebar.checkbox("Show Cluster Centers", value=True)
    
    # Wind data layers
    st.sidebar.subheader("🌬️ Wind Data Layers")
    show_mean_wind = st.sidebar.checkbox("Mean Wind Speed", value=False, help="Show mean wind speed heatmap")
    show_wind_std = st.sidebar.checkbox("Wind Standard Deviation", value=False, help="Show wind variability heatmap")
    
    # Wind data styling options
    if show_mean_wind or show_wind_std:
        st.sidebar.subheader("🎨 Wind Layer Styling")
        wind_opacity = st.sidebar.slider("Wind Layer Opacity", 0.1, 1.0, st.session_state.get('wind_opacity', 0.6), 0.1)
        wind_radius = st.sidebar.slider("Wind Layer Radius", 10, 50, st.session_state.get('wind_radius', 25), 5)
        wind_blur = st.sidebar.slider("Wind Layer Blur", 5, 25, st.session_state.get('wind_blur', 15), 5)
        
        # Store in session state
        st.session_state.wind_opacity = wind_opacity
        st.session_state.wind_radius = wind_radius
        st.session_state.wind_blur = wind_blur
    
    # ======================================================
    # 🎯 PRESET CONFIGURATIONS
    # ======================================================
    st.sidebar.subheader("🎯 Preset Configurations")
    
    preset_col1, preset_col2 = st.sidebar.columns(2)
    
    with preset_col1:
        if st.button("🏆 Premium", use_container_width=True):
            st.session_state.min_wind_speed = 8.0
            st.session_state.max_grid_distance = 20
            st.session_state.wind_input = 0.6
            st.session_state.grid_input = 0.3
            st.session_state.env_input = 0.1
            st.rerun()
    
    with preset_col2:
        if st.button("⚖️ Balanced", use_container_width=True):
            st.session_state.min_wind_speed = 6.5
            st.session_state.max_grid_distance = 35
            st.session_state.wind_input = 0.5
            st.session_state.grid_input = 0.3
            st.session_state.env_input = 0.2
            st.rerun()
    
    if st.sidebar.button("💰 Cost-Focused", use_container_width=True):
        st.session_state.min_wind_speed = 6.0
        st.session_state.max_grid_distance = 25
        st.session_state.wind_input = 0.4
        st.session_state.grid_input = 0.5
        st.session_state.env_input = 0.1
        st.rerun()
    
    # ======================================================
    # 🚀 CALCULATION BUTTONS
    # ======================================================
    st.sidebar.subheader("🚀 Calculate Optimal Zones")

    col1, col2 = st.sidebar.columns(2)

    with col1:
        calculate_btn = st.button("🚀 Run Analysis", type="primary", use_container_width=True, help="Click to calculate optimal zones with current criteria")

    with col2:
        clear_cache_btn = st.button("🗑️ Clear Cache", use_container_width=True, help="Clear cached results and start fresh")
    
    # Show calculation status
    if 'optimal_zones' in st.session_state and 'cluster_stats' in st.session_state:
        st.sidebar.success("✅ Analysis Complete")
        st.sidebar.metric("Zones Found", len(st.session_state.optimal_zones))
        st.sidebar.warning("⚠️ **Parameter Change Detected**")
        st.sidebar.markdown("*Click 'Run Analysis' to recalculate with new parameters*")
    else:
        st.sidebar.info("⏳ Ready to Analyze")
        st.sidebar.markdown("*Click 'Run Analysis' to start*")
    
    if clear_cache_btn:
        if 'optimal_zones' in st.session_state:
            del st.session_state.optimal_zones
        if 'cluster_stats' in st.session_state:
            del st.session_state.cluster_stats
        st.rerun()
    
    # ======================================================
    # 📊 DATA PROCESSING
    # ======================================================
    # Only run calculation when explicitly requested
    if calculate_btn:
        # Create progress containers
        progress_container = st.container()
        status_container = st.container()
        
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            time_text = st.empty()
        
        with status_container:
            st.info("🔄 Starting optimal zones calculation...")
            
            from src.analysis.optimal_zones import calculate_optimal_zones_with_progress
            import time
            
            start_time = time.time()
            
            def progress_callback(progress, message):
                progress_bar.progress(progress)
                status_text.text(message)
                
                # Estimate time remaining
                elapsed = time.time() - start_time
                if progress > 0.1:  # Only show estimate after 10% progress
                    remaining = elapsed * (1 - progress) / progress
                    time_text.text(f"⏱️ Estimated time remaining: {remaining:.0f}s")
                else:
                    time_text.text("⏱️ Calculating...")
            
            # Handle auto-detection of wind farm type
            if wind_farm_type == "Auto-Detect":
                st.info("🔍 Auto-detecting wind farm types based on location...")
                # For auto-detect, we'll pass a special flag to the calculation function
                actual_wind_farm_type = "Auto-Detect"
            else:
                actual_wind_farm_type = wind_farm_type
            
            # Update parameters with progress callback
            zones_gdf, cluster_stats = calculate_optimal_zones_with_progress(
                grid_resolution=grid_resolution,
                min_wind_speed=min_wind_speed,
                max_grid_distance=max_grid_distance,
                weights={'wind': wind_weight, 'grid': grid_weight, 'environmental': env_weight},
                wind_farm_type=actual_wind_farm_type,
                progress_callback=progress_callback
            )
            
            st.session_state.optimal_zones = zones_gdf
            st.session_state.cluster_stats = cluster_stats
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            time_text.empty()
            
            st.success("✅ Optimal zones calculation complete!")
    else:
        # Check if we have cached results
        if 'optimal_zones' in st.session_state and 'cluster_stats' in st.session_state:
            zones_gdf = st.session_state.optimal_zones
            cluster_stats = st.session_state.cluster_stats
        else:
            # No calculation has been run yet
            st.info("🎯 **Ready to Analyze!** Click the 'Run Analysis' button to calculate optimal zones with your selected criteria.")
            
            # Show current criteria without running calculation
            st.subheader("📋 Current Selection Criteria")
            
            criteria_col1, criteria_col2, criteria_col3 = st.columns(3)
            
            with criteria_col1:
                st.metric("Wind Farm Type", wind_farm_type)
                st.metric("Min Wind Speed", f"{min_wind_speed:.1f} m/s")
                st.metric("Max Grid Distance", f"{max_grid_distance} km")
            
            with criteria_col2:
                st.metric("Wind Weight", f"{wind_weight:.1%}")
                st.metric("Grid Weight", f"{grid_weight:.1%}")
            
            with criteria_col3:
                st.metric("Environmental Weight", f"{env_weight:.1%}")
                st.metric("Grid Resolution", f"{grid_resolution}°")
            
            # Show wind data layer status
            if show_mean_wind or show_wind_std:
                st.subheader("🌬️ Wind Data Layers")
                wind_info_col1, wind_info_col2 = st.columns(2)
                
                with wind_info_col1:
                    if show_mean_wind:
                        st.success("✅ Mean Wind Speed layer will be active")
                    if show_wind_std:
                        st.success("✅ Wind Variability layer will be active")
                        
                with wind_info_col2:
                    st.metric("Layer Opacity", f"{wind_opacity:.1f}")
                    st.metric("Layer Radius", f"{wind_radius}px")
            
            st.stop()
    
    # Filter zones based on selection
    zone_filters = []
    if show_excellent:
        zone_filters.append('Excellent')
    if show_good:
        zone_filters.append('Good')
    if show_moderate:
        zone_filters.append('Moderate')
    if show_marginal:
        zone_filters.append('Marginal')
    
    if zone_filters:
        zones_gdf = zones_gdf[zones_gdf['zone_category'].isin(zone_filters)]
    
    # Layer visibility controls
    show_layers = {
        'optimal_zones': show_optimal,
        'wind_heatmap': show_wind,
        'grid_connectivity': show_grid,
        'cluster_centers': show_clusters,
        'mean_wind_speed': show_mean_wind,
        'wind_standard_deviation': show_wind_std
    }
    
    # ======================================================
    # 📊 CURRENT CRITERIA DISPLAY
    # ======================================================
    st.subheader("📋 Current Selection Criteria")

    criteria_col1, criteria_col2, criteria_col3 = st.columns(3)

    with criteria_col1:
        st.metric("Wind Farm Type", wind_farm_type)
        st.metric("Min Wind Speed", f"{min_wind_speed:.1f} m/s")
        st.metric("Max Grid Distance", f"{max_grid_distance} km")

        with criteria_col2:
            st.metric("Wind Weight", f"{wind_weight:.1%}")
            st.metric("Grid Weight", f"{grid_weight:.1%}")

        with criteria_col3:
            st.metric("Environmental Weight", f"{env_weight:.1%}")
            st.metric("Grid Resolution", f"{grid_resolution}°")
    
    # Wind data layer information
    if show_mean_wind or show_wind_std:
        st.subheader("🌬️ Wind Data Layers")
        wind_info_col1, wind_info_col2 = st.columns(2)
        
        with wind_info_col1:
            if show_mean_wind:
                st.success("✅ Mean Wind Speed layer active")
            if show_wind_std:
                st.success("✅ Wind Variability layer active")
                
        with wind_info_col2:
            st.metric("Layer Opacity", f"{wind_opacity:.1f}")
            st.metric("Layer Radius", f"{wind_radius}px")
    
    # ======================================================
    # 🗺️ MAP VISUALIZATION (Same format as first page)
    # ======================================================
    st.subheader("🗺️ Optimal Zones Map")
    
    # Always use Folium for consistency with first page
    m = create_folium_optimal_zones_map(zones_gdf, cluster_stats, show_layers)
    
    # Add transmission infrastructure like the first page
    m = add_infrastructure_to_map(m)
    
    # Add layer control for wind data layers
    if show_layers.get('mean_wind_speed', False) or show_layers.get('wind_standard_deviation', False):
        from folium import LayerControl
        layer_control = LayerControl(position='topright', collapsed=False)
        layer_control.add_to(m)
    
    # Display the map with key to force refresh when analysis is run
    map_key = f"optimal_zones_map_{len(zones_gdf)}_{hash(str(zones_gdf)) if len(zones_gdf) > 0 else 'empty'}"
    st_folium(m, height=700, width="100%", key=map_key)
    
    # ======================================================
    # 📊 RESULTS SUMMARY
    # ======================================================
    st.subheader("📊 Results Summary")
    
    # Check if no zones match the criteria
    if len(zones_gdf) == 0:
        st.warning(f"⚠️ No optimal zones found for {wind_farm_type} wind farms with the current criteria.")
        st.info("💡 Try adjusting your selection criteria:")
        st.markdown("""
        - **Wind Farm Type**: Consider switching between Onshore/Offshore
        - **Wind Speed**: Lower the minimum wind speed requirement
        - **Grid Distance**: Increase the maximum grid distance
        - **Weights**: Adjust the scoring weights to be more flexible
        """)
        return
    
    # Statistics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Wind Farm Type", wind_farm_type)
        st.metric("Total Zones", len(zones_gdf))
        if len(zones_gdf) > 0:
            st.success(f"✅ Found {len(zones_gdf)} optimal zones")
        else:
            st.warning("⚠️ No zones found")

    with col2:
        excellent_count = len(zones_gdf[zones_gdf['zone_category'] == 'Excellent'])
        st.metric("Excellent Zones", excellent_count)

    with col3:
        if len(zones_gdf) > 0:
            avg_wind = zones_gdf['wind_speed_mps'].mean()
            st.metric("Avg Wind Speed", f"{avg_wind:.1f} m/s")
        else:
            st.metric("Avg Wind Speed", "N/A")

    with col4:
        if len(zones_gdf) > 0:
            avg_cost = zones_gdf['grid_cost_eur'].mean()
            st.metric("Avg Grid Cost", f"€{avg_cost/1000:.0f}k")
        else:
            st.metric("Avg Grid Cost", "N/A")
    
    # Wind speed analysis for optimal zones
    if len(zones_gdf) > 0:
        st.subheader("🌬️ Wind Speed Analysis at Optimal Zones")
        
        # Use existing wind speed data from zones instead of historical data
        if 'wind_speed_mps' in zones_gdf.columns:
            # Overall wind speed distribution
            st.subheader("📊 Overall Wind Speed Distribution")
            all_wind_speeds = zones_gdf['wind_speed_mps'].tolist()
            
            if all_wind_speeds:
                import pandas as pd
                import numpy as np
                
                # Create overall histogram
                wind_df = pd.DataFrame({'Wind Speed (m/s)': all_wind_speeds})
                chart_data = wind_df['Wind Speed (m/s)'].value_counts().sort_index().reset_index()
                chart_data.columns = ['Wind Speed (m/s)', 'Count']
                st.bar_chart(chart_data, x="Wind Speed (m/s)", y="Count")
                st.caption("📊 **Overall Wind Speed Distribution** - Distribution of wind speeds across all optimal zones")
                
                # Overall statistics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Overall Mean", f"{np.mean(all_wind_speeds):.1f} m/s")
                with col2:
                    st.metric("Overall Max", f"{np.max(all_wind_speeds):.1f} m/s")
                with col3:
                    st.metric("Overall Min", f"{np.min(all_wind_speeds):.1f} m/s")
                with col4:
                    st.metric("Overall Std Dev", f"{np.std(all_wind_speeds):.1f} m/s")
            
            # Group by zone category and show wind speed distribution
            st.subheader("📈 Wind Speed by Zone Category")
            for category in zones_gdf['zone_category'].unique():
                category_zones = zones_gdf[zones_gdf['zone_category'] == category]
                if len(category_zones) > 0:
                    st.write(f"**{category} Zones** ({len(category_zones)} locations)")
                    
                    # Get wind speed data for this category
                    category_wind_speeds = category_zones['wind_speed_mps'].tolist()
                    
                    if category_wind_speeds:
                        import pandas as pd
                        import numpy as np
                        
                        # Create a histogram of wind speeds for this category
                        wind_df = pd.DataFrame({'Wind Speed (m/s)': category_wind_speeds})
                        chart_data = wind_df['Wind Speed (m/s)'].value_counts().sort_index().reset_index()
                        chart_data.columns = ['Wind Speed (m/s)', 'Count']
                        
                        # Create histogram with axis titles
                        st.bar_chart(chart_data, x="Wind Speed (m/s)", y="Count")
                        st.caption(f"📈 **{category} Zones Wind Speed Distribution** - Wind speed distribution for {category} zone category")
                        
                        # Show statistics
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Mean Wind Speed", f"{np.mean(category_wind_speeds):.1f} m/s")
                        with col2:
                            st.metric("Max Wind Speed", f"{np.max(category_wind_speeds):.1f} m/s")
                        with col3:
                            st.metric("Min Wind Speed", f"{np.min(category_wind_speeds):.1f} m/s")
                        with col4:
                            st.metric("Std Deviation", f"{np.std(category_wind_speeds):.1f} m/s")
                    else:
                        st.info(f"No wind speed data available for {category} zones")
        else:
            st.info("Wind speed data not available in zones data")
        
        # Top zones table
        st.subheader("🏆 Top Optimal Zones")
        top_zones = zones_gdf.nlargest(10, 'composite_score')[
            ['latitude', 'longitude', 'zone_category', 'wind_speed_mps',
             'grid_distance_km', 'grid_cost_eur', 'composite_score']
        ]
        
        # Add capacity factor if available
        if 'capacity_factor' in zones_gdf.columns:
            top_zones = zones_gdf.nlargest(10, 'composite_score')[
                ['latitude', 'longitude', 'zone_category', 'wind_speed_mps',
                 'capacity_factor', 'grid_distance_km', 'grid_cost_eur', 'composite_score']
            ]
            # Format capacity factor as percentage
            top_zones['capacity_factor'] = (top_zones['capacity_factor'] * 100).round(1).astype(str) + '%'
        elif 'capacity_factor_score' in zones_gdf.columns:
            # Use capacity factor score if available
            top_zones = zones_gdf.nlargest(10, 'composite_score')[
                ['latitude', 'longitude', 'zone_category', 'wind_speed_mps',
                 'capacity_factor_score', 'grid_distance_km', 'grid_cost_eur', 'composite_score']
            ]
            # Rename for display and format as percentage
            top_zones = top_zones.rename(columns={'capacity_factor_score': 'capacity_factor'})
            top_zones['capacity_factor'] = (top_zones['capacity_factor'] * 100).round(1).astype(str) + '%'
        
        st.dataframe(top_zones, use_container_width=True)
        
        # Download results
        st.subheader("💾 Download Results")
        csv_data = zones_gdf.to_csv(index=False)
        st.download_button(
            label="Download Optimal Zones CSV",
            data=csv_data,
            file_name=f"optimal_zones_{min_wind_speed}ms_{max_grid_distance}km.csv",
            mime="text/csv"
        )
    else:
        st.warning("⚠️ No zones found matching your criteria. Try adjusting the selection parameters.")

if __name__ == "__main__":
    render_optimal_zones_map()
