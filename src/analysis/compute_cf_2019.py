import xarray as xr
import numpy as np

# ============================================================
# ⚙️ 3 MW Generic Turbine Power Curve
# ============================================================
def power_output(v, vin=3, vrated=12, vout=25, rated_power=3_000_000):
    """
    Compute instantaneous turbine power output (W) for wind speed array v (m/s).
    """
    v = np.asarray(v)
    power = np.zeros_like(v, dtype=float)

    mask_1 = (v >= vin) & (v < vrated)
    mask_2 = (v >= vrated) & (v < vout)

    # cubic ramp-up between cut-in and rated
    power[mask_1] = rated_power * ((v[mask_1] - vin) / (vrated - vin)) ** 3
    # constant at rated power until cut-out
    power[mask_2] = rated_power

    return power


# ============================================================
# 🌬 Capacity Factor from ERA5 2019
# ============================================================
def compute_cf_2019(lat, lon, nc_path="data/era5/era5_ireland_wind_2019.nc",
                    rated_power=3_000_000, dd_fraction=None):
    """
    Estimate annual capacity factor for a 3 MW turbine at a given site using ERA5 2019 data.
    
    Parameters
    ----------
    lat, lon : float
        Site coordinates.
    nc_path : str
        Path to ERA5 NetCDF containing 10 m eastward/northward wind components.
    rated_power : float
        Turbine rated power in watts (default = 3 MW).
    dd_fraction : float or array-like, optional
        Dispatch-down fraction (0–1). If scalar, applied uniformly;
        if array-like, must match hourly time series length.
    """
    ds = xr.open_dataset(nc_path)
    u = ds["eastward_wind_at_10_metres"]
    v = ds["northward_wind_at_10_metres"]
    wspd = np.sqrt(u**2 + v**2)

    # --- Select nearest grid point ---
    wspd_site = wspd.sel(latitude=lat, longitude=lon, method="nearest")

    # --- Convert to 1D hourly series ---
    wind_series = wspd_site.to_series().dropna().astype(float)

    # --- Compute power output per hour ---
    power = power_output(wind_series.values, rated_power=rated_power)

    # --- Optional: apply dispatch-down (DD) fraction ---
    if dd_fraction is not None:
        if np.isscalar(dd_fraction):
            power *= (1 - dd_fraction)
        else:
            dd = np.clip(np.asarray(dd_fraction), 0, 1)
            power *= (1 - dd[: len(power)])  # match length if needed

    # --- Capacity Factor ---
    cf = power.mean() / rated_power
    return float(np.clip(cf, 0, 0.55))
