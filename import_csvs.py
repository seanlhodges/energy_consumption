import pandas as pd
import glob
import os

import datetime
import re

def remove_day_suffix(text):
  """Removes ordinal suffixes from a string."""
  return re.sub(r"(?<=\d)(st|nd|rd|th)", "", text)


# Define the path to the Downloads folder
downloads_folder = "/Users/shodges/scripts/genesisenergy/data"

# Define the file pattern to match
# Note: The double asterisk (**) is used to match any characters in the filename
file_pattern = os.path.join(downloads_folder, 'Genesis*.csv')

# Get a list of all matching CSV files
csv_files = glob.glob(file_pattern, recursive=True)

# Check if any files were found
if not csv_files:
    print(f"No CSV files found matching the pattern {file_pattern}")
    exit(1)
else:
    print(f"Found {len(csv_files)} CSV files.")
    
# Print the list of found files
#    for file in csv_files:
#        print(file)

# Read each CSV file into a DataFrame and store them in a list
# Initialize an empty list to store DataFrames
dataframes = []

# Loop through each CSV file and read it into a DataFrame
for file in csv_files:
    df = pd.read_csv(file)
    dataframes.append(df)

# Concatenate all DataFrames into a single DataFrame
combined_df = pd.concat(dataframes, ignore_index=True)

# Print the combined DataFrame
print(combined_df)

# Optionally, save the combined DataFrame to a new CSV file
#combined_df.to_csv(os.path.join(downloads_folder, "combined_data.csv"), index=False)


# Apply the function to the column
combined_df['date1'] = combined_df['date'].apply(remove_day_suffix)

combined_df['datetime'] = pd.to_datetime(combined_df['date1'], format='%I:%M%p %d %B %Y')
combined_df = combined_df.sort_values(by='datetime')
combined_df['YYYYMMDD'] = combined_df['datetime'].dt.strftime('%Y-%m-%d')
combined_df['Weekday'] = pd.to_datetime(combined_df['datetime'], format='%a').dt.day_name()
combined_df['Month'] = pd.to_datetime(combined_df['datetime'], format='%b').dt.month_name()
combined_df['Year'] = pd.to_datetime(combined_df['datetime'], format='%Y').dt.year

# Set time of day based on your specified time frames
combined_df.loc[combined_df.set_index('datetime').index.indexer_between_time('18:00', '23:59'), 'd_time'] = 'Po'
combined_df.loc[combined_df.set_index('datetime').index.indexer_between_time('0:00', '5:59'), 'd_time'] = 'Atapo'
combined_df.loc[combined_df.set_index('datetime').index.indexer_between_time('6:00', '11:59'), 'd_time'] = 'Ata'
combined_df.loc[combined_df.set_index('datetime').index.indexer_between_time('12:00', '17:59'), 'd_time'] = 'Ahiahi'

combined_df.loc[combined_df.set_index('datetime').index.indexer_between_time('0:00', '3:59'), 'd_time1'] = 'Atapo'
combined_df.loc[combined_df.set_index('datetime').index.indexer_between_time('4:00', '7:59'), 'd_time1'] = 'Breakfast'
combined_df.loc[combined_df.set_index('datetime').index.indexer_between_time('8:00', '11:59'), 'd_time1'] = 'Ata'
combined_df.loc[combined_df.set_index('datetime').index.indexer_between_time('12:00', '15:59'), 'd_time1'] = 'Ahiahi'
combined_df.loc[combined_df.set_index('datetime').index.indexer_between_time('16:00', '19:59'), 'd_time1'] = 'Dinner'
combined_df.loc[combined_df.set_index('datetime').index.indexer_between_time('20:00', '23:59'), 'd_time1'] = 'Po'

combined_df[['usage','units']] = combined_df['usage'].str.split(' ',expand=True)
combined_df['usage'] = pd.to_numeric(combined_df['usage'], errors='coerce')
combined_df['dollars'] = combined_df['dollars'].str.replace('$','')
combined_df['dollars'] = pd.to_numeric(combined_df['dollars'], errors='coerce')

combined_df.to_csv('combined.csv', index=False)

ICP_NUMBER = '0084942401PC5B0'
df = combined_df.copy()

df['ICP_NUMBER'] = ICP_NUMBER
df['ESIID'] = df['ICP_NUMBER']
df['USAGE_DATE'] = df['YYYYMMDD']
df['REVISION_DATE'] = datetime.date.today().strftime('%Y-%m-%d')
df['USAGE_START_TIME'] = df['datetime'].dt.strftime('%H:%M')
df['USAGE_END_TIME'] = (df['datetime']+ pd.Timedelta(hours=1)).dt.strftime('%H:%M')
df['USAGE_KWH'] = df['usage']
df['ESTIMATED_ACTUAL'] = 'A'
df['CONSUMPTION_SURPLUSGENERATION'] = 'Consumption'
df['CATEGORY'] = df['d_time1']

drop_columns = ['ICP_NUMBER','date', 'date1', 'datetime', 'YYYYMMDD', 'Weekday', 'Month', 'Year', 'd_time', 'd_time1', 'units','dollars', 'usage','type']
df.drop(columns=drop_columns, inplace=True)

df.to_csv('IntervalData.csv', index=False)
print(df)

import plotly.graph_objects as go
import pandas as pd

df = combined_df.copy()
df['Category'] = df['d_time1']

# Create a bar chart
# Aggregate to monthly totals
df_monthly = df.groupby(['Month', 'Category'])['usage'].mean().reset_index()

ordered_months = ["January", "February", "March", "April", "May", "June",
      "July", "August", "September", "October", "November", "December"]

# sorting data accoring to ordered_months
df_monthly['to_sort']=df_monthly['Month'].apply(lambda x:ordered_months.index(x))
df_monthly = df_monthly.sort_values('to_sort')

ordered_dayparts = ["Atapo", "Breakfast", "Ata", "Ahiahi", "Dinner", "Po"]

fig = go.Figure()
for category in ordered_dayparts:
    df_category = df_monthly[df_monthly['Category'] == category]
    fig.add_trace(go.Bar(x=df_category['Month'], y=df_category['usage'], name=category))

fig.update_layout(
    title='Monthly Totals by Category',
    xaxis_title='Month',
    yaxis_title='Mean Value',
    barmode='group' # Display bars side by side
)

fig.show()