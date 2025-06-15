import pandas as pd
import numpy as np
import dash
from dash import dcc, html, Input, Output, State, ctx, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go # Import graph_objects for more control
import plotly.io as pio

# Use dark theme
pio.templates.default = "plotly_dark"

# Load your data
# IMPORTANT: Ensure 'electricity_usage.parquet' is in the same directory as your script,
# or provide the full path.
try:
    df = pd.read_parquet("gas_usage.parquet")
except FileNotFoundError:
    print("Error: 'gas_usage.parquet' not found.")
    print("Please make sure the file is in the correct directory or provide the full path.")
    print("Generating dummy data for demonstration.")
    # Create dummy data if the file is not found
    np.random.seed(42)
    dates = pd.to_datetime(pd.date_range(start='2024-01-01', end='2025-03-31', freq='H'))
    df = pd.DataFrame({
        "index": dates.astype(np.int64) // 10**6, # Convert to milliseconds for 'index'
        "date": dates.strftime("%I:%M%p %dth %B %Y"),
        "usage": np.random.rand(len(dates)) * 2 + 0.1,  # Random usage between 0.1 and 2.1
        "dollars": np.random.rand(len(dates)) * 0.5 + 0.05,  # Random dollars between 0.05 and 0.55
        "type": "actual",
        "date1": dates.strftime("%I:%M%p %d %B %Y"),
        "YYYYMMDD": dates.strftime("%Y-%m-%d"),
        "Weekday": dates.strftime("%A"),
        "Month": dates.strftime("%B"),
        "Year": dates.strftime("%Y").astype(int),
        "d_time": "Atapo",
        "d_time1": "Atapo",
        "units": "kWh"
    })


# --- Data Preprocessing ---
df["timestamp"] = pd.to_datetime(df["index"], unit="ms")
df["date_only"] = pd.to_datetime(df["YYYYMMDD"])
df["hour"] = df["timestamp"].dt.hour
df["day"] = df["timestamp"].dt.day
df["month_num"] = df["timestamp"].dt.month
df["month_name"] = df["timestamp"].dt.strftime("%B")
df["year"] = df["timestamp"].dt.year

max_usage = df["usage"].max()

# Calculate max daily usage
daily_summary = df.groupby('date_only').agg(
                usage=('usage', 'sum'),
                dollars=('dollars', 'sum')
            ).reset_index()

max_daily_usage = daily_summary['usage'].max()

# Define the order of months for consistent plotting
month_order = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
]
df['month_name'] = pd.Categorical(df['month_name'], categories=month_order, ordered=True)

# Create a mapping for month names to numbers for date construction
month_num_map = {name: i + 1 for i, name in enumerate(month_order)}

# The billing periods are roughtly aligned with Māori months, so we can use Māori month names for the dashboard
# Define the order of monthsin Māori for consistent plotting
maori_month_order = [
    'Kohi-tātea', 'Hui-tanguru', 'Poutū-te-rangi', 'Paenga-whāwhā',
    'Haratua', 'Pipiri', 'Hōngoingoi', 'Here-turi-kōkā',
    'Mahuru', 'Whiringa-ā-nuku', 'Whiringa-ā-rangi', 'Hakihea'
]
# Create a mapping for Māori month names to numbers for date construction
maori_month_num_map = {name: i + 1 for i, name in enumerate(maori_month_order)}


# Create the app
# app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
# app.title = "Gas Usage Dashboard"
dash.register_page(__name__)

# --- App Layout ---
layout = dbc.Container([
    html.H3("Gas Usage & Cost", className="text-center my-4"),

    dbc.Tabs(id="gas-tabs", active_tab='gas-monthly-tab', children=[
        dbc.Tab(label='Monthly View', tab_id='gas-monthly-tab'),
        dbc.Tab(label='Daily View', tab_id='gas-daily-tab'),
        dbc.Tab(label='Hourly View', tab_id='gas-hourly-tab'),
    ]),
    
    dbc.Row([
        dbc.Col(dcc.Graph(id='gas-usage-graph', config={'displayModeBar': False}))
    ]),

    dbc.Row(id='gas-day-nav', className="my-3 justify-content-center", style={'display': 'none'}, children=[
        dbc.Col(dbc.Button('← Previous Day', id='gas-prev-day', n_clicks=0, color="secondary"), width="auto"),
        dbc.Col(dbc.Button('Next Day →', id='gas-next-day', n_clicks=0, color="secondary"), width="auto")
    ]),
    
    dbc.Row(id='gas-cards', className="my-4 justify-content-center"),
    
    # Store drill-down state
    dcc.Store(id='gas-selected-year-store', data={}),
    dcc.Store(id='gas-selected-month-store', data={}),
    dcc.Store(id='gas-selected-date-store', data={})
])

# --- Callbacks ---

# Callback to update graph, cards, and day navigation based on tab and selected filters
@callback(
    Output('gas-usage-graph', 'figure'),
    Output('gas-cards', 'children'),
    Output('gas-day-nav', 'style'),
    Output('gas-tabs', 'active_tab'), # To programmatically change tabs
    Input('gas-tabs', 'active_tab'),
    Input('gas-selected-year-store', 'data'),
    Input('gas-selected-month-store', 'data'),
    Input('gas-selected-date-store', 'data')
)
def update_graph(active_tab, selected_year_data, selected_month_data, selected_date_data):
    # Initialize variables
    fig = go.Figure()
    cards_content = []
    nav_style = {'display': 'none'}
    
    # Extract values from dcc.Store
    selected_year = selected_year_data.get('year') if selected_year_data else 2025
    selected_month = selected_month_data.get('month') if selected_month_data else None
    selected_date = pd.to_datetime(selected_date_data.get('date')) if selected_date_data and selected_date_data.get('date') else None

    current_df = df.copy()
    graph_title = ""
    total_usage = 0
    total_dollars = 0

    # --- Monthly View ---
    if active_tab == 'gas-monthly-tab':
        graph_title = f"{selected_year}" # Title change
        
        # Aggregate monthly totals, ensuring all months are present
        monthly_summary = current_df.groupby(['year', 'month_name']).agg(
            usage=('usage', 'sum'),
            dollars=('dollars', 'sum')
        ).reset_index()

        # Create a full DataFrame with all years and months for consistent display
        all_years = sorted(df['year'].unique())
        full_index_data = []
        for year in all_years:
            for month in month_order:
                full_index_data.append({'year': year, 'month_name': month})
        
        full_df = pd.DataFrame(full_index_data)
        monthly_summary_full = pd.merge(full_df, monthly_summary, 
                                        on=['year', 'month_name'], how='left').fillna(0)
        # Ensure month_name categorical order is applied after merge/fillna
        monthly_summary_full['month_name'] = pd.Categorical(
            monthly_summary_full['month_name'], categories=month_order, ordered=True
        )
        monthly_summary_full = monthly_summary_full.sort_values(by=['year', 'month_name'])

        # Create the bar chart
        fig = go.Figure(data=[
            go.Bar(name='Usage (kWh)', x=monthly_summary_full['month_name'], y=monthly_summary_full['usage'],
                marker_color='darkgrey', legendgroup='1',
                hovertemplate='<b>Month:</b> %{x}<br><b>Usage:</b> %{y:.2f} kWh<extra></extra>',
                # IMPORTANT CHANGE HERE: customdata is now a list [year, month_name] for each point
                customdata=monthly_summary_full[['year', 'month_name']].values.tolist()
                ),

        ])
        fig.update_layout(barmode='group', 
                            title={
                                  'text': graph_title,
                                  'y':0.9,
                                  'x':0.5,
                                  'xanchor': 'center',
                                  'yanchor': 'top'},
                            title_font=dict(family="Arial", size=30, weight="bold"),
                            xaxis_title="Month", 
                            yaxis_title="Total (kWh)", 
                            legend_title="Metric",
                            clickmode='event+select')

        total_usage = df['usage'].sum()
        total_dollars = df['dollars'].sum()

    # --- Daily View ---
    elif active_tab == 'gas-daily-tab':
        # Need both year and month for a full month range
        if selected_year and selected_month:
            current_df = df[(df['year'] == selected_year) & (df['month_name'] == selected_month)]
            graph_title = f"{selected_month} {selected_year}" # Title change

            daily_summary = current_df.groupby('date_only').agg(
                usage=('usage', 'sum'),
                dollars=('dollars', 'sum')
            ).reset_index()

            # Create a full date range for the selected month and year
            selected_month_num = month_num_map.get(selected_month)
            if selected_month_num is None: # Fallback if month name is not recognized
                fig = px.bar(title="Invalid month selected for daily totals.")
                fig.update_layout(xaxis={'visible': False}, yaxis={'visible': False})
                return fig, [], {'display': 'none'}, dash.no_update

            start_of_month = pd.Timestamp(year=selected_year, month=selected_month_num, day=1)
            end_of_month = (start_of_month + pd.DateOffset(months=1)) - pd.Timedelta(days=1)
            full_date_range = pd.date_range(start=start_of_month, end=end_of_month, freq='D')

            # Create a DataFrame from the full date range for merging
            full_days_df = pd.DataFrame({'date_only': full_date_range})

            # Merge the daily summary onto the full date range and fill NaN usage with 0
            daily_summary_full = pd.merge(full_days_df, daily_summary,
                                          on='date_only', how='left').fillna({'usage': 0})

            # Sort by date
            daily_summary_full = daily_summary_full.sort_values(by='date_only')

            # Create the bar chart - ONLY USAGE
            fig = go.Figure(data=[
                go.Bar(name='Usage (kWh)', x=daily_summary_full['date_only'], y=daily_summary_full['usage'],
                       marker_color='darkgrey', legendgroup='1',
                       hovertemplate='<b>Date:</b> %{x|%Y-%m-%d}<br><b>Usage:</b> %{y:.2f} kWh<extra></extra>')
            ])
            fig.update_layout(barmode='group', 
                                title={
                                  'text': graph_title,
                                  'y':0.9,
                                  'x':0.5,
                                  'xanchor': 'center',
                                  'yanchor': 'top'},
                              title_font=dict(family="Arial", size=30, weight="bold"),
                              xaxis_title="Date", 
                              yaxis_title="Total (kWh)", 
                              yaxis_range=[0, max_daily_usage], 
                              legend_title="Metric")
            
            total_usage = daily_summary['usage'].sum()
            total_dollars = daily_summary['dollars'].sum()
            # print(daily_summary.head())  # Debugging line to check daily_summary content
        else:
            # If no year is selected for daily view, show an empty graph
            fig = px.bar(title="Please select a year from the 'Monthly View' to see daily totals.")
            fig.update_layout(xaxis={'visible': False}, yaxis={'visible': False})
            return fig, [], {'display': 'none'}, active_tab # Stay on current tab if no year

    # --- Hourly View ---
    elif active_tab == 'gas-hourly-tab':
        if selected_date:
            current_df = df[df['date_only'] == selected_date]
            graph_title = f"{selected_date.strftime('%A')} {selected_date.strftime('%d %b %Y')}"

            hourly_summary = current_df.groupby('hour').agg(
                usage=('usage', 'sum'),
                dollars=('dollars', 'sum')
            ).reset_index().sort_values(by='hour')
            
            # Ensure all 24 hours are present
            all_hours = pd.DataFrame({'hour': range(24)})
            hourly_summary_full = pd.merge(all_hours, hourly_summary, on='hour', how='left').fillna(0)


            fig = go.Figure(data=[
                go.Bar(name='Usage (kWh)', x=hourly_summary_full['hour'], y=hourly_summary_full['usage'],
                       marker_color='darkgrey', legendgroup='1',
                       hovertemplate='<b>Hour:</b> %{x}:00<br><b>Usage:</b> %{y:.2f} kWh<extra></extra>'),
                # go.Bar(name='Cost ($)', x=hourly_summary_full['hour'], y=hourly_summary_full['dollars'],
                #        marker_color='lightcoral', legendgroup='1',
                #        hovertemplate='<b>Hour:</b> %{x}:00<br><b>Cost:</b> $%{y:.2f}<extra></extra>')
            ])
            fig.update_layout(barmode='group', 
                              title={
                                  'text': graph_title,
                                  'y':0.9,
                                  'x':0.5,
                                  'xanchor': 'center',
                                  'yanchor': 'top'},
                              title_font=dict(family="Arial", size=30, weight="bold"),
                              xaxis_title="Hour of Day", 
                              yaxis_title="Total (kWh)", 
                              yaxis_range=[0, max_usage], 
                              legend_title="Metric")
            
            total_usage = hourly_summary['usage'].sum()
            total_dollars = hourly_summary['dollars'].sum()
            nav_style = {'display': 'flex', 'justifyContent': 'center', 'gap': '10px', 'margin': '20px'}
        else:
            # If no date is selected for hourly view, show an empty graph
            fig = px.bar(title="Please select a day from the 'Daily View' to see hourly totals.")
            fig.update_layout(xaxis={'visible': False}, yaxis={'visible': False})
            return fig, [], {'display': 'none'}, active_tab # Stay on current tab if no date

    # Update cards
    cards_content = [
        dbc.Col([
            dbc.Card(
                dbc.CardBody([
                    html.H6("Total Usage", className="card-title"),
                    html.P(f"{total_usage:.2f} kWh", className="card-text fs-4"),
                ]),
                color="primary", outline=True, className="text-center mx-2"
            )]),
        dbc.Col([
            dbc.Card(
                dbc.CardBody([
                    html.H6(f"Summary for {graph_title}", className="card-title"),
                    html.P(f"${total_dollars:.2f} NZD", className="card-text fs-4")
                ]),
                color="info", outline=True, className="text-center mx-2"
            )
        ]),    
    ]
    
    return fig, cards_content, nav_style, active_tab

# Callback to handle bar clicks for drilldown and day navigation
# In the drilldown callback:
@callback(
    Output('gas-selected-year-store', 'data'),
    Output('gas-selected-month-store', 'data'),
    Output('gas-selected-date-store', 'data'),
    Output('gas-tabs', 'active_tab', allow_duplicate=True),
    Input('gas-usage-graph', 'clickData'),
    Input('gas-prev-day', 'n_clicks'),
    Input('gas-next-day', 'n_clicks'),
    State('gas-tabs', 'active_tab'),
    State('gas-selected-year-store', 'data'),
    State('gas-selected-month-store', 'data'),
    State('gas-selected-date-store', 'data'),
    prevent_initial_call=True
)
def drilldown(clickData, prev_clicks, next_clicks, active_tab,
              selected_year_data, selected_month_data, selected_date_data):

    trigger_id = ctx.triggered_id if ctx.triggered else None

    year_data = selected_year_data
    month_data = selected_month_data
    date_data = selected_date_data
    new_active_tab = active_tab

    # --- Handle Graph Clicks ---
    if trigger_id == 'gas-usage-graph' and clickData:
        point = clickData['points'][0]

        # ... inside drilldown, within the 'if active_tab == 'monthly-tab':' block ...

        if active_tab == 'gas-monthly-tab':
            # From Monthly to Daily
            # point['x'] will still be the month name (e.g., 'May')
            # Now, point['customdata'] will be the list [year, month_name] for the clicked bar

            clicked_customdata = point.get('customdata')

            if clicked_customdata is None or not isinstance(clicked_customdata, list) or len(clicked_customdata) < 1:
                # Add a more specific warning for debugging
                print(f"Warning: Clicked monthly bar for {point.get('x')} has missing or malformed customdata. Not drilling down.")
                print(f"Received customdata: {clicked_customdata}")
                return dash.no_update, dash.no_update, dash.no_update, dash.no_update

            # Now, extract the year from the customdata list (it's the first element)
            clicked_year = clicked_customdata[0]
            # clicked_month_from_customdata = clicked_customdata[1] # You could also get month from here, but point['x'] is already the month name

            # Ensure clicked_year is an integer
            year_data = {'year': int(clicked_year)}
            month_data = {'month': point['x']} # Use point['x'] as it's directly the clicked month name
            date_data = {} # Clear date selection
            new_active_tab = 'gas-daily-tab'

        elif active_tab == 'gas-daily-tab':
            # From Daily to Hourly
            clicked_date_str = point['x']
            date_data = {'date': clicked_date_str}
            new_active_tab = 'gas-hourly-tab'

    # --- Handle Day Navigation Buttons ---
    elif trigger_id in ['gas-prev-day', 'gas-next-day']:
        if date_data and date_data.get('date'):
            current_date = pd.to_datetime(date_data['date'])
            delta = -1 if trigger_id == 'prev-day' else 1
            new_date = (current_date + pd.Timedelta(days=delta)).strftime('%Y-%m-%d')
            date_data = {'date': new_date}
            new_active_tab = 'gas-hourly-tab' # Stay on the hourly tab

    return year_data, month_data, date_data, new_active_tab

