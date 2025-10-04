# ============================================================
# 🚀 AI-ASSISTED CODE NOTICE
# This file was developed with assistance from OpenAI's ChatGPT (GPT-5)
# as part of the NASA Space Apps 2025 project:
# “TerraWatt — Will It Rain on My Parade?”
# ============================================================

import folium
import rasterio
import numpy as np
from matplotlib import cm as mpl_cm
from matplotlib.colors import Normalize

def add_raster_layer(m, tif_path, name, cmap="viridis", opacity=0.7, vmin=None, vmax=None):
    """Add a GeoTIFF as an interactive Folium overlay with correct color mapping."""
    with rasterio.open(tif_path) as src:
        arr = src.read(1)
        bounds = src.bounds
        lat_min, lat_max = bounds.bottom, bounds.top
        lon_min, lon_max = bounds.left, bounds.right

        # Handle range
        if vmin is None: vmin = np.nanmin(arr)
        if vmax is None: vmax = np.nanmax(arr)

        # Normalize + apply colormap
        norm = Normalize(vmin=vmin, vmax=vmax)
        cmap_obj = mpl_cm.get_cmap(cmap)
        rgba_img = (cmap_obj(norm(arr)) * 255).astype(np.uint8)

        # Folium expects a (M, N, 4) RGBA array
        folium.raster_layers.ImageOverlay(
            image=rgba_img,
            bounds=[[lat_min, lon_min], [lat_max, lon_max]],
            opacity=opacity,
            name=name,
        ).add_to(m)

        # Add color legend
        import branca.colormap as cm
        colorbar = cm.LinearColormap(
            colors=[mpl_cm.get_cmap(cmap)(x) for x in np.linspace(0, 1, 6)],
            vmin=vmin, vmax=vmax, caption=name
        )
        colorbar.add_to(m)
