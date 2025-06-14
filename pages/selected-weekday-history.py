import dash
from dash import dcc
from dash import html, callback
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

# Use dark theme
pio.templates.default = "plotly_dark"

# --- 1. Load and Process Both Data Files ---
# Assuming 'gas_usage.parquet' and 'electricity_usage.parquet' exist in the same directory
try:
    gas_df = pd.read_parquet("gas_usage.parquet")
except FileNotFoundError:
    print("Error: 'gas_usage.parquet' not found. Please ensure it's in the same directory.")
    # Create a dummy dataframe for testing if file is missing
    from datetime import datetime, timedelta
    data = []
    start_date = datetime.now() - timedelta(days=5*30) # 5 months ago
    for i in range(5*30*24): # 5 months of hourly data
        current_datetime = start_date + timedelta(hours=i)
        data.append({
            'index': current_datetime.timestamp() * 1000, # ms since epoch
            'usage': i % 100 + 10, # Ensure non-zero usage
            'dollars': ((i % 100) + 10) * 0.15 # Ensure non-zero dollars
        })
    gas_df = pd.DataFrame(data)

try:
    elec_df = pd.read_parquet("electricity_usage.parquet")
except FileNotFoundError:
    print("Error: 'electricity_usage.parquet' not found. Please ensure it's in the same directory.")
    # Create a dummy dataframe for testing if file is missing
    from datetime import datetime, timedelta
    data = []
    start_date = datetime.now() - timedelta(days=5*30) # 5 months ago
    for i in range(5*30*24): # 5 months of hourly data
        current_datetime = start_date + timedelta(hours=i)
        data.append({
            'index': current_datetime.timestamp() * 1000, # ms since epoch
            'usage': (i % 120) + 5, # Ensure non-zero usage
            'dollars': ((i % 120) + 5) * 0.25 # Ensure non-zero dollars
        })
    elec_df = pd.DataFrame(data)


def process_df(df_input):
    df_output = df_input.copy()
    df_output["timestamp"] = pd.to_datetime(df_output["index"], unit="ms")
    df_output['weekday'] = df_output['timestamp'].dt.day_name()
    df_output["hour"] = df_output["timestamp"].dt.hour
    df_output['date'] = df_output['timestamp'].dt.date
    return df_output

processed_dfs = {
    'gas': process_df(gas_df),
    'electricity': process_df(elec_df)
}

# print("Processed Gas DataFrame Head:")
# print(processed_dfs['gas'].head())
# print("\nProcessed Electricity DataFrame Head:")
# print(processed_dfs['electricity'].head())


# app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
# app.title = "Profiling daily energy usage by weekday"

dash.register_page(__name__)

# --- App Layout ---
layout = html.Div([
    html.H3("Hourly Energy Data by Weekday", className="text-center my-4"),
    html.Div([
        dbc.Row([
            dbc.Col([
                html.Label("Select Data Source:"),
                dcc.Dropdown(
                    id='data-source-selector',
                    options=[
                        {'label': 'Gas', 'value': 'gas'},
                        {'label': 'Electricity', 'value': 'electricity'}
                    ],
                    value='gas',
                    style={"width": "70%", "color": "black"}  # override dark theme
                ),
        ], width=4),
            # --- NEW: Add Metric Selector ---           
            dbc.Col([
                html.Label("Select Metric:"),
                dcc.Dropdown(
                    id='metric-selector',
                    options=[
                        {'label': 'Usage', 'value': 'usage'},
                        {'label': 'Dollars', 'value': 'dollars'}
                    ],
                    value='usage',
                    style={"width": "70%", "color": "black"}  # override dark theme
                ),
            ], width=4),
            dbc.Col([      
                html.Label("Select Weekday:"),
                dcc.Dropdown(
                    id='weekday-selector',
                    options=[{'label': i, 'value': i} for i in processed_dfs['gas']['weekday'].unique()],
                    value='Sunday',
                    style={"width": "70%", "color": "black"}  # override dark theme
                ),
            ], width=4),
        ]),
    ]),
    html.Div(id='graph-container')
])

# --- Callbacks ---

# Callback to update weekday dropdown options based on selected data source
@callback(
    Output('weekday-selector', 'options'),
    [Input('data-source-selector', 'value')]
)
def set_weekday_options(selected_source):
    df_to_use = processed_dfs[selected_source]
    # Ensure options are sorted for better UI
    return [{'label': i, 'value': i} for i in sorted(df_to_use['weekday'].unique(),
                                                    key=lambda x: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].index(x))]

# Main callback to update graphs
@callback(
    Output('graph-container', 'children'),
    [Input('data-source-selector', 'value'),
     Input('metric-selector', 'value'),
     Input('weekday-selector', 'value')]
)
def update_graphs(selected_source, selected_metric, selected_weekday):
    df_to_plot = processed_dfs[selected_source]

    filtered_df = df_to_plot[df_to_plot['weekday'] == selected_weekday].copy()

    # --- NEW: Calculate the global maximum for the selected metric and weekday ---
    # Check if filtered_df is empty to avoid error on .max()
    if filtered_df.empty or selected_metric not in filtered_df.columns:
        return html.Div(f"No data available for {selected_weekday} with {selected_metric} in {selected_source} file.")

    # Find the maximum value across all hours for the selected metric on the chosen weekday
    # (across all historical occurrences of that weekday)
    global_max_y = filtered_df[selected_metric].max()

    # Add a small buffer for better visualization (e.g., 5-10% more than max)
    ymax_with_buffer = global_max_y * 1.10
    if ymax_with_buffer == 0: # Avoid division by zero or range [0,0] if all values are zero
        ymax_with_buffer = 1 # Set a small default if max is 0

    last_six_dates = sorted(filtered_df['date'].unique(), reverse=True)[:6]

    graphs = []
    if not last_six_dates:
        return html.Div(f"No recent data found for {selected_weekday} in {selected_source}.")

    for date in last_six_dates:
        day_df = filtered_df[filtered_df['date'] == date]

        if selected_metric not in day_df.columns:
            return html.Div(f"Error: Column '{selected_metric}' not found in data for {selected_source}.")

        fig = go.Figure(
            data=[go.Bar(x=day_df['hour'], y=day_df[selected_metric])],
            layout=go.Layout(
                title=f"{selected_source.capitalize()} {selected_metric.capitalize()} on {date} ({selected_weekday})",
                xaxis={'title': 'Hour of Day', 'dtick': 1}, # dtick=1 ensures all hours are shown
                yaxis={'title': selected_metric.capitalize(), 'range': [0, ymax_with_buffer]} # Apply the calculated ymax
            )
        )
        graphs.append(
            html.Div(
                dcc.Graph(figure=fig),
                style={'width': '100%', 'display': 'inline-block'}
            )
        )
    return graphs
