"""
create_era5_ireland_climatology.py
----------------------------------
Downloads ERA5 reanalysis data (10 m winds) for Ireland (1994–2024)
and computes a long-term mean wind-speed climatology map.
Skips years already processed.
Outputs: GeoTIFF + CSV + NetCDF.
"""

import os
import numpy as np
import pandas as pd
import xarray as xr
import planetary_computer
import pystac_client
import rioxarray

# ============================================================
# CONFIG
# ============================================================
OUT_DIR = os.path.join("data", "era5")
os.makedirs(OUT_DIR, exist_ok=True)

YEARS = range(1994, 2020)
LAT_MIN, LAT_MAX = 51.4, 55.5
LON_MIN, LON_MAX = -11.0, -5.3
COLLECTION = "era5-pds"
ERA5_KIND = "an"  # analysis
VARS = [
    "eastward_wind_at_10_metres",
    "northward_wind_at_10_metres"
]

print("📡 Starting ERA5-PDS climatology fetch for Ireland (1994–2024)...")

# ============================================================
# HELPER: Fetch single year
# ============================================================
def fetch_year(year: int):
    """Fetch u10/v10 data for one year and return daily mean wind speed."""
    catalog = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1/")
    search = catalog.search(
        collections=[COLLECTION],
        datetime=f"{year}-01-01/{year}-12-31",
        query={"era5:kind": {"eq": ERA5_KIND}},
    )
    items = list(search.get_all_items())  # ✅ ensures full list of items

    if len(items) == 0:
        print(f"⚠️ No ERA5 data found for {year}")
        return None

    print(f"📥 {len(items)} ERA5 items found for {year} — loading...")
    signed_items = [planetary_computer.sign(i) for i in items]

    yearly = []
    for item in signed_items:
        datasets = []
        for var in VARS:
            if var in item.assets:
                asset = item.assets[var]
                ds_var = xr.open_dataset(asset.href, **asset.extra_fields.get("xarray:open_kwargs", {}))
                datasets.append(ds_var)
            else:
                # Some assets may use alternative variable names
                alt_keys = [k for k in item.assets.keys() if "10" in k and "wind" in k]
                for alt in alt_keys:
                    asset = item.assets[alt]
                    ds_var = xr.open_dataset(asset.href, **asset.extra_fields.get("xarray:open_kwargs", {}))
                    datasets.append(ds_var)
        if datasets:
            ds = xr.combine_by_coords(datasets, join="override")
            yearly.append(ds)

    if not yearly:
        print(f"⚠️ No valid datasets for {year}")
        return None

    ds_year = xr.concat(yearly, dim="time")

    # Handle coordinate naming
    lat_name = "lat" if "lat" in ds_year.dims else "latitude"
    lon_name = "lon" if "lon" in ds_year.dims else "longitude"

    # Subset region (Ireland)
    ds_clip = ds_year.sel(
        {lat_name: slice(LAT_MAX, LAT_MIN),
         lon_name: slice(LON_MIN % 360, LON_MAX % 360)}
    )

    # Compute wind speed magnitude
    wspd = np.sqrt(
        ds_clip["eastward_wind_at_10_metres"] ** 2 +
        ds_clip["northward_wind_at_10_metres"] ** 2
    )

    # Ensure time index is monotonic
    wspd = wspd.sortby("time")

    # Convert to daily mean
    wspd_daily = wspd.resample(time="1D").mean()
    return wspd_daily




# ============================================================
# MAIN LOOP
# ============================================================
all_years = []
for yr in YEARS:
    yearly_nc = os.path.join(OUT_DIR, f"era5_ireland_wind_{yr}.nc")

    if os.path.exists(yearly_nc):
        print(f"⏩ Skipping {yr} — already downloaded.")
        ds_y = xr.open_dataset(yearly_nc)
        all_years.append(ds_y)
        continue

    try:
        print(f"📡 Fetching ERA5 {yr}...")
        ds_y = fetch_year(yr)
        if ds_y is not None:
            ds_y.to_netcdf(yearly_nc)
            print(f"✅ Saved → {yearly_nc}")
            all_years.append(ds_y)
    except Exception as e:
        print(f"❌ Failed for {yr}: {e}")

if not all_years:
    raise RuntimeError("❌ No ERA5 data retrieved.")

# ============================================================
# LONG-TERM MEAN
# ============================================================
# Convert to DataFrame preserving spatial grid
df_map = ds_mean.to_dataframe(name="wind_speed_10m").reset_index()
df_map = df_map.dropna(subset=["wind_speed_10m"])

# Save CSV for heatmap layer
df_map.to_csv(csv_path, index=False)

# Also save area-mean (for trend plots)
df_mean = ds_mean.mean(dim=["latitude", "longitude"]).to_dataframe(name="mean_wind_speed").reset_index()
df_mean.to_csv(csv_path.replace(".csv", "_national_average.csv"), index=False)

# Save outputs
tif_path = os.path.join(OUT_DIR, "era5_ireland_mean_wind_1994_2024.tif")
nc_path = os.path.join(OUT_DIR, "era5_ireland_mean_wind_1994_2024.nc")
csv_path = os.path.join(OUT_DIR, "era5_ireland_mean_wind_1994_2024.csv")

# GeoTIFF export
ds_mean.rio.set_spatial_dims(x_dim="longitude", y_dim="latitude", inplace=True)
ds_mean.rio.write_crs("EPSG:4326", inplace=True)
ds_mean.rio.to_raster(tif_path)

# NetCDF export
ds_mean.to_netcdf(nc_path)

# CSV export (flatten grid)
df_mean = ds_mean.to_dataframe(name="wind_speed_10m").reset_index()
df_mean.to_csv(csv_path, index=False)

# Optional: print country-mean scalar
scalar_mean = float(ds_mean.mean(dim=["latitude", "longitude"]).values)
print(f"🌬 Average wind speed over Ireland (1994–2024): {scalar_mean:.2f} m/s")

# Done
print(f"✅ Saved climatology GeoTIFF → {tif_path}")
print(f"✅ Saved mean NetCDF → {nc_path}")
print(f"✅ Saved full grid CSV → {csv_path}")



