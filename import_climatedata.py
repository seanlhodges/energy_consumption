import os
import glob
import pandas as pd
import plotly.graph_objects as go
# --- file: air_temperature_pipeline.py ---


DATA_FOLDER = "/Users/shodges/scripts/genesisenergy/data"
CSV_PATTERN = os.path.join(DATA_FOLDER, "air_temperature_data*.csv")
PARQUET_FILE = os.path.join(DATA_FOLDER, "air_temperature_data.parquet")

def load_and_combine_csvs():
    files = glob.glob(CSV_PATTERN)
    df_list = [pd.read_csv(file) for file in files]
    df = pd.concat(df_list, ignore_index=True)
    df["Time"] = pd.to_datetime(df["Time"])
    df = df.drop_duplicates().sort_values("Time")
    return df

def parquet_needs_update(existing_df, latest_csv_df):
    # Check if any new timestamps exist in latest_csv_df not in existing
    return not latest_csv_df["Time"].isin(existing_df["Time"]).all()

# Step 1: Check if parquet file exists
if os.path.exists(PARQUET_FILE):
    print("📦 Existing Parquet found. Checking for updates...")
    existing_df = pd.read_parquet(PARQUET_FILE)
    latest_csv_df = load_and_combine_csvs()
    
    if parquet_needs_update(existing_df, latest_csv_df):
        print("🔄 New data found. Updating Parquet file...")
        combined_df = pd.concat([existing_df, latest_csv_df]).drop_duplicates().sort_values("Time")
        combined_df.to_parquet(PARQUET_FILE, index=False)
    else:
        print("✅ No new data found. Using cached Parquet.")
        combined_df = existing_df
else:
    print("🚀 No existing Parquet. Loading CSVs and creating new Parquet...")
    combined_df = load_and_combine_csvs()
    combined_df.to_parquet(PARQUET_FILE, index=False)

# Plotting
fig = go.Figure()
for site in combined_df["SiteName"].unique():
    site_df = combined_df[combined_df["SiteName"] == site]
    fig.add_trace(go.Scatter(
        x=site_df["Time"],
        y=site_df["Value"],
        mode='lines',
        name=site
    ))

fig.update_layout(
    title="10-Minute Air Temperature Time Series",
    xaxis_title="Date/Time",
    yaxis_title="Temperature (°C)",
    template="plotly_white"
)

fig.show()
