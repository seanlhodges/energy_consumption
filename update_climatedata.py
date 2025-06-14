import pandas as pd
import os
from datetime import datetime, timedelta
from hilltoppy import Hilltop
import plotly.graph_objects as go

# Configuration
PARQUET_FILE = 'air_temperature_data.parquet'
BASE_URL = 'https://extranet.trc.govt.nz/getdata/'
HTS = 'boo.hts'
SITE = 'Patea at Stratford'
MEASUREMENT = 'Air Temperature (Continuous)'
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Initialise Hilltop connection
ht = Hilltop(BASE_URL, HTS)

# Load existing data if available
if os.path.exists(PARQUET_FILE):
    df_existing = pd.read_parquet(PARQUET_FILE)
    df_existing['Time'] = pd.to_datetime(df_existing['Time'])
    latest_time = df_existing['Time'].max()
else:
    df_existing = pd.DataFrame()
    latest_time = datetime(2025, 1, 1)  # Default starting point

# Check if data is more than 2 days old
now = datetime.now()
if latest_time < now - timedelta(days=2):
    from_date = latest_time.strftime(DATE_FORMAT)
    to_date = now.strftime(DATE_FORMAT)

    print(f"Fetching new data from {from_date} to {to_date}...")

    # Fetch new data
    df_new = ht.get_data(SITE, MEASUREMENT, from_date=from_date, to_date=to_date)

    # Convert Time to datetime
    df_new['Time'] = pd.to_datetime(df_new['Time'])

    # Combine and deduplicate
    df_combined = pd.concat([df_existing, df_new])
    df_combined = df_combined.drop_duplicates(subset=['SiteName', 'MeasurementName', 'Time'])

    # Save updated data
    df_combined.to_parquet(PARQUET_FILE, index=False)
    print("Air temperature data updated and saved to Parquet.")
else:
    df_combined = df_existing
    print("Air temperature data is up to date. No fetch required.")
