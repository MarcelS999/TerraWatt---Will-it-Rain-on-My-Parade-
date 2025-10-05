#!/usr/bin/env python3
"""
Analyze ERA5 wind data structure and content.

AI USE DECLARATION:
This file was developed with significant assistance from AI tools:
1. Cursor AI (https://cursor.sh/) - Primary development environment
2. ChatGPT (OpenAI - https://openai.com/chatgpt) - Conversational AI assistance

Project: TerraWatt — Will It Rain on My Parade?
Challenge: NASA Space Apps 2025
"""

import os
import pandas as pd

def analyze_era5_data():
    """Analyze ERA5 data files."""
    print("=== ERA5 Data Analysis ===")
    
    # Check file sizes
    print("\n1. File Sizes:")
    era5_dir = "data/era5"
    for file in os.listdir(era5_dir):
        if file.endswith(('.nc', '.csv', '.tif')):
            size = os.path.getsize(f'{era5_dir}/{file}') / (1024*1024)
            print(f"  {file}: {size:.1f} MB")
    
    # Analyze CSV data
    print("\n2. Main Wind Data (CSV):")
    df = pd.read_csv(f'{era5_dir}/era5_ireland_mean_wind_1994_2024.csv')
    print(f"  Shape: {df.shape}")
    print(f"  Columns: {df.columns.tolist()}")
    print(f"  Latitude range: {df.latitude.min():.2f} to {df.latitude.max():.2f}")
    print(f"  Longitude range: {df.longitude.min():.2f} to {df.longitude.max():.2f}")
    print(f"  Wind speed range: {df.wind_speed_10m.min():.2f} to {df.wind_speed_10m.max():.2f} m/s")
    print(f"  Unique latitudes: {df.latitude.nunique()}")
    print(f"  Unique longitudes: {df.longitude.nunique()}")
    
    # Sample data
    print("\n  Sample data:")
    print(df.head(3).to_string(index=False))
    
    # Monthly data
    print("\n3. Monthly Means:")
    df_monthly = pd.read_csv(f'{era5_dir}/era5_ireland_monthly_means.csv')
    print(f"  Shape: {df_monthly.shape}")
    print(f"  Columns: {df_monthly.columns.tolist()}")
    print("\n  Monthly wind speeds:")
    print(df_monthly.to_string(index=False))
    
    # Seasonal data
    print("\n4. Seasonal Means:")
    df_seasonal = pd.read_csv(f'{era5_dir}/era5_ireland_seasonal_means.csv')
    print(f"  Shape: {df_seasonal.shape}")
    print(f"  Columns: {df_seasonal.columns.tolist()}")
    print("\n  Seasonal wind speeds:")
    print(df_seasonal.to_string(index=False))
    
    # 2020 daily data
    print("\n5. 2020 Daily Data:")
    if os.path.exists(f'{era5_dir}/era5_ie_2020_daily_mean.csv'):
        df_2020 = pd.read_csv(f'{era5_dir}/era5_ie_2020_daily_mean.csv')
        print(f"  Shape: {df_2020.shape}")
        print(f"  Columns: {df_2020.columns.tolist()}")
        print(f"  Date range: {df_2020.iloc[0, 0]} to {df_2020.iloc[-1, 0]}")
    else:
        print("  File not found")
    
    # NetCDF files
    print("\n6. NetCDF Files:")
    nc_files = [f for f in os.listdir(era5_dir) if f.endswith('.nc')]
    print(f"  Found {len(nc_files)} NetCDF files")
    print("  Files:")
    for file in sorted(nc_files):
        size = os.path.getsize(f'{era5_dir}/{file}') / (1024*1024)
        print(f"    {file}: {size:.1f} MB")
    
    # GeoTIFF files
    print("\n7. GeoTIFF Files:")
    tif_files = [f for f in os.listdir(era5_dir) if f.endswith('.tif')]
    print(f"  Found {len(tif_files)} GeoTIFF files")
    for file in sorted(tif_files):
        size = os.path.getsize(f'{era5_dir}/{file}') / (1024*1024)
        print(f"    {file}: {size:.1f} MB")
    
    print("\n=== Analysis Complete ===")

if __name__ == "__main__":
    analyze_era5_data()
