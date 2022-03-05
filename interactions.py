
from dash import html
from dash import dcc

import pandas as pd
from zipfile import ZipFile

import pathlib
# __file__ = 'apps/app_overview/views.py'
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

states = dfs['train']['State'].unique()
states_options = [{'label': state, 'value': state} for state in states]
start_date = pd.to_datetime(dfs['train']['Order Date']).dt.date.min()
end_date = pd.to_datetime(dfs['train']['Order Date']).dt.date.max()


def get_interactions():
    return html.Div(
        [
            html.P(
                'Filter by date:',
                className="control_label"
            ),
            dcc.DatePickerRange(
                id='date_picker',
                start_date=str(start_date),
                end_date=str(end_date),
                className="dcc_control"
            ),
            html.P(
                'Filter by well status:',
                className="control_label"
            ),
            dcc.Dropdown(
                id='customer_state',
                options=states_options,
                value=[],
                multi=True,
                className="dcc_control"
            ),
            html.Button(
                id='app_overview_state',
                n_clicks=0,
                className="btn btn-primary position-relative mt-5",
                children="Go"
            )
        ],
        className="pretty_container col-4"
    )
