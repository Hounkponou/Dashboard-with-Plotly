import pandas as pd
from dash import html
from dash import dcc
import numpy as np
from dash import dash_table
import dash_daq as daq
from dash.dependencies import Input, Output, State
from plotly.tools import mpl_to_plotly
from plotly.offline import init_notebook_mode, plot_mpl
import plotly.express as px
import plotly.graph_objs as go
from .interactions import get_interactions
from utils.kpi import generate_kpi, literal_number
import utils.graphs as utils_graphs
from app import app
from zipfile import ZipFile
import pathlib
import matplotlib.pyplot as plt
import seaborn as sns
# Data Import
#__file__ = 'apps/app_overview/views.py'
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath('../../data').resolve()
dfs = {}
files = ['train.csv']
with ZipFile(DATA_PATH.joinpath("commerce.zip")) as z:
    if not files:
        files = z.namelist()
    for file in files:
        filename = file.split('.')[0]
        with z.open(file) as f:
            dfs[filename] = pd.read_csv(f)
focus = 'train'
for col in ['Order Date', 'Ship Date']:
    dfs[focus][col] = pd.to_datetime(dfs[focus][col], errors='coerce')

dfs[focus]['time_to_deliver'] = (
    dfs[focus]['Ship Date'] -
    dfs[focus]['Order Date']
)
dfs[focus]['time_to_deliver'] = (
    dfs[focus]['time_to_deliver'].dt.days +
    dfs[focus]['time_to_deliver'].dt.components['hours'].div(24)
)

#First Part
def create_layout():
    card = get_interactions()
    right_col = html.Div(id='rightCol', className="col-7")
    content = [
        html.Div([
            card,
            right_col
        ], className='row flex-display mt-5'),
        html.Div(
            id='mainContainer',
        )
    ]
    return content



@app.callback(
    Output('rightCol', 'children'),
    Input('app_overview_state', 'n_clicks'),
    State('customer_state', 'value'),
    State('date_picker', 'start_date'),
    State('date_picker', 'end_date')
)
def update_right_col(n_clicks, customer_state, start, end):

    start = pd.to_datetime(start).date()
    end = pd.to_datetime(end).date()
    if customer_state:
        condition1 = dfs[focus]['State'].isin(customer_state)
    else:
        condition1 = dfs[focus]['State'].notnull()
    condition2 = dfs[focus]['Order Date'].dt.date.ge(start)
    condition3 = dfs[focus]['Order Date'].dt.date.le(end)

    temp = dfs[focus][condition1 & condition2 & condition3]

### KPI GENERATION ###
    np_avg_delivery_time = round(temp['time_to_deliver'].mean(), 1)
    nb_orders = temp['Order ID'].nunique()
    nb_customers = temp['Customer ID'].nunique()
    nb_category = temp['Category'].nunique()
    nb_Sub_Category = temp['Sub-Category'].nunique()

    kpi1 = generate_kpi('Nb. of orders', literal_number(nb_orders))
    kpi2 = generate_kpi('Nb. customers', literal_number(nb_customers))
    kpi3 = generate_kpi('Categories', literal_number(nb_category))
    kpi4 = generate_kpi('Sub_Categories', literal_number(nb_Sub_Category))
    kpi5 = generate_kpi('Average Delivery Time', literal_number(np_avg_delivery_time))


    temp['moy'] = temp['Order Date'].dt.to_period('M')

    vc = temp['moy'].value_counts().sort_index().to_frame()
    labels = vc.index.astype(str).tolist()
    values = vc[['moy']]

    #First Fig
    fig = utils_graphs.generate_hbar_fig(labels=labels, data=values)
    graph = dcc.Graph(id='orders_per_date', figure=fig)


    return [
        html.Div(
            [
                html.Div(
                    [kpi1, kpi2, kpi3, kpi4,kpi5],
                    id="tripleContainer"),
            ],
            id="infoContainer",
            className="row",
        ),
        html.Div(
            [html.P("Order Mean"),graph],
            id="countGraphContainer",
            className="pretty_container")
    ]

@app.callback(
    Output('mainContainer', 'children'),
    Input('app_overview_state', 'n_clicks'),
    State('customer_state', 'value'),
    State('date_picker', 'start_date'),
    State('date_picker', 'end_date')
)
def update_maincontent(n_clicks, customer_state, start, end, order_status_weight=None):
    start = pd.to_datetime(start).date()
    end = pd.to_datetime(end).date()
    if customer_state:
       condition1 = dfs[focus]['State'].isin(customer_state)
    else:
        condition1 = dfs[focus]['State'].notnull()
    condition2 = dfs[focus]['Order Date'].dt.date.ge(start)
    condition3 = dfs[focus]['Order Date'].dt.date.le(end)

    temp = dfs[focus][condition1 & condition2 & condition3]
    temp['Month'] = temp['Order Date'].dt.month_name()
    temp['Year'] =temp['Order Date'].dt.year

    vc = temp['Ship Mode'].value_counts().to_frame()
    labels = vc.index.tolist()
    values = vc['Ship Mode'].tolist()

    #Pie Chart 1
    fig = utils_graphs.generate_pie_fig(labels=labels, data=values, hole=0.3)
    graph = dcc.Graph(id='Ship Mode', figure=fig)

    #Second Pie Chart
    vc1 = temp['Product Name'].value_counts(normalize=True).head(5).to_frame()
    labels1 = vc1.index.tolist()
    values = vc1['Product Name'].tolist()
    fig2 = utils_graphs.generate_pie_fig(labels=labels1, data=values, hole=0.3)
    graph2 = dcc.Graph(id='Product Name', figure=fig2)

    #Sales Per Year
    Total_Sales_per_Year = temp.groupby(by=['Year']).sum()
    fig3 = px.line(Total_Sales_per_Year, x=Total_Sales_per_Year.index, y='Sales', markers=True)
    graph3 = dcc.Graph(id='Sales Per Year', figure=fig3)

    #SEGMENT HISTOGRAM
    fig5 = px.histogram(temp, x='Segment', color='Segment', title='Segment')
    graph5 = dcc.Graph(id='Segment', figure=fig5)


    #CATEGORY FIG
    fig6=px.histogram(temp,x='Category',color='Category', title='Category')
    fig6=fig6.update_layout(paper_bgcolor='rgba(0,0,0,0)')
    graph6=dcc.Graph(id='Category',figure=fig6)


    #SUB CATEGORY
    fig7 = px.histogram(temp, x='Sub-Category', color='Sub-Category', title='Sub Category')
    fig7 = fig7.update_layout(paper_bgcolor="rgba(0,0,0,0)", barmode="stack")
    graph7 = dcc.Graph(id='Sub-Category', figure=fig7)


    #MAP
    #State Name and Code
    state = ['Alabama', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut', 'Delaware', 'Florida',
             'Georgia', 'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana', 'Maine',
             'Maryland',
             'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada',
             'New Hampshire',
             'New Jersey', 'New Mexico', 'New York', 'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon',
             'Pennsylvania',
             'Rhode Island', 'South Carolina', 'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia',
             'Washington',
             'West Virginia', 'Wisconsin', 'Wyoming']
    state_code = ['AL', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA',
                  'ME', 'MD', 'MA',
                  'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA',
                  'RI', 'SC', 'SD', 'TN',
                  'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']

    state_df = pd.DataFrame(state, state_code)  # Create a dataframe
    state_df.reset_index(level=0, inplace=True)
    state_df.columns = ['State Code', 'State']
    sales = dfs[focus].groupby(["State"]).sum().sort_values("Sales", ascending=False)
    sales.reset_index(level=0, inplace=True)
    sales.drop('Postal Code', 1, inplace=True)
    sales = sales.sort_values('State', ascending=True)
    sales.reset_index(inplace=True)
    sales.drop('index', 1, inplace=True)
    sales.insert(1, 'State Code', state_df['State Code'])



    sales['text'] = sales['State']
    fig4 = go.Figure(data=go.Choropleth(locations=sales['State Code'],  # Spatial coordinates
        text=sales['text'],
        z=sales['Sales'].astype(float),  # Data to be color-coded
        locationmode='USA-states',  # set of locations match entries in `locations`
        colorscale='BLUES',
        colorbar_title="Sales"
    ))
    fig4.update_layout(
        title_text='Sales',
        geo_scope='usa',  # limite map scope to USA
    )
    graph4 = dcc.Graph(id='Sales Per Year', figure=fig4)

    content = [
        html.Div(
            [
                html.Div([html.P("Ship Mode"),
                    graph],
                    className='pretty_container col-5'),

                html.Div([html.P("Most Popular Product"),
                          graph2],
                         className='pretty_container col-5'),
                html.Div([html.P("Sales Per Year"),
                          graph3],
                         className='pretty_container col-5'),
                html.Div([html.P("Sales Per Year"),
                          graph5],
                         className='pretty_container col-5'),
                html.Div([html.P("CATEGORY"),
                          graph6],
                         className='pretty_container col-5'),
                html.Div([html.P("SUB CATEGORY"),
                          graph7],
                         className='pretty_container col-5'),
                html.Div([html.P("Sales"),
                          graph4],
                         className='pretty_container')
            ],
            className='row'
        ),
    ]
    return content


