
# callbacks.py - Dash Callback Functions

from dash.dependencies import Input, Output, State
from dash import dcc, html, dash_table
import pandas as pd
from sqlalchemy import create_engine

# Database connection setup (reused from config)
engine = create_engine('sqlite:///products.db')

def register_callbacks(app):
    @app.callback(
        Output('output-container', 'children'),
        [Input('table-dropdown', 'value')]
    )
    def update_table(selected_table):
        if selected_table:
            query = f"SELECT * FROM {selected_table}"
            df = pd.read_sql(query, engine)
            return dash_table.DataTable(
                columns=[{'name': i, 'id': i} for i in df.columns],
                data=df.to_dict('records')
            )
        return "Please select a table to display data."
    



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
        Input('table-dropdown', 'value'),
        Input('date-granularity-dropdown', 'value')]
    )
    def update_price_history_table(selected_sku, selected_table, granularity):
        if selected_sku and selected_table and granularity:
            # Create the history table name dynamically
            history_table = f"{selected_table}History"
            query = f"SELECT sku, timestamp, price FROM {history_table} WHERE sku = '{selected_sku}'"
            df = pd.read_sql(query, engine)

            # Ensure 'timestamp' is in datetime format
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            # Step 1: Set 'timestamp' as the index for resampling
            df.set_index('timestamp', inplace=True)

            # Step 2: Resample the numeric columns only based on the selected granularity
            numeric_df = df[['price']].resample(granularity).mean().reset_index()  # Resample only the 'price' column

            # Step 3: Retain 'sku' and assign it back to the resampled DataFrame
            # 'sku' is the same for all rows, so we can assign it directly
            numeric_df['sku'] = selected_sku

            # Step 4: Pivot the resampled DataFrame to have 'timestamp' as columns
            pivot_df = numeric_df.pivot_table(index='sku', columns='timestamp', values='price', aggfunc='first')

            # Step 5: Flatten the MultiIndex columns for better readability
            pivot_df.columns = [str(col) for col in pivot_df.columns]

            # Step 6: Reset the index to make 'sku' a column again
            pivot_df.reset_index(inplace=True)

            # Step 7: Sort columns by date in descending order
            sorted_columns = ['sku'] + sorted([col for col in pivot_df.columns if col != 'sku'], reverse=True)
            pivot_df = pivot_df[sorted_columns]  # Reorder the columns

            # Step 8: Format the columns and data for Dash DataTable
            columns = [{"name": col, "id": col} for col in pivot_df.columns]
            data = pivot_df.to_dict('records')

            return columns, data
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
            query = f"SELECT sku, timestamp, stock FROM {history_table} WHERE sku = '{selected_sku}'"
            df = pd.read_sql(query, engine)
            pivot_df = df.pivot_table(index='sku', columns='timestamp', values='stock', aggfunc='first')
            pivot_df.columns = [str(col) for col in pivot_df.columns]
            pivot_df.reset_index(inplace=True)
            sorted_columns = ['sku'] + sorted([col for col in pivot_df.columns if col != 'sku'], reverse=True)
            pivot_df = pivot_df[sorted_columns]
            columns = [{"name": col, "id": col} for col in pivot_df.columns]
            data = pivot_df.to_dict('records')
            return columns, data
        return [], []

    @app.callback(
        Output('price-history-graph', 'figure'),
        [Input('sku-dropdown', 'value'),
        Input('table-dropdown', 'value')]
    )
    def update_price_history_graph(selected_sku, selected_table):
        if not selected_sku or not selected_table:
            return {}
        history_table = f"{selected_table}History"
        query = f"SELECT sku, timestamp, price FROM {history_table} WHERE sku = '{selected_sku}'"
        df_price = pd.read_sql(query, engine)
        pivot_df = df_price.pivot_table(index='sku', columns='timestamp', values='price', aggfunc='first')
        pivot_df.reset_index(inplace=True)
        pivot_df = pivot_df.sort_index(axis=1, ascending=False)
        if pivot_df.empty or selected_sku not in pivot_df['sku'].values:
            return {}

        sku_data = pivot_df[pivot_df['sku'] == selected_sku].iloc[0, 1:]
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
                'xaxis': {'title': 'Date'},
                'yaxis': {'title': 'Price'},
                'height': 450
            }
        }
        return figure

    @app.callback(
        Output('stock-history-graph', 'figure'),
        [Input('sku-dropdown', 'value'),
        Input('table-dropdown', 'value')]
    )
    def update_stock_history_graph(selected_sku, selected_table):
        if not selected_sku or not selected_table:
            return {}
        history_table = f"{selected_table}History"
        query = f"SELECT sku, timestamp, stock FROM {history_table} WHERE sku = '{selected_sku}'"
        df_stock = pd.read_sql(query, engine)
        pivot_df = df_stock.pivot_table(index='sku', columns='timestamp', values='stock', aggfunc='first')
        pivot_df.reset_index(inplace=True)
        pivot_df = pivot_df.sort_index(axis=1, ascending=False)
        if pivot_df.empty or selected_sku not in pivot_df['sku'].values:
            return {}

        sku_data = pivot_df[pivot_df['sku'] == selected_sku].iloc[0, 1:]
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
                'xaxis': {'title': 'Date'},
                'yaxis': {'title': 'Stock'},
                'height': 450
            }
        }
        return figure
