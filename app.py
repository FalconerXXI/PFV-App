import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import pandas as pd
from sqlalchemy import create_engine
import dash_bootstrap_components as dbc
import pandas as pd
from dash.dcc import send_data_frame

# Set up SQLite connection
DB_PATH = 'sqlite:///products.db'  # Use the path to your SQLite database
engine = create_engine(DB_PATH)

# Create a Dash application with multi-page support
app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Application layout with navigation
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    # Navigation bar
    dbc.NavbarSimple(
        brand="PFV Analysis Application",
        brand_href="/",
        color="primary",
        dark=True,
        children=[
            dbc.NavItem(dbc.NavLink("Home", href='/')),
            dbc.NavItem(dbc.NavLink("Analysis", href='/page-1')),
            dbc.NavItem(dbc.NavLink("Viewing", href='/page-2')),
            dbc.NavItem(dbc.NavLink("Editing", href='/page-3')),
        ]
    ),
    html.Div(id='page-content')
])

home_layout = dbc.Container(
    fluid=True,
    style={'padding': '20px'},
    children=[
        html.H1("PFV Analysis Application - Home", style={'textAlign': 'center', 'marginBottom': '40px', 'fontSize': '32px', 'fontWeight': 'bold'}),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Database Statistics", style={'fontWeight': 'bold'}),
                    dbc.CardBody(
                        [
                            html.P(id='total-days-tracked', style={'fontSize': '18px'}),
                            html.P(id='last-update-time', style={'fontSize': '18px'}),
                            html.P(id='total-products', style={'fontSize': '18px'}),
                            html.P(id='total-brands', style={'fontSize': '18px'}),
                        ]
                    )
                ])
            ], width=12),
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Top 10 Largest Price Changes (US)", style={'fontWeight': 'bold'}),
                    dbc.CardBody(
                        dash_table.DataTable(
                            id='top-10-price-change-us',
                            columns=[{'name': 'SKU', 'id': 'sku'}, {'name': 'Price Change', 'id': 'price_change'}],
                            data=[],  # Data populated dynamically
                            style_table={'height': '300px', 'overflowY': 'auto'},
                            style_cell={'textAlign': 'left', 'padding': '5px', 'fontFamily': 'Arial'},
                            style_header={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'},
                        )
                    )
                ])
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Top 10 Largest Price Changes (CA)", style={'fontWeight': 'bold'}),
                    dbc.CardBody(
                        dash_table.DataTable(
                            id='top-10-price-change-ca',
                            columns=[{'name': 'SKU', 'id': 'sku'}, {'name': 'Price Change', 'id': 'price_change'}],
                            data=[],  # Data populated dynamically
                            style_table={'height': '300px', 'overflowY': 'auto'},
                            style_cell={'textAlign': 'left', 'padding': '5px', 'fontFamily': 'Arial'},
                            style_header={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'},
                        )
                    )
                ])
            ], width=6),
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Top 10 Largest Stock Changes (US)", style={'fontWeight': 'bold'}),
                    dbc.CardBody(
                        dash_table.DataTable(
                            id='top-10-stock-change-us',
                            columns=[{'name': 'SKU', 'id': 'sku'}, {'name': 'stock_change', 'id': 'stock_change'}],
                            data=[],  # Data populated dynamically
                            style_table={'height': '300px', 'overflowY': 'auto'},
                            style_cell={'textAlign': 'left', 'padding': '5px', 'fontFamily': 'Arial'},
                            style_header={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'},
                        )
                    )
                ])
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Top 10 Largest Stock Changes (CA)", style={'fontWeight': 'bold'}),
                    dbc.CardBody(
                        dash_table.DataTable(
                            id='top-10-stock-change-ca',
                            columns=[{'name': 'SKU', 'id': 'sku'}, {'name': 'stock_change', 'id': 'stock_change'}],
                            data=[],  # Data populated dynamically
                            style_table={'height': '300px', 'overflowY': 'auto'},
                            style_cell={'textAlign': 'left', 'padding': '5px', 'fontFamily': 'Arial'},
                            style_header={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'},
                        )
                    )
                ])
            ], width=6),
        ]),
    ]
)


# Page 1 Layout - Product Analysis
page1_layout = dbc.Container(
    fluid=True,
    style={'padding': '20px'},
    children=[
        # Title
        html.H1("Individual Product Analysis", style={'textAlign': 'center', 'marginBottom': '40px', 'fontSize': '32px', 'fontWeight': 'bold'}),
        # Filter Section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Filter Options", style={'fontWeight': 'bold', 'textAlign': 'center'}),
                    dbc.CardBody([
                        html.Label("Select a Table:", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='page-1-table-dropdown',
                            options=[
                                {'label': 'DirectDialUS', 'value': 'DirectDialUS'},
                                {'label': 'DirectDialCA', 'value': 'DirectDialCA'}
                            ],
                            placeholder="Select a Table",
                            style={'marginBottom': '20px'}
                        ),
                        html.Label("Select a Brand:", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='page-1-brand-dropdown',
                            options=[],  # Options populated dynamically
                            placeholder="Select a Brand",
                            style={'marginBottom': '20px'}
                        ),
                        html.Label("Select a SKU:", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='page-1-sku-dropdown',
                            options=[],  # Options populated dynamically
                            placeholder="Select a SKU",
                            style={'marginBottom': '20px'}
                        ),
                        html.Label("Select a Date Granularity", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='page-1-date-granularity-dropdown',
                            options=[
                                {'label': 'Daily', 'value': 'D'},
                                {'label': 'Monthly', 'value': 'M'}
                            ],
                            value='D',  # Default to 'Daily'
                            placeholder='Select Date Granularity'
                        ),
                        # Add a button to collapse/expand the filters
                        dbc.Button("Apply Filters", id='apply-filters-button', color='primary', style={'marginTop': '20px'}),
                    ])
                ], style={'marginBottom': '30px'})
            ], width=3),  # Sidebar width reduced

            # Main Product Table
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Product Details", style={'fontWeight': 'bold'}),
                    dbc.CardBody(
                        dash_table.DataTable(
                            id='page-1-product-table',
                            columns=[],  # Columns populated dynamically
                            data=[],  # Data populated dynamically
                            style_table={'height': '300px', 'overflowY': 'auto'},
                            style_cell={'textAlign': 'left', 'padding': '5px', 'fontFamily': 'Arial'},
                            style_header={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'},
                        ),
                    )
                ], style={'marginBottom': '30px'})
            ], width=9)  # Adjust the width of the table column
        ]),

        # Price and Stock History Tables
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Price History Table", style={'fontWeight': 'bold'}),
                    dbc.CardBody(
                        dash_table.DataTable(
                            id='page-1-price-history-table',
                            columns=[],  # Columns populated dynamically
                            data=[],  # Data populated dynamically
                            style_table={'height': '200px', 'overflowY': 'auto'},
                            style_cell={'textAlign': 'left', 'padding': '5px', 'fontFamily': 'Arial'},
                            style_header={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'},
                        ),
                    )
                ], style={'marginBottom': '30px'})
            ], width=6),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Stock History Table", style={'fontWeight': 'bold'}),
                    dbc.CardBody(
                        dash_table.DataTable(
                            id='page-1-stock-history-table',
                            columns=[],  # Columns populated dynamically
                            data=[],  # Data populated dynamically
                            style_table={'height': '200px', 'overflowY': 'auto'},
                            style_cell={'textAlign': 'left', 'padding': '5px', 'fontFamily': 'Arial'},
                            style_header={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'},
                        ),
                    )
                ], style={'marginBottom': '30px'})
            ], width=6),
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Price History Graph", style={'fontWeight': 'bold'}),
                    dbc.CardBody(
                        dcc.Graph(
                            id='page-1-price-history-graph',  # Graph ID for Price History
                            style={'height': '450px'}  # Set the graph height to 500px
                        )
                    )
                ], style={'marginBottom': '30px'})
            ], width=6),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Stock History Graph", style={'fontWeight': 'bold'}),
                    dbc.CardBody(
                        dcc.Graph(
                            id='page-1-stock-history-graph',  # Graph ID for Stock History
                            style={'height': '450px'}  # Set the graph height to 500px
                        )
                    )
                ], style={'marginBottom': '30px'})
            ], width=6),
        ])
    ]
)

# Page 2 Layout - Database Overview
page2_layout = dbc.Container(
    fluid=True,
    style={'padding': '20px'},
    children=[
        html.H1("Database Overview", style={'textAlign': 'center', 'marginBottom': '40px', 'fontSize': '32px', 'fontWeight': 'bold'}),
        # Dropdown to select table
        dbc.Row([
            dbc.Col([
                html.Label("Select a Table:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(
                    id='overview-table-dropdown',
                    options=[
                        {'label': 'DirectDialUS', 'value': 'DirectDialUS'},
                        {'label': 'DirectDialCA', 'value': 'DirectDialCA'}
                    ],
                    placeholder="Select a Table",
                    style={'marginBottom': '20px'}
                )
            ], width=3),
        ]),
        # DataTable to display the table data
        # Search Bar
        dbc.Row([dbc.Col(dbc.Input(id='search-bar', placeholder='Search for products...', type='text', style={'marginBottom': '20px'}), width=12)]),

        # Filters
        dbc.Row([
            dbc.Col([html.Label("Filter by Category:", style={'fontWeight': 'bold'}), dcc.Dropdown(id='category-filter', options=[], placeholder="Select Category", style={'marginBottom': '20px'})], width=3),
            dbc.Col([html.Label("Price Range:", style={'fontWeight': 'bold'}), dcc.RangeSlider(id='price-range-slider', min=0, max=1000, step=10, marks={i: f"${i}" for i in range(0, 1001, 100)}, value=[100, 500])], width=5),
            dbc.Col([html.Label("Availability:", style={'fontWeight': 'bold'}), dcc.Dropdown(id='availability-filter', options=[{'label': 'In Stock', 'value': 'in_stock'}, {'label': 'Out of Stock', 'value': 'out_of_stock'}], placeholder="Select Availability", style={'marginBottom': '20px'})], width=2)
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Product Details", style={'fontWeight': 'bold'}),
                    dbc.CardBody(
                        dash_table.DataTable(
                            id='overview-table',
                            columns=[],  # Columns populated dynamically
                            data=[], 
                            page_size=2000,  # You can adjust the page size based on your needs
                            virtualization=True, # Data populated dynamically
                            style_table={'height': '300px', 'overflowY': 'auto'},
                            style_cell={'textAlign': 'left', 'padding': '5px', 'fontFamily': 'Arial'},
                            style_header={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'},
                            fixed_rows={'headers': True},  # Sticky headers
                        ),
                    )
                ], style={'marginBottom': '30px'})
            ], width=12) 
        ]),
        # Download button and dcc.Download component
        dbc.Row([
            dbc.Col([
                dbc.Button("Export to CSV", id="export-csv-button", color="primary", style={'marginTop': '20px'}),
                dcc.Download(id="download-csv")
            ], width=12)
        ])
    ]
)
# Page 2 Layout - Database Overview
page3_layout = dbc.Container(
    fluid=True,
    style={'padding': '20px'},
    children=[
        html.H1("Edit Database", style={'textAlign': 'center', 'marginBottom': '40px', 'fontSize': '32px', 'fontWeight': 'bold'}),
        # Dropdown to select table
        dbc.Row([
            dbc.Col([
                html.Label("Select a Table:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(
                    id='edit-dropdown',
                    options=[
                        {'label': 'DirectDialUS', 'value': 'DirectDialUS'},
                        {'label': 'DirectDialCA', 'value': 'DirectDialCA'}
                    ],
                    placeholder="Select a Table",
                    style={'marginBottom': '20px'}
                )
            ], width=3),
        ]),
        # DataTable to display the table data
        # Search Bar
        dbc.Row([dbc.Col(dbc.Input(id='search-bar', placeholder='Search for products...', type='text', style={'marginBottom': '20px'}), width=12)]),
         # Editable DataTable for editing data
         
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Over", style={'fontWeight': 'bold'}),
                    dbc.CardBody(
                        dash_table.DataTable(
                            id='edit-overview-table',
                            columns=[],  # Columns populated dynamically
                            data=[], 
                            page_size=2000,  # You can adjust the page size based on your needs
                            virtualization=True, # Data populated dynamically
                            editable=True,  # Enable table editing
                            row_deletable=True,
                            style_table={'height': '300px', 'overflowY': 'auto'},
                            style_cell={'textAlign': 'left', 'padding': '5px', 'fontFamily': 'Arial'},
                            style_header={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'},
                            fixed_rows={'headers': True},  # Sticky headers
                        ),
                    )
                ], style={'marginBottom': '30px'})
            ], width=12) 
        ]),

        # Buttons for CRUD operations
        dbc.Row([
            dbc.Col([
                dbc.Button("Add Row", id="add-row-button", color="success", style={'marginTop': '20px', 'marginRight': '10px'}),
                dbc.Button("Save Changes", id="save-changes-button", color="primary", style={'marginTop': '20px'}),
                dbc.Button("Export to CSV", id="export-edit-csv-button", color="secondary", style={'marginTop': '20px', 'marginLeft': '10px'}),
                dcc.Download(id="download-edit-csv")
            ], width=12)
        ]),
        
        # Hidden div for storing data for the selected table
        dcc.Store(id='edit-table-store'),
        # Download button and dcc.Download component
        dbc.Row([
            dbc.Col([
                dbc.Button("Export to CSV", id="export-csv-button", color="primary", style={'marginTop': '20px'}),
                dcc.Download(id="download-csv")
            ], width=12)
        ])
    ]
)



# Callbacks to render page content based on URL
@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/':
        return home_layout
    elif pathname == '/page-1':
        return page1_layout
    elif pathname == '/page-2':
        return page2_layout
    elif pathname == '/page-3':
        return page3_layout
    else:
        return html.H1('404 - Page Not Found', style={'textAlign': 'center'})
@app.callback(
    [Output('total-days-tracked', 'children'),
     Output('last-update-time', 'children'),
     Output('total-products', 'children'),
     Output('total-brands', 'children'),
     Output('top-10-price-change-us', 'data'),
     Output('top-10-price-change-ca', 'data'),
     Output('top-10-stock-change-us', 'data'),
     Output('top-10-stock-change-ca', 'data')],
    [Input('url', 'pathname')]
)
def update_home_stats(pathname):
    if pathname == '/':
        print("Home page detected. Starting data fetch...")

        # Get min and max timestamps from history tables
        query_us = "SELECT MIN(timestamp) as min_time, MAX(timestamp) as max_time FROM DirectDialUSHistory"
        query_ca = "SELECT MIN(timestamp) as min_time, MAX(timestamp) as max_time FROM DirectDialCAHistory"

        df_us = pd.read_sql(query_us, engine)
        df_ca = pd.read_sql(query_ca, engine)

        print("Query for US history: ", query_us)
        print("Query for CA history: ", query_ca)
        print("US History Dataframe:\n", df_us)
        print("CA History Dataframe:\n", df_ca)

        # Convert timestamps to datetime objects
        min_time_us = pd.to_datetime(df_us['min_time'].iloc[0], errors='coerce')
        max_time_us = pd.to_datetime(df_us['max_time'].iloc[0], errors='coerce')
        min_time_ca = pd.to_datetime(df_ca['min_time'].iloc[0], errors='coerce')
        max_time_ca = pd.to_datetime(df_ca['max_time'].iloc[0], errors='coerce')

        print("Min and Max Time (US):", min_time_us, max_time_us)
        print("Min and Max Time (CA):", min_time_ca, max_time_ca)

        # Determine the overall min and max times
        min_time = min(filter(pd.notna, [min_time_us, min_time_ca]))
        max_time = max(filter(pd.notna, [max_time_us, max_time_ca]))

        if min_time and max_time:
            total_days_tracked = (max_time - min_time).days + 1
        else:
            total_days_tracked = 0
        total_days_tracked_text = f"Total number of days tracked: {total_days_tracked}"
        print("Total days tracked:", total_days_tracked_text)

        # Last update time
        last_update_time = max_time if max_time else 'No data available'
        last_update_time_text = f"Last update time: {last_update_time}"
        print("Last update time:", last_update_time_text)

        # Total number of products
        query_products_us = "SELECT COUNT(DISTINCT sku) as total_products FROM DirectDialUS"
        query_products_ca = "SELECT COUNT(DISTINCT sku) as total_products FROM DirectDialCA"

        df_products_us = pd.read_sql(query_products_us, engine)
        df_products_ca = pd.read_sql(query_products_ca, engine)

        print("US Products Dataframe:\n", df_products_us)
        print("CA Products Dataframe:\n", df_products_ca)

        total_products = df_products_us['total_products'].iloc[0] + df_products_ca['total_products'].iloc[0]
        total_products_text = f"Total number of products: {total_products}"
        print("Total products:", total_products_text)

        # Total number of brands
        query_brands_us = "SELECT COUNT(DISTINCT brand) as total_brands FROM DirectDialUS"
        query_brands_ca = "SELECT COUNT(DISTINCT brand) as total_brands FROM DirectDialCA"

        df_brands_us = pd.read_sql(query_brands_us, engine)
        df_brands_ca = pd.read_sql(query_brands_ca, engine)

        print("US Brands Dataframe:\n", df_brands_us)
        print("CA Brands Dataframe:\n", df_brands_ca)

        total_brands = max(df_brands_us['total_brands'].iloc[0], df_brands_ca['total_brands'].iloc[0])
        total_brands_text = f"Total number of brands: {total_brands}"
        print("Total brands:", total_brands_text)

        # Calculate start date dynamically using datetime objects
        start_date_us = min_time_us if min_time_us and min_time_us >= max_time_us - pd.Timedelta(days=7) else max_time_us - pd.Timedelta(days=7)
        start_date_ca = min_time_ca if min_time_ca and min_time_ca >= max_time_ca - pd.Timedelta(days=7) else max_time_ca - pd.Timedelta(days=7)

        # Convert datetime to string in the format required for SQL queries
        start_date_us_str = start_date_us.strftime('%Y-%m-%d')
        start_date_ca_str = start_date_ca.strftime('%Y-%m-%d')
        print("Start date US:", start_date_us_str)
        print("Start date CA:", start_date_ca_str)

        # Top 10 Largest Price Changes in US
        query_price_change_us = f"""
            SELECT sku, MAX(price) - MIN(price) as price_change
            FROM DirectDialUSHistory
            WHERE timestamp >= '{start_date_us_str}'
            GROUP BY sku
            ORDER BY price_change DESC
            LIMIT 10
        """
        df_price_change_us = pd.read_sql(query_price_change_us, engine)
        top_10_price_change_us = df_price_change_us.to_dict('records')
        print("Top 10 Price Changes (US):\n", top_10_price_change_us)

        # Top 10 Largest Price Changes in CA
        query_price_change_ca = f"""
            SELECT sku, MAX(price) - MIN(price) as price_change
            FROM DirectDialCAHistory
            WHERE timestamp >= '{start_date_ca_str}'
            GROUP BY sku
            ORDER BY price_change DESC
            LIMIT 10
        """
        df_price_change_ca = pd.read_sql(query_price_change_ca, engine)
        top_10_price_change_ca = df_price_change_ca.to_dict('records')
        print("Top 10 Price Changes (CA):\n", top_10_price_change_ca)

        # Top 10 Largest Stock Changes in US
        query_stock_change_us = f"""
            SELECT sku, MAX(stock) - MIN(stock) as stock_change
            FROM DirectDialUSHistory
            WHERE timestamp >= '{start_date_us_str}'
            GROUP BY sku
            ORDER BY stock_change DESC
            LIMIT 10
        """
        df_stock_change_us = pd.read_sql(query_stock_change_us, engine)
        top_10_stock_change_us = df_stock_change_us.to_dict('records')
        print("Top 10 Stock Changes (US):\n", top_10_stock_change_us)

        # Top 10 Largest Stock Changes in CA
        query_stock_change_ca = f"""
            SELECT sku, MAX(stock) - MIN(stock) as stock_change
            FROM DirectDialCAHistory
            WHERE timestamp >= '{start_date_ca_str}'
            GROUP BY sku
            ORDER BY stock_change DESC
            LIMIT 10
        """
        df_stock_change_ca = pd.read_sql(query_stock_change_ca, engine)
        top_10_stock_change_ca = df_stock_change_ca.to_dict('records')
        print("Top 10 Stock Changes (CA):\n", top_10_stock_change_ca)

        return (total_days_tracked_text, last_update_time_text, total_products_text, total_brands_text,
                top_10_price_change_us, top_10_price_change_ca, top_10_stock_change_us, top_10_stock_change_ca)
    else:
        return dash.no_update



# Callback for Page 2 to display the overview table
@app.callback(
    [Output('edit-overview-table', 'columns'),
     Output('edit-overview-table', 'data')],
    [Input('edit-dropdown', 'value')]
)
def update_edit_overview_table(selected_table):
    if selected_table:
        query = f"SELECT * FROM {selected_table}"
        df = pd.read_sql(query, engine)
        columns = [{"name": i, "id": i} for i in df.columns]
        data = df.to_dict('records')
        return columns, data
    return [], []

@app.callback(
    [Output('overview-table', 'columns'),
     Output('overview-table', 'data')],
    [Input('overview-table-dropdown', 'value')]
)
def update_overview_table(selected_table):
    if selected_table:
        query = f"SELECT * FROM {selected_table}"
        df = pd.read_sql(query, engine)
        columns = [{"name": i, "id": i} for i in df.columns]
        data = df.to_dict('records')
        return columns, data
    return [], []

# Callbacks for Page 1 - Product Analysis
@app.callback(
    Output('page-1-brand-dropdown', 'options'),
    Input('page-1-table-dropdown', 'value')
)
def update_brand_dropdown(selected_table):
    if selected_table:
        query = f"SELECT DISTINCT brand FROM {selected_table}"
        df = pd.read_sql(query, engine)
        options = [{'label': brand, 'value': brand} for brand in df['brand']]
        return options
    return []

@app.callback(
    Output('page-1-sku-dropdown', 'options'),
    [Input('page-1-brand-dropdown', 'value'),
     Input('page-1-table-dropdown', 'value')]
)
def update_sku_dropdown(selected_brand, selected_table):
    if selected_brand and selected_table:
        query = f"SELECT DISTINCT sku FROM {selected_table} WHERE brand = :brand"
        df = pd.read_sql(query, engine, params={"brand": selected_brand})

        options = [{'label': sku, 'value': sku} for sku in df['sku']]
        return options
    return []

@app.callback(
    [Output('page-1-product-table', 'columns'),
     Output('page-1-product-table', 'data')],
    [Input('page-1-sku-dropdown', 'value'),
     Input('page-1-table-dropdown', 'value')]
)
def update_product_table(selected_sku, selected_table):
    if selected_sku and selected_table:
        query = f"SELECT * FROM {selected_table} WHERE sku = :sku"
        df = pd.read_sql(query, engine, params={"sku": selected_sku})
        columns = [{"name": i, "id": i} for i in df.columns]
        data = df.to_dict('records')
        return columns, data
    return [], []

@app.callback(
    [Output('page-1-price-history-table', 'columns'),
     Output('page-1-price-history-table', 'data')],
    [Input('page-1-sku-dropdown', 'value'),
     Input('page-1-table-dropdown', 'value'),
     Input('page-1-date-granularity-dropdown', 'value')]
)
def update_price_history_table(selected_sku, selected_table, granularity):
    if selected_sku and selected_table and granularity:
        history_table = f"{selected_table}History"
        query = f"SELECT sku, timestamp, price FROM {history_table} WHERE sku = '{selected_sku}'"
        df = pd.read_sql(query, engine)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        numeric_df = df[['price']].resample(granularity).mean().reset_index()
        numeric_df['sku'] = selected_sku
        pivot_df = numeric_df.pivot_table(index='sku', columns='timestamp', values='price', aggfunc='first')
        pivot_df.columns = [str(col) for col in pivot_df.columns]
        pivot_df.reset_index(inplace=True)
        sorted_columns = ['sku'] + sorted([col for col in pivot_df.columns if col != 'sku'], reverse=True)
        pivot_df = pivot_df[sorted_columns]
        columns = [{"name": col, "id": col} for col in pivot_df.columns]
        data = pivot_df.to_dict('records')

        return columns, data
    return [], []

@app.callback(
    [Output('page-1-stock-history-table', 'columns'),
     Output('page-1-stock-history-table', 'data')],
    [Input('page-1-sku-dropdown', 'value'),
     Input('page-1-table-dropdown', 'value'),
     Input('page-1-date-granularity-dropdown', 'value')]
)
def update_stock_history_table(selected_sku, selected_table, granularity):
    if selected_sku and selected_table and granularity:
        history_table = f"{selected_table}History"
        query = f"SELECT sku, timestamp, stock FROM {history_table} WHERE sku = '{selected_sku}'"
        df = pd.read_sql(query, engine)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        numeric_df = df[['stock']].resample(granularity).mean().reset_index()
        numeric_df['sku'] = selected_sku
        pivot_df = numeric_df.pivot_table(index='sku', columns='timestamp', values='stock', aggfunc='first')
        pivot_df.columns = [str(col) for col in pivot_df.columns]
        pivot_df.reset_index(inplace=True)
        sorted_columns = ['sku'] + sorted([col for col in pivot_df.columns if col != 'sku'], reverse=True)
        pivot_df = pivot_df[sorted_columns]
        columns = [{"name": col, "id": col} for col in pivot_df.columns]
        data = pivot_df.to_dict('records')

        return columns, data
    return [], []
@app.callback(
    Output('page-1-price-history-graph', 'figure'),
    [Input('page-1-sku-dropdown', 'value'),
     Input('page-1-table-dropdown', 'value')]
)
def update_price_history_graph(selected_sku, selected_table):
    if not selected_sku or not selected_table:
        return {}

    # Use dynamic table name based on the selected table
    history_table = f"{selected_table}History"
    query = f"SELECT sku, timestamp, price FROM {history_table} WHERE sku = '{selected_sku}'"
    df_price = pd.read_sql(query, engine)

    # Pivot and prepare the data for the graph
    pivot_df = df_price.pivot_table(index='sku', columns='timestamp', values='price', aggfunc='first')
    pivot_df.reset_index(inplace=True)
    pivot_df = pivot_df.sort_index(axis=1, ascending=False)
    
    if pivot_df.empty or selected_sku not in pivot_df['sku'].values:
        return {}

    sku_data = pivot_df[pivot_df['sku'] == selected_sku].iloc[0, 1:]

    # Set Y-axis range dynamically with buffer
    y_min = (min(sku_data.values) // 10) * 10 - 10  # Round down to the nearest 10 and subtract 10
    y_max = (max(sku_data.values) // 10) * 10 + 10  # Round up to the nearest 10 and add 10

    # Create figure with formatted x-axis and y-axis
    figure = {
        'data': [
            {
                'x': list(sku_data.index),  # Dates on the X-axis
                'y': sku_data.values,  # Price values on the Y-axis
                'type': 'line',
                'name': 'Price'
            }
        ],
        'layout': {
            'title': 'Price History Over Time',
            'xaxis': {
                'title': 'Date',
                'tickformat': '%b %d, %Y',  # Display date as 'Sep 30, 2024'
                'tickmode': 'linear',
                'dtick': 86400000.0,  # Interval of one day in milliseconds
            },
            'yaxis': {
                'title': 'Price',
                'tickformat': ',d',  # Format to display as whole dollars
                'tickmode': 'linear',
                'dtick': 10,  # Show tick marks every 10 units (10 dollars)
                'range': [y_min, y_max]  # Set the Y-axis range dynamically
            },
            'height': 450,
            'margin': {'t': 50, 'b': 50, 'l': 50, 'r': 50}  # Adjust margins as needed
        }
    }
    return figure

@app.callback(
    Output('page-1-stock-history-graph', 'figure'),
    [Input('page-1-sku-dropdown', 'value'),
     Input('page-1-table-dropdown', 'value')]
)
def update_stock_history_graph(selected_sku, selected_table):
    if not selected_sku or not selected_table:
        return {}

    # Use dynamic table name based on the selected table
    history_table = f"{selected_table}History"
    query = f"SELECT sku, timestamp, stock FROM {history_table} WHERE sku = '{selected_sku}'"
    df_stock = pd.read_sql(query, engine)

    # Pivot and prepare the data for the graph
    pivot_df = df_stock.pivot_table(index='sku', columns='timestamp', values='stock', aggfunc='first')
    pivot_df.reset_index(inplace=True)
    pivot_df = pivot_df.sort_index(axis=1, ascending=False)

    if pivot_df.empty or selected_sku not in pivot_df['sku'].values:
        return {}

    sku_data = pivot_df[pivot_df['sku'] == selected_sku].iloc[0, 1:]

    # Calculate Y-axis range dynamically
    y_min = min(sku_data.values) - 5  # Subtract a buffer from the minimum
    y_max = max(sku_data.values) + 5  # Add a buffer to the maximum

    # Calculate a suitable dtick based on the range of values
    range_diff = y_max - y_min
    if range_diff <= 10:
        dtick = 1  # Use a small interval for smaller ranges
    elif range_diff <= 50:
        dtick = 5  # Medium interval for moderate ranges
    else:
        dtick = 10  # Larger interval for larger ranges

    # Create the figure with dynamic Y-axis range and tick settings
    figure = {
        'data': [
            {
                'x': list(sku_data.index),  # Dates on the X-axis
                'y': sku_data.values,  # Stock values on the Y-axis
                'type': 'line',
                'name': 'Stock'
            }
        ],
        'layout': {
            'title': 'Stock History Over Time',
            'xaxis': {
                'title': 'Date',
                'tickformat': '%b %d, %Y',  # Display date as 'Sep 30, 2024'
                'tickmode': 'linear',
                'dtick': 86400000.0,  # Interval of one day in milliseconds
            },
            'yaxis': {
                'title': 'Stock',
                'tickformat': ',d',  # Format to display as whole numbers
                'tickmode': 'linear',
                'dtick': dtick,  # Set the dynamic tick interval
                'range': [y_min, y_max]  # Set the dynamic Y-axis range
            },
            'height': 450,
            'margin': {'t': 50, 'b': 50, 'l': 50, 'r': 50}  # Adjust margins as needed
        }
    }
    return figure

@app.callback(
    Output("download-csv", "data"),
    Input("export-csv-button", "n_clicks"),
    State("overview-table", "data"),
    prevent_initial_call=True
)
def download_csv(n_clicks, table_data):
    if n_clicks and table_data:
        df = pd.DataFrame(table_data)
        return send_data_frame(df.to_csv, "table_data.csv")
    
@app.callback(
    Output("edit-table-store", "data"),
    Input("save-changes-button", "n_clicks"),
    State("edit-overview-table", "data"),
    State("edit-dropdown", "value"),
    prevent_initial_call=True
)
def save_changes_to_db(n_clicks, rows, table_name):
    if n_clicks and table_name:
        # Convert rows back to DataFrame
        df = pd.DataFrame(rows)
        
        # Save changes to the database (this will overwrite the table)
        df.to_sql(table_name, engine, if_exists='replace', index=False)
        return rows
    return rows
    
# Run the application
if __name__ == '__main__':
    app.run_server(debug=True)