"""
create_era5_variability_and_rose.py
-----------------------------------
Computes wind-speed variability (standard deviation)
and wind-direction roses for Ireland using ERA5 reanalysis.

Input:
  - Existing yearly NetCDF files in data/era5/ (e.g. era5_ireland_wind_2010.nc)
Output:
  - era5_ireland_std_wind_1994_2020.tif  (spatial variability)
  - era5_ireland_std_wind_1994_2020.nc
  - era5_ireland_wind_rose_1994_2020.csv (wind direction frequency)
"""

import os
import numpy as np
import pandas as pd
import xarray as xr
import rioxarray

# ============================================================
# CONFIG
# ============================================================
OUT_DIR = os.path.join("data", "era5")
os.makedirs(OUT_DIR, exist_ok=True)

START_YEAR, END_YEAR = 1994, 2020
YEARS = range(START_YEAR, END_YEAR + 1)

print(f"📊 Computing ERA5 variability and direction roses ({START_YEAR}–{END_YEAR})...")

# ============================================================
# LOAD ALL YEARLY FILES
# ============================================================
datasets = []
for yr in YEARS:
    nc_path = os.path.join(OUT_DIR, f"era5_ireland_wind_{yr}.nc")
    if not os.path.exists(nc_path):
        print(f"⚠️ Skipping {yr} — file not found.")
        continue

    print(f"📥 Loading {nc_path}")
    ds = xr.open_dataset(nc_path)
    datasets.append(ds)

if not datasets:
    raise RuntimeError("❌ No yearly NetCDF files found. Run create_era5_ireland_climatology.py first.")

# Combine into one dataset
ds_all = xr.concat(datasets, dim="time")

# ============================================================
# COMPUTE WIND SPEED AND DIRECTION
# ============================================================
u = ds_all["eastward_wind_at_10_metres"]
v = ds_all["northward_wind_at_10_metres"]

# Magnitude (speed)
wspd = np.sqrt(u**2 + v**2)

# Direction (in degrees, meteorological convention: 0° = North)
wdir = (180 + np.degrees(np.arctan2(u, v))) % 360

# ============================================================
# CLIMATOLOGY STATISTICS
# ============================================================
print("🧮 Computing spatial std and mean...")
wspd_std = wspd.std(dim="time")
wspd_mean = wspd.mean(dim="time")

# ============================================================
# WIND ROSE DATA (per 10° sector, averaged spatially)
# ============================================================
print("🌪 Computing wind direction frequency distribution...")
dir_bins = np.arange(0, 360, 10)
wdir_flat = wdir.values.flatten()
wdir_flat = wdir_flat[~np.isnan(wdir_flat)]

rose_counts, _ = np.histogram(wdir_flat, bins=dir_bins)
rose_freq = 100 * rose_counts / rose_counts.sum()

df_rose = pd.DataFrame({
    "direction_deg": dir_bins[:-1],
    "frequency_percent": rose_freq.round(2)
})

# ============================================================
# SAVE OUTPUTS
# ============================================================
std_tif_path = os.path.join(OUT_DIR, f"era5_ireland_std_wind_{START_YEAR}_{END_YEAR}.tif")
std_nc_path  = os.path.join(OUT_DIR, f"era5_ireland_std_wind_{START_YEAR}_{END_YEAR}.nc")
rose_csv_path = os.path.join(OUT_DIR, f"era5_ireland_wind_rose_{START_YEAR}_{END_YEAR}.csv")

# GeoTIFF
print("💾 Saving variability (std) maps...")
wspd_std.rio.set_spatial_dims(x_dim="longitude", y_dim="latitude", inplace=True)
wspd_std.rio.write_crs("EPSG:4326", inplace=True)
wspd_std.rio.to_raster(std_tif_path)

# NetCDF
wspd_std.to_netcdf(std_nc_path)

# Wind rose CSV
df_rose.to_csv(rose_csv_path, index=False)

print(f"✅ Saved ERA5 Std GeoTIFF → {std_tif_path}")
print(f"✅ Saved ERA5 Std NetCDF → {std_nc_path}")
print(f"✅ Saved Wind Rose CSV → {rose_csv_path}")
print("🎉 Done!")
