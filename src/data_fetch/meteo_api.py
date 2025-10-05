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

import os
import pandas as pd
import geopandas as gpd
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from time import sleep

# ======================================================
# 🌦️ Load environment variables
# ======================================================
load_dotenv()
USER = os.getenv("METEOMATICS_USERNAME")
PASS = os.getenv("METEOMATICS_PASSWORD")
if not USER or not PASS:
    raise ValueError("❌ Meteomatics credentials missing in .env")

# ======================================================
# 🗺️ File paths
# ======================================================
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
WIND_PATH = os.path.join(PROJECT_ROOT, "data", "wind_farms", "Wind Farms June 2022_ESPG3857.shp")
OUTPUT = os.path.join(PROJECT_ROOT, "data", "processed", "windfarm_forecasts.csv")
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

# ======================================================
# ⚙️ Batch Fetcher
# ======================================================
def fetch_batch(coords, start, end, interval="PT1H", parameters=None):
    if parameters is None:
        parameters = ["wind_speed_100m:ms", "wind_speed_50m:ms"]

    coord_str = "+".join([f"{lat},{lon}" for lat, lon in coords])
    url = (
        f"https://api.meteomatics.com/"
        f"{start}Z--{end}Z:{interval}/"
        f"{','.join(parameters)}/{coord_str}/json?model=mix"
    )

    r = requests.get(url, auth=(USER, PASS))
    if r.status_code != 200:
        print(f"⚠️ API returned {r.status_code}: {r.text[:200]}")
        return None
    return r.json()

# ======================================================
# 💨 Fetch all wind farms in batches
# ======================================================
def batch_forecast():
    gdf = gpd.read_file(WIND_PATH).to_crs(4326)
    farms = [(row.geometry.y, row.geometry.x, row.get("Name", f"Farm_{i}")) for i, row in gdf.iterrows()]
    print(f"✅ Loaded {len(farms)} wind farms")

    start = (datetime.utcnow() - timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%S")
    end = (datetime.utcnow() + timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%S")

    batch_size = 25  # ⚡ Safe number per query
    all_df = []

    for i in range(0, len(farms), batch_size):
        batch = farms[i:i+batch_size]
        coords = [(lat, lon) for lat, lon, _ in batch]
        names = [name for _, _, name in batch]

        print(f"🔹 Fetching batch {i//batch_size+1}/{(len(farms)//batch_size)+1} ({len(batch)} farms)...")
        data = fetch_batch(coords, start, end)
        if not data:
            continue

        # Parse JSON
        dfs = []
        for j, param_data in enumerate(data["data"]):
            param = param_data["parameter"]
            for coord_idx, coord_block in enumerate(param_data["coordinates"]):
                df = pd.DataFrame(coord_block["dates"])
                df["farm_name"] = names[coord_idx]
                df["parameter"] = param
                dfs.append(df)
        df_combined = pd.concat(dfs, ignore_index=True)

        df_pivot = df_combined.pivot_table(
            index=["farm_name", "date"],
            columns="parameter",
            values="value",
            aggfunc="mean"
        ).reset_index()

        all_df.append(df_pivot)
        sleep(1)  # polite pause to avoid rate-limit

    final = pd.concat(all_df, ignore_index=True)
    final["date"] = pd.to_datetime(final["date"])
    final.to_csv(OUTPUT, index=False)
    print(f"💾 Saved → {OUTPUT}")
    return final


if __name__ == "__main__":
    df = batch_forecast()
    if not df.empty:
        print(df.head())
        print("✅ Meteomatics batch forecast complete.")
