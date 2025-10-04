import numpy as np
import pandas as pd

def extrapolate_wind_expected(ref_speed, ref_height: int = 50, hub_height: int = 80, z0: float = 0.03):
    """
    Extrapolate expected wind speed from reference height to hub height using the log law.
    Works with scalars, numpy arrays, and pandas Series.

    Parameters
    ----------
    ref_speed : float, np.ndarray, or pd.Series
        Wind speed(s) at reference height.
    ref_height : int
        Reference height in meters (10 or 50 typically).
    hub_height : int
        Desired hub height (e.g., 80, 100).
    z0 : float, optional
        Surface roughness length (default 0.03 = grassland).

    Returns
    -------
    float, np.ndarray, or pd.Series
        Extrapolated wind speed(s) at hub_height.
    """
    if ref_speed is None:
        return 0.0

    # Convert to numpy array for vectorization
    ref_speed = np.asarray(ref_speed)

    # Replace negative/zero values with 0.0
    ref_speed = np.where(ref_speed > 0, ref_speed, 0.0)

    extrapolated = ref_speed * np.log(hub_height / z0) / np.log(ref_height / z0)

    # Return same type as input
    if isinstance(ref_speed, np.ndarray) and ref_speed.ndim == 0:
        return float(round(extrapolated, 2))
    return np.round(extrapolated, 2)
