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
Enhanced ERA5 API data extraction with solar irradiance support.
Fetches both wind and solar data from ERA5 reanalysis dataset.
"""

import planetary_computer as pc
import pystac_client
import xarray as xr
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# CONFIGURATION
# ============================================================
COLLECTION = "era5-pds"
ERA5_KIND = "an"  # Analysis data
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "era5")

# Wind variables
WIND_VARS = [
    "eastward_wind_at_10_metres",
    "northward_wind_at_10_metres",
    "eastward_wind_at_100_metres", 
    "northward_wind_at_100_metres"
]

# Solar variables
SOLAR_VARS = [
    "surface_solar_radiation_downwards",
    "surface_net_solar_radiation",
    "total_sky_direct_solar_radiation_at_surface",
    "surface_solar_radiation_downward_clear_sky"
]

# Combined variables for comprehensive analysis
ALL_VARS = WIND_VARS + SOLAR_VARS

# ============================================================
# ENHANCED ERA5 DATA FETCHER
# ============================================================
def fetch_era5_data_with_solar(
    lat_min, lat_max, lon_min, lon_max, 
    start_date, end_date,
    variables=None,
    resolution=0.25,
    output_prefix="era5_combined",
    debug=False
):
    """
    Fetch ERA5 wind and solar data for specified region and time period.
    
    Parameters:
    -----------
    lat_min, lat_max : float
        Latitude bounds
    lon_min, lon_max : float  
        Longitude bounds
    start_date, end_date : str
        Date range in format "YYYY-MM-DD"
    variables : list, optional
        List of variables to fetch. If None, fetches all wind and solar variables.
    resolution : float, optional
        Grid resolution in degrees (default: 0.25)
    output_prefix : str, optional
        Prefix for output files
    debug : bool, optional
        Enable debug output
        
    Returns:
    --------
    dict : Dictionary containing processed data and file paths
    """
    
    if variables is None:
        variables = ALL_VARS
    
    print(f"🌍 Fetching ERA5 data for region: {lat_min:.2f}°N to {lat_max:.2f}°N, {lon_min:.2f}°E to {lon_max:.2f}°E")
    print(f"📅 Time period: {start_date} to {end_date}")
    print(f"🌬️ Wind variables: {len([v for v in variables if 'wind' in v])}")
    print(f"☀️ Solar variables: {len([v for v in variables if 'solar' in v or 'radiation' in v])}")
    
    # Connect to Planetary Computer STAC
    catalog = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1/")
    
    # Search for ERA5 data
    search = catalog.search(
        collections=[COLLECTION],
        datetime=f"{start_date}/{end_date}",
        query={"era5:kind": {"eq": ERA5_KIND}},
    )
    
    items = list(search.get_items())
    if not items:
        raise ValueError(f"No ERA5 dataset items found for {start_date} to {end_date}")
    
    print(f"📡 Found {len(items)} ERA5 items")
    
    # Sign items for access
    signed_items = [pc.sign(item) for item in items]
    
    # Process each item
    datasets = []
    for i, item in enumerate(signed_items):
        if debug:
            print(f"Processing item {i+1}/{len(signed_items)}")
        
        item_datasets = []
        for var in variables:
            if var in item.assets:
                asset = item.assets[var]
                try:
                    ds_var = xr.open_dataset(
                        asset.href, 
                        **asset.extra_fields.get("xarray:open_kwargs", {})
                    )
                    item_datasets.append(ds_var)
                    if debug:
                        print(f"  ✅ Loaded {var}")
                except Exception as e:
                    if debug:
                        print(f"  ❌ Failed to load {var}: {e}")
            else:
                if debug:
                    print(f"  ⚠️ Variable {var} not found in assets")
        
        if item_datasets:
            # Combine variables for this time step
            ds_item = xr.merge(item_datasets)
            datasets.append(ds_item)
    
    if not datasets:
        raise ValueError("No valid datasets could be loaded")
    
    # Combine all time steps
    print("🔄 Combining time steps...")
    ds_combined = xr.concat(datasets, dim="time")
    
    # Convert longitude bounds if needed
    if lon_min < 0:
        lon_min_era5 = 360 + lon_min
    else:
        lon_min_era5 = lon_min
        
    if lon_max < 0:
        lon_max_era5 = 360 + lon_max
    else:
        lon_max_era5 = lon_max
    
    # Clip to region
    print("✂️ Clipping to region...")
    lat_slice = slice(float(lat_max), float(lat_min))  # ERA5 is descending
    lon_slice = slice(float(lon_min_era5), float(lon_max_era5))
    
    ds_clipped = ds_combined.sel(
        lat=lat_slice, 
        lon=lon_slice, 
        time=slice(start_date, end_date)
    )
    
    if ds_clipped.dims.get("lat", 0) == 0 or ds_clipped.dims.get("lon", 0) == 0:
        raise ValueError("❌ Empty selection: Check if bbox intersects ERA5 grid")
    
    # Compute derived variables
    print("🧮 Computing derived variables...")
    
    # Wind speed at 10m and 100m
    if "eastward_wind_at_10_metres" in ds_clipped and "northward_wind_at_10_metres" in ds_clipped:
        ds_clipped["wind_speed_10m"] = np.sqrt(
            ds_clipped["eastward_wind_at_10_metres"]**2 + 
            ds_clipped["northward_wind_at_10_metres"]**2
        )
    
    if "eastward_wind_at_100_metres" in ds_clipped and "northward_wind_at_100_metres" in ds_clipped:
        ds_clipped["wind_speed_100m"] = np.sqrt(
            ds_clipped["eastward_wind_at_100_metres"]**2 + 
            ds_clipped["northward_wind_at_100_metres"]**2
        )
    
    # Solar irradiance calculations
    if "surface_solar_radiation_downwards" in ds_clipped:
        # Convert from J/m² to W/m² (assuming hourly data)
        ds_clipped["solar_irradiance"] = ds_clipped["surface_solar_radiation_downwards"] / 3600
        ds_clipped["solar_irradiance"] = ds_clipped["solar_irradiance"].where(
            ds_clipped["solar_irradiance"] > 0, 0
        )
    
    # Clear sky solar radiation
    if "surface_solar_radiation_downward_clear_sky" in ds_clipped:
        ds_clipped["clear_sky_solar"] = ds_clipped["surface_solar_radiation_downward_clear_sky"] / 3600
        ds_clipped["clear_sky_solar"] = ds_clipped["clear_sky_solar"].where(
            ds_clipped["clear_sky_solar"] > 0, 0
        )
    
    # Solar capacity factor (simplified)
    if "solar_irradiance" in ds_clipped:
        # Assume 20% efficiency for solar panels
        ds_clipped["solar_capacity_factor"] = (ds_clipped["solar_irradiance"] / 1000 * 0.20).clip(0, 1)
    
    # Resample to uniform grid if needed
    if resolution != 0.25:  # ERA5 native resolution
        print(f"📐 Resampling to {resolution}° resolution...")
        lat_vals = np.arange(
            float(ds_clipped.lat.min()), 
            float(ds_clipped.lat.max()) + resolution, 
            resolution
        )
        lon_vals = np.arange(
            float(ds_clipped.lon.min()), 
            float(ds_clipped.lon.max()) + resolution, 
            resolution
        )
        
        new_lat = xr.DataArray(lat_vals, dims="lat")
        new_lon = xr.DataArray(lon_vals, dims="lon")
        
        ds_clipped = ds_clipped.interp(lat=new_lat, lon=new_lon, method="linear")
    
    # Convert longitudes back to [-180, 180]
    if "lon" in ds_clipped.coords:
        ds_clipped = ds_clipped.assign_coords(
            lon=ds_clipped.lon.where(ds_clipped.lon <= 180, ds_clipped.lon - 360)
        )
    
    # Create output directory
    os.makedirs(OUT_DIR, exist_ok=True)
    
    # Save outputs
    output_files = {}
    
    # NetCDF file
    nc_path = os.path.join(OUT_DIR, f"{output_prefix}.nc")
    ds_clipped.to_netcdf(nc_path)
    output_files['netcdf'] = nc_path
    print(f"💾 Saved NetCDF: {nc_path}")
    
    # CSV files for each variable
    for var in ds_clipped.data_vars:
        if var in ['wind_speed_10m', 'wind_speed_100m', 'solar_irradiance', 'solar_capacity_factor']:
            # Convert to DataFrame
            df_var = ds_clipped[var].to_dataframe(name=var).reset_index()
            df_var = df_var.dropna(subset=[var])
            
            # Convert longitudes
            if "lon" in df_var.columns:
                df_var["lon"] = df_var["lon"].apply(lambda x: x - 360 if x > 180 else x)
            
            # Save CSV
            csv_path = os.path.join(OUT_DIR, f"{output_prefix}_{var}.csv")
            df_var.to_csv(csv_path, index=False)
            output_files[var] = csv_path
            print(f"💾 Saved {var}: {csv_path}")
    
    # Summary statistics
    summary = {}
    for var in ['wind_speed_10m', 'wind_speed_100m', 'solar_irradiance', 'solar_capacity_factor']:
        if var in ds_clipped.data_vars:
            var_data = ds_clipped[var]
            summary[var] = {
                'mean': float(var_data.mean()),
                'max': float(var_data.max()),
                'min': float(var_data.min()),
                'std': float(var_data.std())
            }
    
    return {
        'dataset': ds_clipped,
        'files': output_files,
        'summary': summary,
        'variables': list(ds_clipped.data_vars),
        'dimensions': dict(ds_clipped.dims)
    }

# ============================================================
# IRELAND-SPECIFIC FETCHER
# ============================================================
def fetch_ireland_solar_wind_data(
    start_date="2020-01-01", 
    end_date="2020-12-31",
    resolution=0.25,
    debug=False
):
    """
    Fetch wind and solar data for Ireland.
    
    Parameters:
    -----------
    start_date, end_date : str
        Date range
    resolution : float
        Grid resolution
    debug : bool
        Enable debug output
        
    Returns:
    --------
    dict : Processed data and file paths
    """
    
    # Ireland bounding box
    lat_min, lat_max = 51.0, 55.5
    lon_min, lon_max = -11.0, -5.0
    
    return fetch_era5_data_with_solar(
        lat_min=lat_min,
        lat_max=lat_max, 
        lon_min=lon_min,
        lon_max=lon_max,
        start_date=start_date,
        end_date=end_date,
        resolution=resolution,
        output_prefix="ireland_solar_wind",
        debug=debug
    )

# ============================================================
# UTILITY FUNCTIONS
# ============================================================
def create_solar_irradiance_map(data_dict, output_path=None):
    """
    Create a simple map visualization of solar irradiance data.
    """
    try:
        import folium
        from folium import plugins
        
        # Get solar irradiance data
        if 'solar_irradiance' in data_dict['files']:
            df = pd.read_csv(data_dict['files']['solar_irradiance'])
        else:
            raise ValueError("Solar irradiance data not found")
        
        # Create map
        m = folium.Map(location=[53.5, -8], zoom_start=7)
        
        # Add solar irradiance heatmap
        heat_data = [[row['lat'], row['lon'], row['solar_irradiance']] 
                    for _, row in df.iterrows() if not pd.isna(row['solar_irradiance'])]
        
        plugins.HeatMap(
            heat_data,
            name="Solar Irradiance (W/m²)",
            radius=20,
            gradient={0.0: 'blue', 0.5: 'yellow', 1.0: 'red'}
        ).add_to(m)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        if output_path:
            m.save(output_path)
            print(f"🗺️ Solar map saved: {output_path}")
        
        return m
        
    except ImportError:
        print("⚠️ Folium not available for map creation")
        return None

# ============================================================
# EXAMPLE USAGE
# ============================================================
if __name__ == "__main__":
    print("🌍 ERA5 Solar & Wind Data Fetcher")
    print("=" * 50)
    
    # Example: Fetch Ireland data for 2020
    try:
        result = fetch_ireland_solar_wind_data(
            start_date="2020-01-01",
            end_date="2020-12-31", 
            debug=True
        )
        
        print("\n📊 Summary Statistics:")
        for var, stats in result['summary'].items():
            print(f"  {var}:")
            print(f"    Mean: {stats['mean']:.2f}")
            print(f"    Range: {stats['min']:.2f} - {stats['max']:.2f}")
            print(f"    Std: {stats['std']:.2f}")
        
        print(f"\n📁 Output files:")
        for var, path in result['files'].items():
            print(f"  {var}: {path}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
