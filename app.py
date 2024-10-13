import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import pandas as pd
from sqlalchemy import create_engine
import dash_bootstrap_components as dbc
import pandas as pd
from dash.dcc import send_data_frame
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager



DB_PATH = 'sqlite:///products.db'
engine = create_engine(DB_PATH, pool_size=10, max_overflow=20, pool_pre_ping=True)
app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
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
                ], style={'marginBottom': '30px'})  # Margin added here
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Weekly Statistics", style={'fontWeight': 'bold'}),
                    dbc.CardBody(
                        [
                            html.P(id='total-new-products', style={'fontSize': '18px'}),
                        ]
                    )
                ], style={'marginBottom': '30px'})  # Margin added here
            ], width=6),
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Top 10 Largest Price Changes (US)", style={'fontWeight': 'bold'}),
                    dbc.CardBody(
                        dash_table.DataTable(
                            id='top-10-price-change-us',
                            columns=[{'name': 'SKU', 'id': 'sku'}, {'name': 'Price Change', 'id': 'price_change'}],
                            data=[],
                            style_table={'height': '350px', 'overflowY': 'auto'},
                            style_cell={'textAlign': 'left', 'padding': '5px', 'fontFamily': 'Arial'},
                            style_header={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'},
                        )
                    )
                ], style={'marginBottom': '30px'})  # Margin added here
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Top 10 Largest Price Changes (CA)", style={'fontWeight': 'bold'}),
                    dbc.CardBody(
                        dash_table.DataTable(
                            id='top-10-price-change-ca',
                            columns=[{'name': 'SKU', 'id': 'sku'}, {'name': 'Price Change', 'id': 'price_change'}],
                            data=[],
                            style_table={'height': '350px', 'overflowY': 'auto'},
                            style_cell={'textAlign': 'left', 'padding': '5px', 'fontFamily': 'Arial'},
                            style_header={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'},
                        )
                    )
                ], style={'marginBottom': '30px'})  # Margin added here
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
                            data=[],
                            style_table={'height': '350px', 'overflowY': 'auto'},
                            style_cell={'textAlign': 'left', 'padding': '5px', 'fontFamily': 'Arial'},
                            style_header={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'},
                        )
                    )
                ], style={'marginBottom': '30px'})  # Margin added here
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Top 10 Largest Stock Changes (CA)", style={'fontWeight': 'bold'}),
                    dbc.CardBody(
                        dash_table.DataTable(
                            id='top-10-stock-change-ca',
                            columns=[{'name': 'SKU', 'id': 'sku'}, {'name': 'stock_change', 'id': 'stock_change'}],
                            data=[],
                            style_table={'height': '350px', 'overflowY': 'auto'},
                            style_cell={'textAlign': 'left', 'padding': '5px', 'fontFamily': 'Arial'},
                            style_header={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'},
                        )
                    )
                ], style={'marginBottom': '30px'})  # Margin added here
            ], width=6),
        ]),
    ]
)

page1_layout = dbc.Container(
    fluid=True,
    style={'padding': '20px'},
    children=[
        html.H1("Individual Product Analysis", style={'textAlign': 'center', 'marginBottom': '40px', 'fontSize': '32px', 'fontWeight': 'bold'}),
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
                            options=[],
                            placeholder="Select a Brand",
                            style={'marginBottom': '20px'}
                        ),
                        html.Label("Select a SKU:", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='page-1-sku-dropdown',
                            options=[],
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
                            value='D',
                            placeholder='Select Date Granularity'
                        ),
                        dbc.Button("Apply Filters", id='apply-filters-button', color='primary', style={'marginTop': '20px'}),
                    ])
                ], style={'marginBottom': '30px'})
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Product Details", style={'fontWeight': 'bold'}),
                    dbc.CardBody(
                        dash_table.DataTable(
                            id='page-1-product-table',
                            columns=[],
                            data=[],
                            style_table={'height': '300px', 'overflowY': 'auto'},
                            style_cell={'textAlign': 'left', 'padding': '5px', 'fontFamily': 'Arial'},
                            style_header={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'},
                        ),
                    )
                ], style={'marginBottom': '30px'})
            ], width=9)
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Price History Table", style={'fontWeight': 'bold'}),
                    dbc.CardBody(
                        dash_table.DataTable(
                            id='page-1-price-history-table',
                            columns=[],
                            data=[],
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
                            columns=[],
                            data=[],
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
                            id='page-1-price-history-graph',
                            style={'height': '450px'}
                        )
                    )
                ], style={'marginBottom': '30px'})
            ], width=6),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Stock History Graph", style={'fontWeight': 'bold'}),
                    dbc.CardBody(
                        dcc.Graph(
                            id='page-1-stock-history-graph',
                            style={'height': '450px'}
                        )
                    )
                ], style={'marginBottom': '30px'})
            ], width=6),
        ])
    ]
)
page2_layout = dbc.Container(
    fluid=True,
    style={'padding': '20px'},
    children=[
        html.H1("Database Overview", style={'textAlign': 'center', 'marginBottom': '40px', 'fontSize': '32px', 'fontWeight': 'bold'}),
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
        dbc.Row([dbc.Col(dbc.Input(id='search-bar', placeholder='Search for products...', type='text', style={'marginBottom': '20px'}), width=12)]),
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
                            columns=[],
                            data=[], 
                            page_size=2000,
                            virtualization=True,
                            style_table={'height': '300px', 'overflowY': 'auto'},
                            style_cell={'textAlign': 'left', 'padding': '5px', 'fontFamily': 'Arial'},
                            style_header={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'},
                            fixed_rows={'headers': True},
                        ),
                    )
                ], style={'marginBottom': '30px'})
            ], width=12) 
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Button("Export to CSV", id="export-csv-button", color="primary", style={'marginTop': '20px'}),
                dcc.Download(id="download-csv")
            ], width=12)
        ])
    ]
)
page3_layout = dbc.Container(
    fluid=True,
    style={'padding': '20px'},
    children=[
        html.H1("Edit Database", style={'textAlign': 'center', 'marginBottom': '40px', 'fontSize': '32px', 'fontWeight': 'bold'}),
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
        dbc.Row([dbc.Col(dbc.Input(id='search-bar', placeholder='Search for products...', type='text', style={'marginBottom': '20px'}), width=12)]),
         
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Over", style={'fontWeight': 'bold'}),
                    dbc.CardBody(
                        dash_table.DataTable(
                            id='edit-overview-table',
                            columns=[],
                            data=[], 
                            page_size=2000,
                            virtualization=True,
                            editable=True,
                            row_deletable=True,
                            style_table={'height': '300px', 'overflowY': 'auto'},
                            style_cell={'textAlign': 'left', 'padding': '5px', 'fontFamily': 'Arial'},
                            style_header={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'},
                            fixed_rows={'headers': True},
                        ),
                    )
                ], style={'marginBottom': '30px'})
            ], width=12) 
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Button("Add Row", id="add-row-button", color="success", style={'marginTop': '20px', 'marginRight': '10px'}),
                dbc.Button("Save Changes", id="save-changes-button", color="primary", style={'marginTop': '20px'}),
                dbc.Button("Export to CSV", id="export-edit-csv-button", color="secondary", style={'marginTop': '20px', 'marginLeft': '10px'}),
                dcc.Download(id="download-edit-csv")
            ], width=12)
        ]),
        dcc.Store(id='edit-table-store'),
        dbc.Row([
            dbc.Col([
                dbc.Button("Export to CSV", id="export-csv-button", color="primary", style={'marginTop': '20px'}),
                dcc.Download(id="download-csv")
            ], width=12)
        ])
    ]
)


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
     Output('total-new-products', 'children'),
     Output('top-10-price-change-us', 'data'),
     Output('top-10-price-change-ca', 'data'),
     Output('top-10-stock-change-us', 'data'),
     Output('top-10-stock-change-ca', 'data')],
    [Input('url', 'pathname')]
)
def update_home_stats(pathname):
    if pathname != '/':
        return dash.no_update

    # Initialize variables to handle the data aggregation and calculations.
    total_days_tracked_text = "Total number of days tracked: 0"
    last_update_time_text = "Last update time: No data available"
    total_products_text = "Total number of products: 0"
    total_brands_text = "Total number of brands: 0"
    total_new_products_text = "Total number of new products: 0"
    top_10_price_change_us = []
    top_10_price_change_ca = []
    top_10_stock_change_us = []
    top_10_stock_change_ca = []

    # Calculate today's date and one week before today for filtering
    today = pd.Timestamp.now().normalize()
    one_week_ago = today - pd.Timedelta(days=7)

    with get_db_connection() as connection:
        # Get combined stats and metrics for both US and CA history tables without 'brand'.
        combined_query = """
            SELECT 
                MIN(timestamp) as min_time, 
                MAX(timestamp) as max_time, 
                COUNT(DISTINCT sku) as total_products,
                CASE 
                    WHEN source = 'DirectDialUSHistory' THEN 'US' 
                    ELSE 'CA' 
                END as region
            FROM (
                SELECT timestamp, sku, 'DirectDialUSHistory' as source FROM DirectDialUSHistory
                UNION ALL
                SELECT timestamp, sku, 'DirectDialCAHistory' as source FROM DirectDialCAHistory
            )
            GROUP BY region
        """
        df_combined = pd.read_sql(combined_query, connection)

        # Extract information for US and CA
        us_data = df_combined[df_combined['region'] == 'US'].iloc[0] if 'US' in df_combined['region'].values else None
        ca_data = df_combined[df_combined['region'] == 'CA'].iloc[0] if 'CA' in df_combined['region'].values else None

        # Calculate total days tracked and last update time
        min_time_us = pd.to_datetime(us_data['min_time'], errors='coerce') if us_data is not None else None
        max_time_us = pd.to_datetime(us_data['max_time'], errors='coerce') if us_data is not None else None
        min_time_ca = pd.to_datetime(ca_data['min_time'], errors='coerce') if ca_data is not None else None
        max_time_ca = pd.to_datetime(ca_data['max_time'], errors='coerce') if ca_data is not None else None

        # Calculate min and max time for all regions and determine tracking period
        min_time = min(filter(pd.notna, [min_time_us, min_time_ca]))
        max_time = max(filter(pd.notna, [max_time_us, max_time_ca]))
        if min_time and max_time:
            total_days_tracked = (max_time - min_time).days + 1
            total_days_tracked_text = f"Total number of days tracked: {total_days_tracked}"
            last_update_time_text = f"Last update time: {max_time}"

        # Calculate total products
        total_products = (us_data['total_products'] if us_data is not None else 0) + (ca_data['total_products'] if ca_data is not None else 0)
        total_products_text = f"Total number of products: {total_products}"

        # Query for total brands separately from the `DirectDialUS` and `DirectDialCA` tables
        query_brands_us = "SELECT COUNT(DISTINCT brand) as total_brands FROM DirectDialUS"
        query_brands_ca = "SELECT COUNT(DISTINCT brand) as total_brands FROM DirectDialCA"
        df_brands_us = pd.read_sql(query_brands_us, connection)
        df_brands_ca = pd.read_sql(query_brands_ca, connection)
        total_brands = (df_brands_us['total_brands'].iloc[0] if not df_brands_us.empty else 0) + \
                       (df_brands_ca['total_brands'].iloc[0] if not df_brands_ca.empty else 0)
        total_brands_text = f"Total number of brands: {total_brands}"

        # Calculate the total number of new products added within the last week
        query_new_products_us = f"""
            SELECT COUNT(DISTINCT sku) as new_products
            FROM DirectDialUS
            WHERE date_added >= '{one_week_ago.strftime('%Y-%m-%d')}'
        """
        query_new_products_ca = f"""
            SELECT COUNT(DISTINCT sku) as new_products
            FROM DirectDialCA
            WHERE date_added >= '{one_week_ago.strftime('%Y-%m-%d')}'
        """
        df_new_products_us = pd.read_sql(query_new_products_us, connection)
        df_new_products_ca = pd.read_sql(query_new_products_ca, connection)
        total_new_products = (df_new_products_us['new_products'].iloc[0] if not df_new_products_us.empty else 0) + \
                             (df_new_products_ca['new_products'].iloc[0] if not df_new_products_ca.empty else 0)
        total_new_products_text = f"Total number of new products: {total_new_products}"

        # Calculate start dates for the last 7 days or the min time in case of less data
        start_date_us = min_time_us if min_time_us and min_time_us >= max_time_us - pd.Timedelta(days=7) else max_time_us - pd.Timedelta(days=7)
        start_date_ca = min_time_ca if min_time_ca and min_time_ca >= max_time_ca - pd.Timedelta(days=7) else max_time_ca - pd.Timedelta(days=7)

        # Convert datetime to string format for SQL queries
        start_date_us_str = start_date_us.strftime('%Y-%m-%d') if start_date_us else None
        start_date_ca_str = start_date_ca.strftime('%Y-%m-%d') if start_date_ca else None

        # Queries for top 10 price and stock changes
        if start_date_us_str:
            query_price_change_us = f"""
                SELECT sku, MAX(price) - MIN(price) as price_change
                FROM DirectDialUSHistory
                WHERE timestamp >= '{start_date_us_str}'
                GROUP BY sku
                ORDER BY price_change DESC
                LIMIT 10
            """
            df_price_change_us = pd.read_sql(query_price_change_us, connection)
            top_10_price_change_us = df_price_change_us.to_dict('records')

            query_stock_change_us = f"""
                SELECT sku, MAX(stock) - MIN(stock) as stock_change
                FROM DirectDialUSHistory
                WHERE timestamp >= '{start_date_us_str}'
                GROUP BY sku
                ORDER BY stock_change DESC
                LIMIT 10
            """
            df_stock_change_us = pd.read_sql(query_stock_change_us, connection)
            top_10_stock_change_us = df_stock_change_us.to_dict('records')

        if start_date_ca_str:
            query_price_change_ca = f"""
                SELECT sku, MAX(price) - MIN(price) as price_change
                FROM DirectDialCAHistory
                WHERE timestamp >= '{start_date_ca_str}'
                GROUP BY sku
                ORDER BY price_change DESC
                LIMIT 10
            """
            df_price_change_ca = pd.read_sql(query_price_change_ca, connection)
            top_10_price_change_ca = df_price_change_ca.to_dict('records')

            query_stock_change_ca = f"""
                SELECT sku, MAX(stock) - MIN(stock) as stock_change
                FROM DirectDialCAHistory
                WHERE timestamp >= '{start_date_ca_str}'
                GROUP BY sku
                ORDER BY stock_change DESC
                LIMIT 10
            """
            df_stock_change_ca = pd.read_sql(query_stock_change_ca, connection)
            top_10_stock_change_ca = df_stock_change_ca.to_dict('records')

    return (total_days_tracked_text, last_update_time_text, total_products_text, total_brands_text, total_new_products_text,
            top_10_price_change_us, top_10_price_change_ca, top_10_stock_change_us, top_10_stock_change_ca)

@app.callback(
    [Output('edit-overview-table', 'columns'),
     Output('edit-overview-table', 'data')],
    [Input('edit-dropdown', 'value')]
)
def update_edit_overview_table(selected_table):
    if selected_table:
        query = f"SELECT * FROM {selected_table}"
        
        # Use context manager for database connection
        with get_db_connection() as connection:
            df = pd.read_sql(query, connection)
            
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
        
        # Use context manager for database connection
        with get_db_connection() as connection:
            df = pd.read_sql(query, connection)
            
        columns = [{"name": i, "id": i} for i in df.columns]
        data = df.to_dict('records')
        return columns, data
    return [], []

@app.callback(
    [Output('page-1-product-table', 'columns'),
     Output('page-1-product-table', 'data')],
    [Input('page-1-sku-dropdown', 'value'),
     Input('page-1-table-dropdown', 'value')]
)
def update_product_table(selected_sku, selected_table):
    if selected_sku and selected_table:
        query = f"SELECT * FROM {selected_table} WHERE sku = :sku"

        # Use the updated context manager for the connection
        with get_db_connection() as connection:
            # Use the raw connection with pandas.read_sql
            df = pd.read_sql(query, connection, params={"sku": selected_sku})

        columns = [{"name": i, "id": i} for i in df.columns]
        data = df.to_dict('records')
        return columns, data

    return [], []

@app.callback(
    [Output('page-1-brand-dropdown', 'options'),
     Output('page-1-sku-dropdown', 'options')],
    [Input('page-1-table-dropdown', 'value'),
     Input('page-1-brand-dropdown', 'value')]
)
def update_dropdowns(selected_table, selected_brand):
    # Initialize empty options
    brand_options, sku_options = [], []

    # If a table is selected, query for brand options
    if selected_table:
        query_brand = f"SELECT DISTINCT brand FROM {selected_table}"
        with get_db_connection() as connection:
            df_brand = pd.read_sql(query_brand, connection)
        brand_options = [{'label': brand, 'value': brand} for brand in df_brand['brand']]

    # If a brand is selected, query for SKU options
    if selected_brand and selected_table:
        query_sku = f"SELECT DISTINCT sku FROM {selected_table} WHERE brand = :brand"
        with get_db_connection() as connection:
            df_sku = pd.read_sql(query_sku, connection, params={"brand": selected_brand})
        sku_options = [{'label': sku, 'value': sku} for sku in df_sku['sku']]

    return brand_options, sku_options

@app.callback(
    [Output('page-1-price-history-table', 'columns'),
     Output('page-1-price-history-table', 'data'),
     Output('page-1-stock-history-table', 'columns'),
     Output('page-1-stock-history-table', 'data')],
    [Input('page-1-sku-dropdown', 'value'),
     Input('page-1-table-dropdown', 'value'),
     Input('page-1-date-granularity-dropdown', 'value')],
    prevent_initial_call=True
)
def update_history_tables(selected_sku, selected_table, granularity):
    # Initialize empty columns and data for both tables
    price_columns, price_data = [], []
    stock_columns, stock_data = [], []

    if selected_sku and selected_table and granularity:
        history_table = f"{selected_table}History"

        # Price History Query
        query_price = f"SELECT sku, timestamp, price FROM {history_table} WHERE sku = '{selected_sku}'"
        # Stock History Query
        query_stock = f"SELECT sku, timestamp, stock FROM {history_table} WHERE sku = '{selected_sku}'"

        with get_db_connection() as connection:
            df_price = pd.read_sql(query_price, connection)
            df_stock = pd.read_sql(query_stock, connection)

        # Process Price History Table
        if not df_price.empty:
            df_price['timestamp'] = pd.to_datetime(df_price['timestamp']).dt.normalize()
            df_price.set_index('timestamp', inplace=True)
            numeric_price_df = df_price[['price']].resample(granularity).mean().reset_index()
            numeric_price_df['sku'] = selected_sku
            pivot_price_df = numeric_price_df.pivot_table(index='sku', columns='timestamp', values='price', aggfunc='first')
            pivot_price_df.columns = [col.strftime('%Y-%m-%d') for col in pivot_price_df.columns]
            pivot_price_df.reset_index(inplace=True)
            sorted_columns = ['sku'] + sorted([col for col in pivot_price_df.columns if col != 'sku'], reverse=True)
            pivot_price_df = pivot_price_df[sorted_columns]
            price_columns = [{"name": col, "id": col} for col in pivot_price_df.columns]
            price_data = pivot_price_df.to_dict('records')

        # Process Stock History Table
        if not df_stock.empty:
            df_stock['timestamp'] = pd.to_datetime(df_stock['timestamp']).dt.normalize()
            df_stock.set_index('timestamp', inplace=True)
            numeric_stock_df = df_stock[['stock']].resample(granularity).mean().reset_index()
            numeric_stock_df['sku'] = selected_sku
            pivot_stock_df = numeric_stock_df.pivot_table(index='sku', columns='timestamp', values='stock', aggfunc='first')
            pivot_stock_df.columns = [col.strftime('%Y-%m-%d') for col in pivot_stock_df.columns]
            pivot_stock_df.reset_index(inplace=True)
            sorted_columns = ['sku'] + sorted([col for col in pivot_stock_df.columns if col != 'sku'], reverse=True)
            pivot_stock_df = pivot_stock_df[sorted_columns]
            stock_columns = [{"name": col, "id": col} for col in pivot_stock_df.columns]
            stock_data = pivot_stock_df.to_dict('records')

    return price_columns, price_data, stock_columns, stock_data

@app.callback(
    Output('page-1-price-history-graph', 'figure'),
    [Input('page-1-sku-dropdown', 'value'),
     Input('page-1-table-dropdown', 'value')]
)
def update_price_history_graph(selected_sku, selected_table):
    if not selected_sku or not selected_table:
        return {}
    history_table = f"{selected_table}History"
    query = f"SELECT sku, timestamp, price FROM {history_table} WHERE sku = '{selected_sku}'"
    
    # Use context manager to manage the database connection
    with get_db_connection() as connection:
        df_price = pd.read_sql(query, connection)
        
    pivot_df = df_price.pivot_table(index='sku', columns='timestamp', values='price', aggfunc='first')
    pivot_df.reset_index(inplace=True)
    pivot_df = pivot_df.sort_index(axis=1, ascending=False)
    
    if pivot_df.empty or selected_sku not in pivot_df['sku'].values:
        return {}

    sku_data = pivot_df[pivot_df['sku'] == selected_sku].iloc[0, 1:]
    y_min = (min(sku_data.values) // 10) * 10 - 10
    y_max = (max(sku_data.values) // 10) * 10 + 10
    figure = {
        'data': [
            {
                'x': list(sku_data.index),
                'y': sku_data.values,
                'type': 'line',
                'name': 'Price'
            }
        ],
        'layout': {
            'title': 'Price History Over Time',
            'xaxis': {
                'title': 'Date',
                'tickformat': '%b %d, %Y',
                'tickmode': 'linear',
                'dtick': 86400000.0,  # Adjust for daily tick marks
            },
            'yaxis': {
                'title': 'Price',
                'tickformat': ',d',
                'tickmode': 'linear',
                'dtick': 10,  # Tick interval of 10 units
                'range': [y_min, y_max]
            },
            'height': 450,
            'margin': {'t': 50, 'b': 50, 'l': 50, 'r': 50}
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
    history_table = f"{selected_table}History"
    query = f"SELECT sku, timestamp, stock FROM {history_table} WHERE sku = '{selected_sku}'"
    
    # Use context manager for database connection
    with get_db_connection() as connection:
        df_stock = pd.read_sql(query, connection)
    
    pivot_df = df_stock.pivot_table(index='sku', columns='timestamp', values='stock', aggfunc='first')
    pivot_df.reset_index(inplace=True)
    pivot_df = pivot_df.sort_index(axis=1, ascending=False)
    
    if pivot_df.empty or selected_sku not in pivot_df['sku'].values:
        return {}

    sku_data = pivot_df[pivot_df['sku'] == selected_sku].iloc[0, 1:]
    y_min = min(sku_data.values) - 5
    y_max = max(sku_data.values) + 5
    range_diff = y_max - y_min
    if range_diff <= 10:
        dtick = 1
    elif range_diff <= 50:
        dtick = 5
    else:
        dtick = 10
    figure = {
        'data': [
            {
                'x': list(sku_data.index),
                'y': sku_data.values,
                'type': 'line',
                'name': 'Stock'
            }
        ],
        'layout': {
            'title': 'Stock History Over Time',
            'xaxis': {
                'title': 'Date',
                'tickformat': '%b %d, %Y',
                'tickmode': 'linear',
                'dtick': 86400000.0,
            },
            'yaxis': {
                'title': 'Stock',
                'tickformat': ',d',
                'tickmode': 'linear',
                'dtick': dtick,
                'range': [y_min, y_max]
            },
            'height': 450,
            'margin': {'t': 50, 'b': 50, 'l': 50, 'r': 50}
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
        df = pd.DataFrame(rows)
        df.to_sql(table_name, engine, if_exists='replace', index=False)
        return rows
    return rows

@contextmanager
def get_db_connection():
    """Context manager to provide a raw database connection from the engine."""
    connection = engine.connect()
    try:
        yield connection
    finally:
        connection.close() 
        
if __name__ == '__main__':
    app.run_server(debug=True)