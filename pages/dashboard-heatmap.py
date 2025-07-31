import pandas as pd
import numpy as np
import dash
from dash import dcc, html, callback
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import calendar
from datetime import datetime, timedelta
import plotly.io as pio
from data_utils import (check_forecast_electricty_data,
                        get_bill_period_start_date)

# Set dark theme
pio.templates.default = "plotly_dark"
# app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY]) #COSMO, #CYBORG, #DARKLY
# server = app.server
# app.title = "Usage and heatmap dashboard"

dash.register_page(__name__)

# -------------------------
# Variables
# -------------------------
# bill_period_start = datetime.strptime("2025-07-13","%Y-%m-%d").date()  # Example bill period start date
bill_period_start = get_bill_period_start_date().date()

# -------------------------
# Load and process data
# -------------------------
df_elec = pd.read_parquet('electricity_usage.parquet')
df_elec['index'] = pd.to_datetime(df_elec['index'])
df_elec['USAGE_DATE'] = df_elec['index'].dt.date
df_elec['USAGE_START_TIME'] = df_elec['index'].dt.strftime('%H:%M')
df_elec['DAY'] = df_elec['index'].dt.day
df_elec['MONTH'] = df_elec['index'].dt.month
df_elec['YEAR'] = df_elec['index'].dt.year
df_elec['USAGE_KWH'] = df_elec['usage']
df_elec['USAGE_COST'] = df_elec['dollars']

df_gas = pd.read_parquet('gas_usage.parquet')
df_gas['index'] = pd.to_datetime(df_gas['index'])
df_gas['USAGE_DATE'] = df_gas['index'].dt.date
df_gas['USAGE_START_TIME'] = df_gas['index'].dt.strftime('%H:%M')
df_gas['DAY'] = df_gas['index'].dt.day
df_gas['MONTH'] = df_gas['index'].dt.month
df_gas['YEAR'] = df_gas['index'].dt.year
df_gas['USAGE_KWH'] = df_gas['usage']
df_gas['USAGE_COST'] = df_gas['dollars']

elec_daily_fixed_charge = 0.90 # 90 cents per day
gas_daily_fixed_charge = 1.5847 # 158.47 cents per day
gas_daily_fixed_charge = 1.96 # 8c per hour = 196 cents per day

forecast = check_forecast_electricty_data()
# Access the monthly forecast
monthly = forecast.get("monthly", {}).get("value")
weekly = forecast.get("weekly", {}).get("value")

# Create the categories
df_elec['Category'] = df_elec['USAGE_DATE'].apply(lambda x: 'Paid' if x < bill_period_start else 'To be billed')
df_gas['Category'] = df_gas['USAGE_DATE'].apply(lambda x: 'Paid' if x < bill_period_start else 'To be billed')
  

df_temp = pd.read_parquet('air_temperature.parquet')
df_temp['Time'] = pd.to_datetime(df_temp['Time'], unit='ms')
df_temp['DAY'] = df_temp['Time'].dt.day
df_temp['MONTH'] = df_temp['Time'].dt.month
df_temp['YEAR'] = df_temp['Time'].dt.year

df_events = pd.read_csv('data/usage-appliances.csv')
df_events = df_events[df_events['Appliance'] == "Dishwasher"]
df_events['Timestamp'] = pd.to_datetime(df_events['Timestamp'])

# Enrich events with runtime and kWh estimates
program_details = {
    "Pots / Pans": {"kWh": 1.35, "runtime": "2:15"},
    "Auto Gentle": {"kWh": 0.75, "runtime": "1:45"},
    "Pre-rinse": {"kWh": 1.1, "runtime": "1:00"},
    "Quick Wash and Dry": {"kWh": 0.85, "runtime": "0:45"},
    "Auto Wash": {"kWh": 1.15, "runtime": "2:30"},
    "Eco Wash": {"kWh": 0.6, "runtime": "3:15"},
    "Quick 1h": {"kWh": 1.15, "runtime": "1:05"},
    "Machine Care": {"kWh": 1.5, "runtime": "2:10"},
    "Short 60C": {"kWh": 1.05, "runtime": "1:29"},
}

df_events['kWh'] = df_events['Program'].map(lambda x: program_details.get(x, {"kWh": 1})['kWh'])
df_events['Runtime'] = df_events['Program'].map(lambda x: program_details.get(x, {"runtime": "1:30"})['runtime'])
df_events['Duration'] = pd.to_timedelta(df_events['Runtime'] + ':00')
df_events['StartTime'] = df_events['Timestamp'] - df_events['Duration']
df_events['Day'] = df_events['Timestamp'].dt.day
df_events['Month'] = df_events['Timestamp'].dt.month

# -------------------------
# Layout
# -------------------------
layout = dbc.Container([
    html.H3("Power & Gas Usage", className="text-center my-4"),

    dcc.Dropdown(
        id="slct_month",
        options=[{"label": calendar.month_name[i], "value": i} for i in range(1, 13)],
        value=datetime.now().month,
        style={"width": "40%", "color": "black"}  # override dark theme
    ),
    html.Br(),
    
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5("Electric Cost", className="card-title"),
                html.H3(id="total_cost", className="card-text")
            ])
        ], color="warning", inverse=True), md=2),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5("Gas Cost", className="card-title"),
                html.H3(id="gas_cost", className="card-text")
            ])
        ], color="secondary", inverse=True), md=2),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5("Bill to date", className="card-title"),
                html.H3(id="bill_to_date", className="card-text")
            ])
        ], color="primary", inverse=True), md=2),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5("Monthly Bill Forecast", className="card-title"),
                html.H3(id="monthly", className="card-text")
            ])
        ], color="success", inverse=True), md=2),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5("Weekly ⚡ Forecast", className="card-title"),
                html.H3(id="weekly", className="card-text")
            ])
        ], color="success", inverse=True), md=2),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5("Avg Daily Temp", className="card-title"),
                html.H3(id="avg_temp", className="card-text")
            ])
        ], color="info", inverse=True), md=2),
    ]),
    html.Br(),


    dbc.Row([
        dbc.Col(dcc.Graph(id="year_bar_fig"), md=12),
    ]),
    html.Br(),
    
    dbc.Row([
        dbc.Col(dcc.Graph(id="gas_year_bar_fig"), md=12),
    ]),
    html.Br(),
            
    dbc.Row([
        dbc.Col(dcc.Graph(id="heatmap_fig"), md=6),
        dbc.Col(dcc.Graph(id="bar_fig"), md=6)
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id="gas_heatmap_fig"), md=6),
        dbc.Col(dcc.Graph(id="gas_bar_fig"), md=6)
    ]),
    
    dbc.Row([
        dbc.Col(dcc.Graph(id="temp_fig"), md=6),
        dbc.Col(dcc.Graph(id="elec_gas_bar_fig"), md=6)
    ]) # , 
    # html.Br(),
    # dash.html.Iframe(
    #     src="https://embed.windy.com/embed.html?type=map&location=coordinates&metricRain=mm&metricTemp=°C&metricWind=km/h&zoom=9&overlay=wind&product=ecmwf&level=surface&lat=-39.37&lon=174.298",  # Replace with your Windy embed URL
    #     style={'width': '80%', 'height': '450px'}
    # )
], fluid=True)

# -------------------------
# Callback
# -------------------------
@callback(
    Output("monthly", "children"),
    Output("weekly", "children"),
    Output("total_cost", "children"),
#    Output("total_kwh", "children"),
    Output("gas_cost", "children"),
#    Output("gas_kwh", "children"),
    Output("avg_temp", "children"),
    Output("bill_to_date", "children"),
#    Output("dish_count", "children"),
    Output("year_bar_fig", "figure"),
    Output("gas_year_bar_fig", "figure"),
    Output("heatmap_fig", "figure"),
    Output("bar_fig", "figure"),
    Output("gas_heatmap_fig", "figure"),
    Output("gas_bar_fig", "figure"),
    Output("temp_fig", "figure"),
    Output("elec_gas_bar_fig", "figure"),
    Input("slct_month", "value")
)

def update_dashboard(selected_month):
    # Filter
    dfm_elec = df_elec[df_elec["MONTH"] == selected_month]
    dfm_gas = df_gas[df_gas["MONTH"] == selected_month]
    dfm_temp = df_temp[df_temp["MONTH"] == selected_month]
    dfm_events = df_events[df_events["Month"] == selected_month]
    
    year = datetime.now().year
    
    elec_daily = df_elec.groupby(['USAGE_DATE','Category'])['USAGE_KWH'].sum().reset_index()
    gas_daily = df_gas.groupby(['USAGE_DATE','Category'])['USAGE_KWH'].sum().reset_index()
        
    first_day = datetime(year, 1, 1)
    last_day = datetime(year, 12, calendar.monthrange(year, selected_month)[1])
    
    # elec_last_P7D = dfm_elec['USAGE_DATE'].max() - timedelta(days=7)
    # elec_last_P14D = dfm_elec['USAGE_DATE'].max() - timedelta(days=14)

    # elec_usage_last_7_days = dfm_elec[dfm_elec['USAGE_DATE'] >= elec_last_P7D]['USAGE_KWH'].sum()
    # elec_usage_prior_7_days = dfm_elec[dfm_elec['USAGE_DATE'] >= elec_last_P14D]['USAGE_KWH'].sum() - elec_usage_last_7_days

    year_bar_fig = go.Figure(go.Bar(
        x=elec_daily[elec_daily['Category'] == 'Paid']['USAGE_DATE'], 
        y=elec_daily[elec_daily['Category'] == 'Paid']['USAGE_KWH'],
        marker_color='orange',
    ))
    
    # Add bars for "To be billed" category
    year_bar_fig.add_trace(go.Bar(
        x=elec_daily[elec_daily['Category'] == 'To be billed']['USAGE_DATE'], 
        y=elec_daily[elec_daily['Category'] == 'To be billed']['USAGE_KWH'],
        marker_color='navajowhite',
    ))
    
    year_bar_fig.update_layout(
        yaxis_title='kWh',
        yaxis=dict(rangemode="tozero"),
        xaxis=dict(range=[first_day, last_day]),
        height=100,
        margin=dict(t=0, b=0),
        showlegend=False
    )

    gas_year_bar_fig = go.Figure(go.Bar(
        x=gas_daily[gas_daily['Category'] == 'Paid']['USAGE_DATE'], 
        y=gas_daily[gas_daily['Category'] == 'Paid']['USAGE_KWH'],
        marker_color='darkgrey',
    ))

    # Add bars for "To be billed" category
    gas_year_bar_fig.add_trace(go.Bar(
        x=gas_daily[gas_daily['Category'] == 'To be billed']['USAGE_DATE'], 
        y=gas_daily[gas_daily['Category'] == 'To be billed']['USAGE_KWH'],
        marker_color='white',
    ))

    gas_year_bar_fig.update_layout(
        yaxis_title='kWh',
        yaxis=dict(rangemode="tozero"),
        xaxis=dict(range=[first_day, last_day]),
        height=100,
        margin=dict(t=0, b=0),
        showlegend=False
    )
    
    first_day = datetime(year, selected_month, 1)
    last_day = datetime(year, selected_month, calendar.monthrange(year, selected_month)[1])

    # Big numbers
    total_cost = round(dfm_elec["USAGE_COST"].sum(), 1)
    total_kwh = round(dfm_elec["USAGE_KWH"].sum(), 1)
    gas_cost = round(dfm_gas["USAGE_COST"].sum(), 1)
    gas_kwh = round(dfm_gas["USAGE_KWH"].sum(), 1)
    
    # To be billed amounts
    elec_to_be_billed_kwh = round(dfm_elec[dfm_elec['USAGE_DATE'] >= bill_period_start]["USAGE_KWH"].sum(), 1)
    elec_to_be_billed_cost = round(dfm_elec[dfm_elec['USAGE_DATE'] >= bill_period_start]["USAGE_COST"].sum(), 1)
    gas_to_be_billed_kwh = round(dfm_gas[dfm_gas['USAGE_DATE'] >= bill_period_start]["USAGE_KWH"].sum(), 1)
    gas_to_be_billed_cost = round(dfm_gas[dfm_gas['USAGE_DATE'] >= bill_period_start]["USAGE_COST"].sum(), 1)
    # print(f"Electricity to be billed: {elec_to_be_billed_kwh} kWh, ${elec_to_be_billed_cost}")
    # print(f"Gas to be billed: {gas_to_be_billed_kwh} kWh, ${gas_to_be_billed_cost}")
    if elec_to_be_billed_kwh > 0:
        total_cost = elec_to_be_billed_cost
        total_kwh = elec_to_be_billed_kwh
    if gas_to_be_billed_kwh > 0:
        gas_cost = gas_to_be_billed_cost
        gas_kwh = gas_to_be_billed_kwh



    if 'Time' in dfm_temp.columns:
        avg_temp = round(dfm_temp.resample('D', on='Time')['Value'].mean().mean(), 1)
    else:
        avg_temp = round(dfm_temp.resample('D')['Value'].mean().mean(), 1)

    dish_count = len(dfm_events)

    # Heatmap
    hourly = dfm_elec.groupby(['DAY', 'USAGE_START_TIME'])['USAGE_KWH'].mean().reset_index()
    heatmap_data = hourly.pivot(index='USAGE_START_TIME', columns='DAY', values='USAGE_KWH')
    heatmap_fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values, zmin=0, zmax=2.5,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale='hot', #'YlOrRd_r', # 'Viridis'
    ))
    
    # Overlay event markers
    # Align to heatmap y-axis
    dfm_events['Heatmap_Time'] = dfm_events['Timestamp'].dt.floor('60min').dt.strftime('%H:%M')

    heatmap_fig.add_trace(go.Scatter(
        x=dfm_events['Day'],
        y=dfm_events['Heatmap_Time'],
        mode='markers',
        marker=dict(color='white', size=8, symbol='x'),
        name='Dishwasher Finish',
        hovertext=dfm_events.apply(lambda row: f"{row['Timestamp'].strftime('%Y-%m-%d %H:%M')}<br>Program: {row['Program']}<br>kWh: {row['kWh']}", axis=1),
        hoverinfo='text',
        showlegend=False
    ))
    
    heatmap_fig.update_layout(
        title='Hourly Electricity Usage',
        xaxis=dict(range=[1, calendar.monthrange(year, selected_month)[1]], dtick=1)
    )

    # Bar chart for Select Month - Daily Totals
    elec_daily = dfm_elec.groupby(['USAGE_DATE','Category'])['USAGE_KWH'].sum().reset_index()
    elec_daily = dfm_elec.groupby(['USAGE_DATE','Category'])['USAGE_COST'].sum().reset_index()
    elec_daily['FIXED_CHARGE'] = elec_daily_fixed_charge
    elec_daily['ELEC_COST'] = elec_daily['USAGE_COST'] - elec_daily['FIXED_CHARGE']  # Subtract fixed charge to daily cost
    
    bar_fig = go.Figure(go.Bar(
        x=elec_daily[elec_daily['Category'] == 'Paid']['USAGE_DATE'], 
        y=elec_daily[elec_daily['Category'] == 'Paid']['FIXED_CHARGE'],
        marker_color='khaki',  # Use a different color for the fixed charge

    ))

    bar_fig.add_trace(go.Bar(
        x=elec_daily[elec_daily['Category'] == 'Paid']['USAGE_DATE'], 
        y=elec_daily[elec_daily['Category'] == 'Paid']['ELEC_COST'],
        marker_color='orange',
        text=elec_daily[elec_daily['Category'] == 'Paid']['USAGE_COST'].apply(lambda x: f"${x:.2f}" if x > 0 else "")

    ))

    # Add bars for "To be billed" category
    
    bar_fig.add_trace(go.Bar(
        x=elec_daily[elec_daily['Category'] == 'To be billed']['USAGE_DATE'], 
        y=elec_daily[elec_daily['Category'] == 'To be billed']['FIXED_CHARGE'],
        marker_color='lightgoldenrodyellow',  # Use a different color for the fixed charge

    ))
    
    bar_fig.add_trace(go.Bar(
        x=elec_daily[elec_daily['Category'] == 'To be billed']['USAGE_DATE'], 
        y=elec_daily[elec_daily['Category'] == 'To be billed']['ELEC_COST'],
        marker_color='navajowhite',
        text=elec_daily[elec_daily['Category'] == 'To be billed']['USAGE_COST'].apply(lambda x: f"${x:.2f}" if x > 0 else "")
    ))
    
    bar_fig.update_layout(
        barmode='stack',
        title='Daily Electricity Cost', 
        xaxis_title='Date', 
        yaxis_title='$',
        yaxis=dict(rangemode="tozero"),
        xaxis=dict(range=[first_day, last_day]),
        showlegend=False
    )


    # Gas Heatmap
    gas_hourly = dfm_gas.groupby(['DAY', 'USAGE_START_TIME'])['USAGE_KWH'].mean().reset_index()
    gas_heatmap_data = gas_hourly.pivot(index='USAGE_START_TIME', columns='DAY', values='USAGE_KWH')
    gas_heatmap_fig = go.Figure(data=go.Heatmap(
        z=gas_heatmap_data.values,zmin=0, zmax=10,
        x=gas_heatmap_data.columns,
        y=gas_heatmap_data.index,
        colorscale='Viridis'
    ))
    
    gas_heatmap_fig.update_layout(
        title='Hourly Gas Usage',
        xaxis=dict(range=[1, calendar.monthrange(year, selected_month)[1]], dtick=1)
    )

    # Bar chart
    gas_daily = dfm_gas.groupby(['USAGE_DATE','Category'])['USAGE_KWH'].sum().reset_index()
    gas_daily = dfm_gas.groupby(['USAGE_DATE','Category'])['USAGE_COST'].sum().reset_index()
    gas_daily['FIXED_CHARGE'] = gas_daily_fixed_charge
    gas_daily['GAS_COST'] = gas_daily['USAGE_COST'] - gas_daily['FIXED_CHARGE']  # Subtract fixed charge to daily cost
    elec_daily['ENERGY_COST'] = elec_daily['USAGE_COST'] + gas_daily['USAGE_COST']  # Total cost for both energy sources
    
    bill_to_date = elec_daily[elec_daily['Category'] == 'To be billed']['USAGE_COST'].sum() + gas_daily[gas_daily['Category'] == 'To be billed']['USAGE_COST'].sum()
        
    
    gas_bar_fig = go.Figure(go.Bar(
        x=gas_daily[gas_daily['Category'] == 'Paid']['USAGE_DATE'], 
        y=gas_daily[gas_daily['Category'] == 'Paid']['FIXED_CHARGE'],
        marker_color='khaki',  # Use a different color for the fixed charge

    ))

    gas_bar_fig.add_trace(go.Bar(
        x=gas_daily[gas_daily['Category'] == 'Paid']['USAGE_DATE'], 
        y=gas_daily[gas_daily['Category'] == 'Paid']['GAS_COST'],
        marker_color='darkgrey',
        text=gas_daily[gas_daily['Category'] == 'Paid']['USAGE_COST'].apply(lambda x: f"${x:.2f}" if x > 0 else "")

    ))

    # Add bars for "To be billed" category
    
    gas_bar_fig.add_trace(go.Bar(
        x=gas_daily[gas_daily['Category'] == 'To be billed']['USAGE_DATE'], 
        y=gas_daily[gas_daily['Category'] == 'To be billed']['FIXED_CHARGE'],
        marker_color='lightgoldenrodyellow',  # Use a different color for the fixed charge

    ))
    
    gas_bar_fig.add_trace(go.Bar(
        x=gas_daily[gas_daily['Category'] == 'To be billed']['USAGE_DATE'], 
        y=gas_daily[gas_daily['Category'] == 'To be billed']['GAS_COST'],
        marker_color='white',
        text=gas_daily[gas_daily['Category'] == 'To be billed']['USAGE_COST'].apply(lambda x: f"${x:.2f}" if x > 0 else "")
    ))
    
    gas_bar_fig.update_layout(
        barmode='stack',
        title='Daily Gas Cost', 
        xaxis_title='Date', 
        yaxis_title='$',
        yaxis=dict(rangemode="tozero"),
        xaxis=dict(range=[first_day, last_day]),
        showlegend=False
    )


    # Temperature
    temp_fig = go.Figure()
    temp_fig.add_trace(go.Scatter(
        x=dfm_temp['Time'], 
        y=dfm_temp['Value'], 
        mode='lines', 
        name='10-min Temp',
        line=dict(color='white', width=1)
    ))
    
        # Daily means
    dff_temp_copy = dfm_temp.copy()
    dff_temp_copy.set_index('Time', inplace=True)
    daily_means = dff_temp_copy['Value'].resample('D').mean().dropna().reset_index()

    temp_fig.add_trace(go.Bar(
        x=daily_means['Time'],
        y=daily_means['Value'],
        name='Daily Mean Temperature',
        marker=dict(color='green')
    ))
    
    temp_fig.update_layout(
        title='Air Temperature (10-min)', 
        xaxis_title='Time', 
        yaxis_title='°C',
        xaxis=dict(range=[first_day, last_day]),
        showlegend=False,
    )

    # Dishwasher event timeline
    timeline_fig = go.Figure()
    for _, row in dfm_events.iterrows():
        timeline_fig.add_trace(go.Scatter(
            x=[row['StartTime'], row['Timestamp']],
            y=[row['Program']]*2,
            mode='lines+markers',
            name=row['Program'],
            line=dict(width=4),
            hovertext=f"{row['Program']}, {row['kWh']} kWh",
            showlegend=False
        ))
    timeline_fig.update_layout(
        title='Dishwasher Program Timeline', 
        xaxis_title='Time', 
        yaxis_title='Program',
        xaxis=dict(range=[first_day, last_day]),
        showlegend=False,)


# Power and Gas total cost
    elec_gas_bar_fig = go.Figure(go.Bar(
        x=elec_daily[elec_daily['Category'] == 'Paid']['USAGE_DATE'], 
        y=elec_daily[elec_daily['Category'] == 'Paid']['USAGE_COST'],
        marker_color='orange',  # Use a different color for the fixed charge

    ))

    elec_gas_bar_fig.add_trace(go.Bar(
        x=elec_daily[elec_daily['Category'] == 'Paid']['USAGE_DATE'], 
        y=gas_daily[gas_daily['Category'] == 'Paid']['USAGE_COST'],
        marker_color='darkgrey',
        text=elec_daily[elec_daily['Category'] == 'Paid']['ENERGY_COST'].apply(lambda x: f"${x:.2f}" if x > 0 else "")
    ))

    # Add bars for "To be billed" category
    
    elec_gas_bar_fig.add_trace(go.Bar(
        x=elec_daily[elec_daily['Category'] == 'To be billed']['USAGE_DATE'], 
        y=elec_daily[elec_daily['Category'] == 'To be billed']['USAGE_COST'],
        marker_color='lightgoldenrodyellow',  # Use a different color for the fixed charge

    ))
    
    elec_gas_bar_fig.add_trace(go.Bar(
        x=elec_daily[elec_daily['Category'] == 'To be billed']['USAGE_DATE'], 
        y=gas_daily[gas_daily['Category'] == 'To be billed']['USAGE_COST'],
        marker_color='white',
        text=elec_daily[elec_daily['Category'] == 'To be billed']['ENERGY_COST'].apply(lambda x: f"${x:.2f}" if x > 0 else "")
    ))
    
    elec_gas_bar_fig.update_layout(
        barmode='stack',
        title='Daily Energy Cost', 
        xaxis_title='Date', 
        yaxis_title='$',
        yaxis=dict(rangemode="tozero"),
        xaxis=dict(range=[first_day, last_day]),
        showlegend=False
    )

    return f"${monthly:.2f}",f"${weekly:.2f}",f"${total_cost:.2f}",f"${gas_cost:.2f}", f"{avg_temp}°C", f"{bill_to_date:.2f}", year_bar_fig, gas_year_bar_fig, heatmap_fig, bar_fig, gas_heatmap_fig, gas_bar_fig, temp_fig, elec_gas_bar_fig # f"{total_kwh} kWh", f"{gas_kwh} kWh", f"{dish_count}", 

