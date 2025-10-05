#!/usr/bin/env python3
"""
Test script to create a simple map with wind farm tooltips.

AI USE DECLARATION:
This file was developed with significant assistance from AI tools:
1. Cursor AI (https://cursor.sh/) - Primary development environment
2. ChatGPT (OpenAI - https://openai.com/chatgpt) - Conversational AI assistance

Project: TerraWatt — Will It Rain on My Parade?
Challenge: NASA Space Apps 2025
"""

import os
import sys

# Add src to path (from notebooks folder)
sys.path.append('../src')

def create_test_map():
    """Create a test map with wind farm tooltips."""
    print("Creating test map with wind farm tooltips...")
    
    try:
        import folium
        from streamlit_folium import st_folium
        import geopandas as gpd
        import pandas as pd
        
        # Create a simple map
        m = folium.Map(location=[53.5, -8], zoom_start=7, tiles="CartoDB positron")
        
        # Load wind farm data
        wind_path = "../data/wind_farms/Wind Farms June 2022_ESPG3857.shp"
        
        if not os.path.exists(wind_path):
            print(f"Wind farm data not found: {wind_path}")
            return False
        
        print(f"Loading wind farm data from: {wind_path}")
        wind_farms = gpd.read_file(wind_path).to_crs("EPSG:4326")
        
        print(f"Loaded {len(wind_farms)} wind farms")
        print(f"Columns: {wind_farms.columns.tolist()}")
        
        # Import our extraction functions
        from src.visualization.optimal_zones_viz import (
            extract_wind_farm_name, 
            extract_wind_farm_capacity, 
            create_wind_farm_popup
        )
        
        # Add wind farms to map
        for i, (idx, row) in enumerate(wind_farms.head(10).iterrows()):  # Limit to first 10 for testing
            if row.geometry and not row.geometry.is_empty:
                # Get coordinates
                if row.geometry.geom_type == "Point":
                    coords = [row.geometry.y, row.geometry.x]
                else:
                    coords = [row.geometry.centroid.y, row.geometry.centroid.x]
                
                # Extract information
                name = extract_wind_farm_name(row)
                capacity = extract_wind_farm_capacity(row)
                
                print(f"Wind Farm {i+1}: {name} (Capacity: {capacity} MW)")
                
                # Create popup
                popup_html = create_wind_farm_popup(name, capacity, row)
                
                # Add marker
                folium.CircleMarker(
                    location=coords,
                    radius=6,
                    color="#009E73",
                    fill=True,
                    fillOpacity=0.8,
                    popup=folium.Popup(popup_html, max_width=300)
                ).add_to(m)
        
        # Save map
        map_path = "test_wind_farm_map.html"
        m.save(map_path)
        print(f"Test map saved to: {map_path}")
        
        return True
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Try installing required packages: pip install folium geopandas streamlit")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = create_test_map()
    if success:
        print("Test map created successfully!")
    else:
        print("Failed to create test map!")
        sys.exit(1)
