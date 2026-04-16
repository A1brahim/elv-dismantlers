from pathlib import Path
import pandas as pd
from geopy.geocoders import Nominatim
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
# Save Full Geocoded Dataset
# ---------------------------------------------------

output_path = DATA_DIR / "sbr_dismantlers_geocoded.csv"
df.to_csv(output_path, index=False)

print(f"\nGeocoding completed.")
print(f"Saved geocoded dataset to: {output_path}")