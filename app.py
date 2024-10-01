
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import pandas as pd
from sqlalchemy import create_engine
import dash_bootstrap_components as dbc

# Set up SQLite connection
DB_PATH = 'sqlite:///products.db'  # Use the path to your SQLite database
engine = create_engine(DB_PATH)

# Create a Dash application
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Application layout
app.layout = dbc.Container(
    fluid=True,
    style={'padding': '20px', 'height': '100vh'},
    children=[
        # Title
        html.H1("PFV Analysis Application", style={'textAlign': 'center', 'marginBottom': '20px', 'fontSize': '32px'}),

        # First Dropdown: Select Table
        html.Div([
            html.Label("Select a Table:", style={'fontWeight': 'bold', 'fontSize': '16px'}),
            dcc.Dropdown(
                id='table-dropdown',
                options=[
                    {'label': 'DirectDialUS', 'value': 'DirectDialUS'},
                    {'label': 'DirectDialCA', 'value': 'DirectDialCA'}
                ],
                placeholder="Select a Table",
                style={'width': '50%'}
            ),
        ], style={'marginBottom': '20px'}),

        # Second Dropdown: Select Brand (dynamically populated)
        html.Div([
            html.Label("Select a Brand:", style={'fontWeight': 'bold', 'fontSize': '16px'}),
            dcc.Dropdown(
                id='brand-dropdown',
                options=[],  # Options populated dynamically
                placeholder="Select a Brand",
                style={'width': '50%'}
            ),
        ], style={'marginBottom': '20px'}),

        # Third Dropdown: Select SKU (dynamically populated)
        html.Div([
            html.Label("Select a SKU:", style={'fontWeight': 'bold', 'fontSize': '16px'}),
            dcc.Dropdown(
                id='sku-dropdown',
                options=[],  # Options populated dynamically
                placeholder="Select a SKU",
                style={'width': '50%'}
            ),
        ], style={'marginBottom': '20px'}),

        # Main Product Table
        dash_table.DataTable(
            id='product-table',
            columns=[],  # Columns populated dynamically
            data=[],  # Data populated dynamically
            style_table={'height': '300px', 'overflowY': 'auto'},
            style_cell={'textAlign': 'left', 'minWidth': '100px', 'maxWidth': '300px'},
        ),

        # Price History Table
        html.Div([
            html.H3("Price History", style={'marginTop': '30px'}),
            dash_table.DataTable(
                id='price-history-table',
                columns=[],  # Columns populated dynamically
                data=[],  # Data populated dynamically
                style_table={'height': '300px', 'overflowY': 'auto'},
                style_cell={'textAlign': 'left', 'minWidth': '100px', 'maxWidth': '300px'},
            )
        ]),

        # Stock History Table
        html.Div([
            html.H3("Stock History", style={'marginTop': '30px'}),
            dash_table.DataTable(
                id='stock-history-table',
                columns=[],  # Columns populated dynamically
                data=[],  # Data populated dynamically
                style_table={'height': '300px', 'overflowY': 'auto'},
                style_cell={'textAlign': 'left', 'minWidth': '100px', 'maxWidth': '300px'},
            )
        ])
    ]
)

# Callbacks for interactivity
@app.callback(
    [Output('brand-dropdown', 'options')],
    [Input('table-dropdown', 'value')]
)
def update_brand_dropdown(selected_table):
    if selected_table:
        # Fetch distinct brands from the selected table
        query = f"SELECT DISTINCT brand FROM {selected_table}"
        df = pd.read_sql(query, engine)
        return [[{'label': brand, 'value': brand} for brand in df['brand']]]
    return [[]]

@app.callback(
    [Output('sku-dropdown', 'options')],
    [Input('brand-dropdown', 'value'),
     Input('table-dropdown', 'value')]
)
def update_sku_dropdown(selected_brand, selected_table):
    if selected_brand and selected_table:
        # Fetch distinct SKUs based on selected brand
        query = f"SELECT DISTINCT sku FROM {selected_table} WHERE brand = '{selected_brand}'"
        df = pd.read_sql(query, engine)
        return [[{'label': sku, 'value': sku} for sku in df['sku']]]
    return [[]]

@app.callback(
    [Output('product-table', 'columns'),
     Output('product-table', 'data')],
    [Input('sku-dropdown', 'value'),
     Input('table-dropdown', 'value')]
)
def update_product_table(selected_sku, selected_table):
    if selected_sku and selected_table:
        # Fetch products based on selected SKU
        query = f"SELECT * FROM {selected_table} WHERE sku = '{selected_sku}'"
        df = pd.read_sql(query, engine)
        columns = [{"name": i, "id": i} for i in df.columns]
        return columns, df.to_dict('records')
    return [], []

@app.callback(
    [Output('price-history-table', 'columns'),
     Output('price-history-table', 'data')],
    [Input('sku-dropdown', 'value'),
     Input('table-dropdown', 'value')]
)
def update_price_history_table(selected_sku, selected_table):
    if selected_sku and selected_table:
        history_table = f"{selected_table}History"
        query = f"SELECT date, price FROM {history_table} WHERE sku = '{selected_sku}'"
        df = pd.read_sql(query, engine)
        columns = [{"name": i, "id": i} for i in df.columns]
        return columns, df.to_dict('records')
    return [], []

@app.callback(
    [Output('stock-history-table', 'columns'),
     Output('stock-history-table', 'data')],
    [Input('sku-dropdown', 'value'),
     Input('table-dropdown', 'value')]
)
def update_stock_history_table(selected_sku, selected_table):
    if selected_sku and selected_table:
        history_table = f"{selected_table}History"
        query = f"SELECT date, stock FROM {history_table} WHERE sku = '{selected_sku}'"
        df = pd.read_sql(query, engine)
        columns = [{"name": i, "id": i} for i in df.columns]
        return columns, df.to_dict('records')
    return [], []

# Run the application
if __name__ == '__main__':
    app.run_server(debug=True)
