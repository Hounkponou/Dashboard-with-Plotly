
import dash
from dash import dcc
from dash import html
from dash import Input, Output
import dash_bootstrap_components as dbc
from apps.app_overview import views as app_overview_views
from apps.app_order_items import views as app_order_items_views
from apps.app_customers import views as app_customers_views
from apps.app_404 import views as app_404_views
from utils.navbar import GenerateTabs
from utils.header import generate_header
from app import app

header = generate_header()

app.layout = html.Div([
    header,
    GenerateTabs(active_tab='overview').generate_navbar(),
    html.Div(id="app-content", className='container-fluid')
])


@app.callback(
    Output("app-content", "children"),
    [Input("tabs", "active_tab")]
)
def display_page(tab):
    if tab == "overview":
        return app_overview_views.create_layout()
    elif tab == "customers":
        return app_customers_views.clayout()
    else:
        return app_order_items_views.clayout2()


if __name__ == '__main__':
    app.run_server(debug=True)
