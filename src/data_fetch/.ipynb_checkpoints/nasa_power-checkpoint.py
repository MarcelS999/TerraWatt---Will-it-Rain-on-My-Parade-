# ============================================================
# 🚀 AI-ASSISTED CODE NOTICE
# This file was developed with assistance from OpenAI's ChatGPT (GPT-5)
# as part of the NASA Space Apps 2025 project:
# “TerraWatt — Will It Rain on My Parade?”
# ============================================================

import requests
import pandas as pd

def get_wind_data(lat: float, lon: float, start: str, end: str):
    """
    Fetch daily 10m wind speed from NASA POWER API.
    lat, lon: coordinates
    start, end: YYYYMMDD
    """
    url = (
        f"https://power.larc.nasa.gov/api/temporal/daily/point"
        f"?parameters=WS10M"
        f"&community=RE"
        f"&longitude={lon}&latitude={lat}"
        f"&start={start}&end={end}"
        f"&format=JSON"
    )

    r = requests.get(url)
    r.raise_for_status()
    data = r.json()

    # Extract daily data
    records = data["properties"]["parameter"]["WS10M"]
    df = pd.DataFrame(list(records.items()), columns=["date", "wind_speed"])
    df["date"] = pd.to_datetime(df["date"])
    return df
