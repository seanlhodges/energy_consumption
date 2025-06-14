import dash
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc

app = Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.DARKLY])


# Define the navigation bar
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Genesis Electricity", href="/dashboard-genesis")),
        dbc.NavItem(dbc.NavLink("Genesis Gas", href="/dashboard-genesis-gas")),
        dbc.NavItem(dbc.NavLink("Heatmaps", href="/dashboard-heatmap")),
        dbc.NavItem(dbc.NavLink("Compare weekdays", href="/selected-weekday-history")),
    ],
    brand="Energy Usage Dashboard",
    brand_href="/",
    brand_style={"font-size":"2em"},
    color="dark",
    dark=True,
)

footer = dbc.Container(
    dbc.Row(
        [
            dbc.Col(html.A("Sean Hodges | GitHub", href="https://github.com/seanlhodges/genesisenergy"), align="left"),
        ],
    ),
    className="footer",
    fluid=True,
)


#app.layout = html.Div([
    # html.H1('Energy usage views'),
    # html.Div([
    #     html.Div(
    #         dcc.Link(f"{page['name']} - {page['path']}", href=page["relative_path"])
    #     ) for page in dash.page_registry.values()
    # ]),
    #dash.page_container
# ])
app.layout = html.Div([
    navbar,  # Include the navigation bar
    dash.page_container,
    footer,  # Include the footer
])
    
    

if __name__ == '__main__':
    app.run(debug=True)