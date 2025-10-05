#!/usr/bin/env python3
"""
Example script demonstrating solar and wind data analysis using enhanced ERA5 API.

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
import numpy as np

# Add src to path (from notebooks folder)
sys.path.append('../src')

def analyze_solar_wind_resources():
    """Comprehensive solar and wind resource analysis."""
    print("🌍 Solar & Wind Resource Analysis")
    print("=" * 50)
    
    try:
        from src.data_fetch.era5_solar_api import (
            fetch_era5_data_with_solar,
            fetch_ireland_solar_wind_data,
            create_solar_irradiance_map
        )
        
        # Example 1: Small region analysis (Dublin area)
        print("\n📍 Example 1: Dublin Region Analysis")
        print("-" * 40)
        
        dublin_result = fetch_era5_data_with_solar(
            lat_min=53.0, lat_max=53.5,
            lon_min=-6.5, lon_max=-6.0,
            start_date="2020-06-01",  # Summer month for solar
            end_date="2020-06-30",
            variables=[
                "eastward_wind_at_10_metres",
                "northward_wind_at_10_metres",
                "surface_solar_radiation_downwards"
            ],
            resolution=0.25,
            output_prefix="dublin_june_2020",
            debug=True
        )
        
        print("✅ Dublin data fetched successfully")
        
        # Analyze the data
        if 'wind_speed_10m' in dublin_result['files']:
            df_wind = pd.read_csv(dublin_result['files']['wind_speed_10m'])
            print(f"\n🌬️ Wind Analysis (Dublin, June 2020):")
            print(f"  Average wind speed: {df_wind['wind_speed_10m'].mean():.2f} m/s")
            print(f"  Max wind speed: {df_wind['wind_speed_10m'].max():.2f} m/s")
            print(f"  Wind speed std: {df_wind['wind_speed_10m'].std():.2f} m/s")
        
        if 'solar_irradiance' in dublin_result['files']:
            df_solar = pd.read_csv(dublin_result['files']['solar_irradiance'])
            print(f"\n☀️ Solar Analysis (Dublin, June 2020):")
            print(f"  Average irradiance: {df_solar['solar_irradiance'].mean():.2f} W/m²")
            print(f"  Max irradiance: {df_solar['solar_irradiance'].max():.2f} W/m²")
            print(f"  Solar capacity factor: {df_solar['solar_capacity_factor'].mean():.3f}")
        
        # Example 2: Seasonal analysis
        print("\n📅 Example 2: Seasonal Analysis")
        print("-" * 40)
        
        seasons = {
            'Winter': '2020-01-01',
            'Spring': '2020-04-01', 
            'Summer': '2020-07-01',
            'Autumn': '2020-10-01'
        }
        
        seasonal_data = {}
        
        for season, start_date in seasons.items():
            print(f"  Fetching {season} data...")
            
            # Small region for seasonal analysis
            season_result = fetch_era5_data_with_solar(
                lat_min=53.0, lat_max=53.5,
                lon_min=-6.5, lon_max=-6.0,
                start_date=start_date,
                end_date=start_date,  # Single day for each season
                variables=["surface_solar_radiation_downwards"],
                resolution=0.5,
                output_prefix=f"seasonal_{season.lower()}",
                debug=False
            )
            
            if 'solar_irradiance' in season_result['files']:
                df_season = pd.read_csv(season_result['files']['solar_irradiance'])
                avg_irradiance = df_season['solar_irradiance'].mean()
                seasonal_data[season] = avg_irradiance
                print(f"    {season} average irradiance: {avg_irradiance:.2f} W/m²")
        
        # Plot seasonal variation
        print(f"\n📊 Seasonal Solar Irradiance Variation:")
        for season, irradiance in seasonal_data.items():
            print(f"  {season}: {irradiance:.2f} W/m²")
        
        # Example 3: Wind vs Solar correlation
        print("\n🔗 Example 3: Wind-Solar Correlation Analysis")
        print("-" * 40)
        
        if 'wind_speed_10m' in dublin_result['files'] and 'solar_irradiance' in dublin_result['files']:
            df_wind = pd.read_csv(dublin_result['files']['wind_speed_10m'])
            df_solar = pd.read_csv(dublin_result['files']['solar_irradiance'])
            
            # Merge data by coordinates
            df_combined = pd.merge(
                df_wind[['lat', 'lon', 'wind_speed_10m']], 
                df_solar[['lat', 'lon', 'solar_irradiance']],
                on=['lat', 'lon']
            )
            
            correlation = df_combined['wind_speed_10m'].corr(df_combined['solar_irradiance'])
            print(f"  Wind-Solar correlation: {correlation:.3f}")
            
            if correlation < -0.3:
                print("  📈 Strong negative correlation: High wind when low solar")
            elif correlation > 0.3:
                print("  📉 Strong positive correlation: High wind with high solar")
            else:
                print("  📊 Weak correlation: Independent wind and solar patterns")
        
        # Example 4: Renewable energy potential assessment
        print("\n⚡ Example 4: Renewable Energy Potential")
        print("-" * 40)
        
        if 'wind_speed_10m' in dublin_result['files'] and 'solar_irradiance' in dublin_result['files']:
            df_wind = pd.read_csv(dublin_result['files']['wind_speed_10m'])
            df_solar = pd.read_csv(dublin_result['files']['solar_irradiance'])
            
            # Wind potential assessment
            avg_wind = df_wind['wind_speed_10m'].mean()
            if avg_wind > 7.0:
                wind_potential = "Excellent"
            elif avg_wind > 5.0:
                wind_potential = "Good"
            elif avg_wind > 3.0:
                wind_potential = "Moderate"
            else:
                wind_potential = "Poor"
            
            # Solar potential assessment
            avg_solar = df_solar['solar_irradiance'].mean()
            if avg_solar > 200:
                solar_potential = "Excellent"
            elif avg_solar > 150:
                solar_potential = "Good"
            elif avg_solar > 100:
                solar_potential = "Moderate"
            else:
                solar_potential = "Poor"
            
            print(f"  Wind potential: {wind_potential} ({avg_wind:.2f} m/s)")
            print(f"  Solar potential: {solar_potential} ({avg_solar:.2f} W/m²)")
            
            # Combined assessment
            if wind_potential in ["Excellent", "Good"] and solar_potential in ["Excellent", "Good"]:
                combined_potential = "Excellent for hybrid systems"
            elif wind_potential in ["Excellent", "Good"] or solar_potential in ["Excellent", "Good"]:
                combined_potential = "Good for single technology"
            else:
                combined_potential = "Limited renewable potential"
            
            print(f"  Combined potential: {combined_potential}")
        
        print("\n✅ Analysis completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Install required packages:")
        print("   pip install planetary-computer pystac-client xarray pandas")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def create_visualization_examples():
    """Create example visualizations."""
    print("\n🗺️ Visualization Examples")
    print("=" * 30)
    
    try:
        from src.data_fetch.era5_solar_api import create_solar_irradiance_map
        
        print("✅ Solar irradiance map function available")
        print("  Usage: create_solar_irradiance_map(data_dict, output_path)")
        print("  Creates interactive Folium maps with solar irradiance heatmaps")
        
        # Example of how to use the visualization function
        print("\n📝 Example usage:")
        print("""
        # After fetching data with fetch_era5_data_with_solar()
        result = fetch_era5_data_with_solar(...)
        
        # Create solar irradiance map
        map_obj = create_solar_irradiance_map(
            result, 
            output_path="solar_irradiance_map.html"
        )
        """)
        
        return True
        
    except ImportError:
        print("⚠️ Visualization functions require additional packages")
        return False

if __name__ == "__main__":
    print("🚀 Solar & Wind Resource Analysis Example")
    print("=" * 60)
    
    # Run analysis
    success = analyze_solar_wind_resources()
    
    # Show visualization options
    create_visualization_examples()
    
    if success:
        print("\n🎉 Example analysis completed!")
        print("\n💡 Next steps:")
        print("  1. Run full Ireland analysis")
        print("  2. Create interactive maps")
        print("  3. Integrate with optimal zones calculation")
        print("  4. Add solar capacity factor to scoring")
    else:
        print("\n❌ Analysis failed!")
        print("Check dependencies and try again.")
