# --- file: data_utils.py ---
import os
import glob
import re
import json
import datetime
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import calendar
from hilltoppy import Hilltop

# Configuration
PARQUET_FILE = 'air_temperature.parquet'
BASE_URL = 'https://extranet.trc.govt.nz/getdata/'
HTS = 'boo.hts'
SITE = 'Patea at Stratford'
MEASUREMENT = 'Air Temperature (Continuous)'
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
STORE_PATH = "electricity_usage.parquet"
STORE_PATH_GAS = "gas_usage.parquet"
STORE_BILLING = "billing_periods.csv"
METADATA_PATH = "metadata.json"
folder_path = "/Users/shodges/scripts/energy_consumption/data"
if 'CONDA_DEFAULT_ENV' in os.environ:
    DOWNLOADS_FOLDER = "/Users/shodges/scripts/energy_consumption/data"
else:
    DOWNLOADS_FOLDER = "/home/Catnipmadness/scripts/energy_consumption/data"
FILE_PATTERN_ELECTRICITY = os.path.join(DOWNLOADS_FOLDER, 'Genesis Energy - My Hourly Usage*.csv')
FILE_PATTERN_GAS = os.path.join(DOWNLOADS_FOLDER, 'Genesis Energy - Hourly Gas Usage*.csv')


def check_forecast_electricty_data():
    """
    Load the forecast.csv file and return the latest daily (last 7), weekly, and monthly forecast values.
    Dates are returned as ISO 8601 strings.

    Args:
        data_dir (str or Path): Directory where forecast.csv is stored.

    Returns:
        dict: {
            'daily': List of dicts with keys 'date', 'value', 'label',
            'weekly': Dict with keys 'date', 'value', 'label',
            'monthly': Dict with keys 'date', 'value', 'label', 'range'
        }
    """
    
    print(" + Checking forecast data...")

    
    file_path = DOWNLOADS_FOLDER + "/forecasts.csv"
    df = pd.read_csv(file_path, parse_dates=["date"], date_format="%Y-%m-%d")

    # Filter relevant durations
    df = df[df["duration"].isin(["day", "week", "month"])]

    result = {}

    # Last 7 daily forecasts
    daily_df = df[df["duration"] == "day"].sort_values("date", ascending=False).head(7).sort_values("date")
    result["daily"] = [
        {
            "date": row["date"].date().isoformat(),
            "value": row["value"],
            "label": row["forecast"]
        }
        for _, row in daily_df.iterrows()
    ]

    # Latest weekly forecast
    weekly_df = df[df["duration"] == "week"]
    if not weekly_df.empty:
        latest_week = weekly_df.sort_values("date", ascending=False).iloc[0]
        result["weekly"] = {
            "date": latest_week["date"].date().isoformat(),
            "value": latest_week["value"],
            "label": latest_week["forecast"]
        }

    # Latest monthly forecast
    monthly_df = df[df["duration"] == "month"]
    if not monthly_df.empty:
        latest_month = monthly_df.sort_values("date", ascending=False).iloc[0]
        result["monthly"] = {
            "date": latest_month["date"].date().isoformat(),
            "value": latest_month["value"],
            "label": latest_month["forecast"],
            "range": latest_month.get("label", "")
        }

    return result
    # This function is a placeholder for future implementation
    # In a real implementation, you would fetch and process forecast data here.

def check_electricity_data():
    print(" + Checking electricity data...")
    # Load metadata and discover new files
    metadata = load_metadata()
    new_electricity_files = discover_new_electricity_files(metadata)

    if not new_electricity_files:
        print("   - No new electricity files to process.")
        if os.path.exists(STORE_PATH):
            df = pd.read_parquet(STORE_PATH)
        else:
            df = pd.DataFrame()
    else:
        print(f"   - Processing {len(new_electricity_files)} new electricity files.")
        last_dt = metadata.get("last_datetime_electricity")
        new_df = read_and_filter(new_electricity_files, last_dt)

        if not new_df.empty:
            new_df = enrich_datetime_info(new_df)
            new_df = assign_dayparts(new_df)
            new_df = assign_billMonths(new_df)
            new_df = clean_usage_data(new_df)

            # Merge with previous data if exists
            if os.path.exists(STORE_PATH):
                old_df = pd.read_parquet(STORE_PATH)
                df = pd.concat([old_df, new_df], ignore_index=True)
            else:
                df = new_df

            df.sort_values(by='index', ascending=True, inplace=True)
                        
            # Assign bill months as a last step as it needs to be done after all data is merged
            # as every month needs to be updated based on the number of billing days represented
            # in the most current month. It also acknowledges that billing days gets reset every month.
            df = assign_billMonths(df)            


            df.to_parquet(STORE_PATH, index=False)
            metadata["processed_files_electricity"].extend(new_electricity_files)
            #df.to_csv("new_data.csv", index=False)
            metadata["last_datetime_electricity"] = df["index"].max().strftime("%Y-%m-%dT%H:%M:%S")
            save_metadata(metadata)
        else:
            print("   - No new data rows found in the new files.")
            if os.path.exists(STORE_PATH):
                df = pd.read_parquet(STORE_PATH)
            else:
                df = pd.DataFrame()
    return df


def check_gas_data():
    print(" + Checking gas data...")
    # Load metadata and discover new files
    metadata = load_metadata()
    new_gas_files = discover_new_gas_files(metadata)

    if not new_gas_files:
        print("   - No new gas files to process.")
        if os.path.exists(STORE_PATH_GAS):
            df = pd.read_parquet(STORE_PATH_GAS)
        else:
            df = pd.DataFrame()
    else:
        print(f"   - Processing {len(new_gas_files)} new gas files.")
        last_dt = metadata.get("last_datetime_gas")
        new_df = read_and_filter(new_gas_files, last_dt)

        if not new_df.empty:
            new_df = enrich_datetime_info(new_df)
            new_df = assign_dayparts(new_df)
            new_df = assign_billMonths(new_df)
            new_df = clean_usage_data(new_df)

            # Merge with previous data if exists
            if os.path.exists(STORE_PATH_GAS):
                old_df = pd.read_parquet(STORE_PATH_GAS)
                df = pd.concat([old_df, new_df], ignore_index=True)
            else:
                df = new_df

            df.sort_values(by='index', ascending=True, inplace=True)
            
            # Assign bill months as a last step as it needs to be done after all data is merged
            # as every month needs to be updated based on the number of billing days represented
            # in the most current month. It also acknowledges that billing days gets reset every month.
            df = assign_billMonths(df)
            
            df.to_parquet(STORE_PATH_GAS, index=False)
            metadata["processed_files_gas"].extend(new_gas_files)
            #df.to_csv("new_data.csv", index=False)
            metadata["last_datetime_gas"] = df["index"].max().strftime("%Y-%m-%dT%H:%M:%S")
            save_metadata(metadata)
        else:
            print("   - No new data rows found in the new files.")
            if os.path.exists(STORE_PATH_GAS):
                df = pd.read_parquet(STORE_PATH_GAS)
            else:
                df = pd.DataFrame()
    # plot_summary(df, plot_type="monthly_totals")
    return df


def check_air_temperature_data():
    print(" + Checking air temperature data...")
    # Initialise Hilltop connection
    ht = Hilltop(BASE_URL, HTS)

    # Load existing air temperature data if available
    if os.path.exists(PARQUET_FILE):
        df_existing = pd.read_parquet(PARQUET_FILE)
        df_existing['Time'] = pd.to_datetime(df_existing['Time'])
        latest_time = df_existing['Time'].max()
    else:
        df_existing = pd.DataFrame()
        latest_time = datetime(2025, 1, 1)  # Default starting point

    # Check if air temperature data is more than 1 days old
    now = datetime.now()
    if latest_time < now - timedelta(days=1):
        from_date = latest_time.strftime(DATE_FORMAT)
        to_date = now.strftime(DATE_FORMAT)

        print(f"   - Fetching new data from {from_date} to {to_date}...")

        # Fetch new data
        df_new = ht.get_data(SITE, MEASUREMENT, from_date=from_date, to_date=to_date)

        # Convert Time to datetime
        df_new['Time'] = pd.to_datetime(df_new['Time'])

        # Combine and deduplicate
        df_combined = pd.concat([df_existing, df_new])
        df_combined = df_combined.drop_duplicates(subset=['SiteName', 'MeasurementName', 'Time'])

        # Save updated data
        df_combined.to_parquet(PARQUET_FILE, index=False)
        print("   - Air temperature data updated and saved to Parquet.")
    else:
        print("   - Air temperature data is up to date. No fetch required.")
    return None


def remove_day_suffix(text):
    return re.sub(r"(?<=\d)(st|nd|rd|th)", "", text)


def load_metadata():
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, 'r') as f:
            return json.load(f)
    return {"processed_files_electricty": [], "last_datetime_electricity": None}


def save_metadata(metadata):
    with open(METADATA_PATH, 'w') as f:
        json.dump(metadata, f, indent=4)


def discover_new_electricity_files(metadata):
    all_files = glob.glob(FILE_PATTERN_ELECTRICITY)
    return [f for f in all_files if f not in metadata.get("processed_files_electricity", [])]

def discover_new_gas_files(metadata):
    all_files = glob.glob(FILE_PATTERN_GAS)
    return [f for f in all_files if f not in metadata.get("processed_files_gas", [])]


def read_and_filter(files, last_date=None):
    dataframes = []
    for file in files:
        df = pd.read_csv(file)
        df['date1'] = df['date'].apply(remove_day_suffix)
        df['datetime'] = pd.to_datetime(df['date1'], format='%I:%M%p %d %B %Y', errors='coerce')
        df = df.dropna(subset=['datetime'])
        if last_date:
            cutoff = pd.to_datetime(last_date)
            df = df[df['datetime'] > cutoff]
        dataframes.append(df)
    return pd.concat(dataframes, ignore_index=True) if dataframes else pd.DataFrame()


def enrich_datetime_info(df):
    df['YYYYMMDD'] = df['datetime'].dt.strftime('%Y-%m-%d')
    df['Weekday'] = df['datetime'].dt.day_name()
    df['Month'] = df['datetime'].dt.month_name()
    df['Year'] = df['datetime'].dt.year
    return df


def assign_dayparts(df):
    if 'datetime' not in df.columns:
        raise KeyError("'datetime' column is required in the DataFrame.")

    df = df.copy()
    df = df.set_index('datetime')
    df.index.name = None  # Remove name to prevent KeyError
    df['d_time'] = None
    df['d_time1'] = None

    df.loc[df.between_time('18:00', '23:59').index, 'd_time'] = 'Po'
    df.loc[df.between_time('00:00', '05:59').index, 'd_time'] = 'Atapo'
    df.loc[df.between_time('06:00', '11:59').index, 'd_time'] = 'Ata'
    df.loc[df.between_time('12:00', '17:59').index, 'd_time'] = 'Ahiahi'

    df.loc[df.between_time('00:00', '03:59').index, 'd_time1'] = 'Atapo'
    df.loc[df.between_time('04:00', '07:59').index, 'd_time1'] = 'Breakfast'
    df.loc[df.between_time('08:00', '11:59').index, 'd_time1'] = 'Ata'
    df.loc[df.between_time('12:00', '15:59').index, 'd_time1'] = 'Ahiahi'
    df.loc[df.between_time('16:00', '19:59').index, 'd_time1'] = 'Dinner'
    df.loc[df.between_time('20:00', '23:59').index, 'd_time1'] = 'Po'

    return df.reset_index()

def assign_billMonths(df):
    if 'index' not in df.columns:
        raise KeyError("'index' column is required in the DataFrame.")
    
    df = df.copy()
    # df = df.set_index('datetime')
    # df.index.name = None  # Remove name to prevent KeyError
    df['billMonth'] = None
    
    file_path = DOWNLOADS_FOLDER + "/" + STORE_BILLING

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Billing periods file not found: {file_path}")
    else:
        df_bill = pd.read_csv(file_path)

    df_bill['start_date'] = pd.to_datetime(df_bill['bill_period_start'])
    df_bill['end_date'] = pd.to_datetime(df_bill['bill_period_end']).dt.normalize()
    df_bill['duration'] = (df_bill['end_date'] - df_bill['start_date']).dt.days+1
    
    max_day = df['index'].max()
    current_bill_start_date = df_bill['start_date'].max()
    var=max_day-current_bill_start_date+ timedelta(days=1)
    df_bill['days'] = var.days
    df_bill['relative_current_dates'] = df_bill["start_date"]+ timedelta(days=var.days-1)
 
    for i in range(len(df_bill)):
        start_date = df_bill['start_date'].iloc[i]
        end_date = df_bill['relative_current_dates'].iloc[i] + timedelta(days=1)  # Include the end date in the range
        
        # Filter data for the current billing period
        df.loc[(df['index'] >= start_date) & (df['index'] < end_date), 'billMonth'] = df_bill['month'].iloc[i]
        recs = len(df.loc[(df['index'] >= start_date) & (df['index'] < end_date), 'billMonth'])
        if recs > 0:
            print(f"   - Assigning bill month {df_bill['month'].iloc[i]} to {recs} rows")
        
    return df


def clean_usage_data(df):
    df[['usage', 'units']] = df['usage'].str.split(' ', expand=True)
    df['usage'] = pd.to_numeric(df['usage'], errors='coerce')
    df['dollars'] = df['dollars'].str.replace('$', '', regex=False)
    df['dollars'] = pd.to_numeric(df['dollars'], errors='coerce')
    return df


def plot_summary(df, plot_type="bar"):
    
    year = datetime.now().year
    first_day = datetime(year, 1, 1)
    last_day = datetime(year, 12, 31)

    
    df['Category'] = df['d_time1']
    ordered_months = ["January", "February", "March", "April", "May", "June",
                      "July", "August", "September", "October", "November", "December"]
    ordered_dayparts = ["Atapo", "Breakfast", "Ata", "Ahiahi", "Dinner", "Po"]
    
    df['Month'] = pd.Categorical(df['Month'], categories=ordered_months, ordered=True)
    df['Category'] = pd.Categorical(df['Category'], categories=ordered_dayparts, ordered=True)

    if plot_type == "bar":
        df_monthly = df.groupby(['Month', 'Category'])['usage'].mean().reset_index()
        df_monthly = df_monthly.dropna(subset=['usage'])
        fig = go.Figure()
        for category in ordered_dayparts:
            df_cat = df_monthly[df_monthly['Category'] == category]

            fig.add_trace(go.Bar(x=df_cat['Month'], y=df_cat['usage'], name=category))
        fig.update_layout(
            title='Monthly Totals by Category (Mean Usage)',
            xaxis_title='Month',
            yaxis_title='Mean Usage (kWh)',
            barmode='group'
        )

    elif plot_type == "monthly_totals":
        df_monthly = df.groupby(['Month'])['usage'].sum().reset_index()
        df_monthly = df_monthly.dropna(subset=['usage'])
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_monthly['Month'], y=df_monthly['usage']))
        fig.update_layout(
            title='Monthly Totals',
            xaxis_title='Month',
            yaxis_title='Usage (kWh)',
            yaxis=dict(rangemode="tozero"),
            xaxis=dict(range=[first_day, last_day]),
        )

    
    elif plot_type == "box":
        fig = px.box(
            df,
            x='Month',
            y='usage',
            color='Category',
            category_orders={'Month': ordered_months, 'Category': ordered_dayparts},
            points='outliers',
            title='Usage Distribution by Daypart and Month (Box Plot)'
        )
        fig.update_layout(
            xaxis_title='Month',
            yaxis_title='Usage (kWh)'
        )

    elif plot_type == "violin":
        fig = px.violin(
            df,
            x='Month',
            y='usage',
            color='Category',
            category_orders={'Month': ordered_months, 'Category': ordered_dayparts},
            box=True,
            points='all',
            title='Usage Distribution by Daypart and Month (Violin Plot)'
        )
        fig.update_layout(
            xaxis_title='Month',
            yaxis_title='Usage (kWh)'
        )

    else:
        raise ValueError("plot_type must be one of: 'monthly_totals', 'bar', 'box', or 'violin'")

    fig.show()


def create_usage_plot(df, plot_type="bar"):
    ordered_months = ["January", "February", "March", "April", "May", "June",
                      "July", "August", "September", "October", "November", "December"]
    ordered_dayparts = ["Atapo", "Breakfast", "Ata", "Ahiahi", "Dinner", "Po"]

    df['Month'] = pd.Categorical(df['Month'], categories=ordered_months, ordered=True)
    df['Category'] = pd.Categorical(df['d_time1'], categories=ordered_dayparts, ordered=True)

    if plot_type == "bar":
        df_monthly = df.groupby(['Month', 'Category'])['usage'].mean().reset_index()
        fig = go.Figure()
        for category in ordered_dayparts:
            df_cat = df_monthly[df_monthly['Category'] == category]
            fig.add_trace(go.Bar(x=df_cat['Month'], y=df_cat['usage'], name=category))
        fig.update_layout(
            title='Monthly Totals by Category (Mean Usage)',
            xaxis_title='Month',
            yaxis_title='Mean Usage (kWh)',
            barmode='group'
        )
    elif plot_type == "box":
        fig = px.box(df, x='Month', y='usage', color='Category',
                     category_orders={'Month': ordered_months, 'Category': ordered_dayparts},
                     points='outliers',
                     title='Usage Distribution by Daypart and Month (Box Plot)')
        fig.update_layout(xaxis_title='Month', yaxis_title='Usage (kWh)')
    elif plot_type == "violin":
        fig = px.violin(df, x='Month', y='usage', color='Category',
                        category_orders={'Month': ordered_months, 'Category': ordered_dayparts},
                        box=True, points='all',
                        title='Usage Distribution by Daypart and Month (Violin Plot)')
        fig.update_layout(xaxis_title='Month', yaxis_title='Usage (kWh)')
    else:
        raise ValueError("plot_type must be one of: 'bar', 'box', or 'violin'")
    return fig


def check_data():
    print("Checking all data...")
    df_electric = check_electricity_data()
    df_gas = check_gas_data()
    check_air_temperature_data()
    print("Data checks complete.")
    return df_electric
