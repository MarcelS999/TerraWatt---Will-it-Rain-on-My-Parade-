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
optimal_zones.py
----------------
Calculate optimal wind farm zones based on wind resources, grid connectivity,
and economic factors. Uses multi-criteria analysis to identify the best
locations for wind farm development in Ireland.
"""

import os
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from shapely.geometry import Point, Polygon
from scipy.spatial.distance import cdist
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# CONFIG
# ============================================================
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
ERA5_DIR = os.path.join(PROJECT_ROOT, "data", "era5")
GRID_DIR = os.path.join(PROJECT_ROOT, "data", "osm")
WIND_DIR = os.path.join(PROJECT_ROOT, "data", "wind_farms")

MEAN_TIF = os.path.join(ERA5_DIR, "era5_ireland_mean_1994_2024.tif")
STD_TIF = os.path.join(ERA5_DIR, "era5_ireland_std_1994_2024.tif")
SUBS_PATH = os.path.join(GRID_DIR, "substations_110kV_clean.geojson")
LINES_PATH = os.path.join(GRID_DIR, "lines_110kV_clean.geojson")
WIND_PATH = os.path.join(WIND_DIR, "Wind Farms June 2022_ESPG3857.shp")

# ============================================================
# DATA LOADING
# ============================================================
def load_era5_wind_data():
    """Load ERA5 wind data from CSV file."""
    csv_path = os.path.join(ERA5_DIR, "era5_ireland_mean_wind_1994_2024.csv")
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        # Convert longitude from 0-360 to -180 to 180
        df['longitude'] = df['longitude'] - 360
        return df
    return None

def load_grid_infrastructure():
    """Load transmission infrastructure data."""
    subs = gpd.read_file(SUBS_PATH).to_crs("EPSG:4326")
    lines = gpd.read_file(LINES_PATH).to_crs("EPSG:4326")
    return subs, lines

def load_existing_wind_farms():
    """Load existing wind farms data."""
    if os.path.exists(WIND_PATH):
        wind_farms = gpd.read_file(WIND_PATH).to_crs("EPSG:4326")
        return wind_farms
    return None

# ============================================================
# WIND RESOURCE ANALYSIS
# ============================================================
def calculate_wind_score(lat, lon, wind_data):
    """Calculate wind resource score for a location (0-1, higher is better)."""
    # Find nearest wind data point
    distances = np.sqrt((wind_data['latitude'] - lat)**2 + (wind_data['longitude'] - lon)**2)
    nearest_idx = distances.idxmin()
    wind_speed = wind_data.loc[nearest_idx, 'wind_speed_10m']
    
    # Realistic wind speed scoring for Irish conditions
    # Minimum viable: 6 m/s, Excellent: 10+ m/s
    # Use sigmoid function for more realistic scoring
    if wind_speed < 6.0:
        wind_score = 0.0
    elif wind_speed >= 10.0:
        wind_score = 1.0
    else:
        # Sigmoid curve between 6-10 m/s
        wind_score = 1 / (1 + np.exp(-2 * (wind_speed - 8)))
    
    return wind_score

def calculate_capacity_factor_score(lat, lon, wind_data):
    """Calculate capacity factor score using wind speed (DO NOT MODIFY CF FORMULATION)."""
    # Find nearest wind data point
    distances = np.sqrt((wind_data['latitude'] - lat)**2 + (wind_data['longitude'] - lon)**2)
    nearest_idx = distances.idxmin()
    wind_speed = wind_data.loc[nearest_idx, 'wind_speed_10m']
    
    # Using simplified relationship: CF ≈ 0.005 * (wind_speed)^2.5
    cf = 0.005 * (wind_speed ** 2.5)
    # Normalize to 0-1 scale (assuming max CF of 0.5)
    cf_score = np.clip(cf / 0.5, 0, 1)
    return cf_score

def calculate_actual_capacity_factor(lat, lon, wind_data):
    """Calculate actual capacity factor (0-1) based on wind speed."""
    # Find nearest wind data point
    distances = np.sqrt((wind_data['latitude'] - lat)**2 + (wind_data['longitude'] - lon)**2)
    nearest_idx = distances.idxmin()
    wind_speed = wind_data.loc[nearest_idx, 'wind_speed_10m']
    
    # Using the same relationship as the score function: CF ≈ 0.005 * (wind_speed)^2.5
    cf = 0.005 * (wind_speed ** 2.5)
    # Return actual capacity factor (0-1)
    return np.clip(cf, 0, 1)

def calculate_wind_variability_score(lat, lon, wind_data):
    """Calculate wind variability score (lower std dev = higher score for better CF)."""
    # Find nearest wind data point
    distances = np.sqrt((wind_data['latitude'] - lat)**2 + (wind_data['longitude'] - lon)**2)
    nearest_idx = distances.idxmin()
    wind_speed = wind_data.loc[nearest_idx, 'wind_speed_10m']
    
    # For now, use a simplified variability score based on wind speed
    # Lower wind speeds typically have lower variability
    # This is a proxy - in reality we'd need actual std dev data
    if wind_speed < 7.0:
        variability_score = 0.9  # Low variability (good)
    elif wind_speed < 8.5:
        variability_score = 0.7  # Medium variability
    elif wind_speed < 10.0:
        variability_score = 0.5  # Higher variability
    else:
        variability_score = 0.3  # High variability (less predictable)
    
    return variability_score

# ============================================================
# GRID CONNECTIVITY ANALYSIS
# ============================================================
def calculate_grid_score(lat, lon, subs, lines):
    """Calculate grid connectivity score (0-1, higher is better)."""
    point = Point(lon, lat)
    
    # Distance to nearest substation
    subs['distance'] = subs.geometry.distance(point) * 111  # Convert to km
    min_subs_dist = subs['distance'].min()
    
    # Distance to nearest transmission line
    lines['distance'] = lines.geometry.distance(point) * 111  # Convert to km
    min_line_dist = lines['distance'].min()
    
    # Use the closer of the two (substation or line)
    min_dist = min(min_subs_dist, min_line_dist)
    
    # Realistic grid scoring based on Irish transmission infrastructure
    # Excellent: <5km, Good: 5-15km, Moderate: 15-30km, Poor: >30km
    if min_dist <= 5:
        grid_score = 1.0
    elif min_dist <= 15:
        # Linear interpolation between 1.0 and 0.7
        grid_score = 1.0 - 0.3 * (min_dist - 5) / 10
    elif min_dist <= 30:
        # Linear interpolation between 0.7 and 0.3
        grid_score = 0.7 - 0.4 * (min_dist - 15) / 15
    else:
        # Exponential decay for very far distances
        grid_score = 0.3 * np.exp(-(min_dist - 30) / 20)
    
    return np.clip(grid_score, 0, 1)

def calculate_grid_cost(lat, lon, subs):
    """Calculate estimated grid connection cost."""
    point = Point(lon, lat)
    subs['distance'] = subs.geometry.distance(point) * 111  # Convert to km
    min_dist = subs['distance'].min()
    
    # Cost model: base cost + per km cost
    base_cost = 250_000  # €250k base cost
    per_km_cost = 25_000  # €25k per km
    total_cost = base_cost + per_km_cost * min_dist
    
    return total_cost

# ============================================================
# ENVIRONMENTAL CONSTRAINTS
# ============================================================
def calculate_environmental_score(lat, lon, existing_wind_farms=None):
    """Calculate environmental suitability score (0-1, higher is better)."""
    point = Point(lon, lat)
    
    # Distance to existing wind farms (avoid clustering)
    if existing_wind_farms is not None and len(existing_wind_farms) > 0:
        existing_wind_farms['distance'] = existing_wind_farms.geometry.distance(point) * 111
        min_existing_dist = existing_wind_farms['distance'].min()
        
        # Realistic environmental scoring
        # Too close (<3km): very poor, close (3-8km): poor, moderate (8-15km): good, far (>15km): excellent
        if min_existing_dist < 3:
            env_score = 0.1  # Very poor - too close to existing farms
        elif min_existing_dist < 8:
            # Linear interpolation between 0.1 and 0.6
            env_score = 0.1 + 0.5 * (min_existing_dist - 3) / 5
        elif min_existing_dist < 15:
            # Linear interpolation between 0.6 and 0.9
            env_score = 0.6 + 0.3 * (min_existing_dist - 8) / 7
        else:
            env_score = 1.0  # Excellent - far from existing farms
    else:
        env_score = 1.0  # No existing farms, excellent score
    
    return np.clip(env_score, 0, 1)

def calculate_offshore_grid_score(lat, lon, subs, lines):
    """Calculate offshore grid connectivity score (distance to shore)."""
    point = Point(lon, lat)
    
    # For offshore, we care about distance to shore (substations)
    subs['distance'] = subs.geometry.distance(point) * 111  # Convert to km
    min_subs_dist = subs['distance'].min()
    
    # Offshore grid scoring - closer to shore is better
    # Excellent: <10km, Good: 10-20km, Moderate: 20-40km, Poor: >40km
    if min_subs_dist <= 10:
        grid_score = 1.0
    elif min_subs_dist <= 20:
        grid_score = 1.0 - 0.3 * (min_subs_dist - 10) / 10
    elif min_subs_dist <= 40:
        grid_score = 0.7 - 0.4 * (min_subs_dist - 20) / 20
    else:
        grid_score = 0.3 * np.exp(-(min_subs_dist - 40) / 20)
    
    return np.clip(grid_score, 0, 1)

def calculate_offshore_environmental_score(lat, lon, existing_wind_farms=None):
    """Calculate offshore environmental suitability score."""
    point = Point(lon, lat)
    
    # Offshore environmental considerations
    # Distance to existing offshore wind farms (avoid clustering)
    if existing_wind_farms is not None and len(existing_wind_farms) > 0:
        existing_wind_farms['distance'] = existing_wind_farms.geometry.distance(point) * 111
        min_existing_dist = existing_wind_farms['distance'].min()
        
        # Offshore spacing requirements (larger than onshore)
        if min_existing_dist < 5:
            env_score = 0.1  # Very poor - too close to existing farms
        elif min_existing_dist < 15:
            # Linear interpolation between 0.1 and 0.6
            env_score = 0.1 + 0.5 * (min_existing_dist - 5) / 10
        elif min_existing_dist < 30:
            # Linear interpolation between 0.6 and 0.9
            env_score = 0.6 + 0.3 * (min_existing_dist - 15) / 15
        else:
            env_score = 1.0  # Excellent - far from existing farms
    else:
        env_score = 1.0  # No existing farms, excellent score
    
    return np.clip(env_score, 0, 1)

# ============================================================
# OPTIMAL ZONES CALCULATION
# ============================================================
def calculate_optimal_zones(
    grid_resolution=0.1,  # degrees
    min_wind_speed=6.0,  # m/s
    max_grid_distance=50,  # km
    weights={'wind': 0.5, 'grid': 0.3, 'environmental': 0.2},
    wind_farm_type="Onshore"
):
    """
    Calculate optimal zones for wind farm development.
    
    Parameters:
    -----------
    grid_resolution : float
        Grid resolution in degrees for analysis
    min_wind_speed : float
        Minimum wind speed threshold (m/s)
    max_grid_distance : float
        Maximum distance to grid infrastructure (km)
    weights : dict
        Weights for different criteria
    
    Returns:
    --------
    gdf : GeoDataFrame
        Optimal zones with scores and metadata
    """
    
    print("🌬️ Loading wind resource data...")
    wind_data = load_era5_wind_data()
    if wind_data is None:
        raise ValueError("Wind data not found!")
    
    print("🏗️ Loading grid infrastructure...")
    subs, lines = load_grid_infrastructure()
    
    print("🌱 Loading existing wind farms...")
    existing_wind_farms = load_existing_wind_farms()
    
    # Auto-detection function for wind farm type using OpenStreetMap
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
            
            # Check for water bodies
            water_response = requests.get(overpass_url, params={'data': water_query}, timeout=10)
            if water_response.status_code == 200:
                water_data = water_response.json()
                if water_data.get('elements'):
                    return 'Offshore'  # Found water bodies
            
            # If no water found, assume onshore
            return 'Onshore'
            
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
        # Use simple method for faster processing (OSM API is too slow)
        return determine_onshore_offshore_simple(lat, lon)
    
    # Create analysis grid
    print("📊 Creating analysis grid...")
    lat_min, lat_max = 51.0, 55.5
    lon_min, lon_max = -11.0, -5.0
    
    lats = np.arange(lat_min, lat_max, grid_resolution)
    lons = np.arange(lon_min, lon_max, grid_resolution)
    
    grid_points = []
    for lat in lats:
        for lon in lons:
            grid_points.append({
                'latitude': lat,
                'longitude': lon,
                'geometry': Point(lon, lat)
            })
    
    print(f"🔍 Analyzing {len(grid_points)} grid points...")
    
    # Calculate scores for each point
    results = []
    for i, point in enumerate(grid_points):
        if i % 100 == 0:
            print(f"   Progress: {i}/{len(grid_points)}")
        
        lat, lon = point['latitude'], point['longitude']
        
        # Calculate individual scores
        wind_score = calculate_wind_score(lat, lon, wind_data)
        cf_score = calculate_capacity_factor_score(lat, lon, wind_data)
        actual_cf = calculate_actual_capacity_factor(lat, lon, wind_data)
        variability_score = calculate_wind_variability_score(lat, lon, wind_data)
        # Adjust scoring based on wind farm type
        if wind_farm_type == "Auto-Detect":
            # Auto-detect: determine type for this location
            location_type = determine_onshore_offshore(lat, lon)
            if location_type == "Offshore":
                grid_score = calculate_offshore_grid_score(lat, lon, subs, lines)
                env_score = calculate_offshore_environmental_score(lat, lon, existing_wind_farms)
            else:  # Onshore
                grid_score = calculate_grid_score(lat, lon, subs, lines)
                env_score = calculate_environmental_score(lat, lon, existing_wind_farms)
        elif wind_farm_type == "Offshore":
            # Offshore wind farms have different considerations
            grid_score = calculate_offshore_grid_score(lat, lon, subs, lines)
            env_score = calculate_offshore_environmental_score(lat, lon, existing_wind_farms)
        else:  # Onshore
            grid_score = calculate_grid_score(lat, lon, subs, lines)
            env_score = calculate_environmental_score(lat, lon, existing_wind_farms)
        
        # Check constraints
        wind_speed = 5 + wind_score * 7  # Convert back to m/s
        point_geom = Point(lon, lat)
        subs['distance'] = subs.geometry.distance(point_geom) * 111
        min_grid_dist = subs['distance'].min()
        
        # Skip if doesn't meet constraints
        if wind_speed < min_wind_speed or min_grid_dist > max_grid_distance:
            continue
        
        # Calculate weighted composite score (normalized to 0-1)
        # Ensure weights sum to 1.0
        total_weight = sum(weights.values())
        normalized_weights = {k: v/total_weight for k, v in weights.items()}
        
        # Combine wind resource and variability for better capacity factors
        # Lower variability (higher score) leads to better capacity factors
        wind_composite = 0.7 * wind_score + 0.3 * variability_score
        
        composite_score = (
            normalized_weights['wind'] * wind_composite +
            normalized_weights['grid'] * grid_score +
            normalized_weights['environmental'] * env_score
        )
        
        # Ensure composite score is between 0 and 1
        composite_score = np.clip(composite_score, 0, 1)
        
        # Calculate additional metrics
        grid_cost = calculate_grid_cost(lat, lon, subs)
        
        # Determine location type for auto-detection
        if wind_farm_type == "Auto-Detect":
            location_type = determine_onshore_offshore(lat, lon)
        else:
            location_type = wind_farm_type
            
        results.append({
            'latitude': lat,
            'longitude': lon,
            'geometry': Point(lon, lat),
            'wind_score': wind_score,
            'capacity_factor_score': cf_score,
            'capacity_factor': actual_cf,
            'variability_score': variability_score,
            'wind_composite_score': wind_composite,
            'grid_score': grid_score,
            'environmental_score': env_score,
            'composite_score': composite_score,
            'wind_farm_type': location_type,
            'wind_speed_mps': wind_speed,
            'grid_distance_km': min_grid_dist,
            'grid_cost_eur': grid_cost,
            'zone_category': categorize_zone(composite_score, wind_speed, min_grid_dist)
        })
    
    print(f"✅ Found {len(results)} suitable locations")
    
    # Filter results based on wind farm type criteria
    if wind_farm_type != "Auto-Detect":
        # Filter to only include zones that match the selected wind farm type
        filtered_results = []
        for result in results:
            if result['wind_farm_type'] == wind_farm_type:
                filtered_results.append(result)
        results = filtered_results
        print(f"✅ Filtered to {len(results)} {wind_farm_type.lower()} locations")
    
    # Convert to GeoDataFrame
    gdf = gpd.GeoDataFrame(results, crs="EPSG:4326")
    
    return gdf

def categorize_zone(composite_score, wind_speed, grid_distance):
    """Categorize zones based on suitability (realistic thresholds)."""
    # Excellent: High composite score, good wind, close to grid
    if composite_score >= 0.8 and wind_speed >= 8.5 and grid_distance <= 15:
        return "Excellent"
    # Good: Good composite score, decent wind, reasonable grid distance
    elif composite_score >= 0.65 and wind_speed >= 7.5 and grid_distance <= 25:
        return "Good"
    # Moderate: Moderate composite score, acceptable wind, further from grid
    elif composite_score >= 0.45 and wind_speed >= 6.5 and grid_distance <= 35:
        return "Moderate"
    # Marginal: Low scores or poor conditions
    else:
        return "Marginal"

# ============================================================
# SIMPLE K-MEANS CLUSTERING (without sklearn)
# ============================================================
def simple_kmeans(coords, n_clusters, max_iters=100, tolerance=1e-4):
    """Simple k-means clustering implementation."""
    n_points, n_dims = coords.shape
    n_clusters = min(n_clusters, n_points)
    
    # Initialize centroids randomly
    np.random.seed(42)
    centroids = coords[np.random.choice(n_points, n_clusters, replace=False)]
    
    for _ in range(max_iters):
        # Assign points to nearest centroid
        distances = cdist(coords, centroids)
        labels = np.argmin(distances, axis=1)
        
        # Update centroids
        new_centroids = np.array([coords[labels == k].mean(axis=0) 
                                 for k in range(n_clusters)])
        
        # Check for convergence
        if np.allclose(centroids, new_centroids, atol=tolerance):
            break
        centroids = new_centroids
    
    return labels, centroids

def cluster_optimal_zones(gdf, n_clusters=10):
    """Cluster optimal zones into distinct development areas."""
    if len(gdf) == 0:
        return gdf, []
    
    # Extract coordinates for clustering
    coords = gdf[['longitude', 'latitude']].values
    
    # Perform simple k-means clustering
    cluster_labels, centroids = simple_kmeans(coords, min(n_clusters, len(gdf)))
    
    gdf['cluster_id'] = cluster_labels
    
    # Calculate cluster statistics
    cluster_stats = []
    for cluster_id in range(len(centroids)):
        cluster_data = gdf[gdf['cluster_id'] == cluster_id]
        if len(cluster_data) > 0:
            cluster_stats.append({
                'cluster_id': cluster_id,
                'count': len(cluster_data),
                'avg_score': cluster_data['composite_score'].mean(),
                'avg_wind_speed': cluster_data['wind_speed_mps'].mean(),
                'avg_grid_distance': cluster_data['grid_distance_km'].mean(),
                'centroid_lat': cluster_data['latitude'].mean(),
                'centroid_lon': cluster_data['longitude'].mean()
            })
    
    return gdf, cluster_stats

# ============================================================
# SCORING VALIDATION
# ============================================================
def validate_scoring_system(zones_gdf):
    """Validate that the scoring system is working correctly."""
    print("🔍 Validating scoring system...")
    
    # Check score ranges
    wind_scores = zones_gdf['wind_score']
    variability_scores = zones_gdf['variability_score']
    grid_scores = zones_gdf['grid_score']
    env_scores = zones_gdf['environmental_score']
    composite_scores = zones_gdf['composite_score']
    
    print(f"   Wind scores: {wind_scores.min():.3f} - {wind_scores.max():.3f}")
    print(f"   Variability scores: {variability_scores.min():.3f} - {variability_scores.max():.3f}")
    print(f"   Grid scores: {grid_scores.min():.3f} - {grid_scores.max():.3f}")
    print(f"   Environmental scores: {env_scores.min():.3f} - {env_scores.max():.3f}")
    print(f"   Composite scores: {composite_scores.min():.3f} - {composite_scores.max():.3f}")
    
    # Check normalization
    if composite_scores.min() < 0 or composite_scores.max() > 1:
        print("⚠️  Warning: Composite scores not properly normalized!")
    else:
        print("✅ All scores properly normalized (0-1)")
    
    # Check zone distribution
    zone_counts = zones_gdf['zone_category'].value_counts()
    print(f"   Zone distribution: {zone_counts.to_dict()}")
    
    return True

# ============================================================
# PROGRESS-ENABLED CALCULATION
# ============================================================
def calculate_optimal_zones_with_progress(
    grid_resolution=0.1,
    min_wind_speed=6.0,
    max_grid_distance=50,
    weights={'wind': 0.5, 'grid': 0.3, 'environmental': 0.2},
    wind_farm_type="Onshore",
    progress_callback=None
):
    """Calculate optimal zones with progress reporting."""
    
    if progress_callback:
        progress_callback(0.05, "Loading wind resource data...")
    
    wind_data = load_era5_wind_data()
    if wind_data is None:
        raise ValueError("Wind data not found!")
    
    if progress_callback:
        progress_callback(0.10, "Loading grid infrastructure...")
    
    subs, lines = load_grid_infrastructure()
    
    if progress_callback:
        progress_callback(0.15, "Loading existing wind farms...")
    
    existing_wind_farms = load_existing_wind_farms()
    
    # Auto-detection function for wind farm type using OpenStreetMap
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
            
            # Check for water bodies
            water_response = requests.get(overpass_url, params={'data': water_query}, timeout=10)
            if water_response.status_code == 200:
                water_data = water_response.json()
                if water_data.get('elements'):
                    return 'Offshore'  # Found water bodies
            
            # If no water found, assume onshore
            return 'Onshore'
            
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
        # Use simple method for faster processing (OSM API is too slow)
        return determine_onshore_offshore_simple(lat, lon)
    
    if progress_callback:
        progress_callback(0.20, "Creating analysis grid...")
    
    # Create analysis grid based on wind farm type
    if wind_farm_type == "Auto-Detect":
        # Auto-detect analysis - cover all areas and determine type per location
        lat_min, lat_max = 51.0, 55.5
        lon_min, lon_max = -11.0, -5.0
        
        if progress_callback:
            progress_callback(0.22, "Creating comprehensive grid for auto-detection...")
    elif wind_farm_type == "Offshore":
        # Offshore analysis - focus on coastal waters
        lat_min, lat_max = 51.0, 55.5
        lon_min, lon_max = -11.0, -5.0
        
        # Filter to offshore areas (beyond coastline)
        # This is a simplified approach - in reality you'd use coastline data
        offshore_buffer = 0.1  # degrees from shore
        lat_min = max(lat_min, 51.0 + offshore_buffer)
        lat_max = min(lat_max, 55.5 - offshore_buffer)
        lon_min = max(lon_min, -11.0 + offshore_buffer)
        lon_max = min(lon_max, -5.0 - offshore_buffer)
        
        if progress_callback:
            progress_callback(0.22, "Focusing on offshore areas...")
    else:  # Onshore
        # Onshore analysis - focus on land areas
        lat_min, lat_max = 51.0, 55.5
        lon_min, lon_max = -11.0, -5.0
    
    lats = np.arange(lat_min, lat_max, grid_resolution)
    lons = np.arange(lon_min, lon_max, grid_resolution)
    
    grid_points = []
    for lat in lats:
        for lon in lons:
            grid_points.append({
                'latitude': lat,
                'longitude': lon,
                'geometry': Point(lon, lat)
            })
    
    total_points = len(grid_points)
    results = []
    
    if progress_callback:
        progress_callback(0.25, f"Analyzing {total_points} grid points...")
    
    # Pre-calculate grid distances for efficiency
    if progress_callback:
        progress_callback(0.22, "Pre-calculating grid distances...")
    
    # Create a more efficient grid distance lookup
    grid_distance_cache = {}
    
    # Calculate scores for each point
    for i, point in enumerate(grid_points):
        # Update progress
        progress = 0.25 + 0.60 * (i / total_points)
        if i % max(1, total_points // 20) == 0:  # Update every 5%
            if progress_callback:
                progress_callback(progress, f"Analyzing point {i+1}/{total_points}...")
        
        lat, lon = point['latitude'], point['longitude']
        
        # Calculate individual scores
        wind_score = calculate_wind_score(lat, lon, wind_data)
        cf_score = calculate_capacity_factor_score(lat, lon, wind_data)
        actual_cf = calculate_actual_capacity_factor(lat, lon, wind_data)
        variability_score = calculate_wind_variability_score(lat, lon, wind_data)
        # Adjust scoring based on wind farm type
        if wind_farm_type == "Auto-Detect":
            # Auto-detect: determine type for this location
            location_type = determine_onshore_offshore(lat, lon)
            if location_type == "Offshore":
                grid_score = calculate_offshore_grid_score(lat, lon, subs, lines)
                env_score = calculate_offshore_environmental_score(lat, lon, existing_wind_farms)
            else:  # Onshore
                grid_score = calculate_grid_score(lat, lon, subs, lines)
                env_score = calculate_environmental_score(lat, lon, existing_wind_farms)
        elif wind_farm_type == "Offshore":
            # Offshore wind farms have different considerations
            grid_score = calculate_offshore_grid_score(lat, lon, subs, lines)
            env_score = calculate_offshore_environmental_score(lat, lon, existing_wind_farms)
        else:  # Onshore
            grid_score = calculate_grid_score(lat, lon, subs, lines)
            env_score = calculate_environmental_score(lat, lon, existing_wind_farms)
        
        # Check constraints
        wind_speed = 5 + wind_score * 7  # Convert back to m/s
        point_geom = Point(lon, lat)
        
        # Use cached distance if available, otherwise calculate
        cache_key = f"{lat:.3f}_{lon:.3f}"
        if cache_key in grid_distance_cache:
            min_grid_dist = grid_distance_cache[cache_key]
        else:
            subs['distance'] = subs.geometry.distance(point_geom) * 111
            min_grid_dist = subs['distance'].min()
            grid_distance_cache[cache_key] = min_grid_dist
        
        # Skip if doesn't meet constraints
        if wind_speed < min_wind_speed or min_grid_dist > max_grid_distance:
            continue
        
        # Calculate weighted composite score (normalized to 0-1)
        total_weight = sum(weights.values())
        normalized_weights = {k: v/total_weight for k, v in weights.items()}
        
        # Combine wind resource and variability for better capacity factors
        wind_composite = 0.7 * wind_score + 0.3 * variability_score
        
        composite_score = (
            normalized_weights['wind'] * wind_composite +
            normalized_weights['grid'] * grid_score +
            normalized_weights['environmental'] * env_score
        )
        
        composite_score = np.clip(composite_score, 0, 1)
        
        # Calculate additional metrics
        grid_cost = calculate_grid_cost(lat, lon, subs)
        
        # Determine location type for auto-detection
        if wind_farm_type == "Auto-Detect":
            location_type = determine_onshore_offshore(lat, lon)
        else:
            location_type = wind_farm_type
            
        results.append({
            'latitude': lat,
            'longitude': lon,
            'geometry': Point(lon, lat),
            'wind_score': wind_score,
            'capacity_factor_score': cf_score,
            'capacity_factor': actual_cf,
            'variability_score': variability_score,
            'wind_composite_score': wind_composite,
            'grid_score': grid_score,
            'environmental_score': env_score,
            'composite_score': composite_score,
            'wind_farm_type': location_type,
            'wind_speed_mps': wind_speed,
            'grid_distance_km': min_grid_dist,
            'grid_cost_eur': grid_cost,
            'zone_category': categorize_zone(composite_score, wind_speed, min_grid_dist)
        })
    
    if progress_callback:
        progress_callback(0.85, f"Found {len(results)} suitable locations, filtering...")
    
    # Filter results based on wind farm type criteria
    if wind_farm_type != "Auto-Detect":
        # Filter to only include zones that match the selected wind farm type
        filtered_results = []
        for result in results:
            if result['wind_farm_type'] == wind_farm_type:
                filtered_results.append(result)
        results = filtered_results
        if progress_callback:
            progress_callback(0.87, f"Filtered to {len(results)} {wind_farm_type.lower()} locations")
    
    if progress_callback:
        progress_callback(0.90, f"Clustering {len(results)} locations...")
    
    # Convert to GeoDataFrame
    gdf = gpd.GeoDataFrame(results, crs="EPSG:4326")
    
    # Cluster zones
    clustered_zones, cluster_stats = cluster_optimal_zones(gdf)
    
    if progress_callback:
        progress_callback(1.0, f"Complete! Generated {len(gdf)} zones in {len(cluster_stats)} clusters")
    
    return clustered_zones, cluster_stats

# ============================================================
# MAIN FUNCTION
# ============================================================
def generate_optimal_zones():
    """Main function to generate optimal zones."""
    print("🚀 Starting optimal zones calculation...")
    
    # Calculate optimal zones
    optimal_zones = calculate_optimal_zones()
    
    # Validate scoring system
    validate_scoring_system(optimal_zones)
    
    # Cluster zones
    print("🔗 Clustering optimal zones...")
    clustered_zones, cluster_stats = cluster_optimal_zones(optimal_zones)
    
    print(f"✅ Generated {len(optimal_zones)} optimal zones in {len(cluster_stats)} clusters")
    
    return clustered_zones, cluster_stats

if __name__ == "__main__":
    zones, stats = generate_optimal_zones()
    print(f"Generated {len(zones)} optimal zones")
    print(f"Zone categories: {zones['zone_category'].value_counts().to_dict()}")
