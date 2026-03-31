from pathlib import Path
import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time

from config import PROCESSED_DATA_DIR

# ---------------------------------------------------
# Load Latest Dataset
# ---------------------------------------------------

DATA_DIR = Path(PROCESSED_DATA_DIR)
csv_files = sorted(DATA_DIR.glob("**/sbr_dismantlers_*.csv"))

if not csv_files:
    raise FileNotFoundError("No SBR CSV files found.")

df = pd.read_csv(csv_files[-1])

# ---------------------------------------------------
# Fjugesta Coordinates
# ---------------------------------------------------

fjugesta_coords = (59.1615, 14.8703)

# ---------------------------------------------------
# Geocode UNIQUE Cities Only
# ---------------------------------------------------

geolocator = Nominatim(user_agent="sbr_analysis")

unique_cities = df["city"].unique()
city_coords = {}

print("Geocoding cities...")

for city in unique_cities:
    try:
        location = geolocator.geocode(f"{city}, Sweden")
        if location:
            city_coords[city] = (location.latitude, location.longitude)
        else:
            city_coords[city] = (None, None)
        time.sleep(1)  # Respect rate limits
    except:
        city_coords[city] = (None, None)

# ---------------------------------------------------
# Map Coordinates Back to Dataset
# ---------------------------------------------------

df["lat"] = df["city"].map(lambda x: city_coords[x][0])
df["lon"] = df["city"].map(lambda x: city_coords[x][1])

# ---------------------------------------------------
# Distance Calculation
# ---------------------------------------------------

def calculate_distance(row):
    if pd.notnull(row["lat"]) and pd.notnull(row["lon"]):
        return geodesic(fjugesta_coords, (row["lat"], row["lon"])).km
    return None

df["distance_km"] = df.apply(calculate_distance, axis=1)

# ---------------------------------------------------
# Radius Filters
# ---------------------------------------------------

within_50 = df[df["distance_km"] <= 50].sort_values("distance_km")
within_100 = df[df["distance_km"] <= 100].sort_values("distance_km")

print("\n--- Operators within 50 km ---")
print(within_50[["company", "city", "distance_km"]])

print("\n--- Operators within 100 km ---")
print(within_100[["company", "city", "distance_km"]])

# ---------------------------------------------------
# Save Output
# ---------------------------------------------------

within_50.to_csv("figures/operators_within_50km.csv", index=False)
within_100.to_csv("figures/operators_within_100km.csv", index=False)

print("\nRadius analysis completed.")