from datetime import timedelta
import pandas as pd

df_events = pd.read_csv('data/usage-appliances.csv', parse_dates=['Timestamp'])
df_events['DAY'] = df_events['Timestamp'].dt.day
df_events['TIME'] = df_events['Timestamp'].dt.strftime('%H:%M')

# Define metadata: duration and estimated kWh usage
program_metadata = {
    "Pots / Pans":      {"duration": timedelta(hours=2, minutes=15), "kWh": 1.35},
    "Auto Wash":      {"duration": timedelta(hours=2, minutes=30), "kWh": 1.15},
    "Auto Gentle":       {"duration": timedelta(hours=1, minutes=45), "kWh": 0.75},
    "Pre-rinse":       {"duration": timedelta(hours=1, minutes=0), "kWh": 1.1},
    "Quick 1h":       {"duration": timedelta(hours=3, minutes=15), "kWh": 0.6},
    "Eco Wash":     {"duration": timedelta(hours=3, minutes=15), "kWh": 0.6},
    "Machine Care": {"duration": timedelta(hours=2, minutes=10), "kWh": 1.5},
    "Short 60C":       {"duration": timedelta(hours=1, minutes=29), "kWh": 1.05},
    "Quick Wash and Dry":       {"duration": timedelta(hours=0, minutes=45), "kWh": 0.85},
    # Add more programs here
}


# Ensure Timestamp is in datetime format
df_events['Timestamp'] = pd.to_datetime(df_events['Timestamp'])

# Map duration and kWh to each row
df_events['Duration'] = df_events['Program'].map(lambda p: program_metadata.get(p, {}).get('duration', pd.NaT))
df_events['kWh'] = df_events['Program'].map(lambda p: program_metadata.get(p, {}).get('kWh', None))

# Calculate StartTime
df_events['StartTime'] = df_events['Timestamp'] - df_events['Duration']

print(df_events)

