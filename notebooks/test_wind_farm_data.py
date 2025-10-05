#!/usr/bin/env python3
"""
Test script to examine wind farm data structure and test extraction functions.

AI USE DECLARATION:
This file was developed with significant assistance from AI tools:
1. Cursor AI (https://cursor.sh/) - Primary development environment
2. ChatGPT (OpenAI - https://openai.com/chatgpt) - Conversational AI assistance

Project: TerraWatt — Will It Rain on My Parade?
Challenge: NASA Space Apps 2025
"""

import os
import sys
import pandas as pd

# Add src to path (from notebooks folder)
sys.path.append('../src')

def test_wind_farm_data():
    """Test wind farm data loading and field extraction."""
    print("Testing wind farm data structure...")
    
    try:
        import geopandas as gpd
        
        # Load wind farm data
        wind_path = "../data/wind_farms/Wind Farms June 2022_ESPG3857.shp"
        
        if not os.path.exists(wind_path):
            print(f"Wind farm data not found at: {wind_path}")
            return False
        
        print(f"Loading wind farm data from: {wind_path}")
        wind_farms = gpd.read_file(wind_path)
        
        print(f"Data shape: {wind_farms.shape}")
        print(f"Columns: {wind_farms.columns.tolist()}")
        
        # Show sample data
        print("\nSample data (first 3 rows):")
        for i, (idx, row) in enumerate(wind_farms.head(3).iterrows()):
            print(f"\n--- Row {i+1} ---")
            for col in wind_farms.columns:
                if col != 'geometry':
                    value = row[col]
                    if pd.notna(value):
                        print(f"  {col}: {value}")
        
        # Test extraction functions
        print("\nTesting extraction functions...")
        
        from src.visualization.optimal_zones_viz import extract_wind_farm_name, extract_wind_farm_capacity, create_wind_farm_popup
        
        for i, (idx, row) in enumerate(wind_farms.head(3).iterrows()):
            print(f"\n--- Testing Row {i+1} ---")
            
            # Test name extraction
            name = extract_wind_farm_name(row)
            print(f"  Extracted name: {name}")
            
            # Test capacity extraction
            capacity = extract_wind_farm_capacity(row)
            print(f"  Extracted capacity: {capacity}")
            
            # Test popup creation
            popup_html = create_wind_farm_popup(name, capacity, row)
            print(f"  Popup HTML length: {len(popup_html)} characters")
            print(f"  Popup preview: {popup_html[:200]}...")
        
        print("\nWind farm data test completed successfully!")
        return True
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Try installing geopandas: pip install geopandas")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = test_wind_farm_data()
    if success:
        print("\nAll tests passed!")
    else:
        print("\nTests failed!")
        sys.exit(1)
