#!/usr/bin/env python3
"""
Simple script to examine wind farm data structure without geopandas.

AI USE DECLARATION:
This file was developed with significant assistance from AI tools:
1. Cursor AI (https://cursor.sh/) - Primary development environment
2. ChatGPT (OpenAI - https://openai.com/chatgpt) - Conversational AI assistance

Project: TerraWatt — Will It Rain on My Parade?
Challenge: NASA Space Apps 2025
"""

import os
import sys

def examine_wind_farm_data():
    """Examine wind farm data structure using basic file operations."""
    print("Examining wind farm data structure...")
    
    # Check if files exist
    wind_dir = "../data/wind_farms"
    if not os.path.exists(wind_dir):
        print(f"Wind farm directory not found: {wind_dir}")
        return False
    
    print(f"Wind farm directory contents:")
    for file in os.listdir(wind_dir):
        print(f"  {file}")
    
    # Try to read the DBF file directly (contains attribute data)
    dbf_path = os.path.join(wind_dir, "Wind Farms June 2022_ESPG3857.dbf")
    if os.path.exists(dbf_path):
        print(f"\nDBF file found: {dbf_path}")
        print("DBF files contain attribute data for shapefiles")
        print("This would contain fields like Name, Capacity, etc.")
    else:
        print(f"DBF file not found: {dbf_path}")
    
    # Check if we can use a different approach
    try:
        import pandas as pd
        print("\nTrying to read with pandas...")
        # This might work for some DBF files
        try:
            df = pd.read_csv(dbf_path.replace('.dbf', '.csv'))
            print(f"CSV version found with columns: {df.columns.tolist()}")
        except:
            print("No CSV version found")
    except ImportError:
        print("Pandas not available")
    
    return True

if __name__ == "__main__":
    examine_wind_farm_data()
