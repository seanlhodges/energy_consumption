import pandas as pd
from datetime import datetime, timedelta
import os

def assign_billMonths(df):
    if 'index' not in df.columns:
        raise KeyError("'index' column is required in the DataFrame.")
    
    df = df.copy()
    # df = df.set_index('datetime')
    # df.index.name = None  # Remove name to prevent KeyError
    df['billMonth'] = None
    
    file_path = "data/billing_periods.csv"

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
        df.loc[(df['index'] >= start_date) & (df['index'] <= end_date), 'billMonth'] = df_bill['month'].iloc[i]
        recs = len(df[(df['index'] >= start_date) & (df['index'] <= end_date)])
        print(f"Assigning bill month {df_bill['month'].iloc[i]} to {recs} rows for dates from {start_date} to {end_date}")
        
    return df
    # return df.reset_index()


files = ["electricity_usage.parquet", "gas_usage.parquet"]

for f in files:
    df = pd.read_parquet(f)
    df = assign_billMonths(df)    
    df.to_parquet(f, index=False)
