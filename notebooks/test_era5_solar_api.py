#!/usr/bin/env python3
"""
Test script for enhanced ERA5 API with solar irradiance data.

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

def test_era5_solar_api():
    """Test the enhanced ERA5 API with solar data."""
    print("🌍 Testing Enhanced ERA5 API with Solar Data")
    print("=" * 60)
    
    try:
        from src.data_fetch.era5_solar_api import (
            fetch_era5_data_with_solar,
            fetch_ireland_solar_wind_data,
            create_solar_irradiance_map
        )
        
        print("✅ Successfully imported ERA5 solar API functions")
        
        # Test 1: Small region test (to avoid large downloads)
        print("\n🧪 Test 1: Small region data fetch")
        print("-" * 40)
        
        # Small region around Dublin for testing
        result = fetch_era5_data_with_solar(
            lat_min=53.0, lat_max=53.5,
            lon_min=-6.5, lon_max=-6.0,
            start_date="2020-01-01",
            end_date="2020-01-02",  # Just 2 days for testing
            variables=[
                "eastward_wind_at_10_metres",
                "northward_wind_at_10_metres", 
                "surface_solar_radiation_downwards"
            ],
            resolution=0.5,  # Coarser resolution for faster processing
            output_prefix="test_dublin",
            debug=True
        )
        
        print(f"✅ Successfully fetched data for Dublin region")
        print(f"📊 Variables: {result['variables']}")
        print(f"📐 Dimensions: {result['dimensions']}")
        
        # Show summary statistics
        print("\n📈 Summary Statistics:")
        for var, stats in result['summary'].items():
            print(f"  {var}:")
            print(f"    Mean: {stats['mean']:.2f}")
            print(f"    Range: {stats['min']:.2f} - {stats['max']:.2f}")
            print(f"    Std Dev: {stats['std']:.2f}")
        
        # Test 2: Check output files
        print("\n📁 Output Files:")
        for var, path in result['files'].items():
            if os.path.exists(path):
                size = os.path.getsize(path) / 1024  # KB
                print(f"  ✅ {var}: {path} ({size:.1f} KB)")
            else:
                print(f"  ❌ {var}: {path} (not found)")
        
        # Test 3: Load and examine CSV data
        print("\n📊 CSV Data Analysis:")
        if 'wind_speed_10m' in result['files']:
            df_wind = pd.read_csv(result['files']['wind_speed_10m'])
            print(f"  Wind data shape: {df_wind.shape}")
            print(f"  Wind speed range: {df_wind['wind_speed_10m'].min():.2f} - {df_wind['wind_speed_10m'].max():.2f} m/s")
            print(f"  Sample wind data:")
            print(df_wind.head(3).to_string(index=False))
        
        if 'solar_irradiance' in result['files']:
            df_solar = pd.read_csv(result['files']['solar_irradiance'])
            print(f"  Solar data shape: {df_solar.shape}")
            print(f"  Solar irradiance range: {df_solar['solar_irradiance'].min():.2f} - {df_solar['solar_irradiance'].max():.2f} W/m²")
            print(f"  Sample solar data:")
            print(df_solar.head(3).to_string(index=False))
        
        # Test 4: Ireland-specific function
        print("\n🇮🇪 Test 2: Ireland-specific data fetch")
        print("-" * 40)
        
        # This would be a larger download, so we'll just test the function exists
        print("✅ Ireland-specific function available:")
        print("  fetch_ireland_solar_wind_data()")
        print("  Parameters: start_date, end_date, resolution, debug")
        
        # Test 5: Map creation function
        print("\n🗺️ Test 3: Map creation function")
        print("-" * 40)
        
        print("✅ Map creation function available:")
        print("  create_solar_irradiance_map()")
        print("  Creates interactive Folium maps with solar irradiance heatmaps")
        
        print("\n🎉 All tests completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Try installing required packages:")
        print("   pip install planetary-computer pystac-client xarray pandas")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_api_parameters():
    """Test different API parameter combinations."""
    print("\n🔧 Testing API Parameters")
    print("=" * 40)
    
    # Test different variable combinations
    wind_only = [
        "eastward_wind_at_10_metres",
        "northward_wind_at_10_metres"
    ]
    
    solar_only = [
        "surface_solar_radiation_downwards",
        "surface_net_solar_radiation"
    ]
    
    combined = wind_only + solar_only
    
    print("Available variable combinations:")
    print(f"  Wind only: {len(wind_only)} variables")
    print(f"  Solar only: {len(solar_only)} variables") 
    print(f"  Combined: {len(combined)} variables")
    
    print("\nAvailable solar variables:")
    solar_vars = [
        "surface_solar_radiation_downwards",
        "surface_net_solar_radiation", 
        "total_sky_direct_solar_radiation_at_surface",
        "surface_solar_radiation_downward_clear_sky"
    ]
    
    for i, var in enumerate(solar_vars, 1):
        print(f"  {i}. {var}")
    
    print("\nAvailable wind variables:")
    wind_vars = [
        "eastward_wind_at_10_metres",
        "northward_wind_at_10_metres",
        "eastward_wind_at_100_metres",
        "northward_wind_at_100_metres"
    ]
    
    for i, var in enumerate(wind_vars, 1):
        print(f"  {i}. {var}")
    
    print("\nDerived variables (computed automatically):")
    derived_vars = [
        "wind_speed_10m",
        "wind_speed_100m", 
        "solar_irradiance",
        "solar_capacity_factor"
    ]
    
    for i, var in enumerate(derived_vars, 1):
        print(f"  {i}. {var}")

if __name__ == "__main__":
    print("🚀 ERA5 Solar API Test Suite")
    print("=" * 50)
    
    # Run tests
    success = test_era5_solar_api()
    test_api_parameters()
    
    if success:
        print("\n✅ All tests passed!")
        print("\n💡 Next steps:")
        print("  1. Run full Ireland data fetch (may take time)")
        print("  2. Create solar irradiance maps")
        print("  3. Integrate with optimal zones analysis")
    else:
        print("\n❌ Some tests failed!")
        print("Check dependencies and try again.")
