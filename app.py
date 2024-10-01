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
                placeholder="Select a Brand",
                style={'width': '50%'}
            ),
        ], style={'marginBottom': '20px'}),

        # Third Dropdown: Select SKU (dynamically populated, allows typing)
        html.Div([
            html.Label("Select or Type an SKU:", style={'fontWeight': 'bold', 'fontSize': '16px'}),
            dcc.Dropdown(
                id='sku-dropdown',
                placeholder="Select or Type an SKU",
                style={'width': '50%'},
                searchable=True,  # Allow typing/searching SKUs
                clearable=True,  # Allow clearing the selected SKU
            ),
        ], style={'marginBottom': '30px'}),

        # Table to display selected SKU information
        dash_table.DataTable(
            id='sku-table',
            columns=[],  # Columns will be dynamically set
            data=[],     # Data will be dynamically set
            style_table={
                'width': '100%',  # Make the table take the full width of the container
                'maxHeight': '70vh',  # Adjust the height to fit the screen
                'overflowY': 'auto',
                'padding': '10px'  # Add padding around the table
            },
            style_cell={
                'textAlign': 'left',
                'padding': '5px',
                'fontSize': '12px',  # Smaller text size to fit more content
                'fontFamily': 'Arial, sans-serif'
            },
            style_header={
                'fontWeight': 'bold',
                'fontSize': '14px',  # Smaller text size for header
                'backgroundColor': '#e1e1e1',  # Light background for header
                'color': '#333333'  # Dark text color for header
            }
        )
    ]
)


# Callback to populate the Brand dropdown based on selected table
@app.callback(
    Output('brand-dropdown', 'options'),
    Input('table-dropdown', 'value')
)
def update_brand_dropdown(selected_table):
    if selected_table:
        # Query the database to get brands for the selected table
        query = f"SELECT DISTINCT brand FROM {selected_table}"
        df = pd.read_sql(query, engine)

        # Return a list of options for the Brand dropdown
        return [{'label': brand, 'value': brand} for brand in df['brand'].unique()]
    return []


# Callback to populate the SKU dropdown based on selected table and brand
@app.callback(
    Output('sku-dropdown', 'options'),
    Input('table-dropdown', 'value'),
    Input('brand-dropdown', 'value')
)
def update_sku_dropdown(selected_table, selected_brand):
    if selected_table and selected_brand:
        # Query the database to get SKUs for the selected table and brand
        query = f"SELECT sku FROM {selected_table} WHERE brand = '{selected_brand}'"
        df = pd.read_sql(query, engine)

        # Return a list of options for the SKU dropdown
        return [{'label': sku, 'value': sku} for sku in df['sku'].unique()]
    return []


# Callback to display the selected SKU information
@app.callback(
    [Output('sku-table', 'columns'), Output('sku-table', 'data')],
    Input('table-dropdown', 'value'),
    Input('sku-dropdown', 'value')
)
def display_sku_data(selected_table, selected_sku):
    if selected_table and selected_sku:
        # Query the database to get the selected SKU data
        query = f"SELECT * FROM {selected_table} WHERE sku = '{selected_sku}'"
        df = pd.read_sql(query, engine)

        # Define the columns and data for the table
        columns = [{'name': col, 'id': col} for col in df.columns]
        data = df.to_dict('records')

        return columns, data
    return [], []


# Run the Dash application
if __name__ == '__main__':
    app.run_server(debug=True)
