import requests
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import json
import time

# -------------------------------------------------
# CONFIG
# -------------------------------------------------

CACHE_DIR = Path(__file__).resolve().parents[2] / "data/market_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

ELECTRICITY_CACHE_FILE = CACHE_DIR / "electricity_se3.csv"

# Cache duration (hours)
CACHE_TTL_HOURS = 24


# -------------------------------------------------
# HELPER: Check cache freshness
# -------------------------------------------------

def is_cache_valid(file_path, ttl_hours=None):
    if ttl_hours is None:
        ttl_hours = CACHE_TTL_HOURS

    if not file_path.exists():
        return False

    last_modified = datetime.fromtimestamp(file_path.stat().st_mtime)
    return datetime.now() - last_modified < timedelta(hours=ttl_hours)

# -------------------------------------------------
# FETCH: Electricity (SE3)
# -------------------------------------------------

def fetch_electricity_se3(days_back=365):
    records = []

    for i in range(days_back):
        date = datetime.today().date() - timedelta(days=i+1)
        url = f"https://www.elprisetjustnu.se/api/v1/prices/{date.strftime('%Y/%m-%d')}_SE3.json"

        try:
            response = requests.get(url, timeout=5)

            if response.status_code != 200:
                continue

            data = response.json()

            for entry in data:
                records.append({
                    "datetime": entry["time_start"],
                    "price_sek_kwh": entry["SEK_per_kWh"]
                })

        except Exception as e:
            print(f"Error fetching {url}: {e}")
            time.sleep(1)  # Brief pause before retrying
            continue

    df = pd.DataFrame(records)

    if df.empty:
        return df

    # Robust datetime handling
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce", utc=True)
    df = df.dropna(subset=["datetime"])

    # Daily aggregation (cleaner)
    df["date"] = df["datetime"].dt.tz_convert("Europe/Stockholm").dt.date
    df = df.groupby("date", as_index=False)["price_sek_kwh"].mean()

    # Convert to MWh
    df["price_sek_mwh"] = df["price_sek_kwh"] * 1000

    return df[["date", "price_sek_mwh"]]


# -------------------------------------------------
# PUBLIC FUNCTION (WITH CACHE)
# -------------------------------------------------

def get_electricity_se3(force_refresh=False):
    """
    Returns electricity prices (SE3) as DataFrame:
    date | price_sek_mwh
    """

    # Use cache if valid
    if not force_refresh and is_cache_valid(ELECTRICITY_CACHE_FILE):
        return pd.read_csv(ELECTRICITY_CACHE_FILE, parse_dates=["date"])

    # Fetch fresh data
    df = fetch_electricity_se3()

    # Check AFTER fetch
    if df.empty:
        print("⚠️ Warning: Electricity data is empty after fetch.")
        return df

    # Save to cache
    df.to_csv(ELECTRICITY_CACHE_FILE, index=False)

    return df


# -------------------------------------------------
# QUICK METRICS (OPTIONAL)
# -------------------------------------------------

def compute_electricity_metrics(df):
    """
    Returns key electricity metrics:
    latest, 7d avg, 30d avg, volatility, trend
    """

    if df.empty:
        return {}

    series = df["price_sek_mwh"]

    latest = series.iloc[-1]
    avg_7d = series.tail(7).mean()
    avg_30d = series.tail(30).mean()
    volatility = series.tail(30).std()

    # Trend (last vs previous window)
    prev_30d = series.tail(60).head(30).mean()

    trend = None
    if prev_30d:
        trend = (avg_30d - prev_30d) / prev_30d

    return {
        "latest": latest,
        "avg_7d": avg_7d,
        "avg_30d": avg_30d,
        "volatility": volatility,
        "trend": trend
    }

# -------------------------------------------------
# TREND METRICS 
# -------------------------------------------------

def compute_electricity_metrics(df):
    """
    Returns:
    - summary metrics
    - enriched dataframe (trend + volatility bands)
    """

    if df.empty:
        return {}, df

    df = df.copy()

    # -------------------------------
    # Time-series structure
    # -------------------------------
    df["trend_30d"] = df["price_sek_mwh"].rolling(30).mean()
    df["vol_30d"] = df["price_sek_mwh"].rolling(30).std()

    df["upper"] = df["trend_30d"] + df["vol_30d"]
    df["lower"] = df["trend_30d"] - df["vol_30d"]

    # -------------------------------
    # Summary metrics
    # -------------------------------
    series = df["price_sek_mwh"]

    latest = series.iloc[-1]
    avg_7d = series.tail(7).mean()
    avg_30d = series.tail(30).mean()
    volatility = series.tail(30).std()

    prev_30d = series.tail(60).head(30).mean()

    trend = None
    if prev_30d:
        trend = (avg_30d - prev_30d) / prev_30d

    metrics = {
        "latest": latest,
        "avg_7d": avg_7d,
        "avg_30d": avg_30d,
        "volatility": volatility,
        "trend": trend
    }

    return metrics, df