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
df_stacked = df[df['billMonth']!='None'].copy()
# Group and summarise by billing month
summary = df.groupby('billMonth', as_index=False).agg({
    'usage': 'sum',
    'dollars': 'sum'
})

# Sort by month if billMonth has consistent format (e.g. Jan, Feb...)
month_order = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]
summary['billMonth'] = pd.Categorical(summary['billMonth'], categories=month_order, ordered=True)
summary = summary.sort_values('billMonth')

# Create bar charts
fig_running_usage = px.bar(
    summary,
    x='usage',
    y='billMonth',
    orientation='h',
    labels={'usage': 'kWh', 'billMonth': 'Billing Month'},
    title='Electricity Usage (kWh) by Billing Month',
    text='usage',
    text_auto=True
)
fig_running_usage.update_traces(marker_color='orange')
fig_running_usage.update_layout(xaxis_range=[0, 400])  # Set max to 400 kWh

fig_running_cost = px.bar(
    summary,
    x='dollars',
    y='billMonth',
    orientation='h',
    labels={'dollars': 'NZD', 'billMonth': 'Billing Month'},
    title='Electricity Cost (NZD) by Billing Month',
    text='dollars',
    text_auto=True
)
fig_running_cost.update_traces(marker_color='orange')

fig_running_cost.update_layout(
    xaxis_range=[0, 150],
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
    title='Electricity Cost (NZD) by Billing Month',
    # text='dollars',
    # text_auto=True
)

fig_cost_stacked.update_traces(marker_line_width=0)
fig_cost_stacked.update_layout(
    xaxis_range=[0, 150],  # Set max to 150 NZD
    xaxis_tickprefix='$', 
    xaxis_tickformat=',.2f'
)

dash.register_page(__name__)

# app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
# app.title = "Running Total of Electricity Usage and Cost"
layout = dbc.Container([
    html.H3("Electricity Summary by Billing Month"),
    html.P("Based on billing days for each period."),
    dcc.Graph(figure=fig_running_usage),
    dcc.Graph(figure=fig_running_cost),
    dcc.Graph(figure=fig_cost_stacked)
], fluid=True)

# if __name__ == "__main__":
#     app.run(debug=True, port=50001)
