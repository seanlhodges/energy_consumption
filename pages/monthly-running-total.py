import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc
import dash
import dash_bootstrap_components as dbc

# Build Dash app
import plotly.io as pio

# Set dark theme
pio.templates.default = "plotly_dark"

# Load your parquet file
df = pd.read_parquet("electricity_usage.parquet")  # Replace with actual file path
df['billMonth'] = df['billMonth'].astype(str)
df['hour']= df['index'].dt.hour#.astype(str)

# last billMonth value in dataframe
last_bill_month = df['billMonth'].iloc[-1] if not df.empty else 'None'

# Filter out rows where billMonth is 'None'
df_stacked = df[df['billMonth']!='None'].copy()

# Group and summarise by billing month
summary = df.groupby('billMonth', as_index=False).agg({
    'usage': 'sum',
    'dollars': 'sum',
    'YYYYMMDD': 'nunique'  # Assuming this is the date column
})
bill_days = summary[summary['billMonth']==last_bill_month]['YYYYMMDD'].values[0] if not summary.empty else 0

# Sort by month if billMonth has consistent format (e.g. Jan, Feb...)
month_order = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]
summary['billMonth'] = pd.Categorical(summary['billMonth'], categories=month_order, ordered=True)
summary = summary.sort_values('billMonth')

# Create bar charts
fig_running_usage = px.bar(
    summary[summary['billMonth']!=last_bill_month],
    x='usage',
    y='billMonth',
    orientation='h',
    labels={'usage': 'kWh', 'billMonth': 'Billing Month'},
    title=f'{bill_days} days of Electricity Usage (kWh) for each Billing Month',
    text='usage',
    text_auto=True
)
fig_running_usage.update_traces(marker_color='orange')

fig_running_usage.add_trace(px.bar(
    summary[summary['billMonth']==last_bill_month],
    x='usage',
    y='billMonth',
    color_discrete_sequence=["#FAFAD2"],  # Light goldenrod yellow),
    text='usage',
    text_auto=True
).data[0]) #.update_traces(marker_color='lightgoldenrodyellow')  # Add last month as a separate trace


fig_running_usage.update_layout(xaxis_range=[0, 400])  # Set max to 400 kWh

fig_running_cost = px.bar(
    summary[summary['billMonth']!=last_bill_month],
    x='dollars',
    y='billMonth',
    orientation='h',
    labels={'dollars': 'NZD', 'billMonth': 'Billing Month'},
    title=f'{bill_days} days of Electricity Cost (NZD) for each Billing Month',
    text='dollars',
    text_auto=True
)
fig_running_cost.update_traces(marker_color='orange')

fig_running_cost.add_trace(px.bar(
    summary[summary['billMonth']==last_bill_month],
    x='dollars',
    y='billMonth',
    color_discrete_sequence=["#FAFAD2"],  # Light goldenrod yellow),
    text='usage',
    text_auto=True
).data[0]) #.update_traces(marker_color='lightgoldenrodyellow')  # Add last month as a separate trace


fig_running_cost.update_layout(
    xaxis_range=[0, 200],
    xaxis_tickprefix='$', 
    xaxis_tickformat=',.2f'
)

fig_cost_stacked = px.bar(
    df_stacked,
    x='dollars',
    y='billMonth',
    color='hour',
    orientation='h',
    labels={'dollars': 'NZD', 'billMonth': 'Billing Month'},
    title=f'{bill_days} days of Electricity Cost (NZD) for each Billing Month',
    # text='dollars',
    # text_auto=True
)

fig_cost_stacked.update_traces(marker_line_width=0)
fig_cost_stacked.update_layout(
    xaxis_range=[0, 200],  # Set max to 150 NZD
    xaxis_tickprefix='$', 
    xaxis_tickformat=',.2f'
)


dash.register_page(__name__)

# app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
# app.title = "Running Total of Electricity Usage and Cost"
layout = dbc.Container([
    html.H3("Electricity Summary by Billing Month", className="text-center my-4"),
    html.H5("Based on billing days for each period.", className="text-center my-4"),
    dcc.Graph(figure=fig_running_usage),
    dcc.Graph(figure=fig_running_cost),
    dcc.Graph(figure=fig_cost_stacked)
], fluid=True)

# if __name__ == "__main__":
#     app.run(debug=True, port=50001)
