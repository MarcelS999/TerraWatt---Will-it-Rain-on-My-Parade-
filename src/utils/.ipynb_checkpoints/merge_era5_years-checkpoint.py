# ============================================================
# 🚀 AI-ASSISTED CODE NOTICE
# This file was developed with assistance from OpenAI's ChatGPT (GPT-5)
# as part of the NASA Space Apps 2025 project:
# “TerraWatt — Will It Rain on My Parade?”
# ============================================================

"""
merge_era5_years.py
-------------------
Merges multiple yearly ERA5 Ireland NetCDF files (e.g., era5_ireland_wind_1994.nc, ...)
into one combined dataset (1994–2024), and computes:
  • 30-year mean wind speed climatology
  • 30-year standard deviation (interannual variability)
  • Monthly climatology (average per month)
  • Seasonal climatology (DJF, MAM, JJA, SON)

Outputs:
  - data/era5/era5_ireland_combined_1994_2024.nc
  - data/era5/era5_ireland_mean_1994_2024.tif
  - data/era5/era5_ireland_std_1994_2024.tif
  - data/era5/era5_ireland_monthly_means.csv
  - data/era5/era5_ireland_seasonal_means.csv
"""

import os
import xarray as xr
import numpy as np
import pandas as pd
import rioxarray

# ============================================================
# CONFIG
# ============================================================
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "era5")
OUT_COMBINED = os.path.join(DATA_DIR, "era5_ireland_combined_1994_2024.nc")
OUT_MEAN_TIF = os.path.join(DATA_DIR, "era5_ireland_mean_1994_2024.tif")
OUT_STD_TIF = os.path.join(DATA_DIR, "era5_ireland_std_1994_2024.tif")
OUT_MONTHLY_CSV = os.path.join(DATA_DIR, "era5_ireland_monthly_means.csv")
OUT_SEASONAL_CSV = os.path.join(DATA_DIR, "era5_ireland_seasonal_means.csv")

# ============================================================
# SCAN AND LOAD DATASETS
# ============================================================
print("📦 Scanning ERA5 NetCDF files...")
nc_files = sorted([
    os.path.join(DATA_DIR, f)
    for f in os.listdir(DATA_DIR)
    if f.endswith(".nc") and "wind_" in f
])

if not nc_files:
    raise FileNotFoundError("❌ No yearly ERA5 NetCDF files found in data/era5/")

print(f"📂 Found {len(nc_files)} yearly files:")
for f in nc_files:
    print("   •", os.path.basename(f))

# ============================================================
# MERGE ALL YEARS
# ============================================================
print("🔗 Merging yearly datasets...")
datasets = [xr.open_dataset(f) for f in nc_files]
ds_all = xr.concat(datasets, dim="time")
print(f"✅ Combined dataset shape: {ds_all.dims}")

# Detect data variable
varname = list(ds_all.data_vars.keys())[0]
print(f"📊 Using variable: {varname}")

# ============================================================
# COMPUTE LONG-TERM MEAN AND STD
# ============================================================
print("🧮 Computing 30-year mean and standard deviation...")

mean_wind = ds_all[varname].mean(dim="time", keep_attrs=True)
std_wind = ds_all[varname].std(dim="time", keep_attrs=True)

# ============================================================
# COMPUTE MONTHLY & SEASONAL CLIMATOLOGY
# ============================================================
print("📆 Computing monthly and seasonal climatologies...")

# Monthly climatology
monthly_clim = ds_all[varname].groupby("time.month").mean(dim="time")

# Convert to DataFrame
monthly_df = monthly_clim.mean(dim=["lat", "lon"]).to_dataframe(name="wind_speed_10m").reset_index()
monthly_df["month_name"] = pd.to_datetime(monthly_df["month"], format='%m').dt.strftime('%b')
monthly_df = monthly_df[["month", "month_name", "wind_speed_10m"]]
monthly_df.to_csv(OUT_MONTHLY_CSV, index=False)
print(f"✅ Saved monthly climatology → {OUT_MONTHLY_CSV}")

# Seasonal climatology
seasons = {
    "DJF": [12, 1, 2],
    "MAM": [3, 4, 5],
    "JJA": [6, 7, 8],
    "SON": [9, 10, 11],
}

seasonal_means = {}
for name, months in seasons.items():
    sel = ds_all[varname].where(ds_all["time.month"].isin(months), drop=True)
    seasonal_means[name] = sel.mean(dim="time")

seasonal_df = pd.DataFrame({
    "Season": list(seasonal_means.keys()),
    "MeanWind": [float(v.mean().values) for v in seasonal_means.values()]
})
seasonal_df.to_csv(OUT_SEASONAL_CSV, index=False)
print(f"✅ Saved seasonal climatology → {OUT_SEASONAL_CSV}")

# ============================================================
# SAVE MERGED DATA
# ============================================================
print("💾 Saving merged dataset and derived products...")

# Save combined NetCDF
ds_all.to_netcdf(OUT_COMBINED)

# Save GeoTIFFs
for da, path, label in [
    (mean_wind, OUT_MEAN_TIF, "mean wind"),
    (std_wind, OUT_STD_TIF, "wind variability (std)"),
]:
    da.rio.set_spatial_dims(x_dim="lon", y_dim="lat", inplace=True)
    da.rio.write_crs("EPSG:4326", inplace=True)
    da.rio.to_raster(path)
    print(f"✅ Saved {label} → {path}")

print("🎉 All done!")
print(f"👉 Outputs saved in: {DATA_DIR}")
print("   • Long-term mean & variability (GeoTIFF)")
print("   • Monthly & seasonal climatology (CSV)")
print("   • Full merged NetCDF (combined archive)")

